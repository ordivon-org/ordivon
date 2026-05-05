#!/usr/bin/env python3
"""Validate PGI BodyEnergyReview payloads."""

from __future__ import annotations

import json
import sys
from pathlib import Path

REQUIRED = [
    "object_type",
    "schema_version",
    "review_id",
    "energy_state",
    "fatigue_level",
    "decision_risk_level",
    "major_decision_allowed",
    "body_signal_summary",
    "minimum_next_step",
    "raw_private_data_recorded",
    "privacy_boundary",
    "authority_boundary",
]

VALID_ENERGY = {"stable", "tired", "exhausted", "ill", "unknown"}
VALID_FATIGUE = {"low", "moderate", "high", "extreme", "unknown"}
VALID_RISK = {"low", "medium", "high", "irreversible"}


def _nonempty(value) -> bool:
    return isinstance(value, str) and bool(value.strip())


def validate_payload(payload: dict) -> list[str]:
    errors: list[str] = []
    for key in REQUIRED:
        if key not in payload:
            errors.append(f"missing required field: {key}")
    if errors:
        return errors

    if payload.get("object_type") != "PGIBodyEnergyReview":
        errors.append("object_type must be PGIBodyEnergyReview")
    if payload.get("energy_state") not in VALID_ENERGY:
        errors.append(f"energy_state must be one of {sorted(VALID_ENERGY)}")
    if payload.get("fatigue_level") not in VALID_FATIGUE:
        errors.append(f"fatigue_level must be one of {sorted(VALID_FATIGUE)}")
    if payload.get("decision_risk_level") not in VALID_RISK:
        errors.append(f"decision_risk_level must be one of {sorted(VALID_RISK)}")

    if not isinstance(payload.get("major_decision_allowed"), bool):
        errors.append("major_decision_allowed must be boolean")
    if not isinstance(payload.get("raw_private_data_recorded"), bool):
        errors.append("raw_private_data_recorded must be boolean")

    for key in ("review_id", "body_signal_summary", "minimum_next_step", "privacy_boundary", "authority_boundary"):
        if not _nonempty(payload.get(key)):
            errors.append(f"{key} must be a non-empty string")

    stop_state = payload.get("energy_state") in {"exhausted", "ill"} or payload.get("fatigue_level") in {
        "high",
        "extreme",
    }
    high_consequence = payload.get("decision_risk_level") in {"high", "irreversible"}
    if stop_state and high_consequence and payload.get("major_decision_allowed") is not False:
        errors.append("high-consequence decisions must be blocked under exhausted/ill/high-fatigue states")

    if payload.get("raw_private_data_recorded") is not False:
        errors.append("raw_private_data_recorded must remain false for PGI-2.05 seed reviews")

    privacy = str(payload.get("privacy_boundary", "")).lower()
    if "no intimate raw data" not in privacy and "non-invasive" not in privacy:
        errors.append("privacy_boundary must state non-invasive/no intimate raw data handling")

    boundary = str(payload.get("authority_boundary", "")).lower()
    if "does not authorize" not in boundary or "not medical advice" not in boundary:
        errors.append("authority_boundary must state this does not authorize action and is not medical advice")

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
        print("Usage: python scripts/validate_pgi_body_energy_review.py <payload.json> [...]")
        return 2
    failed = False
    results = []
    for raw in args:
        path = Path(raw)
        ok, errors = validate_file(path)
        failed = failed or not ok
        results.append({"path": str(path), "valid": ok, "errors": errors})
    print(json.dumps({"tool": "pgi-body-energy-review-validator", "results": results}, indent=2))
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
