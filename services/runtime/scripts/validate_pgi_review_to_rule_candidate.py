#!/usr/bin/env python3
"""Validate PGI ReviewToRuleCandidate payloads."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

REQUIRED = [
    "object_type",
    "schema_version",
    "candidate_id",
    "source_reviews",
    "pattern_basis",
    "evidence_count",
    "severity",
    "emotional_intensity",
    "cool_down_review_completed",
    "proposed_rule",
    "rule_scope",
    "candidate_status",
    "retirement_path",
    "next_review",
    "policy_boundary",
    "authority_boundary",
]

VALID_PATTERN_BASIS = {"single_anecdote", "multiple_examples", "high_severity"}
VALID_SEVERITY = {"low", "medium", "high", "critical"}
VALID_INTENSITY = {"low", "moderate", "high", "extreme", "unknown"}
VALID_STATUS = {"candidate", "needs_more_evidence", "reject"}
OVERREACTION_RE = re.compile(r"\b(?:always|never|forever|ban\s+everything|never\s+again)\b", re.I)


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

    if payload.get("object_type") != "PGIReviewToRuleCandidate":
        errors.append("object_type must be PGIReviewToRuleCandidate")
    if payload.get("pattern_basis") not in VALID_PATTERN_BASIS:
        errors.append(f"pattern_basis must be one of {sorted(VALID_PATTERN_BASIS)}")
    if payload.get("severity") not in VALID_SEVERITY:
        errors.append(f"severity must be one of {sorted(VALID_SEVERITY)}")
    if payload.get("emotional_intensity") not in VALID_INTENSITY:
        errors.append(f"emotional_intensity must be one of {sorted(VALID_INTENSITY)}")
    if payload.get("candidate_status") not in VALID_STATUS:
        errors.append(f"candidate_status must be one of {sorted(VALID_STATUS)}")

    if not _list_of_strings(payload.get("source_reviews")):
        errors.append("source_reviews must be a non-empty list of strings")
    if not isinstance(payload.get("evidence_count"), int) or payload.get("evidence_count") < 1:
        errors.append("evidence_count must be a positive integer")
    if not isinstance(payload.get("cool_down_review_completed"), bool):
        errors.append("cool_down_review_completed must be boolean")

    for key in (
        "candidate_id",
        "proposed_rule",
        "rule_scope",
        "retirement_path",
        "next_review",
        "policy_boundary",
        "authority_boundary",
    ):
        if not _nonempty(payload.get(key)):
            errors.append(f"{key} must be a non-empty string")

    basis = payload.get("pattern_basis")
    status = payload.get("candidate_status")
    evidence_count = payload.get("evidence_count")
    if basis == "single_anecdote" and status == "candidate":
        errors.append("single anecdotes cannot become candidate rules without more evidence or high-severity rationale")
    if evidence_count < 2 and basis != "high_severity" and status == "candidate":
        errors.append("candidate rules need multiple examples unless high_severity is declared")

    if payload.get("emotional_intensity") in {"high", "extreme"} and status == "candidate":
        if payload.get("cool_down_review_completed") is not True:
            errors.append("emotionally intense candidate rules require cool_down_review_completed=true")

    proposed = str(payload.get("proposed_rule", ""))
    if OVERREACTION_RE.search(proposed) and status == "candidate":
        errors.append("candidate rules must not use absolute overreaction language")

    policy = str(payload.get("policy_boundary", "")).lower()
    if "candidate only" not in policy or "no policy activation" not in policy:
        errors.append("policy_boundary must state candidate only and no policy activation")

    boundary = str(payload.get("authority_boundary", "")).lower()
    if "does not authorize" not in boundary:
        errors.append("authority_boundary must state that this candidate does not authorize action")

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
        print("Usage: python scripts/validate_pgi_review_to_rule_candidate.py <payload.json> [...]")
        return 2
    failed = False
    results = []
    for raw in args:
        path = Path(raw)
        ok, errors = validate_file(path)
        failed = failed or not ok
        results.append({"path": str(path), "valid": ok, "errors": errors})
    print(json.dumps({"tool": "pgi-review-to-rule-candidate-validator", "results": results}, indent=2))
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
