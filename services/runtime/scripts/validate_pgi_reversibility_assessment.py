#!/usr/bin/env python3
"""Validate PGI ReversibilityAssessment payloads."""

from __future__ import annotations

import json
import sys
from pathlib import Path

REQUIRED = [
    "object_type",
    "schema_version",
    "assessment_id",
    "action_or_claim",
    "side_effect_class",
    "reversibility",
    "blast_radius",
    "rollback_path",
    "irreversible_loss",
    "review_required",
    "authority_boundary",
]

VALID_SIDE_EFFECT = {
    "none",
    "local_doc",
    "local_code",
    "dependency",
    "public_claim",
    "financial",
    "health",
    "relationship",
    "external_system",
}
VALID_REVERSIBILITY = {"reversible", "partially_reversible", "irreversible", "unknown"}
HIGH_SIDE_EFFECT = {"financial", "health", "relationship", "external_system", "public_claim"}


def _nonempty(value) -> bool:
    return isinstance(value, str) and bool(value.strip())


def validate_payload(payload: dict) -> list[str]:
    errors: list[str] = []
    for key in REQUIRED:
        if key not in payload:
            errors.append(f"missing required field: {key}")
    if errors:
        return errors

    if payload.get("object_type") != "PGIReversibilityAssessment":
        errors.append("object_type must be PGIReversibilityAssessment")
    if payload.get("side_effect_class") not in VALID_SIDE_EFFECT:
        errors.append(f"side_effect_class must be one of {sorted(VALID_SIDE_EFFECT)}")
    if payload.get("reversibility") not in VALID_REVERSIBILITY:
        errors.append(f"reversibility must be one of {sorted(VALID_REVERSIBILITY)}")

    for key in ("assessment_id", "action_or_claim", "blast_radius", "rollback_path", "irreversible_loss"):
        if not _nonempty(payload.get(key)):
            errors.append(f"{key} must be a non-empty string")

    if not isinstance(payload.get("review_required"), bool):
        errors.append("review_required must be boolean")

    side_effect = payload.get("side_effect_class")
    if side_effect in HIGH_SIDE_EFFECT and payload.get("review_required") is not True:
        errors.append(f"{side_effect} side effects require review_required=true")

    if payload.get("reversibility") == "unknown" and side_effect in HIGH_SIDE_EFFECT:
        errors.append("high side-effect actions cannot have unknown reversibility")

    boundary = str(payload.get("authority_boundary", "")).lower()
    if "does not authorize" not in boundary:
        errors.append("authority_boundary must state that this assessment does not authorize action")

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
        print("Usage: python scripts/validate_pgi_reversibility_assessment.py <payload.json> [...]")
        return 2
    failed = False
    results = []
    for raw in args:
        path = Path(raw)
        ok, errors = validate_file(path)
        failed = failed or not ok
        results.append({"path": str(path), "valid": ok, "errors": errors})
    print(json.dumps({"tool": "pgi-reversibility-assessment-validator", "results": results}, indent=2))
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
