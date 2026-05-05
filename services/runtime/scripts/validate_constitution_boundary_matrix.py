#!/usr/bin/env python3
"""Validate PGI ConstitutionBoundaryMatrix payloads."""

from __future__ import annotations

import json
import sys
from pathlib import Path

VALID_CLASSIFICATIONS = {"no_go_boundary", "review_gate", "warning", "learning_prompt", "orientation"}
VALID_ACTIVATION = {"candidate_only", "advisory", "existing_no_go_support", "deferred"}


def validate_payload(payload: dict) -> list[str]:
    errors: list[str] = []
    if payload.get("object_type") != "PGIConstitutionBoundaryMatrix":
        errors.append("object_type must be PGIConstitutionBoundaryMatrix")
    boundary = str(payload.get("authority_boundary", "")).lower()
    if "does not authorize" not in boundary or "does not activate policy" not in boundary:
        errors.append("authority_boundary must state no action authorization and no Policy activation")

    rules = payload.get("rules")
    if not isinstance(rules, list) or not rules:
        errors.append("rules must be a non-empty array")
        return errors

    seen = set()
    for idx, rule in enumerate(rules, 1):
        prefix = f"rules[{idx}]"
        rid = rule.get("rule_id")
        if not rid:
            errors.append(f"{prefix}: missing rule_id")
        elif rid in seen:
            errors.append(f"{prefix}: duplicate rule_id {rid}")
        seen.add(rid)

        if rule.get("classification") not in VALID_CLASSIFICATIONS:
            errors.append(f"{prefix}: invalid classification")
        if rule.get("activation_status") not in VALID_ACTIVATION:
            errors.append(f"{prefix}: invalid activation_status")
        if rule.get("activation_status") == "active_policy":
            errors.append(f"{prefix}: active_policy is forbidden")
        for field in ("statement", "reason", "closure_or_review_condition"):
            if not isinstance(rule.get(field), str) or not rule[field].strip():
                errors.append(f"{prefix}: missing {field}")

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
        print("Usage: python scripts/validate_constitution_boundary_matrix.py <matrix.json> [...]")
        return 2

    failed = False
    results = []
    for raw in args:
        path = Path(raw)
        ok, errors = validate_file(path)
        failed = failed or not ok
        results.append({"path": str(path), "valid": ok, "errors": errors})
    print(json.dumps({"tool": "pgi-constitution-boundary-matrix-validator", "results": results}, indent=2))
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
