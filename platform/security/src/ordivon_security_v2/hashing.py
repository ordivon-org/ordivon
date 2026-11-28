from __future__ import annotations

from hashlib import sha256
from pathlib import Path

_CHUNK_BYTES = 1024 * 1024


def sha256_file_hex(path: Path) -> str:
    """Return the lowercase hexadecimal SHA-256 of the exact file bytes."""
    digest = sha256()
    with path.open("rb") as source:
        while chunk := source.read(_CHUNK_BYTES):
            digest.update(chunk)
    return digest.hexdigest()


def sha256_file_digest(path: Path) -> str:
    """Return the canonical qualified SHA-256 digest for the exact file bytes."""
    return "sha256:" + sha256_file_hex(path)
