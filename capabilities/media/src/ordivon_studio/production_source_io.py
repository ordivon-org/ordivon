"""Read Production source once and bind interpretation to those exact bytes."""
from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any

from .strict_json import decode_object


def read_bound_bytes(path: Path) -> tuple[bytes, str]:
    data = path.read_bytes()
    return data, "sha256:" + hashlib.sha256(data).hexdigest()


def read_bound_object(path: Path) -> tuple[dict[str, Any], str]:
    data, digest = read_bound_bytes(path)
    return decode_object(data), digest


def relative_child(root: Path, relative: str) -> Path:
    candidate = Path(relative)
    if candidate.is_absolute():
        raise ValueError(f"Production source path must be relative: {relative}")
    resolved_root = root.resolve()
    resolved = (root / candidate).resolve()
    if resolved != resolved_root and resolved_root not in resolved.parents:
        raise ValueError(f"Production source path escapes Production root: {relative}")
    return resolved
