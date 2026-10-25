"""Local black-box CONNECT oracle for declared Network consumer egress policy.

The upstream is a loopback spy, not the real provider or Internet. No production
services, credentials, VPN identities, netns, or global routes are modified.
"""

from __future__ import annotations

import json
import queue
import shutil
import socket
import socketserver
import subprocess
import tempfile
import threading
import time
from contextlib import contextmanager
from pathlib import Path

import pytest

CONSUMERS = Path(__file__).resolve().parents[1] / "consumers"
SING_BOX = shutil.which("sing-box")
pytestmark = pytest.mark.skipif(
    SING_BOX is None, reason="sing-box not installed; native semantic probe unavailable"
)


class _Spy(socketserver.ThreadingTCPServer):
    allow_reuse_address = True
    daemon_threads = True


class _Handler(socketserver.BaseRequestHandler):
    def handle(self) -> None:
        self.request.settimeout(2)
        data = b""
        try:
            while b"\r\n\r\n" not in data and len(data) < 4096:
                part = self.request.recv(1024)
                if not part:
                    return
                data += part
            self.server.observed.put(data.split(b"\r\n", 1)[0])
            self.request.sendall(b"HTTP/1.1 200 Connection Established\r\n\r\n")
        except (OSError, TimeoutError):
            return


def _free_port() -> int:
    with socket.socket() as probe:
        probe.bind(("127.0.0.1", 0))
        return int(probe.getsockname()[1])


@contextmanager
def _consumer_proxy(consumer: str, *, disable_terminal_reject: bool = False):
    config = json.loads((CONSUMERS / consumer / "config" / "egress.json").read_text())
    assert len(config["inbounds"]) == 1
    assert len(config["outbounds"]) == 1
    assert config["outbounds"][0]["type"] == "http", "No direct Internet egress in the probe"
    assert config["route"]["rules"][-1] == {"action": "reject"}
    if disable_terminal_reject:
        # Negative control: mutate only a temporary copy. The real source is unchanged.
        config["route"]["rules"][-1] = {
            "action": "route", "outbound": config["outbounds"][0]["tag"]
        }
    with _Spy(("127.0.0.1", 0), _Handler) as spy:
        spy.observed = queue.Queue()
        thread = threading.Thread(target=spy.serve_forever, daemon=True)
        thread.start()
        try:
            config["outbounds"][0]["server"] = "127.0.0.1"
            config["outbounds"][0]["server_port"] = spy.server_address[1]
            listen_port = _free_port()
            config["inbounds"][0]["listen_port"] = listen_port
            with tempfile.TemporaryDirectory(prefix="ordivon-egress-oracle-") as tmp:
                path = Path(tmp) / "consumer.json"
                path.write_text(json.dumps(config), encoding="utf-8")
                subprocess.run(
                    [SING_BOX, "check", "-c", str(path)],
                    check=True, capture_output=True, timeout=10
                )
                process = subprocess.Popen(
                    [SING_BOX, "run", "-c", str(path)],
                    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                )
                try:
                    for _ in range(60):
                        if process.poll() is not None:
                            raise AssertionError("sing-box exited before readiness")
                        try:
                            with socket.create_connection(("127.0.0.1", listen_port), 0.15):
                                break
                        except OSError:
                            time.sleep(0.05)
                    else:
                        raise AssertionError("sing-box local listener not ready")
                    yield listen_port, spy.observed
                finally:
                    process.terminate()
                    try:
                        process.wait(timeout=3)
                    except subprocess.TimeoutExpired:
                        process.kill()
                        process.wait(timeout=3)
        finally:
            spy.shutdown()
            thread.join(timeout=3)


def _connect(port: int, target: str) -> None:
    # HTTP 200 here is NOT the routing oracle: sing-box can acknowledge CONNECT
    # before the downstream reject rule has been applied.
    with socket.create_connection(("127.0.0.1", port), timeout=2) as conn:
        conn.settimeout(1)
        conn.sendall((
            f"CONNECT {target} HTTP/1.1\r\nHost: {target}\r\n\r\n"
        ).encode("ascii"))
        try:
            conn.recv(512)
        except (OSError, TimeoutError):
            pass


@pytest.mark.parametrize(
    ("consumer", "allowed"),
    [
        ("x-reality", ("api.x.com:443",)),
        ("supply-chain", ("registry-1.docker.io:443", "image.pkg.dev:443")),
    ],
)
def test_declared_destinations_reach_spy_but_unknown_or_wrong_port_do_not(
    consumer: str, allowed: tuple[str, ...]
) -> None:
    with _consumer_proxy(consumer) as (port, observed):
        for target in allowed:
            _connect(port, target)
            assert observed.get(timeout=3) == (
                f"CONNECT {target} HTTP/1.1".encode()
            )
        for target in ("example.com:443", allowed[0].split(":")[0] + ":80"):
            _connect(port, target)
            with pytest.raises(queue.Empty):
                observed.get(timeout=0.4)


def test_terminal_reject_negative_control_is_observable() -> None:
    with _consumer_proxy("x-reality", disable_terminal_reject=True) as (port, observed):
        _connect(port, "example.com:443")
        assert observed.get(timeout=3) == b"CONNECT example.com:443 HTTP/1.1"


def test_native_reject_has_no_upstream_effect_even_with_connect_200() -> None:
    """CEGAR: provider CONNECT status alone is not a route-policy oracle.

    The currently installed native sing-box may acknowledge the HTTP CONNECT
    before its route-level reject closes the downstream connection. The
    independent upstream spy must remain empty; do not invent a 403 witness.
    A future sing-box version changing this signature requires requalification.
    """
    curl = shutil.which("curl")
    assert curl, "Native policy qualification requires curl"
    with _consumer_proxy("supply-chain") as (port, observed):
        process = subprocess.run(
            [
                curl, "-q", "-4", "-sS", "-I", "--noproxy", "",
                "-x", f"http://127.0.0.1:{port}",
                "--connect-timeout", "2", "--max-time", "5",
                "-o", "/dev/null", "-w", "%{http_code}|%{http_connect}",
                "https://example.com/",
            ],
            capture_output=True, text=True, timeout=8, check=False,
        )
        assert process.returncode != 0
        assert process.stdout == "000|200", (
            "Provider-native reject signature changed; requalify loaded-policy "
            "semantics rather than defaulting to generic curl-failure proof",
            process.returncode, process.stdout, process.stderr,
        )
        with pytest.raises(queue.Empty):
            observed.get(timeout=0.3)
