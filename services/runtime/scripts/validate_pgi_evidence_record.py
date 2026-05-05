#!/usr/bin/env python3
"""Validate PGI EvidenceRecord payloads.

Local-only validator. Does not call network APIs or authorize action.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

VALID_KINDS = {
    "file_read",
    "command_output",
    "test_result",
    "human_review",
    "receipt",
    "external_source",
    "observation",
    "absence",
    "contradiction",
}

VALID_REPRODUCIBILITY = {"reproducible", "contextual", "non_reproducible", "unknown"}
VALID_FRESHNESS = {"CURRENT", "STALE", "DEGRADED", "MISSING"}
AUTHORITY_BOUNDARY_MARKERS = [
    "does not authorize",
    "not authorization",
    "evidence, not authority",
    "evidence not authority",
    "does not grant authority",
]

REQUIRED = [
    "object_type",
    "schema_version",
    "evidence_id",
    "evidence_kind",
    "source",
    "observed_at",
    "actor",
    "scope",
    "reproducibility",
    "freshness",
    "confidence",
    "supports_claims",
    "limitations",
    "authority_boundary",
]


def validate_payload(payload: dict) -> list[str]:
    errors: list[str] = []

    for key in REQUIRED:
        if key not in payload:
            errors.append(f"missing required field: {key}")

    if errors:
        return errors

    if payload.get("object_type") != "PGIEvidenceRecord":
        errors.append("object_type must be PGIEvidenceRecord")

    if not isinstance(payload.get("schema_version"), str) or not payload["schema_version"].startswith("0."):
        errors.append("schema_version must be prototype string like 0.1")

    if payload.get("evidence_kind") not in VALID_KINDS:
        errors.append(f"evidence_kind must be one of {sorted(VALID_KINDS)}")

    source = payload.get("source")
    if not isinstance(source, dict):
        errors.append("source must be an object")
        source = {}

    if payload.get("evidence_kind") == "file_read" and not source.get("path"):
        errors.append("file_read evidence requires source.path")
    if payload.get("evidence_kind") == "command_output" and not source.get("command"):
        errors.append("command_output evidence requires source.command")

    if payload.get("reproducibility") not in VALID_REPRODUCIBILITY:
        errors.append(f"reproducibility must be one of {sorted(VALID_REPRODUCIBILITY)}")

    freshness = payload.get("freshness")
    if not isinstance(freshness, dict):
        errors.append("freshness must be an object")
        freshness = {}
    if freshness.get("status") not in VALID_FRESHNESS:
        errors.append(f"freshness.status must be one of {sorted(VALID_FRESHNESS)}")
    if freshness.get("status") == "CURRENT" and not freshness.get("last_verified"):
        errors.append("CURRENT evidence requires freshness.last_verified")

    confidence = payload.get("confidence")
    if not isinstance(confidence, (int, float)) or isinstance(confidence, bool):
        errors.append("confidence must be a number")
    elif confidence < 0 or confidence > 1:
        errors.append("confidence must be between 0 and 1")

    supports_claims = payload.get("supports_claims")
    if not isinstance(supports_claims, list) or not supports_claims:
        errors.append("supports_claims must be a non-empty array")

    limitations = payload.get("limitations")
    if not isinstance(limitations, list):
        errors.append("limitations must be an array")

    authority_boundary = str(payload.get("authority_boundary", "")).lower()
    if not any(marker in authority_boundary for marker in AUTHORITY_BOUNDARY_MARKERS):
        errors.append("authority_boundary must state that evidence does not authorize action")

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
        print("Usage: python scripts/validate_pgi_evidence_record.py <payload.json> [payload2.json ...]")
        return 2

    failed = False
    results = []
    for raw in args:
        path = Path(raw)
        ok, errors = validate_file(path)
        failed = failed or not ok
        results.append({"path": str(path), "valid": ok, "errors": errors})

    print(json.dumps({"tool": "pgi-evidence-record-validator", "results": results}, indent=2))
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
