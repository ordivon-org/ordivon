#!/usr/bin/env python3
"""Source consumer policy acceptance through real sing-box and local CONNECT fixture.

No Gluetun process, legacy WG unit, live consumer, secrets or external requests.
Only tests the existing allowlist/rejection routing seam for the named consumer.
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

ROOT = Path(__file__).resolve().parents[2]
CONSUMER_FILES = {
    "model-provider": ("api.deepseek.com", "consumers/model-provider/config/egress.json"),
    "supply-chain": ("registry-1.docker.io", "consumers/supply-chain/config/egress.json"),
    "x-reality": ("api.x.com", "consumers/x-reality/config/egress.json"),
}
EXPECTED = b"NV2_CONSUMER_POLICY_ACCEPTED"


def free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


def wait_listener(process: subprocess.Popen, port: int) -> None:
    for _ in range(65):
        if process.poll() is not None:
            raise AssertionError("sing-box policy fixture exited unexpectedly")
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.settimeout(0.1)
            if sock.connect_ex(("127.0.0.1", port)) == 0:
                return
        time.sleep(0.05)
    raise AssertionError("sing-box policy fixture listener never became ready")


def request(port: int, url: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [
            "/usr/bin/curl", "-4", "--fail", "--noproxy", "",
            "--proxy", f"http://127.0.0.1:{port}",
            "--connect-timeout", "2", "--max-time", "5",
            "--silent", "--show-error", url,
        ], text=True, capture_output=True, check=False, timeout=8,
    )


def main() -> int:
    if len(sys.argv) != 3 or sys.argv[1] not in CONSUMER_FILES:
        raise ValueError("usage: candidate-neutral-route-fixture.py [model-provider|supply-chain|x-reality] DOMAIN")
    name, domain = sys.argv[1:3]
    allowed, relative = CONSUMER_FILES[name]
    if domain != allowed:
        raise ValueError("requested domain is not the designated known permitted probe")
    source = json.loads((ROOT / relative).read_text(encoding="utf-8"))
    if len(source["inbounds"]) != 1 or len(source["outbounds"]) != 1:
        raise ValueError("consumer source must have exactly one inlet and upstream outlet")
    if source["outbounds"][0]["type"] != "http":
        raise ValueError("consumer egress must be a single HTTP proxy without direct fallback")
    if source["route"]["rules"][-1] != {"action": "reject"}:
        raise ValueError("consumer must end in catch-all rejection")

    seen: list[str] = []
    class ProxyFixture(BaseHTTPRequestHandler):
        def do_CONNECT(self) -> None:
            seen.append(self.path)
            self.send_response(200, "Connection Established")
            self.end_headers()
            self.connection.settimeout(3)
            data = b""
            while b"\r\n\r\n" not in data and len(data) < 8192:
                chunk = self.connection.recv(4096)
                if not chunk:
                    break
                data += chunk
            if not data.startswith(b"GET "):
                raise AssertionError(f"unexpected HTTP method tunneled {data[:50]!r}")
            self.connection.sendall(
                b"HTTP/1.1 200 OK\r\nContent-Type: text/plain\r\n"
                + b"Content-Length: " + str(len(EXPECTED)).encode()
                + b"\r\nConnection: close\r\n\r\n" + EXPECTED
            )

        def log_message(self, *args: object) -> None:
            return

    proxy = ThreadingHTTPServer(("127.0.0.1", 0), ProxyFixture)
    server_thread = threading.Thread(target=proxy.serve_forever, daemon=True)
    server_thread.start()
    process = None
    try:
        config = json.loads(json.dumps(source))
        listener = free_port()
        config["inbounds"][0].update(listen="127.0.0.1", listen_port=listener)
        config["outbounds"][0].update(server="127.0.0.1", server_port=proxy.server_port)
        with tempfile.TemporaryDirectory(prefix="nv2-consumer-policy-fixture-") as tmp:
            file = Path(tmp) / "consumer.json"
            file.write_text(json.dumps(config), encoding="utf-8")
            check = subprocess.run(["/usr/bin/sing-box", "check", "-c", str(file)],
                capture_output=True, text=True, timeout=8, check=False)
            if check.returncode:
                raise AssertionError("candidate-neutral source config rejected: " + check.stderr[-400:])
            process = subprocess.Popen(["/usr/bin/sing-box", "run", "-c", str(file)],
                stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, text=True)
            wait_listener(process, listener)
            valid = request(listener, f"http://{domain}:443/allowed-test")
            if valid.returncode or valid.stdout.encode() != EXPECTED:
                raise AssertionError(f"whitelist through upstream failed: rc={valid.returncode} stderr={valid.stderr[-300:]}")
            if seen != [f"{domain}:443"]:
                raise AssertionError(f"allowed route did not reach exactly one upstream CONNECT: {seen!r}")
            invalid = request(listener, "http://example.com:443/rejected-test")
            if invalid.stdout.encode() == EXPECTED or len(seen) != 1:
                raise AssertionError("unknown destination reached carrier proxy fixture")
        print(json.dumps({
            "schemaVersion":1,"kind":"ordivon.network-v2.candidate-neutral-consumer-route-fixture",
            "standing":"CONSUMER_POLICY_FIXTURE_PASS",
            "consumer":name,"allowedDomain":domain,"upstreamConnects":len(seen),
            "unknownDestinationRejected":True,"usesLegacyWireguard":False,
            "productionNetworkMutation":False,"gluetunRuntimeProven":False,
        },separators=(",",":")))
        return 0
    finally:
        if process is not None and process.poll() is None:
            process.terminate()
            try: process.communicate(timeout=3)
            except subprocess.TimeoutExpired:
                process.kill()
                process.communicate(timeout=2)
        proxy.shutdown()
        proxy.server_close()
        server_thread.join(timeout=2)


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as exc:
        print(f"candidate-neutral fixture FAIL: {exc}", file=sys.stderr)
        sys.exit(1)
