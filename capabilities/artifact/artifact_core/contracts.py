from __future__ import annotations

from dataclasses import dataclass
import hashlib
from pathlib import Path
from typing import Any


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def file_fact(path: Path, name: str | None = None) -> dict[str, Any]:
    resolved = path.resolve()
    if not resolved.is_file():
        raise RuntimeError(f"required file is absent: {resolved}")
    return {
        "name": name or resolved.name,
        "path": str(resolved),
        "size": resolved.stat().st_size,
        "digest": {"sha256": sha256_file(resolved)},
    }


@dataclass(frozen=True)
class FileCommitment:
    path: Path
    sha256: str
    size: int
    name: str

    @classmethod
    def from_path(cls, path: Path) -> "FileCommitment":
        resolved = path.resolve()
        if not resolved.is_file():
            raise RuntimeError(f"required file is absent: {resolved}")
        return cls(
            path=resolved,
            sha256=sha256_file(resolved),
            size=resolved.stat().st_size,
            name=resolved.name,
        )

    def verify(self) -> "FileCommitment":
        if not self.path.is_file():
            raise RuntimeError(f"required file is absent: {self.path}")
        if self.path.stat().st_size != self.size:
            raise RuntimeError(f"file size drift: {self.path}")
        if sha256_file(self.path) != self.sha256:
            raise RuntimeError(f"SHA-256 drift: {self.path}")
        return self

    def as_dict(self) -> dict[str, object]:
        return {
            "path": str(self.path),
            "sha256": self.sha256,
            "size": self.size,
            "name": self.name,
        }
