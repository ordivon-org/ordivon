#!/usr/bin/env python3
"""Validate PGI LearningReview payloads."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

REQUIRED = [
    "object_type",
    "schema_version",
    "review_id",
    "learning_track",
    "intent",
    "input_materials",
    "output_artifact",
    "skill_transfer",
    "application_context",
    "consumption_loop_risk",
    "next_application",
    "authority_boundary",
]

VALID_TRACKS = {
    "ai_systems",
    "communication",
    "finance",
    "health",
    "philosophy",
    "product",
    "software_engineering",
    "writing",
}
VALID_RISK = {"none", "watch", "block"}
READ_MORE_ONLY_RE = re.compile(r"^(?:read|watch|consume|study)\s+more\.?$", re.I)


def _nonempty(value) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _list_of_strings(value) -> bool:
    return isinstance(value, list) and all(isinstance(item, str) and item.strip() for item in value)


def validate_payload(payload: dict) -> list[str]:
    errors: list[str] = []
    for key in REQUIRED:
        if key not in payload:
            errors.append(f"missing required field: {key}")
    if errors:
        return errors

    if payload.get("object_type") != "PGILearningReview":
        errors.append("object_type must be PGILearningReview")
    if payload.get("learning_track") not in VALID_TRACKS:
        errors.append(f"learning_track must be one of {sorted(VALID_TRACKS)}")
    if payload.get("consumption_loop_risk") not in VALID_RISK:
        errors.append(f"consumption_loop_risk must be one of {sorted(VALID_RISK)}")

    if not _list_of_strings(payload.get("input_materials")):
        errors.append("input_materials must be a list of non-empty strings")

    for key in (
        "review_id",
        "intent",
        "output_artifact",
        "skill_transfer",
        "application_context",
        "next_application",
        "authority_boundary",
    ):
        if not _nonempty(payload.get(key)):
            errors.append(f"{key} must be a non-empty string")

    output = str(payload.get("output_artifact", "")).strip().lower()
    if output in {"none", "n/a", "not yet", "read only"}:
        errors.append("output_artifact must name a concrete output, not consumption only")

    next_application = str(payload.get("next_application", "")).strip()
    if READ_MORE_ONLY_RE.match(next_application):
        errors.append("next_application must apply learning, not only read/watch/study more")

    if payload.get("consumption_loop_risk") == "block" and "pause" not in next_application.lower():
        errors.append("block-level consumption loop risk requires a pause or application-first next step")

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
        print("Usage: python scripts/validate_pgi_learning_review.py <payload.json> [...]")
        return 2
    failed = False
    results = []
    for raw in args:
        path = Path(raw)
        ok, errors = validate_file(path)
        failed = failed or not ok
        results.append({"path": str(path), "valid": ok, "errors": errors})
    print(json.dumps({"tool": "pgi-learning-review-validator", "results": results}, indent=2))
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
