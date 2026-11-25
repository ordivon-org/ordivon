"""R9 disposable cluster + one-shot local wire fault, never a production DSN."""
from __future__ import annotations
import os
from pathlib import Path
import secrets
import socket
import struct
import subprocess
import sys
import threading

root = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(root / "experiments/pg-transaction-r1"))
from probe import Cluster


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

    def __init__(self, cluster: Cluster, hold=False):
        self.hold = hold
        self.root = cluster.root / ("cancel-proxy" if hold else "ack-proxy")
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
            assert self.cut and self.error is None and not self.thread.is_alive(), self.error
            print("wire fault: native COMMIT acknowledgement discarded exactly once", flush=True)


if __name__ == "__main__":
    cluster = Cluster()
    fault = None
    cancel_fault = None
    result = None
    try:
        cluster.start()
        guard = secrets.token_hex(24)
        subprocess.run(
            cluster.psql + ["-v", "ON_ERROR_STOP=1", "-c",
                            f"CREATE TABLE web_note_fixture_guard(token text); INSERT INTO web_note_fixture_guard VALUES ('{guard}')"],
            env=cluster.env, check=True, timeout=10)
        fault = CommitAckFault(cluster)
        cancel_fault = CommitAckFault(cluster, hold=True)
        env = dict(cluster.env)
        env.update(WEB_NOTE_TEST_SOCKET=str(cluster.root), WEB_NOTE_TEST_USER=cluster.user,
                   WEB_NOTE_TEST_PORT="59439", WEB_NOTE_TEST_NODE=os.environ.get("NODE", "node"),
                   WEB_NOTE_TEST_GUARD=guard, WEB_NOTE_TEST_ACK_PROXY=str(fault.root),
                   WEB_NOTE_TEST_CANCEL_PROXY=str(cancel_fault.root))
        result = subprocess.run(
            ["cargo", "test", "--manifest-path", str(Path(__file__).resolve().parents[1] / "Cargo.toml"),
             "--locked", "--offline", "--test", "native", "--", "--nocapture"],
            env=env, check=False, timeout=180)
    finally:
        try:
            if fault is not None:
                fault.close(require_cut=result is not None and result.returncode == 0)
        finally:
            try:
                if cancel_fault is not None:
                    cancel_fault.close(require_cut=result is not None and result.returncode == 0)
            finally:
                cluster.close()
    raise SystemExit(result.returncode)
