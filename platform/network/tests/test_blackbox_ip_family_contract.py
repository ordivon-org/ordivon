"""The real Blackbox owner must not let an IPv4 witness prove IPv6 or vice versa."""

from __future__ import annotations

import shutil
import socket
import subprocess
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import ProxyHandler, build_opener

import pytest

NETWORK = Path(__file__).resolve().parents[1]


class _OK(BaseHTTPRequestHandler):
    def do_GET(self) -> None:
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"ok")

    def log_message(self, *args: object) -> None:
        pass


class _IPv6Server(ThreadingHTTPServer):
    address_family = socket.AF_INET6


def _port() -> int:
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


def _probe(opener, port: int, module: str, target: str) -> dict[str, str]:
    query = urlencode({"module": module, "target": target})
    with opener.open(f"http://127.0.0.1:{port}/probe?{query}", timeout=7) as response:
        metrics = response.read().decode()
    return {
        key: value
        for line in metrics.splitlines()
        if line.startswith(("probe_success ", "probe_ip_protocol "))
        for key, value in [line.split(None, 1)]
    }


def test_blackbox_http_modules_refuse_fallback_by_configuration() -> None:
    # The exporter defaults to cross-family fallback. An IPv4-only or
    # IPv6-only target literal is insufficient to test this hostname rule.
    import json

    data = json.loads(subprocess.check_output(
        ["/usr/bin/yq", "-o=json", ".", str(NETWORK / "config/blackbox/blackbox.yml")],
        text=True,
    ))
    for family, value in (("ipv4", "ip4"), ("ipv6", "ip6")):
        http = data["modules"][f"http_2xx_{family}"]["http"]
        assert http["preferred_ip_protocol"] == value
        assert http.get("ip_protocol_fallback") is False, family


def test_blackbox_ip_family_is_exact_even_when_other_family_works() -> None:
    exporter_binary = shutil.which("prometheus-blackbox-exporter") or shutil.which(
        "blackbox_exporter"
    )
    if exporter_binary is None:
        pytest.skip(
            "native Blackbox Exporter not installed; strict config CDC remains mandatory"
        )
    try:
        ipv6 = _IPv6Server(("::1", 0), _OK)
    except OSError:
        pytest.skip("this host has no IPv6 loopback")
    ipv4 = ThreadingHTTPServer(("127.0.0.1", 0), _OK)
    exporter_port = _port()
    ipv4_thread = threading.Thread(target=ipv4.serve_forever, daemon=True)
    ipv6_thread = threading.Thread(target=ipv6.serve_forever, daemon=True)
    ipv4_thread.start()
    ipv6_thread.start()
    exporter = subprocess.Popen(
        [
            exporter_binary,
            f"--config.file={NETWORK / 'config/blackbox/blackbox.yml'}",
            f"--web.listen-address=127.0.0.1:{exporter_port}",
        ],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    opener = build_opener(ProxyHandler({}))
    try:
        for _ in range(60):
            if exporter.poll() is not None:
                raise AssertionError("Blackbox failed to start")
            try:
                with opener.open(f"http://127.0.0.1:{exporter_port}/metrics", timeout=1):
                    break
            except OSError:
                time.sleep(0.05)
        else:
            raise AssertionError("Blackbox readiness timed out")

        target4 = f"http://127.0.0.1:{ipv4.server_port}/"
        target6 = f"http://[::1]:{ipv6.server_port}/"
        pairs = [
            ("http_2xx_ipv4", target4, "1", "4"),
            ("http_2xx_ipv6", target6, "1", "6"),
            ("http_2xx_ipv4", target6, "0", None),
            ("http_2xx_ipv6", target4, "0", None),
        ]
        for module, target, want_success, want_protocol in pairs:
            got = _probe(opener, exporter_port, module, target)
            assert got["probe_success"] == want_success, (module, target, got)
            if want_protocol:
                assert got["probe_ip_protocol"] == want_protocol, (module, target, got)
    finally:
        exporter.terminate()
        try:
            exporter.wait(timeout=3)
        except subprocess.TimeoutExpired:
            exporter.kill()
            exporter.wait(timeout=3)
        ipv4.shutdown()
        ipv6.shutdown()
        ipv4.server_close()
        ipv6.server_close()
        ipv4_thread.join(timeout=3)
        ipv6_thread.join(timeout=3)
