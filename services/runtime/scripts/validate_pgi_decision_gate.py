#!/usr/bin/env python3
"""Validate PGI DecisionGate payloads.

DecisionGate is review evidence only. READY_WITHOUT_AUTHORIZATION does not
authorize execution, merge, deploy, trade, or external action.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

REQUIRED = [
    "object_type",
    "schema_version",
    "decision_id",
    "action_or_claim",
    "risk_level",
    "claim_ref",
    "evidence_refs",
    "confidence_assessment_ref",
    "failure_predicate_ref",
    "constitution_checks",
    "ethical_triad_review_ref",
    "reversibility",
    "downside",
    "decision_posture",
    "missing_evidence",
    "review_trigger",
    "authority_boundary",
]

VALID_RISK = {"low", "medium", "high", "irreversible"}
VALID_REVERSIBILITY = {"reversible", "partially_reversible", "irreversible", "unknown"}
VALID_POSTURE = {"READY_WITHOUT_AUTHORIZATION", "DEGRADED", "BLOCKED", "NEEDS_REVIEW"}
VALID_CHECK_RESULT = {"pass", "warn", "block"}


def _nonempty_string(value) -> bool:
    return isinstance(value, str) and bool(value.strip())


def validate_payload(payload: dict) -> list[str]:
    errors: list[str] = []
    for key in REQUIRED:
        if key not in payload:
            errors.append(f"missing required field: {key}")
    if errors:
        return errors

    if payload.get("object_type") != "PGIDecisionGate":
        errors.append("object_type must be PGIDecisionGate")

    if payload.get("risk_level") not in VALID_RISK:
        errors.append(f"risk_level must be one of {sorted(VALID_RISK)}")
    if payload.get("reversibility") not in VALID_REVERSIBILITY:
        errors.append(f"reversibility must be one of {sorted(VALID_REVERSIBILITY)}")
    if payload.get("decision_posture") not in VALID_POSTURE:
        errors.append(f"decision_posture must be one of {sorted(VALID_POSTURE)}")

    for key in (
        "decision_id",
        "action_or_claim",
        "claim_ref",
        "confidence_assessment_ref",
        "failure_predicate_ref",
        "ethical_triad_review_ref",
        "downside",
        "review_trigger",
    ):
        if not _nonempty_string(payload.get(key)):
            errors.append(f"{key} must be a non-empty string")

    evidence_refs = payload.get("evidence_refs")
    if not isinstance(evidence_refs, list) or not evidence_refs:
        errors.append("evidence_refs must be a non-empty array")

    missing = payload.get("missing_evidence")
    if not isinstance(missing, list):
        errors.append("missing_evidence must be an array")
        missing = []

    if payload.get("decision_posture") == "READY_WITHOUT_AUTHORIZATION" and missing:
        errors.append("READY_WITHOUT_AUTHORIZATION cannot have missing_evidence")

    checks = payload.get("constitution_checks")
    if not isinstance(checks, list) or not checks:
        errors.append("constitution_checks must be a non-empty array")
    else:
        for idx, check in enumerate(checks, 1):
            if not isinstance(check, dict):
                errors.append(f"constitution_checks[{idx}] must be an object")
                continue
            if not _nonempty_string(check.get("rule_id")):
                errors.append(f"constitution_checks[{idx}]: missing rule_id")
            if check.get("result") not in VALID_CHECK_RESULT:
                errors.append(f"constitution_checks[{idx}]: result must be one of {sorted(VALID_CHECK_RESULT)}")

    if payload.get("risk_level") in {"high", "irreversible"} and payload.get("decision_posture") == "READY_WITHOUT_AUTHORIZATION":
        if payload.get("reversibility") == "unknown":
            errors.append("high/irreversible READY posture cannot have unknown reversibility")

    boundary = str(payload.get("authority_boundary", "")).lower()
    if "does not authorize" not in boundary or "execution" not in boundary:
        errors.append("authority_boundary must state that DecisionGate does not authorize execution")

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
        print("Usage: python scripts/validate_pgi_decision_gate.py <decision-gate.json> [...]")
        return 2
    failed = False
    results = []
    for raw in args:
        path = Path(raw)
        ok, errors = validate_file(path)
        failed = failed or not ok
        results.append({"path": str(path), "valid": ok, "errors": errors})
    print(json.dumps({"tool": "pgi-decision-gate-validator", "results": results}, indent=2))
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
