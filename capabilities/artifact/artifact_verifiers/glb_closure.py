"""Bound the declared GLB input resource graph before native import.

This is not a glTF conformance checker. Khronos remains the authority for
format semantics, Assimp/Blender/Godot for their native observations.
"""

from __future__ import annotations

import struct
from typing import Any, BinaryIO

from artifact_core.json_validation import decode_json


def assess_declared_resources(value: Any) -> list[str]:
    """Admit core, untextured GLB only; no unknown extension or external URI."""
    if not isinstance(value, dict):
        return ["GLB JSON root is not an object"]
    issues = []
    buffers = value.get("buffers", [])
    if not isinstance(buffers, list):
        issues.append("GLB buffers must be an array")
    else:
        if len(buffers) > 1:
            issues.append("bounded GLB admits at most one embedded buffer")
        for row in buffers:
            if not isinstance(row, dict) or "uri" in row:
                issues.append("GLB buffer is malformed or declares a URI")
    # All three current profiles explicitly exclude textures.
    for field in ("images", "textures"):
        if value.get(field, []) != []:
            issues.append(f"bounded GLB forbids {field}")
    for field in ("extensionsUsed", "extensionsRequired"):
        if value.get(field, []) != []:
            issues.append(f"unqualified GLB {field}")
    # No unknown resource-bearing extension object is admitted even if its
    # name was omitted from extensionsUsed. Application extras are opaque
    # core metadata; do not infer their consumer semantics.
    pending = [value]
    while pending:
        node = pending.pop()
        if isinstance(node, dict):
            if node.get("extensions", {}) != {}:
                issues.append("unqualified GLB extension object")
            pending.extend(v for k, v in node.items() if k != "extras")
        elif isinstance(node, list):
            pending.extend(node)
    return issues


def inspect_glb_stream(stream: BinaryIO, size: int) -> dict[str, Any]:
    """Read the container header and JSON, seek over the embedded binary.

    Cost is O(JSON bytes + resource declarations), not O(BIN bytes).
    No arbitrary extension or full process dependency closure is claimed.
    """
    issues: list[str] = []
    json_size = 0
    binary_size = 0
    try:
        header = stream.read(12)
        if len(header) != 12:
            raise ValueError("truncated GLB header")
        magic, version, declared_size = struct.unpack("<4sII", header)
        if magic != b"glTF" or version != 2 or declared_size != size:
            raise ValueError("GLB magic/version/container length mismatch")
        header = stream.read(8)
        if len(header) != 8:
            raise ValueError("missing GLB JSON chunk")
        json_size, kind = struct.unpack("<I4s", header)
        if kind != b"JSON" or not json_size or json_size % 4 or json_size > size - 20:
            raise ValueError("invalid GLB JSON chunk")
        raw = stream.read(json_size)
        if len(raw) != json_size:
            raise ValueError("truncated GLB JSON chunk")
        value = decode_json(raw.decode("utf-8"))
        issues.extend(assess_declared_resources(value))
        remaining = size - stream.tell()
        if remaining:
            header = stream.read(8)
            if len(header) != 8:
                raise ValueError("truncated GLB binary chunk header")
            binary_size, kind = struct.unpack("<I4s", header)
            if kind != b"BIN\0" or binary_size % 4 or binary_size != remaining - 8:
                raise ValueError("unqualified GLB chunk or inconsistent BIN length")
            stream.seek(binary_size, 1)
        if stream.tell() != size:
            raise ValueError("GLB container length mismatch")
    except (UnicodeError, ValueError, OSError, RecursionError) as error:
        issues.append(str(error))
    return {
        "status": "FAIL" if issues else "PASS",
        "scope": "DECLARED_CORE_UNTEXTURED_GLB_RESOURCES_ONLY",
        "jsonBytes": json_size,
        "embeddedBinaryBytes": binary_size,
        "failures": issues,
    }
