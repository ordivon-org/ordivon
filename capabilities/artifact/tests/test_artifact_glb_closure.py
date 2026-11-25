"""Declared GLB resource boundaries before native effects."""

from __future__ import annotations

import json
import struct
from pathlib import Path
from unittest import mock

import pytest

from scripts import artifact_design3d as native

BASE = (
    Path(__file__).resolve().parents[1]
    / "artifact-delivery/shadow-contracts/design-3d-glb-static-mesh-smoke-r1.json"
)


def encode_glb(path, value, binary=b""):
    data = json.dumps(value, separators=(",", ":")).encode()
    data += b" " * (-len(data) % 4)
    binary += b"\0" * (-len(binary) % 4)
    tail = struct.pack("<I4s", len(data), b"JSON") + data
    if binary:
        tail += struct.pack("<I4s", len(binary), b"BIN\0") + binary
    path.write_bytes(struct.pack("<4sII", b"glTF", 2, 12 + len(tail)) + tail)


@pytest.mark.parametrize(
    "fields",
    [
        {"buffers": [{"byteLength": 4, "uri": "sidecar.bin"}]},
        {"images": [{"uri": "sidecar.png"}]},
        {
            "extensionsUsed": ["VENDOR_resource"],
            "extensions": {"VENDOR_resource": {"uri": "sidecar.bin"}},
        },
    ],
)
def test_declared_resource_is_rejected_before_native(tmp_path, fields):
    subject = tmp_path / "scene.glb"
    encode_glb(subject, {"asset": {"version": "2.0"}, **fields})
    with mock.patch.object(
        native, "run", side_effect=AssertionError("native effect before closure")
    ) as runner:
        result = native.verify_glb(subject, BASE, tmp_path / "evidence")
    runner.assert_not_called()
    assert result["status"] == "FAIL"
    assert result["inputClosure"]["status"] == "FAIL"


def test_resource_inspection_does_not_read_embedded_binary(tmp_path):
    from io import BytesIO

    from artifact_verifiers.glb_closure import inspect_glb_stream

    subject = tmp_path / "large.glb"
    encode_glb(
        subject, {"asset": {"version": "2.0"}, "buffers": [{"byteLength": 1048576}]}, b"0" * 1048576
    )

    class Counted(BytesIO):
        read_bytes = 0

        def read(self, n=-1):
            value = super().read(n)
            self.read_bytes += len(value)
            return value

    stream = Counted(subject.read_bytes())
    result = inspect_glb_stream(stream, len(stream.getvalue()))
    assert result["status"] == "PASS", result
    assert result["embeddedBinaryBytes"] == 1048576
    assert stream.read_bytes == 28 + result["jsonBytes"]


def test_duplicate_keys_and_unknown_chunks_fail_before_native(tmp_path):
    from io import BytesIO

    from artifact_verifiers.glb_closure import inspect_glb_stream

    raw = b'{"asset":{"version":"2.0"},"buffers":[],"buffers":[]}'
    raw += b" " * (-len(raw) % 4)
    chunk = struct.pack("<I4s", len(raw), b"JSON") + raw
    data = struct.pack("<4sII", b"glTF", 2, 12 + len(chunk)) + chunk
    assert inspect_glb_stream(BytesIO(data), len(data))["status"] == "FAIL"
    subject = tmp_path / "unknown.glb"
    encode_glb(subject, {"asset": {"version": "2.0"}}, b"data")
    data = subject.read_bytes().replace(b"BIN\0", b"JUNK")
    assert inspect_glb_stream(BytesIO(data), len(data))["status"] == "FAIL"
