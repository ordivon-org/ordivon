from __future__ import annotations

import hashlib
from dataclasses import dataclass
from pathlib import Path
from typing import Any


def _sha256_and_size(path: Path) -> tuple[str, int]:
    """Observe SHA-256 and byte length from one opened stream.

    Unlike a later path.stat(), this size describes the bytes hashed.
    It is not a claim that the pathname remains stable after reading.
    """
    digest = hashlib.sha256()
    size = 0
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
            size += len(chunk)
    return digest.hexdigest(), size


def sha256_file(path: Path) -> str:
    return _sha256_and_size(path)[0]


def file_fact(path: Path, name: str | None = None) -> dict[str, Any]:
    resolved = path.resolve()
    if not resolved.is_file():
        raise RuntimeError(f"required file is absent: {resolved}")
    digest, size = _sha256_and_size(resolved)
    return {
        "name": name or resolved.name,
        "path": str(resolved),
        "size": size,
        "digest": {"sha256": digest},
    }


@dataclass(frozen=True)
class FileCommitment:
    path: Path
    sha256: str
    size: int
    name: str

    @classmethod
    def from_path(cls, path: Path) -> FileCommitment:
        resolved = path.resolve()
        if not resolved.is_file():
            raise RuntimeError(f"required file is absent: {resolved}")
        digest, size = _sha256_and_size(resolved)
        return cls(
            path=resolved,
            sha256=digest,
            size=size,
            name=resolved.name,
        )

    def verify(self) -> FileCommitment:
        if not self.path.is_file():
            raise RuntimeError(f"required file is absent: {self.path}")
        current_sha, current_size = _sha256_and_size(self.path)
        if current_size != self.size:
            raise RuntimeError(f"file size drift: {self.path}")
        if current_sha != self.sha256:
            raise RuntimeError(f"SHA-256 drift: {self.path}")
        return self

    def as_dict(self) -> dict[str, object]:
        return {
            "path": str(self.path),
            "sha256": self.sha256,
            "size": self.size,
            "name": self.name,
        }
