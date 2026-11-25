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


def canonical_relative_file_path(value: object) -> bool:
    """Portable Production-relative file name, before filesystem resolution."""
    return (
        isinstance(value, str)
        and bool(value)
        and "\\" not in value
        and "\x00" not in value
        and ":" not in value.split("/")[0]
        and all(part not in ("", ".", "..") for part in value.split("/"))
    )


def local_source_path(root: Path, selected: str) -> Path:
    """Resolve a canonical Production-local reference before any file read."""
    # Keep escaping references distinct from lexical aliases.
    resolved = relative_child(root, selected)
    if not canonical_relative_file_path(selected):
        raise ValueError(f"invalid Production-local source path: {selected}")
    return resolved


def claims_source_path(root: Path, production: dict[str, Any]) -> Path:
    """Resolve the one claim set explicitly selected by the Production."""
    sources = production.get("sources")
    selected = sources.get("claims") if isinstance(sources, dict) else None
    if not isinstance(selected, str) or not selected:
        raise TypeError("Production must reference one claims source")
    return local_source_path(root, selected)
