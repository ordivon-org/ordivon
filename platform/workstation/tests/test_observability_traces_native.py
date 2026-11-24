"""Opt-in native Vector acceptance; never start or modify production services."""

from __future__ import annotations

import os
import queue
import socket
import subprocess
import threading
import time
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlsplit, urlunsplit

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[1]

pytestmark = pytest.mark.skipif(
    os.environ.get("ORDIVON_NATIVE_VECTOR_TEST") != "1",
    reason="explicit native Vector acceptance (requires /usr/bin/vector)",
)


def _ports() -> tuple[int, int]:
    with socket.socket() as a, socket.socket() as b:
        a.bind(("127.0.0.1", 0))
        b.bind(("127.0.0.1", 0))
        return a.getsockname()[1], b.getsockname()[1]


def _trace_fixture() -> tuple[bytes, bytes, bytes, bytes]:
    # Minimal OTLP protobuf fixture: ExportTraceServiceRequest / ResourceSpans /
    # ScopeSpans / Span. All length-delimited fields here fit in one byte.
    trace_id = bytes.fromhex("1234567890abcdef1234567890abcdef")
    span_id = bytes.fromhex("1122334455667788")
    name = b"ordivon-native-trace"
    now = time.time_ns()

    def field(tag: int, value: bytes) -> bytes:
        assert len(value) < 128
        return bytes((tag, len(value))) + value

    span = (
        field(0x0A, trace_id)
        + field(0x12, span_id)
        + field(0x2A, name)
        + b"\x39" + now.to_bytes(8, "little")
        + b"\x41" + (now + 1000).to_bytes(8, "little")
    )
    return field(0x0A, field(0x12, field(0x12, span))), trace_id, span_id, name


def test_native_vector_forwards_trace_identity(tmp_path: Path) -> None:
    received: queue.Queue[tuple[str, str, bytes]] = queue.Queue()

    class Sink(BaseHTTPRequestHandler):
        def do_POST(self) -> None:
            body = self.rfile.read(int(self.headers["Content-Length"]))
            received.put((self.path, self.headers.get("Content-Type", ""), body))
            self.send_response(200)
            self.send_header("Content-Type", "application/x-protobuf")
            self.send_header("Content-Length", "0")
            self.end_headers()

        def log_message(self, *args: object) -> None:
            pass

    config = yaml.safe_load((ROOT / "observability/vector.yaml").read_text())
    grpc_port, http_port = _ports()
    sink = ThreadingHTTPServer(("127.0.0.1", 0), Sink)
    thread = threading.Thread(target=sink.serve_forever, daemon=True)
    thread.start()
    proc = None
    try:
        # Preserve the real source, codec, input edges and sink configuration.
        # Only isolate the trace slice and remap storage/listener destinations.
        source = config["sources"]["otel"]
        source["grpc"]["address"] = f"127.0.0.1:{grpc_port}"
        source["http"]["address"] = f"127.0.0.1:{http_port}"
        forward = config["sinks"]["otel_traces_tempo"]
        destination = urlsplit(forward["protocol"]["uri"])
        forward["protocol"]["uri"] = urlunsplit(
            destination._replace(netloc=f"127.0.0.1:{sink.server_port}")
        )
        data = tmp_path / "data"
        data.mkdir()
        config_path = tmp_path / "vector.yaml"
        config_path.write_text(yaml.safe_dump({
            "data_dir": str(data),
            "sources": {"otel": source},
            "sinks": {"otel_traces_tempo": forward},
        }))
        payload, trace_id, span_id, name = _trace_fixture()
        log_path = tmp_path / "vector.log"
        with log_path.open("wb") as log:
            proc = subprocess.Popen(
                ["/usr/bin/vector", "--config", str(config_path)],
                stdout=log, stderr=log,
            )
            for _ in range(60):
                assert proc.poll() is None, log_path.read_text(errors="replace")
                try:
                    with socket.create_connection(("127.0.0.1", http_port), 0.2):
                        break
                except OSError:
                    time.sleep(0.1)
            else:
                pytest.fail("isolated OTLP listener unavailable")
            request = urllib.request.Request(
                f"http://127.0.0.1:{http_port}/v1/traces",
                data=payload,
                headers={"Content-Type": "application/x-protobuf"},
                method="POST",
            )
            opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
            with opener.open(request, timeout=4) as response:
                assert response.status == 200
            path, content_type, body = received.get(timeout=10)
            assert path == "/v1/traces"
            assert content_type == "application/x-protobuf"
            assert trace_id in body and span_id in body and name in body
    finally:
        if proc is not None:
            proc.terminate()
            try:
                proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                proc.kill()
                proc.wait()
        sink.shutdown()
        sink.server_close()
        thread.join(timeout=2)
