"""Read Production source once and bind interpretation to those exact bytes."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any


def read_bound_bytes(path: Path) -> tuple[bytes, str]:
    data = path.read_bytes()
    return data, "sha256:" + hashlib.sha256(data).hexdigest()


def read_bound_object(path: Path) -> tuple[dict[str, Any], str]:
    data, digest = read_bound_bytes(path)
    value = json.loads(data)
    if not isinstance(value, dict):
        raise TypeError(f"{path} must contain one JSON object")
    return value, digest


def relative_child(root: Path, relative: str) -> Path:
    candidate = Path(relative)
    if candidate.is_absolute():
        raise ValueError(f"Production source path must be relative: {relative}")
    resolved_root = root.resolve()
    resolved = (root / candidate).resolve()
    if resolved != resolved_root and resolved_root not in resolved.parents:
        raise ValueError(f"Production source path escapes Production root: {relative}")
    return resolved
