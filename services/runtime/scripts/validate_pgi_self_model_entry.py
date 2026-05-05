#!/usr/bin/env python3
"""Validate PGI SelfModelEntry payloads."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

REQUIRED = [
    "object_type",
    "schema_version",
    "entry_id",
    "domain",
    "update_type",
    "observation",
    "evidence_refs",
    "pattern_status",
    "self_language",
    "verdict_language_present",
    "next_review",
    "authority_boundary",
]

VALID_DOMAINS = {
    "body",
    "builder",
    "emotion",
    "finance",
    "learning",
    "relationship",
    "social_commitment",
    "values",
}
VALID_UPDATE_TYPES = {
    "bias",
    "capability",
    "constraint",
    "direction",
    "recurring_failure",
    "strength",
    "value",
}
VALID_PATTERN_STATUS = {"not_enough_evidence", "candidate_pattern", "confirmed_pattern", "retired"}
PUNITIVE_RE = re.compile(
    r"\bI\s+am\s+(?:always|never|broken|lazy|a\s+failure|doomed|hopeless)\b|"
    r"\bthis\s+proves\s+who\s+I\s+am\b|"
    r"\bfixed\s+identity\b",
    re.I,
)


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

    if payload.get("object_type") != "PGISelfModelEntry":
        errors.append("object_type must be PGISelfModelEntry")
    if payload.get("domain") not in VALID_DOMAINS:
        errors.append(f"domain must be one of {sorted(VALID_DOMAINS)}")
    if payload.get("update_type") not in VALID_UPDATE_TYPES:
        errors.append(f"update_type must be one of {sorted(VALID_UPDATE_TYPES)}")
    if payload.get("pattern_status") not in VALID_PATTERN_STATUS:
        errors.append(f"pattern_status must be one of {sorted(VALID_PATTERN_STATUS)}")

    for key in ("entry_id", "observation", "self_language", "next_review", "authority_boundary"):
        if not _nonempty(payload.get(key)):
            errors.append(f"{key} must be a non-empty string")

    if not isinstance(payload.get("verdict_language_present"), bool):
        errors.append("verdict_language_present must be boolean")
    if not _list_of_strings(payload.get("evidence_refs")):
        errors.append("evidence_refs must be a non-empty list of strings")

    if payload.get("verdict_language_present") is not False:
        errors.append("verdict_language_present must remain false")

    self_language = str(payload.get("self_language", ""))
    if PUNITIVE_RE.search(self_language):
        errors.append("self_language must not contain fixed or punitive identity verdicts")

    if payload.get("pattern_status") == "confirmed_pattern" and len(payload.get("evidence_refs", [])) < 2:
        errors.append("confirmed_pattern requires at least two evidence_refs")

    if payload.get("pattern_status") == "not_enough_evidence":
        observation = str(payload.get("observation", "")).lower()
        if "not enough evidence" not in observation and "insufficient evidence" not in observation:
            errors.append("not_enough_evidence entries must explicitly name evidence insufficiency")

    boundary = str(payload.get("authority_boundary", "")).lower()
    if "does not authorize" not in boundary or "not a verdict" not in boundary:
        errors.append("authority_boundary must state this does not authorize action and is not a verdict")

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
        print("Usage: python scripts/validate_pgi_self_model_entry.py <payload.json> [...]")
        return 2
    failed = False
    results = []
    for raw in args:
        path = Path(raw)
        ok, errors = validate_file(path)
        failed = failed or not ok
        results.append({"path": str(path), "valid": ok, "errors": errors})
    print(json.dumps({"tool": "pgi-self-model-entry-validator", "results": results}, indent=2))
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
