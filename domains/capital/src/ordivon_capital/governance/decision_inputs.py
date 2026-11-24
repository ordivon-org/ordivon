"""Shared parsing rules and error type for specific Governance decisions.

These helpers establish input shape, not permission or account authority.
"""
from __future__ import annotations

import json
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any

DECISION_IMPLEMENTATION = "LOCAL_DETERMINISTIC_PYTHON"


class PolicyDecisionError(RuntimeError):
    """Fail-closed bounded policy-decision error."""


def _load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text())
    if not isinstance(value, dict):
        raise PolicyDecisionError(f"expected JSON object: {path}")
    return value


def _resolve(repo: Path, relative: str) -> Path:
    path = (repo / relative).resolve()
    try:
        path.relative_to(repo.resolve())
    except ValueError as exc:
        raise PolicyDecisionError(f"policy input path escapes repository: {relative}") from exc
    if not path.is_file():
        raise PolicyDecisionError(f"policy input unavailable: {relative}")
    return path


def _decimal(value: Any) -> Decimal:
    try:
        return Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError) as exc:
        raise PolicyDecisionError(f"invalid decimal policy fact: {value!r}") from exc


def _require_local_implementation(cfg: dict[str, Any]) -> None:
    if cfg.get("decisionImplementation") != DECISION_IMPLEMENTATION:
        raise PolicyDecisionError(
            f"unexpected policy decision implementation: {cfg.get('decisionImplementation')!r}"
        )
