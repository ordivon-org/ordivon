#!/usr/bin/env python3
"""Typed task-local binding support for Cross-domain Verification R3."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator
from ordivon_composition import CircuitContractError

BINDING_SCHEMA = (
    Path(__file__).resolve().parents[1]
    / "schemas"
    / "cross-domain-verification-r3-binding.schema.json"
)


def _load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise CircuitContractError(f"{path}: root must be an object")
    return value


def validate_binding(value: dict[str, Any]) -> None:
    schema = _load_json(BINDING_SCHEMA)
    validator = Draft202012Validator(schema)
    errors = sorted(
        validator.iter_errors(value),
        key=lambda item: [str(part) for part in item.absolute_path],
    )
    if errors:
        first = errors[0]
        location = "/".join(str(part) for part in first.absolute_path) or "<root>"
        raise CircuitContractError(
            f"cross-domain R3 binding schema violation at {location}: {first.message}"
        )


def load_binding(path: Path) -> dict[str, Any]:
    value = _load_json(path)
    validate_binding(value)
    return value


def resolve_repo_file(repo_root: Path, relative: str) -> Path:
    path = Path(relative)
    if path.is_absolute() or ".." in path.parts:
        raise CircuitContractError(
            f"binding path must be repo-relative without traversal: {relative}"
        )
    root = repo_root.resolve()
    candidate = (root / path).resolve()
    try:
        candidate.relative_to(root)
    except ValueError as exc:
        raise CircuitContractError(
            f"binding path escapes repository: {relative}"
        ) from exc
    if not candidate.is_file():
        raise CircuitContractError(f"binding path is not a file: {relative}")
    return candidate
