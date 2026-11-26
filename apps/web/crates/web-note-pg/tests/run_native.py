"""R9 disposable cluster + one-shot local wire fault, never a production DSN."""
from __future__ import annotations
import os
import argparse
import json
from pathlib import Path
import secrets
import socket
import struct
import subprocess
import sys
import threading
from contextlib import ExitStack

root = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(root / "experiments/pg-transaction-r1"))
from probe import Cluster
from qualification import discover, print_report


def read_exact(sock: socket.socket, size: int) -> bytes:
    result = bytearray()
    while len(result) < size:
        part = sock.recv(size - len(result))
        if not part:
            raise EOFError("server closed before COMMIT acknowledgement")
        result.extend(part)
    return bytes(result)


class CommitAckFault:
    """Forward the unencrypted local PG protocol; discard only COMMIT ACK."""

    def __init__(self, cluster: Cluster, hold=False, name=None):
        self.hold = hold
        self.root = cluster.root / (name or ("cancel-proxy" if hold else "ack-proxy"))
        self.root.mkdir(mode=0o700)
        self.listener = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        self.listener.bind(str(self.root / ".s.PGSQL.59439"))
        self.listener.listen(1)
        self.listener.settimeout(40)
        self.target = cluster.root / ".s.PGSQL.59439"
        self.cut = False
        self.error: Exception | None = None
        self.thread = threading.Thread(target=self.run, daemon=True)
        self.thread.start()

    def run(self):
        try:
            with self.listener.accept()[0] as frontend, socket.socket(
                socket.AF_UNIX, socket.SOCK_STREAM
            ) as backend:
                backend.connect(str(self.target))

                disconnected = threading.Event()

                def forward():
                    try:
                        while part := frontend.recv(65536):
                            backend.sendall(part)
                    except OSError:
                        pass
                    finally:
                        disconnected.set()

                upstream = threading.Thread(target=forward, daemon=True)
                upstream.start()
                try:
                    while True:
                        header = read_exact(backend, 5)
                        size = struct.unpack("!I", header[1:])[0]
                        if not 4 <= size <= 16 * 1024 * 1024:
                            raise RuntimeError("invalid PG frame")
                        payload = read_exact(backend, size - 4)
                        if header[:1] == b"C" and payload == b"COMMIT\0":
                            self.cut = True
                            if self.hold:
                                (self.root / "commit-reached").write_text("committed")
                                if not disconnected.wait(timeout=10):
                                    raise RuntimeError("caller did not close cancelled carrier")
                            break
                        frontend.sendall(header + payload)
                finally:
                    for carrier in (frontend, backend):
                        try:
                            carrier.shutdown(socket.SHUT_RDWR)
                        except OSError:
                            pass
                    upstream.join(timeout=2)
        except Exception as exc:
            self.error = exc

    def close(self, require_cut: bool):
        self.listener.close()
        self.thread.join(timeout=3)
        if require_cut:
            if not self.cut or self.error is not None or self.thread.is_alive():
                raise RuntimeError(f"required wire fault not confirmed: {self.error}")
            print("wire fault: native COMMIT acknowledgement discarded exactly once", flush=True)


if __name__ == "__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("--lane", choices=["all","native","stateful","concurrent","migration","effect"], default="all")
    args=parser.parse_args()
    targets=("native","stateful","concurrent","migration","effect") if args.lane=="all" else (args.lane,)
    print(f"native qualification scope: {args.lane}", flush=True)
    manifest = Path(__file__).resolve().parents[1] / "Cargo.toml"
    base = ["cargo", "nextest"]
    # Compile and discover before launching any disposable database or wire
    # fixture. Cold builds cannot consume the one-shot listener's deadline.
    build = ["--manifest-path", str(manifest), "--locked", "--offline"]
    env_base = {k: v for k, v in os.environ.items() if not k.startswith(("NEXTEST_", "PG", "PROPTEST_"))}
    subprocess.run(base + ["--version"], env=env_base, check=True, timeout=10)
    selection = ["--tests"] if args.lane=="all" else [arg for target in targets for arg in ("--test",target)]
    discovery = subprocess.run(base + ["list"] + build + selection + ["--message-format","json"],
                   env=env_base, cwd=manifest.parent, check=True, timeout=180, stdout=subprocess.PIPE)
    expected=discover(json.loads(discovery.stdout),targets)
    print("native discovery:", json.dumps({k:sorted(v) for k,v in expected.items()}),flush=True)
    cluster = Cluster()
    result = None
    faults_by_target = {
        "native": [
            ("WEB_NOTE_TEST_ACK_PROXY", "ack-proxy", False),
            ("WEB_NOTE_TEST_CANCEL_PROXY", "cancel-proxy", True),
        ],
        "effect": [
            (f"WEB_{kind.upper()}_TEST_ACK_PROXY", f"{kind}-proxy", False)
            for kind in ("effect", "grant", "revoke", "session", "login", "challenge", "dpop")
        ],
    }
    try:
        cluster.start()
        guard = secrets.token_hex(24)
        subprocess.run(
            cluster.psql + ["-v", "ON_ERROR_STOP=1", "-c",
                            f"CREATE TABLE web_note_fixture_guard(token text); INSERT INTO web_note_fixture_guard VALUES ('{guard}')"],
            env=cluster.env, check=True, timeout=10)
        env = dict(env_base)
        env.update(WEB_NOTE_TEST_SOCKET=str(cluster.root), WEB_NOTE_TEST_USER=cluster.user,
                   WEB_NOTE_TEST_PORT="59439", WEB_NOTE_TEST_NODE=os.environ.get("NODE", "node"),
                   WEB_NOTE_TEST_GUARD=guard)
        for target in targets:
            report = manifest.parent / "target" / "nextest" / target / (target + ".xml")
            report.unlink(missing_ok=True)
            result = None
            target_env = dict(env)
            with ExitStack() as stack:
                for key, name, hold in faults_by_target.get(target, ()):
                    fault = CommitAckFault(cluster, hold=hold, name=name)
                    stack.callback(lambda f=fault: f.close(require_cut=result is not None and result.returncode == 0))
                    target_env[key] = str(fault.root)
                result = subprocess.run(base + ["run"] + build + ["--test", target,
                    "--profile", target, "--no-tests", "fail", "--retries", "0", "--test-threads", "1",
                    "--status-level", "pass", "--success-output", "final"],
                    env=target_env, cwd=manifest.parent, check=False, timeout=180)
            if result.returncode != 0:
                break
            print_report(report, expected[target])
    finally:
        cluster.close()
    if result.returncode == 0:
        print(f"native qualification complete: scope={args.lane}; discovery/JUnit/fixture cleanup confirmed", flush=True)
    raise SystemExit(result.returncode)
