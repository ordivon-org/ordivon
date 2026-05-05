#!/usr/bin/env python3
"""Validate PGI ControlBoundaryReview payloads."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

REQUIRED = [
    "object_type",
    "schema_version",
    "review_id",
    "domain",
    "decision_or_event",
    "controllable_factors",
    "uncontrollable_factors",
    "mixed_factors",
    "process_quality",
    "outcome_quality",
    "process_outcome_quadrant",
    "outcome_interpretation",
    "review_posture",
    "authority_boundary",
]

VALID_DOMAINS = {
    "ai_work",
    "body",
    "coding",
    "emotion",
    "finance",
    "learning",
    "project",
    "relationship",
}
VALID_PROCESS = {"good", "degraded", "poor", "unknown"}
VALID_OUTCOME = {"good", "bad", "mixed", "pending", "unknown"}
VALID_QUADRANTS = {
    "good_process_good_outcome",
    "good_process_bad_outcome",
    "bad_process_good_outcome",
    "bad_process_bad_outcome",
    "mixed_or_pending",
}
VALID_POSTURES = {"maintain", "learn", "repair", "investigate", "hold"}

BAD_OUTCOME_PROVES_BAD_PROCESS = re.compile(
    r"bad\s+outcome\s+(?:proves|means|shows)\s+(?:bad|poor)\s+process|"
    r"loss\s+(?:proves|means|shows)\s+(?:bad|poor)\s+decision",
    re.I,
)
GOOD_OUTCOME_PROVES_GOOD_PROCESS = re.compile(
    r"good\s+outcome\s+(?:proves|means|shows)\s+good\s+process|"
    r"profit\s+(?:proves|means|shows)\s+good\s+decision|"
    r"passed\s+because\s+the\s+process\s+was\s+good",
    re.I,
)


def _list_of_strings(value) -> bool:
    return isinstance(value, list) and all(isinstance(item, str) and item.strip() for item in value)


def _expected_quadrant(process: str, outcome: str) -> str:
    if process == "good" and outcome == "good":
        return "good_process_good_outcome"
    if process == "good" and outcome == "bad":
        return "good_process_bad_outcome"
    if process in {"degraded", "poor"} and outcome == "good":
        return "bad_process_good_outcome"
    if process in {"degraded", "poor"} and outcome == "bad":
        return "bad_process_bad_outcome"
    return "mixed_or_pending"


def validate_payload(payload: dict) -> list[str]:
    errors: list[str] = []
    for key in REQUIRED:
        if key not in payload:
            errors.append(f"missing required field: {key}")
    if errors:
        return errors

    if payload.get("object_type") != "PGIControlBoundaryReview":
        errors.append("object_type must be PGIControlBoundaryReview")
    if payload.get("domain") not in VALID_DOMAINS:
        errors.append(f"domain must be one of {sorted(VALID_DOMAINS)}")
    if payload.get("process_quality") not in VALID_PROCESS:
        errors.append(f"process_quality must be one of {sorted(VALID_PROCESS)}")
    if payload.get("outcome_quality") not in VALID_OUTCOME:
        errors.append(f"outcome_quality must be one of {sorted(VALID_OUTCOME)}")
    if payload.get("process_outcome_quadrant") not in VALID_QUADRANTS:
        errors.append(f"process_outcome_quadrant must be one of {sorted(VALID_QUADRANTS)}")
    if payload.get("review_posture") not in VALID_POSTURES:
        errors.append(f"review_posture must be one of {sorted(VALID_POSTURES)}")

    for key in ("controllable_factors", "uncontrollable_factors", "mixed_factors"):
        if not _list_of_strings(payload.get(key)):
            errors.append(f"{key} must be a list of non-empty strings")

    if not payload.get("controllable_factors") and not payload.get("mixed_factors"):
        errors.append("at least one controllable or mixed factor is required for a practical review")

    expected = _expected_quadrant(str(payload.get("process_quality")), str(payload.get("outcome_quality")))
    if payload.get("process_outcome_quadrant") != expected:
        errors.append(f"process_outcome_quadrant must be {expected} for the given process/outcome qualities")

    interpretation = str(payload.get("outcome_interpretation", "")).strip()
    if not interpretation:
        errors.append("outcome_interpretation must be a non-empty string")
    if BAD_OUTCOME_PROVES_BAD_PROCESS.search(interpretation):
        errors.append("outcome_interpretation must not claim bad outcome proves bad process")
    if GOOD_OUTCOME_PROVES_GOOD_PROCESS.search(interpretation):
        errors.append("outcome_interpretation must not claim good outcome proves good process")

    boundary = str(payload.get("authority_boundary", "")).lower()
    if "does not authorize" not in boundary:
        errors.append("authority_boundary must state that this review does not authorize action")

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
        print("Usage: python scripts/validate_pgi_control_boundary_review.py <payload.json> [...]")
        return 2
    failed = False
    results = []
    for raw in args:
        path = Path(raw)
        ok, errors = validate_file(path)
        failed = failed or not ok
        results.append({"path": str(path), "valid": ok, "errors": errors})
    print(json.dumps({"tool": "pgi-control-boundary-review-validator", "results": results}, indent=2))
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
