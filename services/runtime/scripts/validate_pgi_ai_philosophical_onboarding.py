#!/usr/bin/env python3
"""Validate PGI AIPhilosophicalOnboarding payloads."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

REQUIRED = [
    "object_type",
    "schema_version",
    "onboarding_id",
    "ai_role",
    "allowed_posture",
    "forbidden_patterns",
    "required_boundaries",
    "red_team_prompts",
    "correction_behavior",
    "human_agency_statement",
    "authority_boundary",
]

VALID_ROLES = {"coding_agent", "reviewer", "researcher", "planner", "companion_governance_assistant"}
FORBIDDEN = {
    "vague_motivation",
    "false_certainty",
    "therapy_claim",
    "financial_advice_claim",
    "action_authorization",
    "identity_verdict",
    "policy_activation",
    "privacy_overreach",
}
AUTHORITY_RE = re.compile(r"\b(?:you must|I authorize|approved to|definitely|diagnose|buy now|execute now)\b", re.I)


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

    if payload.get("object_type") != "PGIAIPhilosophicalOnboarding":
        errors.append("object_type must be PGIAIPhilosophicalOnboarding")
    if payload.get("ai_role") not in VALID_ROLES:
        errors.append(f"ai_role must be one of {sorted(VALID_ROLES)}")

    for key in ("forbidden_patterns", "required_boundaries", "red_team_prompts"):
        if not _list_of_strings(payload.get(key)):
            errors.append(f"{key} must be a non-empty list of strings")

    for key in (
        "onboarding_id",
        "allowed_posture",
        "correction_behavior",
        "human_agency_statement",
        "authority_boundary",
    ):
        if not _nonempty(payload.get(key)):
            errors.append(f"{key} must be a non-empty string")

    forbidden = set(payload.get("forbidden_patterns", []))
    missing = sorted(FORBIDDEN - forbidden)
    if missing:
        errors.append(f"forbidden_patterns missing required patterns: {missing}")

    required_boundaries = " ".join(payload.get("required_boundaries", [])).lower()
    for phrase in (
        "does not authorize action",
        "not therapy",
        "not financial advice",
        "candidate rule is not policy",
        "privacy boundary",
    ):
        if phrase not in required_boundaries:
            errors.append(f"required_boundaries must include '{phrase}'")

    combined = " ".join(
        [str(payload.get("allowed_posture", "")), str(payload.get("correction_behavior", ""))]
        + list(payload.get("red_team_prompts", []))
    )
    if AUTHORITY_RE.search(combined):
        errors.append("onboarding text must not contain authority-overreach language")

    agency = str(payload.get("human_agency_statement", "")).lower()
    if "human" not in agency or "decision" not in agency:
        errors.append("human_agency_statement must preserve human decision agency")

    boundary = str(payload.get("authority_boundary", "")).lower()
    if "does not authorize" not in boundary or "not an authority over the creator" not in boundary:
        errors.append("authority_boundary must state this does not authorize action and is not an authority over the creator")

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
        print("Usage: python scripts/validate_pgi_ai_philosophical_onboarding.py <payload.json> [...]")
        return 2
    failed = False
    results = []
    for raw in args:
        path = Path(raw)
        ok, errors = validate_file(path)
        failed = failed or not ok
        results.append({"path": str(path), "valid": ok, "errors": errors})
    print(json.dumps({"tool": "pgi-ai-philosophical-onboarding-validator", "results": results}, indent=2))
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
