#!/usr/bin/env python3
"""Validate PGI AntiOverforceIntake payloads."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

REQUIRED = [
    "object_type",
    "schema_version",
    "intake_id",
    "domain",
    "stalled_work",
    "constraint_classes",
    "body_energy_signal",
    "emotion_signal",
    "strategic_signal",
    "current_impulse",
    "chosen_response",
    "next_safe_step",
    "review_time",
    "authority_boundary",
]

VALID_DOMAINS = {
    "ai_work",
    "body",
    "coding",
    "emotion",
    "finance",
    "learning",
    "project",
    "relationship",
}
VALID_CONSTRAINTS = {
    "physical",
    "emotional",
    "strategic",
    "environmental",
    "conceptual",
    "tooling",
    "social",
    "financial",
    "unknown",
}
VALID_RESPONSES = {
    "continue_with_smaller_step",
    "pause",
    "rest",
    "redesign",
    "refuse",
    "seek_help",
    "split_scope",
}

OVERFORCE_RE = re.compile(
    r"try\s+harder|push\s+through|grind\s+harder|force\s+it|work\s+all\s+night|ignore\s+(?:fatigue|panic|pain)",
    re.I,
)
STOP_SIGNAL_RE = re.compile(r"exhausted|sleep\s+debt|panic|acute\s+pain|burnout|dizzy|unsafe", re.I)


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

    if payload.get("object_type") != "PGIAntiOverforceIntake":
        errors.append("object_type must be PGIAntiOverforceIntake")
    if payload.get("domain") not in VALID_DOMAINS:
        errors.append(f"domain must be one of {sorted(VALID_DOMAINS)}")

    constraints = payload.get("constraint_classes")
    if not _list_of_strings(constraints):
        errors.append("constraint_classes must be a list of non-empty strings")
        constraints = []
    else:
        invalid = sorted(set(constraints) - VALID_CONSTRAINTS)
        if invalid:
            errors.append(f"constraint_classes contains invalid values: {invalid}")
        if not constraints:
            errors.append("constraint_classes must not be empty")

    if payload.get("chosen_response") not in VALID_RESPONSES:
        errors.append(f"chosen_response must be one of {sorted(VALID_RESPONSES)}")

    for key in (
        "intake_id",
        "stalled_work",
        "body_energy_signal",
        "emotion_signal",
        "strategic_signal",
        "current_impulse",
        "next_safe_step",
        "review_time",
    ):
        if not _nonempty(payload.get(key)):
            errors.append(f"{key} must be a non-empty string")

    impulse = str(payload.get("current_impulse", ""))
    next_step = str(payload.get("next_safe_step", ""))
    body = str(payload.get("body_energy_signal", ""))
    emotion = str(payload.get("emotion_signal", ""))
    chosen = str(payload.get("chosen_response", ""))

    if OVERFORCE_RE.search(next_step):
        errors.append("next_safe_step must not encode overforce language")

    has_stop_signal = bool(STOP_SIGNAL_RE.search(body) or STOP_SIGNAL_RE.search(emotion))
    if has_stop_signal and chosen == "continue_with_smaller_step":
        errors.append("stop signals require pause/rest/redesign/seek_help/refuse, not continuation")

    if OVERFORCE_RE.search(impulse) and chosen == "continue_with_smaller_step" and "unknown" in constraints:
        errors.append("overforce impulse with unknown constraints cannot continue without constraint classification")

    if {"physical", "emotional"}.intersection(constraints) and chosen == "continue_with_smaller_step":
        if "downshift" not in next_step.lower() and "smaller" not in next_step.lower():
            errors.append("continuation under physical/emotional constraint must explicitly downshift or shrink scope")

    boundary = str(payload.get("authority_boundary", "")).lower()
    if "does not authorize" not in boundary:
        errors.append("authority_boundary must state that this intake does not authorize action")

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
        print("Usage: python scripts/validate_pgi_anti_overforce_intake.py <payload.json> [...]")
        return 2
    failed = False
    results = []
    for raw in args:
        path = Path(raw)
        ok, errors = validate_file(path)
        failed = failed or not ok
        results.append({"path": str(path), "valid": ok, "errors": errors})
    print(json.dumps({"tool": "pgi-anti-overforce-intake-validator", "results": results}, indent=2))
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
