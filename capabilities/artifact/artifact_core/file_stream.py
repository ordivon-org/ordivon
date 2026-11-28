"""One descriptor-based regular-file observation primitive.

This is local byte identity, not source-path continuity, filesystem isolation,
or attestation of the bytes loaded by a separate native process.
"""
from __future__ import annotations

import hashlib
import os
import stat
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path
from typing import BinaryIO


@contextmanager
def open_regular_file(path: Path, *, label: str = "input") -> Iterator[BinaryIO]:
    """Open once, reject final aliases and nonregular descriptors where supported."""
    flags = os.O_RDONLY
    for name in ("O_CLOEXEC", "O_NONBLOCK", "O_NOFOLLOW", "O_BINARY"):
        flags |= getattr(os, name, 0)
    handle = os.open(path, flags)
    try:
        if not stat.S_ISREG(os.fstat(handle).st_mode):
            raise ValueError(f"{label} is not a regular file: {path}")
        with os.fdopen(handle, "rb", closefd=False) as stream:
            yield stream
    finally:
        os.close(handle)


def observe_stream(stream: BinaryIO, copy_to: BinaryIO | None = None) -> tuple[str, int]:
    """Digest and count exactly the same bytes; optionally copy that observation."""
    digest = hashlib.sha256()
    size = 0
    for block in iter(lambda: stream.read(1024 * 1024), b""):
        if copy_to is not None:
            copy_to.write(block)
        digest.update(block)
        size += len(block)
    return digest.hexdigest(), size
