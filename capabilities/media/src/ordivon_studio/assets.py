from __future__ import annotations

import hashlib
import json
import mimetypes
import os
import shutil
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True, slots=True)
class BlobInfo:
    digest: str
    size_bytes: int
    media_type: str

    def as_dict(self) -> dict[str, object]:
        return {
            "digest": self.digest,
            "sizeBytes": self.size_bytes,
            "mediaType": self.media_type,
        }


def hash_file(path: Path, chunk_size: int = 1024 * 1024) -> BlobInfo:
    if not path.is_file():
        raise FileNotFoundError(path)
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(chunk_size):
            digest.update(chunk)
    media_type = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
    return BlobInfo(
        digest=f"sha256:{digest.hexdigest()}",
        size_bytes=path.stat().st_size,
        media_type=media_type,
    )


def r2_object_key(digest: str) -> str:
    algorithm, separator, hexadecimal = digest.partition(":")
    if separator != ":" or algorithm != "sha256" or len(hexadecimal) != 64:
        raise ValueError(f"unsupported digest: {digest}")
    int(hexadecimal, 16)
    return f"objects/sha256/{hexadecimal[:2]}/{hexadecimal}"


def archive_blob(path: Path, cache_root: Path) -> dict[str, object]:
    """Copy one exact Blob into the local content-addressed cache.

    Existing objects are reused only after byte verification. New objects are first
    copied and verified under a temporary name, then admitted without overwriting an
    existing digest address.
    """
    blob = hash_file(path)
    object_key = r2_object_key(blob.digest)
    destination = cache_root / object_key
    destination.parent.mkdir(parents=True, exist_ok=True)

    if destination.exists():
        existing = hash_file(destination)
        if existing.digest != blob.digest or existing.size_bytes != blob.size_bytes:
            raise RuntimeError(f"content-addressed destination conflicts with source: {destination}")
        return {
            "blob": blob.as_dict(),
            "objectKey": object_key,
            "cachePath": str(destination),
            "disposition": "existing",
        }

    temporary_path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(prefix=".ordivon-blob-", dir=destination.parent, delete=False) as temporary:
            temporary_path = Path(temporary.name)
            with path.open("rb") as source:
                shutil.copyfileobj(source, temporary)
            temporary.flush()
            os.fsync(temporary.fileno())

        copied = hash_file(temporary_path)
        if copied.digest != blob.digest or copied.size_bytes != blob.size_bytes:
            raise RuntimeError("temporary archive copy does not match source Blob")

        try:
            os.link(temporary_path, destination)
            disposition = "created"
        except FileExistsError:
            existing = hash_file(destination)
            if existing.digest != blob.digest or existing.size_bytes != blob.size_bytes:
                raise RuntimeError(f"content-addressed destination conflicts with source: {destination}")
            disposition = "existing"

        archived = hash_file(destination)
        if archived.digest != blob.digest or archived.size_bytes != blob.size_bytes:
            raise RuntimeError("archived Blob verification failed")
        return {
            "blob": blob.as_dict(),
            "objectKey": object_key,
            "cachePath": str(destination),
            "disposition": disposition,
        }
    finally:
        if temporary_path is not None:
            temporary_path.unlink(missing_ok=True)


def materialize_blob(digest: str, cache_root: Path, destination: Path) -> dict[str, object]:
    """Recover one exact cached Blob into a working path without mutating the cache.

    The cache object is verified against the requested digest before any copy. The
    working copy is then copied through a temporary file and reverified before
    admission. An existing exact destination converges; different existing bytes fail
    closed instead of being overwritten.
    """
    object_key = r2_object_key(digest)
    source = cache_root / object_key
    if not source.is_file():
        raise FileNotFoundError(source)

    archived = hash_file(source)
    if archived.digest != digest:
        raise RuntimeError(f"cached object does not match requested digest: {source}")

    destination.parent.mkdir(parents=True, exist_ok=True)
    if destination.exists():
        existing = hash_file(destination)
        if existing.digest != digest or existing.size_bytes != archived.size_bytes:
            raise RuntimeError(f"materialization destination contains different bytes: {destination}")
        return {
            "blob": existing.as_dict(),
            "objectKey": object_key,
            "cachePath": str(source),
            "path": str(destination),
            "disposition": "existing",
        }

    temporary_path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(prefix=".ordivon-materialize-", dir=destination.parent, delete=False) as temporary:
            temporary_path = Path(temporary.name)
            with source.open("rb") as cached:
                shutil.copyfileobj(cached, temporary)
            temporary.flush()
            os.fsync(temporary.fileno())

        copied = hash_file(temporary_path)
        if copied.digest != digest or copied.size_bytes != archived.size_bytes:
            raise RuntimeError("temporary materialized copy does not match cached Blob")

        try:
            os.link(temporary_path, destination)
            disposition = "created"
        except FileExistsError:
            existing = hash_file(destination)
            if existing.digest != digest or existing.size_bytes != archived.size_bytes:
                raise RuntimeError(f"materialization destination contains different bytes: {destination}")
            disposition = "existing"

        materialized = hash_file(destination)
        if materialized.digest != digest or materialized.size_bytes != archived.size_bytes:
            raise RuntimeError("materialized Blob verification failed")
        return {
            "blob": materialized.as_dict(),
            "objectKey": object_key,
            "cachePath": str(source),
            "path": str(destination),
            "disposition": disposition,
        }
    finally:
        if temporary_path is not None:
            temporary_path.unlink(missing_ok=True)


def probe_media(path: Path, ffprobe: str = "/usr/bin/ffprobe") -> dict[str, Any]:
    if not path.is_file():
        raise FileNotFoundError(path)
    result = subprocess.run(
        [
            ffprobe,
            "-v",
            "error",
            "-show_format",
            "-show_streams",
            "-of",
            "json",
            str(path),
        ],
        check=False,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or f"ffprobe exited {result.returncode}")
    return json.loads(result.stdout)
