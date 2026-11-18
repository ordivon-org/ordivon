"""Strict source JSON and acyclic metadata reads for derived navigation.
No independent source authority or persisted index.
"""

from __future__ import annotations

import json
from collections.abc import Iterable, Mapping
from pathlib import Path
from typing import Any


def _json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"expected JSON object: {path}")
    return value


def _walk_values(value: Any, key: str) -> Iterable[Any]:
    # DFS enter/leave markers preserve JSON preorder without Python recursion.
    # Only ancestors count as cycles: a shared child in a DAG is still visited
    # once per occurrence, matching the original recursive walk.
    pending = [(value, False)]
    ancestors: set[int] = set()
    while pending:
        current, leaving = pending.pop()
        if leaving:
            ancestors.remove(id(current))
            continue
        if not isinstance(current, (Mapping, list)):
            continue
        marker = id(current)
        if marker in ancestors:
            raise ValueError("creative-index owner metadata contains a cycle")
        ancestors.add(marker)
        pending.append((current, True))
        if isinstance(current, Mapping):
            if key in current:
                yield current[key]
            children = current.values()
        else:
            children = current
        pending.extend((child, False) for child in reversed(tuple(children)))


def _first_string(value: Any, key: str) -> str | None:
    for candidate in _walk_values(value, key):
        if isinstance(candidate, str) and candidate:
            return candidate
    return None
