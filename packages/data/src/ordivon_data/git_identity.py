"""Bounded native Git batch identity qualification, not a Git object store.

Git supplies object framing and tree traversal. Standard hashlib checks the
canonical object header plus returned bytes against the requested OID.
"""

from __future__ import annotations

import hashlib
import re

_MAX_BATCH_BYTES = 8 * 1024 * 1024
_MAX_CUT_BYTES = 64 * 1024 * 1024
_MAX_OBJECTS = 20_000
_MAX_ODPS_BYTES = 2 * 1024 * 1024


def qualify_batch_sizes(
    raw: bytes, expected: list[tuple[str, str]], algorithm: str
) -> list[tuple[bytes, int]]:
    """Admit exact ordered headers before requesting object contents."""
    if algorithm not in ("sha1", "sha256"):
        raise ValueError("unsupported Git object format")
    width = 40 if algorithm == "sha1" else 64
    if len(expected) > _MAX_OBJECTS:
        raise ValueError("Git cut exceeds bounded object count")
    rows = raw.splitlines()
    if len(rows) != len(expected) or not raw.endswith(b"\n"):
        raise ValueError("incomplete Git object batch")
    result = []
    total = 0
    for row, (oid, kind) in zip(rows, expected, strict=True):
        if len(oid) != width or re.fullmatch(r"[0-9a-f]+", oid) is None:
            raise ValueError("invalid Git cut object identity")
        if kind not in ("commit", "tree", "blob"):
            raise ValueError("unsupported Git cut object kind")
        if row == oid.encode("ascii") + b" missing":
            raise ValueError(
                "committed ODPS source cannot be resolved: missing local object"
            )
        prefix = f"{oid} {kind} ".encode("ascii")
        size_text = row[len(prefix) :]
        if (
            not row.startswith(prefix)
            or re.fullmatch(rb"0|[1-9][0-9]{0,7}", size_text) is None
        ):
            raise ValueError("incomplete Git object batch")
        size = int(size_text)
        if kind == "blob" and not 0 < size <= _MAX_ODPS_BYTES:
            raise ValueError("Git ODPS source exceeds bounded input size")
        frame_size = size + len(row) + 2
        if frame_size > _MAX_BATCH_BYTES:
            raise ValueError("Git object exceeds bounded batch bytes")
        total += frame_size
        if total > _MAX_CUT_BYTES:
            raise ValueError("Git cut exceeds bounded object bytes")
        result.append((row, size))
    return result


def partition_object_batches(
    headers: list[tuple[bytes, int]],
) -> list[list[tuple[bytes, int]]]:
    """Maximal contiguous batches, retaining exact admitted order."""
    batches: list[list[tuple[bytes, int]]] = []
    current: list[tuple[bytes, int]] = []
    used = 0
    for header, size in headers:
        frame_size = len(header) + size + 2
        if size < 0 or frame_size > _MAX_BATCH_BYTES:
            raise ValueError("Git object exceeds bounded batch bytes")
        if current and used + frame_size > _MAX_BATCH_BYTES:
            batches.append(current)
            current = []
            used = 0
        current.append((header, size))
        used += frame_size
    if current:
        batches.append(current)
    return batches


def verify_object_batch(
    raw: bytes,
    headers: list[tuple[bytes, int]],
    algorithm: str,
    *,
    commit: str,
    root_tree: str,
    require_commit: bool = True,
) -> dict[str, bytes]:
    """Verify ordered frames and retain only selected metadata blobs."""
    if len(raw) > _MAX_BATCH_BYTES:
        raise ValueError("Git cut exceeds bounded object bytes")
    view = memoryview(raw)
    offset = 0
    commit_seen = False
    blobs: dict[str, bytes] = {}
    for header, size in headers:
        start = offset + len(header) + 1
        end = start + size
        if raw[offset:start] != header + b"\n" or raw[end : end + 1] != b"\n":
            raise ValueError("incomplete Git object batch")
        oid, kind, size_text = header.split(b" ")
        digest = hashlib.new(algorithm)
        digest.update(kind + b" " + size_text + b"\0")
        digest.update(view[start:end])
        if digest.hexdigest().encode("ascii") != oid:
            label = "ODPS blob" if kind == b"blob" else kind.decode("ascii")
            raise ValueError(f"Git {label} identity mismatch")
        if kind == b"commit":
            if (
                commit_seen
                or oid != commit.encode("ascii")
                or not raw.startswith(
                    b"tree " + root_tree.encode("ascii") + b"\n", start, end
                )
            ):
                raise ValueError("Git commit root tree identity mismatch")
            commit_seen = True
        if kind == b"blob":
            blobs[oid.decode("ascii")] = bytes(view[start:end])
        offset = end + 1
    if offset != len(raw) or commit_seen != require_commit:
        raise ValueError("incomplete Git object batch")
    return blobs
