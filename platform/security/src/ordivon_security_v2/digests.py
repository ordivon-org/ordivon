from __future__ import annotations

from hashlib import sha256
from pathlib import Path

_CHUNK_BYTES = 1024 * 1024


def sha256_bytes(data: bytes) -> str:
    """Return one canonical prefixed SHA-256 digest for in-memory bytes."""
    return "sha256:" + sha256(data).hexdigest()


def sha256_file_hex_and_size(path: Path) -> tuple[str, int]:
    """Read a file once and return its lowercase SHA-256 plus observed byte length."""
    digest = sha256()
    byte_length = 0
    with path.open("rb") as source:
        while chunk := source.read(_CHUNK_BYTES):
            digest.update(chunk)
            byte_length += len(chunk)
    return digest.hexdigest(), byte_length


def sha256_file_hex(path: Path) -> str:
    """Return the lowercase hexadecimal SHA-256 digest of a file."""
    digest, _ = sha256_file_hex_and_size(path)
    return digest


def sha256_file(path: Path) -> str:
    """Return one canonical prefixed SHA-256 digest for a file."""
    return "sha256:" + sha256_file_hex(path)
