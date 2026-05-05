#!/usr/bin/env python3
"""Validate PGI EthicalTriadReview payloads."""

from __future__ import annotations

import json
import sys
from pathlib import Path

REQUIRED = [
    "object_type",
    "schema_version",
    "review_id",
    "action_or_claim",
    "consequence_review",
    "rule_review",
    "character_review",
    "tradeoffs",
    "decision_posture",
    "authority_boundary",
]

VALID_POSTURES = {"READY_WITHOUT_AUTHORIZATION", "DEGRADED", "BLOCKED", "NEEDS_REVIEW"}


def _nonempty_string(value) -> bool:
    return isinstance(value, str) and bool(value.strip())


def validate_payload(payload: dict) -> list[str]:
    errors: list[str] = []
    for key in REQUIRED:
        if key not in payload:
            errors.append(f"missing required field: {key}")
    if errors:
        return errors

    if payload.get("object_type") != "PGIEthicalTriadReview":
        errors.append("object_type must be PGIEthicalTriadReview")

    for key in ("action_or_claim", "consequence_review", "rule_review", "character_review"):
        if not _nonempty_string(payload.get(key)):
            errors.append(f"{key} must be a non-empty string")

    tradeoffs = payload.get("tradeoffs")
    if not isinstance(tradeoffs, list) or not tradeoffs:
        errors.append("tradeoffs must be a non-empty array")

    if payload.get("decision_posture") not in VALID_POSTURES:
        errors.append(f"decision_posture must be one of {sorted(VALID_POSTURES)}")

    boundary = str(payload.get("authority_boundary", "")).lower()
    if "does not authorize" not in boundary and "not authorization" not in boundary:
        errors.append("authority_boundary must state that review does not authorize action")

    combined = " ".join(str(payload.get(k, "")) for k in ("consequence_review", "rule_review", "character_review"))
    if "profit proves right" in combined.lower() or "good outcome proves good process" in combined.lower():
        errors.append("review must not use good outcome as proof of good process")

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
        print("Usage: python scripts/validate_pgi_ethical_triad_review.py <review.json> [...]")
        return 2
    failed = False
    results = []
    for raw in args:
        path = Path(raw)
        ok, errors = validate_file(path)
        failed = failed or not ok
        results.append({"path": str(path), "valid": ok, "errors": errors})
    print(json.dumps({"tool": "pgi-ethical-triad-review-validator", "results": results}, indent=2))
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
