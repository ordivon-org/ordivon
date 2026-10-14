#!/usr/bin/env python3
"""Run real sing-box -> local HTTP-proxy fixture, NOT a real Gluetun/VPN test.

Uses only random loopback listeners; never touches Network-v2 namespaces,
systemd, Podman, credentials, routes, or production fixed port assignments.
"""
from __future__ import annotations

from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
import socket
import subprocess
import sys
import tempfile
import threading
import time

NETWORK_ROOT = Path(__file__).resolve().parents[3]
SOURCE = NETWORK_ROOT / "consumers/browserless/config/provider-carrier-gluetun-candidate.json"
EXPECTED_BODY = b"NETWORK_V2_UPSTREAM_FIXTURE"
TIMEOUT_SECONDS = 7


def free_loopback_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def wait_for_listener(process: subprocess.Popen, port: int) -> None:
    deadline = time.monotonic() + TIMEOUT_SECONDS
    while time.monotonic() < deadline:
        if process.poll() is not None:
            raise RuntimeError("sing-box terminated before listener became ready")
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(0.15)
            if s.connect_ex(("127.0.0.1", port)) == 0:
                return
        time.sleep(0.05)
    raise RuntimeError("sing-box isolated listener did not become ready")


def run_proxy_request(port: int, url: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [
            "/usr/bin/curl", "-4", "--noproxy", "",
            "-x", f"http://127.0.0.1:{port}", "--max-time", "4",
            "--silent", "--show-error", url,
        ], text=True, capture_output=True, check=False, timeout=6,
    )


def main() -> int:
    original = json.loads(SOURCE.read_text(encoding="utf-8"))
    inbound = original["inbounds"]
    outbound = original["outbounds"]
    rules = original["route"]["rules"]
    if len(inbound) != 1 or len(outbound) != 1 or outbound[0]["type"] != "http":
        raise ValueError("fixture expects exactly one inbound and upstream HTTP proxy")
    if not any(rule.get("ip_is_private") is True and rule.get("action") == "reject" for rule in rules):
        raise ValueError("candidate must reject private destinations")
    if original["route"].get("final") != outbound[0]["tag"]:
        raise ValueError("candidate must send all non-rejected destinations to single proxy")

    requests_seen: list[str] = []

    class UpstreamFixture(BaseHTTPRequestHandler):
        def do_CONNECT(self) -> None:
            # sing-box HTTP outbound uses CONNECT even for a plain HTTP target.
            # A fake direct GET proxy would falsely fail this actual two-hop seam.
            requests_seen.append(self.path)
            self.send_response(200, "Connection Established")
            self.end_headers()
            self.connection.settimeout(3)
            request = b""
            while b"\r\n\r\n" not in request and len(request) < 16_384:
                chunk = self.connection.recv(4096)
                if not chunk:
                    break
                request += chunk
            if not request.startswith(b"GET "):
                raise AssertionError(f"unexpected tunneled method {request[:40]!r}")
            self.connection.sendall(
                b"HTTP/1.1 200 OK\r\n"
                b"Content-Type: text/plain\r\n"
                + b"Content-Length: " + str(len(EXPECTED_BODY)).encode()
                + b"\r\nConnection: close\r\n\r\n" + EXPECTED_BODY
            )

        def log_message(self, fmt: str, *args: object) -> None:
            pass

    server = ThreadingHTTPServer(("127.0.0.1", 0), UpstreamFixture)
    worker = threading.Thread(target=server.serve_forever, daemon=True)
    worker.start()
    process = None
    try:
        config = json.loads(json.dumps(original))
        front_port = free_loopback_port()
        config["inbounds"][0].update(listen="127.0.0.1", listen_port=front_port)
        config["outbounds"][0].update(server="127.0.0.1", server_port=server.server_port)
        # This change is confined to a TEMPORARY CONFIG; the production source is unchanged.
        with tempfile.TemporaryDirectory(prefix="network-v2-gluetun-fixture-") as tmp:
            cfg = Path(tmp) / "candidate-fixture.json"
            cfg.write_text(json.dumps(config), encoding="utf-8")
            validator = subprocess.run(
                ["/usr/bin/sing-box", "check", "-c", str(cfg)],
                capture_output=True, text=True, check=False, timeout=8,
            )
            if validator.returncode:
                raise RuntimeError("candidate sing-box schema check failed: " + validator.stderr[-800:])
            process = subprocess.Popen(
                ["/usr/bin/sing-box", "run", "-c", str(cfg)],
                stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, text=True,
            )
            wait_for_listener(process, front_port)
            success = run_proxy_request(front_port, "http://example.com/network-v2-offline-fixture")
            if success.returncode or success.stdout.encode() != EXPECTED_BODY:
                process.terminate()
                _, diagnosis = process.communicate(timeout=3)
                raise AssertionError(f"local proxy hop failed: rc={success.returncode} stderr={success.stderr[-600:]} diag={diagnosis[-1400:]}")
            if len(requests_seen) != 1 or "example.com" not in requests_seen[0]:
                raise AssertionError(f"expected one upstream HTTP proxy request, saw {requests_seen!r}")
            rejected = run_proxy_request(front_port, "http://127.0.0.1:49123/private-deny")
            private_rejected = EXPECTED_BODY.decode() not in rejected.stdout and len(requests_seen) == 1
            if not private_rejected:
                raise AssertionError("private destination reached upstream fixture")
        evidence = {
            "schemaVersion": 1,
            "kind": "ordivon.network-v2.gluetun-offline-two-hop-fixture",
            "standing": "FIXTURE_PASS",
            "twoHopExecutionProven": True,
            "providerIdentityUsed": False,
            "productionNetworkMutation": False,
            "gluetunContainerPortProven": False,
            "gluetunFirewallRuntimeProven": False,
            "upstreamFixtureRequests": len(requests_seen),
            "privateDestinationRejected": True,
            "transport": "real-sing-box-loopback-httpproxy-fixture",
        }
        print(json.dumps(evidence, separators=(",", ":")))
        return 0
    finally:
        if process is not None and process.poll() is None:
            process.terminate()
            try:
                process.communicate(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
                process.communicate(timeout=3)
        server.shutdown()
        server.server_close()
        worker.join(timeout=2)


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as error:
        print(f"isolated fixture FAIL: {error}", file=sys.stderr)
        sys.exit(1)
