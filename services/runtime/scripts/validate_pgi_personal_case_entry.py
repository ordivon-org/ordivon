#!/usr/bin/env python3
"""Validate PGI PersonalCaseEntry payloads."""

from __future__ import annotations

import json
import sys
from pathlib import Path

REQUIRED = [
    "object_type",
    "schema_version",
    "case_id",
    "domain",
    "case_type",
    "privacy_level",
    "summary",
    "artifact_refs",
    "review_refs",
    "lesson_summary",
    "self_model_refs",
    "public_safe_summary",
    "raw_private_data_recorded",
    "externalization_allowed",
    "authority_boundary",
]

VALID_DOMAINS = {"ai_work", "body", "builder", "emotion", "finance", "learning", "relationship"}
VALID_CASE_TYPES = {"decision", "review", "failure", "success", "constraint", "repair", "learning"}
VALID_PRIVACY = {"private", "sensitive", "public_safe"}


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

    if payload.get("object_type") != "PGIPersonalCaseEntry":
        errors.append("object_type must be PGIPersonalCaseEntry")
    if payload.get("domain") not in VALID_DOMAINS:
        errors.append(f"domain must be one of {sorted(VALID_DOMAINS)}")
    if payload.get("case_type") not in VALID_CASE_TYPES:
        errors.append(f"case_type must be one of {sorted(VALID_CASE_TYPES)}")
    if payload.get("privacy_level") not in VALID_PRIVACY:
        errors.append(f"privacy_level must be one of {sorted(VALID_PRIVACY)}")

    for key in ("case_id", "summary", "lesson_summary", "public_safe_summary", "authority_boundary"):
        if not _nonempty(payload.get(key)):
            errors.append(f"{key} must be a non-empty string")

    for key in ("artifact_refs", "review_refs"):
        if not _list_of_strings(payload.get(key)) or not payload.get(key):
            errors.append(f"{key} must be a non-empty list of strings")
    if not _list_of_strings(payload.get("self_model_refs")):
        errors.append("self_model_refs must be a list of strings; use ['none'] when not linked yet")

    for key in ("raw_private_data_recorded", "externalization_allowed"):
        if not isinstance(payload.get(key), bool):
            errors.append(f"{key} must be boolean")

    if payload.get("raw_private_data_recorded") is not False:
        errors.append("raw_private_data_recorded must remain false for casebook entries")
    if payload.get("externalization_allowed") is True and payload.get("privacy_level") != "public_safe":
        errors.append("externalization_allowed=true requires privacy_level=public_safe")

    public_summary = str(payload.get("public_safe_summary", "")).lower()
    if "redacted" not in public_summary and payload.get("privacy_level") != "public_safe":
        errors.append("non-public cases need a redacted public_safe_summary")

    boundary = str(payload.get("authority_boundary", "")).lower()
    if "does not authorize" not in boundary or "not publication approval" not in boundary:
        errors.append("authority_boundary must state this does not authorize action and is not publication approval")

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
        print("Usage: python scripts/validate_pgi_personal_case_entry.py <payload.json> [...]")
        return 2
    failed = False
    results = []
    for raw in args:
        path = Path(raw)
        ok, errors = validate_file(path)
        failed = failed or not ok
        results.append({"path": str(path), "valid": ok, "errors": errors})
    print(json.dumps({"tool": "pgi-personal-case-entry-validator", "results": results}, indent=2))
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
