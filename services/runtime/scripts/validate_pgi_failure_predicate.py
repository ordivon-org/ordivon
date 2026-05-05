#!/usr/bin/env python3
"""Validate PGI FailurePredicate payloads.

Local-only validator for falsifiability records. Findings are review evidence
only and do not authorize action.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

REQUIRED = [
    "object_type",
    "schema_version",
    "predicate_id",
    "claim",
    "claim_type",
    "would_disconfirm",
    "measurement",
    "review_window",
    "action_if_disconfirmed",
    "authority_boundary",
]

NON_FALSIFIABLE_MARKERS = {
    "none",
    "nothing",
    "never",
    "cannot fail",
    "impossible to disconfirm",
    "always true",
    "not applicable",
}


def _bad_marker(value: str) -> str | None:
    lower = value.strip().lower()
    for marker in NON_FALSIFIABLE_MARKERS:
        if marker in lower:
            return marker
    return None


def validate_payload(payload: dict) -> list[str]:
    errors: list[str] = []
    for key in REQUIRED:
        if key not in payload:
            errors.append(f"missing required field: {key}")
    if errors:
        return errors

    if payload.get("object_type") != "PGIFailurePredicate":
        errors.append("object_type must be PGIFailurePredicate")

    would_disconfirm = payload.get("would_disconfirm")
    if not isinstance(would_disconfirm, list) or not would_disconfirm:
        errors.append("would_disconfirm must be a non-empty array")
    else:
        for item in would_disconfirm:
            if not isinstance(item, str) or not item.strip():
                errors.append("would_disconfirm entries must be non-empty strings")
                continue
            marker = _bad_marker(item)
            if marker:
                errors.append(f"would_disconfirm uses non-falsifiable marker: {marker}")

    for key in ("measurement", "review_window", "action_if_disconfirmed"):
        value = payload.get(key)
        if not isinstance(value, str) or not value.strip():
            errors.append(f"{key} must be a non-empty string")
            continue
        marker = _bad_marker(value)
        if marker:
            errors.append(f"{key} uses non-falsifiable marker: {marker}")

    authority = str(payload.get("authority_boundary", "")).lower()
    if "does not authorize" not in authority and "not authorization" not in authority:
        errors.append("authority_boundary must state that this predicate does not authorize action")

    return errors


def validate_file(path: Path) -> tuple[bool, list[str]]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        return False, [f"invalid JSON: {e}"]
    errors = validate_payload(payload)
    return not errors, errors


def main(argv: list[str] | None = None) -> int:
    args = argv if argv is not None else sys.argv[1:]
    if not args:
        print("Usage: python scripts/validate_pgi_failure_predicate.py <payload.json> [...]")
        return 2

    failed = False
    results = []
    for raw in args:
        path = Path(raw)
        ok, errors = validate_file(path)
        failed = failed or not ok
        results.append({"path": str(path), "valid": ok, "errors": errors})

    print(json.dumps({"tool": "pgi-failure-predicate-validator", "results": results}, indent=2))
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
