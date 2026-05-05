#!/usr/bin/env python3
"""Validate PGI BuilderChangeReview payloads."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

REQUIRED = [
    "object_type",
    "schema_version",
    "change_id",
    "change_surface",
    "intent",
    "files_touched",
    "truth_impact",
    "value_impact",
    "action_impact",
    "complexity_delta",
    "debt_declared",
    "anti_overforce_checked",
    "improves_decision_maker",
    "tests_or_receipts",
    "authority_boundary",
]

VALID_SURFACES = {
    "adapter",
    "ai_onboarding",
    "architecture",
    "checker",
    "cli",
    "docs",
    "fixture",
    "pack",
    "roadmap",
    "schema",
}
VALID_COMPLEXITY = {"reduces", "neutral", "increases", "unknown"}
VISION_ONLY_RE = re.compile(r"vision|civilization|flywheel|destiny|everything", re.I)


def _nonempty(value) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _list_of_strings(value) -> bool:
    return isinstance(value, list) and bool(value) and all(isinstance(item, str) and item.strip() for item in value)


def validate_payload(payload: dict) -> list[str]:
    errors: list[str] = []
    for key in REQUIRED:
        if key not in payload:
            errors.append(f"missing required field: {key}")
    if errors:
        return errors

    if payload.get("object_type") != "PGIBuilderChangeReview":
        errors.append("object_type must be PGIBuilderChangeReview")
    if payload.get("change_surface") not in VALID_SURFACES:
        errors.append(f"change_surface must be one of {sorted(VALID_SURFACES)}")
    if payload.get("complexity_delta") not in VALID_COMPLEXITY:
        errors.append(f"complexity_delta must be one of {sorted(VALID_COMPLEXITY)}")

    for key in (
        "change_id",
        "intent",
        "truth_impact",
        "value_impact",
        "action_impact",
        "improves_decision_maker",
        "authority_boundary",
    ):
        if not _nonempty(payload.get(key)):
            errors.append(f"{key} must be a non-empty string")

    for key in ("files_touched", "tests_or_receipts"):
        if not _list_of_strings(payload.get(key)):
            errors.append(f"{key} must be a list of non-empty strings")

    if not isinstance(payload.get("debt_declared"), bool):
        errors.append("debt_declared must be boolean")
    if not isinstance(payload.get("anti_overforce_checked"), bool):
        errors.append("anti_overforce_checked must be boolean")

    if payload.get("complexity_delta") == "increases":
        if payload.get("debt_declared") is not True:
            errors.append("complexity-increasing changes must declare debt")
        if payload.get("anti_overforce_checked") is not True:
            errors.append("complexity-increasing changes must pass anti-overforce review")

    combined = " ".join(
        str(payload.get(k, "")) for k in ("intent", "truth_impact", "value_impact", "action_impact")
    )
    if VISION_ONLY_RE.search(combined) and not payload.get("tests_or_receipts"):
        errors.append("vision-heavy builder changes require tests_or_receipts")

    improves = str(payload.get("improves_decision_maker", "")).strip().lower()
    if improves in {"unclear", "unknown", "n/a", "not sure"}:
        errors.append("improves_decision_maker must explain the governance benefit")

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
        print("Usage: python scripts/validate_pgi_builder_change_review.py <payload.json> [...]")
        return 2
    failed = False
    results = []
    for raw in args:
        path = Path(raw)
        ok, errors = validate_file(path)
        failed = failed or not ok
        results.append({"path": str(path), "valid": ok, "errors": errors})
    print(json.dumps({"tool": "pgi-builder-change-review-validator", "results": results}, indent=2))
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
