"""One private input observation for multiple native media readers.

This is attempt-local custody, not a content store or an immutable filesystem.
"""
from __future__ import annotations

import shutil
import stat
import tempfile
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

from .assets import BlobInfo, UnstableBlobError, hash_file


def _identity(path: Path) -> tuple[int, int, int, int, int]:
    info = path.stat()
    if not stat.S_ISREG(info.st_mode):
        raise ValueError(f"media input must be a regular file: {path}")
    return info.st_dev, info.st_ino, info.st_size, info.st_mtime_ns, info.st_ctime_ns


@contextmanager
def private_input_observation(source: Path) -> Iterator[tuple[Path, BlobInfo]]:
    """Copy once, bind the copy, and retire it before a successful receipt.

    Native readers get only the private path. This detects ordinary source
    drift during copy and snapshot drift during consumption; it does not claim
    atomicity against another process with equivalent filesystem authority.
    """
    source = source.resolve(strict=True)
    before = _identity(source)
    with tempfile.TemporaryDirectory(prefix="ordivon-media-review-") as directory:
        snapshot = Path(directory) / source.name
        shutil.copyfile(source, snapshot)
        if _identity(source) != before or snapshot.stat().st_size != before[2]:
            raise UnstableBlobError(f"media source changed during private copy: {source}")
        observed = hash_file(snapshot)
        identity = _identity(snapshot)
        if observed.size_bytes != identity[2]:
            raise UnstableBlobError("private media input changed before observation")
        yield snapshot, observed
        if _identity(snapshot) != identity or hash_file(snapshot) != observed:
            raise UnstableBlobError("private media input changed during observation")
