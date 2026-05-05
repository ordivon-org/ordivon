#!/usr/bin/env python3
"""Validate PGI MemoryContentRecord payloads."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

REQUIRED = [
    "object_type",
    "schema_version",
    "record_id",
    "content_type",
    "source_ref",
    "source_receipt",
    "last_verified",
    "freshness_state",
    "authority_class",
    "claim_status",
    "contamination_flags",
    "safe_use",
    "next_review",
    "privacy_boundary",
    "authority_boundary",
]

VALID_CONTENT_TYPES = {
    "ai_note",
    "casebook",
    "decision_note",
    "doc_summary",
    "memory_note",
    "receipt_summary",
    "review_summary",
}
VALID_FRESHNESS = {"current", "stale", "superseded", "unknown"}
VALID_AUTHORITY = {"source_of_truth", "supporting_evidence", "current_status", "advisory", "private_note"}
VALID_CLAIM_STATUS = {"fact", "interpretation", "candidate_rule", "policy", "degraded", "unknown"}
VALID_SAFE_USE = {"safe_to_use", "use_with_caution", "do_not_use"}
CONTAMINATION = {
    "candidate_rule_as_policy",
    "degraded_as_fact",
    "stale_as_current",
    "private_as_public",
    "missing_source",
    "none",
}

BAD_SAFE_RE = re.compile(r"use\s+as\s+truth|treat\s+as\s+policy|publish\s+as\s+public", re.I)


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

    if payload.get("object_type") != "PGIMemoryContentRecord":
        errors.append("object_type must be PGIMemoryContentRecord")
    if payload.get("content_type") not in VALID_CONTENT_TYPES:
        errors.append(f"content_type must be one of {sorted(VALID_CONTENT_TYPES)}")
    if payload.get("freshness_state") not in VALID_FRESHNESS:
        errors.append(f"freshness_state must be one of {sorted(VALID_FRESHNESS)}")
    if payload.get("authority_class") not in VALID_AUTHORITY:
        errors.append(f"authority_class must be one of {sorted(VALID_AUTHORITY)}")
    if payload.get("claim_status") not in VALID_CLAIM_STATUS:
        errors.append(f"claim_status must be one of {sorted(VALID_CLAIM_STATUS)}")
    if payload.get("safe_use") not in VALID_SAFE_USE:
        errors.append(f"safe_use must be one of {sorted(VALID_SAFE_USE)}")

    for key in (
        "record_id",
        "source_ref",
        "source_receipt",
        "last_verified",
        "next_review",
        "privacy_boundary",
        "authority_boundary",
    ):
        if not _nonempty(payload.get(key)):
            errors.append(f"{key} must be a non-empty string")

    flags = payload.get("contamination_flags")
    if not _list_of_strings(flags):
        errors.append("contamination_flags must be a non-empty list of strings")
        flags = []
    else:
        invalid = sorted(set(flags) - CONTAMINATION)
        if invalid:
            errors.append(f"contamination_flags contains invalid values: {invalid}")
        if "none" in flags and len(flags) > 1:
            errors.append("contamination_flags cannot combine none with other flags")

    if payload.get("source_receipt").strip().lower() in {"none", "missing", "unknown"}:
        if "missing_source" not in flags:
            errors.append("missing source_receipt must set missing_source contamination flag")

    if payload.get("freshness_state") in {"stale", "superseded", "unknown"}:
        if payload.get("safe_use") == "safe_to_use":
            errors.append("stale/superseded/unknown memory cannot be safe_to_use")

    if payload.get("claim_status") == "candidate_rule" and payload.get("authority_class") == "source_of_truth":
        errors.append("CandidateRule memory cannot be source_of_truth")
    if "candidate_rule_as_policy" in flags and payload.get("safe_use") != "do_not_use":
        errors.append("candidate_rule_as_policy contamination requires do_not_use")
    if "degraded_as_fact" in flags and payload.get("safe_use") != "do_not_use":
        errors.append("degraded_as_fact contamination requires do_not_use")
    if "private_as_public" in flags and payload.get("safe_use") != "do_not_use":
        errors.append("private_as_public contamination requires do_not_use")

    safe_use_text = str(payload.get("safe_use", ""))
    next_review = str(payload.get("next_review", ""))
    if BAD_SAFE_RE.search(safe_use_text) or BAD_SAFE_RE.search(next_review):
        errors.append("safe_use/next_review must not instruct truth, policy, or public laundering")

    privacy = str(payload.get("privacy_boundary", "")).lower()
    if "no private-to-public promotion" not in privacy and "privacy reviewed" not in privacy:
        errors.append("privacy_boundary must state privacy review/no private-to-public promotion")

    boundary = str(payload.get("authority_boundary", "")).lower()
    if "does not authorize" not in boundary or "not source of truth by itself" not in boundary:
        errors.append(
            "authority_boundary must state this does not authorize action and is not source of truth by itself"
        )

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
        print("Usage: python scripts/validate_pgi_memory_content_record.py <payload.json> [...]")
        return 2
    failed = False
    results = []
    for raw in args:
        path = Path(raw)
        ok, errors = validate_file(path)
        failed = failed or not ok
        results.append({"path": str(path), "valid": ok, "errors": errors})
    print(json.dumps({"tool": "pgi-memory-content-record-validator", "results": results}, indent=2))
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
