#!/usr/bin/env python3
"""Real sing-box + observable localhost HTTP proxy/direct leak witnesses.

Not a Gluetun/Podman/Surfshark test. Only disposable loopback sockets.
Explicitly distinguishes proxy HTTP errors from observed direct connections.
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
STATUS_MARKER = "\nNV2_HTTP_STATUS:"
TIMEOUT_SECONDS = 7


def free_loopback_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as conn:
        conn.bind(("127.0.0.1", 0))
        return conn.getsockname()[1]


def wait_for_listener(process: subprocess.Popen, port: int) -> None:
    deadline = time.monotonic() + TIMEOUT_SECONDS
    while time.monotonic() < deadline:
        if process.poll() is not None:
            raise RuntimeError("sing-box terminated before listener became ready")
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as conn:
            conn.settimeout(0.12)
            if conn.connect_ex(("127.0.0.1", port)) == 0:
                return
        time.sleep(0.04)
    raise RuntimeError("isolated sing-box listener did not become ready")


def run_proxy_request(port: int, url: str) -> tuple[int, int, str]:
    result = subprocess.run(
        [
            "/usr/bin/curl", "-4", "--fail", "--noproxy", "",
            "-x", f"http://127.0.0.1:{port}", "--max-time", "4",
            "--silent", "--show-error", "-w", STATUS_MARKER + "%{http_code}", url,
        ], text=True, capture_output=True, check=False, timeout=6,
    )
    try:
        content, status = result.stdout.rsplit(STATUS_MARKER, 1)
        return result.returncode, int(status), content
    except (ValueError, IndexError) as error:
        raise AssertionError(
            f"curl HTTP status missing rc={result.returncode}, stdout={result.stdout[-250:]}, stderr={result.stderr[-250:]}"
        ) from error


def main() -> int:
    modes = {None, "--fault=upstream-offline", "--fault=direct-http-error-leak"}
    mode = sys.argv[1] if len(sys.argv) == 2 else None
    if len(sys.argv) > 2 or mode not in modes:
        raise ValueError("usage: isolated-two-hop-fixture.py [--fault=upstream-offline|--fault=direct-http-error-leak]")

    original = json.loads(SOURCE.read_text(encoding="utf-8"))
    inbound, outbound = original["inbounds"], original["outbounds"]
    rules = original["route"]["rules"]
    if len(inbound) != 1 or len(outbound) != 1 or outbound[0]["type"] != "http":
        raise ValueError("fixture requires exactly one outbound upstream HTTP proxy")
    if not any(r.get("ip_is_private") is True and r.get("action") == "reject" for r in rules):
        raise ValueError("source config must reject private destinations")
    if original["route"].get("final") != outbound[0]["tag"]:
        raise ValueError("source config must route remaining destinations through upstream proxy")

    upstream_requests: list[str] = []
    direct_connections: list[str] = []

    class UpstreamFixture(BaseHTTPRequestHandler):
        def do_CONNECT(self) -> None:
            upstream_requests.append(self.path)
            self.send_response(200, "Connection Established")
            self.end_headers()
            self.connection.settimeout(3)
            received = b""
            while b"\r\n\r\n" not in received and len(received) < 16_384:
                part = self.connection.recv(4096)
                if not part:
                    break
                received += part
            if not received.startswith(b"GET "):
                raise AssertionError("fixture only accepts a tunneled HTTP GET")
            self.connection.sendall(
                b"HTTP/1.1 200 OK\r\nContent-Type: text/plain\r\n"
                + b"Content-Length: " + str(len(EXPECTED_BODY)).encode()
                + b"\r\nConnection: close\r\n\r\n" + EXPECTED_BODY
            )

        def log_message(self, *args: object) -> None:
            pass

    class ForbiddenDirectWitness(BaseHTTPRequestHandler):
        def do_GET(self) -> None:
            direct_connections.append(self.path)
            self.send_response(403)
            self.send_header("Content-Length", "0")
            self.end_headers()

        def log_message(self, *args: object) -> None:
            pass

    upstream = ThreadingHTTPServer(("127.0.0.1", 0), UpstreamFixture)
    direct = ThreadingHTTPServer(("127.0.0.1", 0), ForbiddenDirectWitness)
    threads = []
    for server in (upstream, direct):
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        threads.append(thread)

    process = None
    try:
        config = json.loads(json.dumps(original))
        inbound_port = free_loopback_port()
        config["inbounds"][0].update(listen="127.0.0.1", listen_port=inbound_port)
        offline = mode == "--fault=upstream-offline"
        mutant = mode == "--fault=direct-http-error-leak"
        config["outbounds"][0].update(
            server="127.0.0.1",
            server_port=free_loopback_port() if offline else upstream.server_port,
        )
        if mutant:
            # Deliberately malicious temporary config: a direct connection to
            # an observable localhost target returns HTTP 403 and curl --fail=22.
            config["outbounds"].append({"type": "direct", "tag": "leaky-direct"})
            config["route"]["rules"] = [
                r for r in config["route"]["rules"] if r.get("ip_is_private") is not True
            ]
            config["route"]["final"] = "leaky-direct"

        with tempfile.TemporaryDirectory(prefix="nv2-loopback-twohop-") as directory:
            file = Path(directory) / "fixture-singbox.json"
            file.write_text(json.dumps(config), encoding="utf-8")
            check = subprocess.run(
                ["/usr/bin/sing-box", "check", "-c", str(file)],
                text=True, capture_output=True, check=False, timeout=8,
            )
            if check.returncode:
                raise AssertionError(f"temporary config invalid: {check.stderr[-400:]}")
            process = subprocess.Popen(
                ["/usr/bin/sing-box", "run", "-c", str(file)],
                stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, text=True,
            )
            wait_for_listener(process, inbound_port)
            if mutant:
                rc, status, _ = run_proxy_request(
                    inbound_port, f"http://127.0.0.1:{direct.server_port}/unexpected-direct"
                )
                evidence = {
                    "schemaVersion": 1,
                    "kind": "ordivon.network-v2.negative-oracle-mutation",
                    "standing": "DIRECT_LEAK_DETECTED" if direct_connections else "MUTATION_NOT_OBSERVED",
                    "directWitnessConnections": len(direct_connections),
                    "clientHttpStatus": status,
                    "curlFailExit": rc,
                    "providerIdentityUsed": False,
                    "productionNetworkMutation": False,
                }
                print(json.dumps(evidence, separators=(",", ":")))
                return 40 if direct_connections else 0

            rc, status, content = run_proxy_request(
                inbound_port, "http://example.com/network-v2-offline-fixture"
            )
            if offline:
                # A 403/404 could be an HTTP error from a wrong DIRECT target:
                # its curl --fail exit code alone does NOT prove fail-closed.
                if rc == 0 or status not in (0, 502, 503, 504):
                    raise AssertionError(
                        f"offline proxy returned ambiguous HTTP outcome rc={rc}, http={status}"
                    )
                # Probe a concrete, OBSERVABLE forbidden direct destination.
                prc, pstatus, _ = run_proxy_request(
                    inbound_port, f"http://127.0.0.1:{direct.server_port}/private-check"
                )
                if direct_connections or upstream_requests:
                    raise AssertionError("upstream unavailable: forbidden direct/proxy witness was contacted")
                print(json.dumps({
                    "schemaVersion": 1, "kind": "ordivon.network-v2.gluetun-offline-two-hop-fixture",
                    "standing": "FIXTURE_FAULT_PASS", "upstreamUnavailableFailClosed": True,
                    "upstreamFixtureRequests": 0, "directWitnessConnections": 0,
                    "privateWitnessConnections": 0, "clientHttpStatus": status,
                    "curlExitCode": rc, "privateHttpStatus": pstatus,
                    "providerIdentityUsed": False, "productionNetworkMutation": False,
                    "gluetunContainerPortProven": False,
                }, separators=(",", ":")))
                return 0

            if rc or status != 200 or content.encode() != EXPECTED_BODY:
                raise AssertionError(f"local CONNECT chain failed rc={rc}, status={status}, body={content[:150]}")
            if len(upstream_requests) != 1 or "example.com" not in upstream_requests[0]:
                raise AssertionError(f"upstream CONNECT missing {upstream_requests!r}")
            private_rc, private_http, private_body = run_proxy_request(
                inbound_port, f"http://127.0.0.1:{direct.server_port}/private-check"
            )
            if direct_connections or len(upstream_requests) != 1 or EXPECTED_BODY.decode() in private_body:
                raise AssertionError("private route leaked to observable direct or proxy witness")
        print(json.dumps({
            "schemaVersion": 1, "kind": "ordivon.network-v2.gluetun-offline-two-hop-fixture",
            "standing": "FIXTURE_PASS", "twoHopExecutionProven": True,
            "providerIdentityUsed": False, "productionNetworkMutation": False,
            "gluetunContainerPortProven": False, "gluetunFirewallRuntimeProven": False,
            "upstreamFixtureRequests": len(upstream_requests),
            "directWitnessConnections": len(direct_connections),
            "privateWitnessConnections": len(direct_connections),
            "privateDestinationRejected": True,
            "transport": "real-sing-box-loopback-httpproxy-fixture",
        }, separators=(",", ":")))
        return 0
    finally:
        if process is not None and process.poll() is None:
            process.terminate()
            try:
                process.communicate(timeout=4)
            except subprocess.TimeoutExpired:
                process.kill()
                process.communicate(timeout=2)
        for server, thread in zip((upstream, direct), threads):
            server.shutdown()
            server.server_close()
            thread.join(timeout=3)


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as error:
        print(f"isolated fixture FAIL: {error}", file=sys.stderr)
        sys.exit(1)
