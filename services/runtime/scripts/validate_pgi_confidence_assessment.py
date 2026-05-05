#!/usr/bin/env python3
"""Validate PGI ConfidenceAssessment payloads.

Local-only validator for calibrated confidence records. It does not authorize
action and does not prove correctness.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

VALID_BANDS = {"LOW", "MEDIUM", "HIGH", "VERY_HIGH"}
VALID_CALIBRATION = {"uncalibrated", "insufficient_history", "calibrated"}

REQUIRED = [
    "object_type",
    "schema_version",
    "assessment_id",
    "claim",
    "claim_type",
    "confidence",
    "confidence_band",
    "evidence_refs",
    "base_rate",
    "uncertainty",
    "calibration_status",
    "review_trigger",
    "authority_boundary",
]


def _expected_band(confidence: float) -> str:
    if confidence < 0.4:
        return "LOW"
    if confidence < 0.7:
        return "MEDIUM"
    if confidence < 0.9:
        return "HIGH"
    return "VERY_HIGH"


def validate_payload(payload: dict) -> list[str]:
    errors: list[str] = []
    for key in REQUIRED:
        if key not in payload:
            errors.append(f"missing required field: {key}")
    if errors:
        return errors

    if payload.get("object_type") != "PGIConfidenceAssessment":
        errors.append("object_type must be PGIConfidenceAssessment")

    confidence = payload.get("confidence")
    if not isinstance(confidence, (int, float)) or isinstance(confidence, bool):
        errors.append("confidence must be a number")
        confidence = None
    elif confidence < 0 or confidence > 1:
        errors.append("confidence must be between 0 and 1")

    band = payload.get("confidence_band")
    if band not in VALID_BANDS:
        errors.append(f"confidence_band must be one of {sorted(VALID_BANDS)}")
    elif confidence is not None and band != _expected_band(float(confidence)):
        errors.append(f"confidence_band must be {_expected_band(float(confidence))} for confidence={confidence}")

    evidence_refs = payload.get("evidence_refs")
    if not isinstance(evidence_refs, list) or not evidence_refs:
        errors.append("evidence_refs must be a non-empty array")

    uncertainty = payload.get("uncertainty")
    if not isinstance(uncertainty, list) or not uncertainty:
        errors.append("uncertainty must be a non-empty array")

    if payload.get("calibration_status") not in VALID_CALIBRATION:
        errors.append(f"calibration_status must be one of {sorted(VALID_CALIBRATION)}")

    base_rate = payload.get("base_rate")
    if confidence is not None and confidence >= 0.7:
        if not isinstance(base_rate, (int, float)) or isinstance(base_rate, bool):
            errors.append("confidence >= 0.7 requires numeric base_rate")
        elif base_rate < 0 or base_rate > 1:
            errors.append("base_rate must be between 0 and 1")

    authority = str(payload.get("authority_boundary", "")).lower()
    if "does not authorize" not in authority and "not authorization" not in authority:
        errors.append("authority_boundary must state that confidence does not authorize action")

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
        print("Usage: python scripts/validate_pgi_confidence_assessment.py <payload.json> [...]")
        return 2

    failed = False
    results = []
    for raw in args:
        path = Path(raw)
        ok, errors = validate_file(path)
        failed = failed or not ok
        results.append({"path": str(path), "valid": ok, "errors": errors})

    print(json.dumps({"tool": "pgi-confidence-assessment-validator", "results": results}, indent=2))
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
