#!/usr/bin/env python3
"""Validate PGI RelationshipEmotionReview payloads."""

from __future__ import annotations

import json
import sys
from pathlib import Path

REQUIRED = [
    "object_type",
    "schema_version",
    "review_id",
    "surface",
    "event_summary",
    "pattern_or_commitment",
    "emotion_class",
    "emotion_intensity",
    "decision_risk_level",
    "decision_delay_required",
    "manipulation_risk",
    "next_repair_or_boundary_step",
    "raw_private_data_recorded",
    "do_not_record_acknowledged",
    "privacy_boundary",
    "authority_boundary",
]

VALID_SURFACES = {"emotion", "relationship", "mixed"}
VALID_EMOTION_CLASS = {"signal", "noise", "unmet_need", "mixed", "unknown"}
VALID_INTENSITY = {"low", "moderate", "high", "extreme", "unknown"}
VALID_RISK_LEVEL = {"low", "medium", "high", "irreversible"}
VALID_MANIPULATION = {"none", "watch", "block"}


def _nonempty(value) -> bool:
    return isinstance(value, str) and bool(value.strip())


def validate_payload(payload: dict) -> list[str]:
    errors: list[str] = []
    for key in REQUIRED:
        if key not in payload:
            errors.append(f"missing required field: {key}")
    if errors:
        return errors

    if payload.get("object_type") != "PGIRelationshipEmotionReview":
        errors.append("object_type must be PGIRelationshipEmotionReview")
    if payload.get("surface") not in VALID_SURFACES:
        errors.append(f"surface must be one of {sorted(VALID_SURFACES)}")
    if payload.get("emotion_class") not in VALID_EMOTION_CLASS:
        errors.append(f"emotion_class must be one of {sorted(VALID_EMOTION_CLASS)}")
    if payload.get("emotion_intensity") not in VALID_INTENSITY:
        errors.append(f"emotion_intensity must be one of {sorted(VALID_INTENSITY)}")
    if payload.get("decision_risk_level") not in VALID_RISK_LEVEL:
        errors.append(f"decision_risk_level must be one of {sorted(VALID_RISK_LEVEL)}")
    if payload.get("manipulation_risk") not in VALID_MANIPULATION:
        errors.append(f"manipulation_risk must be one of {sorted(VALID_MANIPULATION)}")

    for key in (
        "review_id",
        "event_summary",
        "pattern_or_commitment",
        "next_repair_or_boundary_step",
        "privacy_boundary",
        "authority_boundary",
    ):
        if not _nonempty(payload.get(key)):
            errors.append(f"{key} must be a non-empty string")

    for key in ("decision_delay_required", "raw_private_data_recorded", "do_not_record_acknowledged"):
        if not isinstance(payload.get(key), bool):
            errors.append(f"{key} must be boolean")

    if payload.get("raw_private_data_recorded") is not False:
        errors.append("raw_private_data_recorded must remain false for relationship/emotion seed reviews")
    if payload.get("do_not_record_acknowledged") is not True:
        errors.append("do_not_record_acknowledged must be true")

    high_emotion = payload.get("emotion_intensity") in {"high", "extreme"}
    high_decision = payload.get("decision_risk_level") in {"high", "irreversible"}
    if high_emotion and high_decision and payload.get("decision_delay_required") is not True:
        errors.append("high emotion plus high-consequence decision requires decision_delay_required=true")

    if payload.get("manipulation_risk") == "block":
        step = str(payload.get("next_repair_or_boundary_step", "")).lower()
        if not any(word in step for word in ("pause", "repair", "boundary", "seek help", "delay")):
            errors.append("block-level manipulation risk requires pause/repair/boundary/seek-help/delay step")

    privacy = str(payload.get("privacy_boundary", "")).lower()
    if "patterns" not in privacy or "no intimate raw data" not in privacy:
        errors.append("privacy_boundary must state patterns-only and no intimate raw data")

    boundary = str(payload.get("authority_boundary", "")).lower()
    if "does not authorize" not in boundary or "not therapy" not in boundary:
        errors.append("authority_boundary must state this does not authorize action and is not therapy")

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
        print("Usage: python scripts/validate_pgi_relationship_emotion_review.py <payload.json> [...]")
        return 2
    failed = False
    results = []
    for raw in args:
        path = Path(raw)
        ok, errors = validate_file(path)
        failed = failed or not ok
        results.append({"path": str(path), "valid": ok, "errors": errors})
    print(json.dumps({"tool": "pgi-relationship-emotion-review-validator", "results": results}, indent=2))
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
