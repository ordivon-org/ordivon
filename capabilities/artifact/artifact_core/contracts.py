from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .file_stream import observe_stream, open_regular_file


def _sha256_and_size(path: Path) -> tuple[str, int]:
    """Observe SHA-256 and byte length from one opened stream.

    Unlike a later path.stat(), this size describes the bytes hashed.
    It is not a claim that the pathname remains stable after reading.
    """
    with open_regular_file(path) as stream:
        return observe_stream(stream)


def sha256_file(path: Path) -> str:
    return _sha256_and_size(path.resolve())[0]


def file_fact(path: Path, name: str | None = None) -> dict[str, Any]:
    commitment = FileCommitment.from_path(path)
    return {
        "name": name or commitment.name,
        "path": str(commitment.path),
        "size": commitment.size,
        "digest": {"sha256": commitment.sha256},
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
        try:
            digest, size = _sha256_and_size(resolved)
        except (FileNotFoundError, ValueError) as error:
            raise RuntimeError(f"required file is absent or not a regular file: {resolved}") from error
        return cls(
            path=resolved,
            sha256=digest,
            size=size,
            name=resolved.name,
        )

    def verify(self) -> FileCommitment:
        try:
            current_sha, current_size = _sha256_and_size(self.path)
        except (FileNotFoundError, ValueError) as error:
            raise RuntimeError(f"required file is absent or not a regular file: {self.path}") from error
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
