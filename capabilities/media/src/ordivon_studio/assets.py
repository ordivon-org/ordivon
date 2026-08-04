from __future__ import annotations

import hashlib
import json
import mimetypes
import subprocess
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
