"""Bounded native Git batch identity qualification, not a Git object store.

Git supplies object framing and tree traversal. Standard hashlib checks the
canonical object header plus returned bytes against the requested OID.
"""

from __future__ import annotations

import hashlib
import re

_MAX_BATCH_BYTES = 8 * 1024 * 1024
_MAX_OBJECTS = 20_000


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
        if kind not in ("commit", "tree"):
            raise ValueError("unsupported Git cut object kind")
        prefix = f"{oid} {kind} ".encode("ascii")
        size_text = row[len(prefix) :]
        if (
            not row.startswith(prefix)
            or re.fullmatch(rb"0|[1-9][0-9]{0,7}", size_text) is None
        ):
            raise ValueError("incomplete Git object batch")
        size = int(size_text)
        total += size + len(row) + 2
        if total > _MAX_BATCH_BYTES:
            raise ValueError("Git cut exceeds bounded object bytes")
        result.append((row, size))
    return result


def verify_object_batch(
    raw: bytes,
    headers: list[tuple[bytes, int]],
    algorithm: str,
    *,
    commit: str,
    root_tree: str,
) -> None:
    """Reject wrong identity, framing, kind, or commit/root relation."""
    if len(raw) > _MAX_BATCH_BYTES:
        raise ValueError("Git cut exceeds bounded object bytes")
    view = memoryview(raw)
    offset = 0
    commit_seen = False
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
            raise ValueError(f"Git {kind.decode('ascii')} identity mismatch")
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
        offset = end + 1
    if offset != len(raw) or not commit_seen:
        raise ValueError("incomplete Git object batch")
