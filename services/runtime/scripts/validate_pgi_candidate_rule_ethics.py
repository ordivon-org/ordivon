#!/usr/bin/env python3
"""Validate PGI CandidateRuleEthicsReview payloads."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

REQUIRED = [
    "object_type",
    "schema_version",
    "review_id",
    "candidate_rule_id",
    "rule_text",
    "consequence_check",
    "rule_boundary_check",
    "virtue_check",
    "false_positive_cost",
    "human_cost",
    "exception_path",
    "expiry_or_review_date",
    "over_control_risk",
    "candidate_status",
    "policy_activation_no_go",
    "authority_boundary",
]

VALID_RISK = {"none", "watch", "block"}
VALID_STATUS = {"candidate", "needs_revision", "reject"}
OVERCONTROL_RE = re.compile(r"track\s+everything|always\s+block|never\s+allow|no\s+exceptions|total\s+control", re.I)


def _nonempty(value) -> bool:
    return isinstance(value, str) and bool(value.strip())


def validate_payload(payload: dict) -> list[str]:
    errors: list[str] = []
    for key in REQUIRED:
        if key not in payload:
            errors.append(f"missing required field: {key}")
    if errors:
        return errors

    if payload.get("object_type") != "PGICandidateRuleEthicsReview":
        errors.append("object_type must be PGICandidateRuleEthicsReview")
    if payload.get("over_control_risk") not in VALID_RISK:
        errors.append(f"over_control_risk must be one of {sorted(VALID_RISK)}")
    if payload.get("candidate_status") not in VALID_STATUS:
        errors.append(f"candidate_status must be one of {sorted(VALID_STATUS)}")
    if payload.get("policy_activation_no_go") is not True:
        errors.append("policy_activation_no_go must remain true")

    for key in (
        "review_id",
        "candidate_rule_id",
        "rule_text",
        "consequence_check",
        "rule_boundary_check",
        "virtue_check",
        "false_positive_cost",
        "human_cost",
        "exception_path",
        "expiry_or_review_date",
        "authority_boundary",
    ):
        if not _nonempty(payload.get(key)):
            errors.append(f"{key} must be a non-empty string")

    if payload.get("over_control_risk") == "block" and payload.get("candidate_status") == "candidate":
        errors.append("block-level over-control risk cannot remain candidate")

    combined = " ".join(
        str(payload.get(key, "")) for key in ("rule_text", "rule_boundary_check", "exception_path", "human_cost")
    )
    if OVERCONTROL_RE.search(combined) and payload.get("candidate_status") == "candidate":
        errors.append("candidate rules must not contain over-control language")

    exception_path = str(payload.get("exception_path", "")).lower()
    if "exception" not in exception_path and "bypass" not in exception_path and "review" not in exception_path:
        errors.append("exception_path must name an exception, bypass, or review route")

    boundary = str(payload.get("authority_boundary", "")).lower()
    if "does not authorize" not in boundary or "candidate only" not in boundary:
        errors.append("authority_boundary must state this does not authorize action and is candidate only")

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
        print("Usage: python scripts/validate_pgi_candidate_rule_ethics.py <payload.json> [...]")
        return 2
    failed = False
    results = []
    for raw in args:
        path = Path(raw)
        ok, errors = validate_file(path)
        failed = failed or not ok
        results.append({"path": str(path), "valid": ok, "errors": errors})
    print(json.dumps({"tool": "pgi-candidate-rule-ethics-validator", "results": results}, indent=2))
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
