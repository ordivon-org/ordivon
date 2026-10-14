#!/usr/bin/env python3
"""Disposable REAL sing-box process restart/restore acceptance; NO systemd/effect.

Runs only a local loopback HTTP CONNECT fixture and a temporary sing-box
config. Distinct from production Supply-Chain service and Gluetun VPN.
"""
from __future__ import annotations

import argparse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
import socket
import subprocess
import sys
import tempfile
import threading
import time

SOURCE = Path(__file__).resolve().parents[1] / "config/egress.json"
CDN = "production.cloudfront.docker.com"
REGISTRY = "registry-1.docker.io"
BODY = "NV2_RESTART_FIXTURE_OK"


def port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def launch(file: Path, listen: int) -> subprocess.Popen:
    check = subprocess.run(
        ["/usr/bin/sing-box", "check", "-c", str(file)],
        capture_output=True, text=True, timeout=8, check=False,
    )
    if check.returncode:
        raise AssertionError("isolated sing-box check failed: " + check.stderr[-250:])
    p = subprocess.Popen(
        ["/usr/bin/sing-box", "run", "-c", str(file)],
        stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, text=True,
    )
    try:
        for _ in range(90):
            if p.poll() is not None:
                raise AssertionError("sing-box fixture exited before listen")
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(0.1)
                if s.connect_ex(("127.0.0.1", listen)) == 0:
                    return p
            time.sleep(0.03)
        raise AssertionError("sing-box listener did not converge")
    except BaseException:
        stop(p)
        raise


def stop(p: subprocess.Popen | None) -> None:
    if p is None:
        return
    if p.poll() is None:
        p.terminate()
    try:
        p.communicate(timeout=4)
    except subprocess.TimeoutExpired:
        p.kill()
        p.communicate(timeout=3)


def request(listen: int, host: str) -> subprocess.CompletedProcess:
    return subprocess.run([
        "/usr/bin/curl", "-4", "--noproxy", "", "--fail",
        "--silent", "--show-error", "--connect-timeout", "2",
        "--max-time", "4", "-x", f"http://127.0.0.1:{listen}",
        f"http://{host}:443/network-v2-sandbox-recovery",
    ], capture_output=True, text=True, timeout=7, check=False)


def main() -> int:
    arg = argparse.ArgumentParser()
    arg.add_argument("--fault", choices=[
        "before-stop", "after-stop", "after-new-run",
        "candidate-startup-error", "candidate-sigkill",
    ], required=True)
    a = arg.parse_args()

    seen: list[str] = []

    class Upstream(BaseHTTPRequestHandler):
        def do_CONNECT(self):
            seen.append(self.path)
            self.send_response(200, "Connection Established")
            self.end_headers()
            self.connection.settimeout(3)
            data = b""
            while b"\r\n\r\n" not in data and len(data) < 8192:
                block = self.connection.recv(4096)
                if not block:
                    break
                data += block
            if not data.startswith(b"GET "):
                raise AssertionError("expected GET inside CONNECT")
            payload = BODY.encode()
            self.connection.sendall(
                b"HTTP/1.1 200 OK\r\nContent-Length: " +
                str(len(payload)).encode() +
                b"\r\nConnection: close\r\n\r\n" + payload
            )

        def log_message(self, *_args):
            pass

    fixture = ThreadingHTTPServer(("127.0.0.1", 0), Upstream)
    worker = threading.Thread(target=fixture.serve_forever, daemon=True)
    worker.start()
    process = None
    try:
        source = json.loads(SOURCE.read_text(encoding="utf-8"))
        if len(source["inbounds"]) != 1 or len(source["outbounds"]) != 1:
            raise AssertionError("single scoped proxy contract changed")
        if source["route"]["rules"][-1] != {"action": "reject"}:
            raise AssertionError("source catch-all deny absent")
        original = json.loads(json.dumps(source))
        original["inbounds"][0].update(listen="127.0.0.1", listen_port=port())
        original["outbounds"][0].update(server="127.0.0.1", server_port=fixture.server_port)
        listen = original["inbounds"][0]["listen_port"]
        candidate = json.loads(json.dumps(original))
        old = json.loads(json.dumps(original))
        rule = next(r for r in old["route"]["rules"] if r.get("inbound") == ["supply-chain-oci"])
        rule["domain"].remove(CDN)
        if CDN not in next(r for r in candidate["route"]["rules"]
                            if r.get("inbound") == ["supply-chain-oci"])["domain"]:
            raise AssertionError("new CDN host absent")

        def assert_policy(expected_cdn: bool):
            before = len(seen)
            resp = request(listen, CDN)
            if expected_cdn:
                if resp.returncode or resp.stdout != BODY or seen[before:] != [CDN + ":443"]:
                    raise AssertionError("candidate CDN CONNECT did not arrive on local upstream")
            else:
                if resp.returncode == 0 or len(seen) != before:
                    raise AssertionError("old policy CDN deny failed")
            before = len(seen)
            reg = request(listen, REGISTRY)
            if reg.returncode or reg.stdout != BODY or seen[before:] != [REGISTRY + ":443"]:
                raise AssertionError("known registry success lost after restart/rollback")
            before = len(seen)
            unknown = request(listen, "example.com")
            if unknown.returncode == 0 or len(seen) != before:
                raise AssertionError("unknown destination escaped scoped policy")

        with tempfile.TemporaryDirectory(prefix="nv2-r6-process-recovery-") as tmp:
            cfg = Path(tmp) / "egress.json"
            original_file_bytes = (json.dumps(old, separators=(",", ":")) + "\n").encode()
            new_file_bytes = (json.dumps(candidate, separators=(",", ":")) + "\n").encode()
            cfg.write_bytes(original_file_bytes)
            process = launch(cfg, listen)
            assert_policy(False)

            recovery_trigger = None
            try:
                # Real temporary file staging, no host configuration effects.
                cfg.write_bytes(new_file_bytes)
                if a.fault == "before-stop":
                    if process.poll() is not None:
                        raise AssertionError("old process died while staged")
                    raise RuntimeError("injected-before-stop")
                stop(process)
                process = None
                if a.fault == "after-stop":
                    raise RuntimeError("injected-after-stop")
                if a.fault == "candidate-startup-error":
                    cfg.write_text("{ invalid-json", encoding="utf-8")
                    launch(cfg, listen)
                    raise AssertionError("invalid candidate unexpectedly started")
                process = launch(cfg, listen)
                assert_policy(True)
                if a.fault == "candidate-sigkill":
                    process.kill()
                    process.wait(timeout=3)
                    raise RuntimeError("injected-candidate-sigkill")
                if a.fault == "after-new-run":
                    raise RuntimeError("injected-after-new-run")
                raise AssertionError("fault mode did not trigger")
            except (RuntimeError, AssertionError) as error:
                recovery_trigger = type(error).__name__ + ":" + str(error)
            finally:
                # Unconditional recovery path: no planned continuation is
                # allowed to skip restoring the temporary preimage.
                stop(process)
                process = None
                cfg.write_bytes(original_file_bytes)
                process = launch(cfg, listen)
                assert_policy(False)
            if cfg.read_bytes() != original_file_bytes:
                raise AssertionError("temporary preimage not restored")
            if recovery_trigger is None:
                raise AssertionError("recovery path executed without a captured failure")
            print(json.dumps({
                "schemaVersion": 1,
                "kind": "ordivon.network-v2.supply-chain-singbox-process-rehearsal",
                "standing": "SANDBOX_PROCESS_AND_POLICY_RESTORED",
                "faultInjected": a.fault,
                "oldCdnHostRejectedAfterRestore": True,
                "oldRegistryHostAllowedAfterRestore": True,
                "unknownHostRejectedAfterRestore": True,
                "originalFileBytesRestored": True,
                "originalSourceReplacedInWorkspace": False,
                "productionServiceTouched": False,
                "surfsharkIdentityUsed": False,
                "actualSystemdRollbackProven": False,
                "actualGluetunRuntimeProven": False,
                "unexpectedFailureRecoveryPathProven": a.fault in {
                    "candidate-startup-error", "candidate-sigkill",
                },
            }, separators=(",", ":")))
            return 0
    finally:
        stop(process)
        fixture.shutdown()
        fixture.server_close()
        worker.join(timeout=3)


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as error:
        print(f"nonproduction sing-box process recovery FAIL: {error}", file=sys.stderr)
        sys.exit(2)
