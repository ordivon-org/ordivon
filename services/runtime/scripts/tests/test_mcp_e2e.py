from __future__ import annotations

import importlib.util
import json
import socket
import subprocess
import sys
import tempfile
import threading
import unittest
from unittest.mock import patch
from pathlib import Path


REPO = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location("ordivon_mcp_e2e", REPO / "scripts/mcp_e2e.py")
assert SPEC is not None and SPEC.loader is not None
MCP_E2E = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MCP_E2E
SPEC.loader.exec_module(MCP_E2E)


class LiveDockerSocketTests(unittest.TestCase):
    def test_stale_unix_socket_is_not_capability(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "docker.sock"
            stale = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            stale.bind(str(path))
            stale.close()
            self.assertTrue(path.exists())
            self.assertIsNone(MCP_E2E.live_docker_socket((path,)))

    def test_live_ping_socket_is_detected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "docker.sock"
            listener = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            listener.bind(str(path))
            listener.listen(2)

            def serve() -> None:
                for _ in range(2):
                    connection, _ = listener.accept()
                    with connection:
                        connection.recv(4096)
                        connection.sendall(b"HTTP/1.0 200 OK\r\n\r\nOK")
                listener.close()

            thread = threading.Thread(target=serve, daemon=True)
            thread.start()
            self.assertEqual(MCP_E2E.live_docker_socket((path,)), path)
            port, host_thread = MCP_E2E.host_network_probe()
            probe = subprocess.run(
                [sys.executable, "-c", MCP_E2E.make_trusted_host_probe_script(port, path)],
                cwd=tmp,
                text=True,
                capture_output=True,
                timeout=15,
                check=False,
            )
            self.assertEqual(probe.returncode, 0, probe.stderr)
            self.assertIs(json.loads(probe.stdout)["dockerPing"], True)
            host_thread.join(timeout=2)
            self.assertFalse(host_thread.is_alive())
            thread.join(timeout=2)
            self.assertFalse(thread.is_alive())


    def test_ping_must_not_accept_http_failure_or_ok_substrings(self) -> None:
        # A failing Docker Engine must not be used as an execution capability.
        # Status and response body are separate parts of the HTTP contract.
        responses = (
            b"HTTP/1.0 503 Service Unavailable\r\n\r\nOK",
            b"HTTP/1.0 200 OK\r\n\r\nNOT_OK",
            b"HTTP/1.0 200 OK\r\nContent-Length: 0\r\n\r\n",
            b"HTTP/1.0 500 Error\r\n\r\nNOT_OK",
            b"OK",
        )
        for response in responses:
            with self.subTest(response=response), tempfile.TemporaryDirectory() as tmp:
                path = Path(tmp) / "docker.sock"
                listener = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
                listener.bind(str(path))
                listener.listen(2)

                def serve() -> None:
                    try:
                        for _ in range(2):
                            connection, _ = listener.accept()
                            with connection:
                                connection.recv(4096)
                                connection.sendall(response)
                    finally:
                        listener.close()

                thread = threading.Thread(target=serve, daemon=True)
                thread.start()
                self.assertIsNone(MCP_E2E.live_docker_socket((path,)))
                port, host_thread = MCP_E2E.host_network_probe()
                probe = subprocess.run(
                    [sys.executable, "-c", MCP_E2E.make_trusted_host_probe_script(port, path)],
                    cwd=tmp,
                    text=True,
                    capture_output=True,
                    timeout=15,
                    check=False,
                )
                self.assertEqual(probe.returncode, 0, probe.stderr)
                self.assertIs(json.loads(probe.stdout)["dockerPing"], False)
                host_thread.join(timeout=2)
                self.assertFalse(host_thread.is_alive())
                thread.join(timeout=2)
                self.assertFalse(thread.is_alive())


class McpJsonRpcEnvelopeTests(unittest.TestCase):
    def test_http_jsonrpc_response_fails_closed_on_malformed_envelopes(self) -> None:
        # Inject a provider response at the network boundary, not a fabricated
        # protocol parser result. JSON-RPC identity and mutual exclusion matter
        # even when the HTTP status and expected result look successful.
        class Response:
            status = 200
            headers = {"Content-Type": "application/json"}

            def __init__(self, envelope: dict[str, object]) -> None:
                self.payload = json.dumps(envelope).encode("utf-8")

            def __enter__(self) -> "Response":
                return self

            def __exit__(self, *args: object) -> None:
                pass

            def read(self) -> bytes:
                return self.payload

        bad = (
            {"jsonrpc": "1.0", "id": 1, "result": {"tools": []}},
            {"id": 1, "result": {"tools": []}},
            {"jsonrpc": "2.0", "result": {"tools": []}},
            {"jsonrpc": "2.0", "id": 1, "result": {"tools": []}, "error": {"code": -32603}},
        )
        for payload in bad:
            with self.subTest(payload=payload):
                client = MCP_E2E.McpClient("http://localhost:80/mcp", "fixture")
                with patch.object(MCP_E2E.urllib.request, "urlopen", return_value=Response(payload)):
                    with self.assertRaisesRegex(ValueError, "invalid JSON-RPC response"):
                        client.request("tools/list")


if __name__ == "__main__":
    unittest.main()
