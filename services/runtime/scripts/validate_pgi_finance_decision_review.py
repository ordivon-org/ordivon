#!/usr/bin/env python3
"""Validate PGI FinanceDecisionReview payloads."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

REQUIRED = [
    "object_type",
    "schema_version",
    "review_id",
    "decision_type",
    "decision_posture",
    "thesis",
    "evidence_summary",
    "base_rate_note",
    "max_loss",
    "time_horizon",
    "review_date",
    "fomo_or_gambling_risk",
    "self_proof_risk",
    "freedom_fragility_assessment",
    "live_trading_no_go",
    "broker_write_boundary",
    "authority_boundary",
]

VALID_DECISIONS = {"buy", "sell", "hold", "position_size", "cash_buffer", "risk_budget", "no_action"}
VALID_POSTURES = {"review_only", "ready_without_authorization", "hold", "reject"}
VALID_RISK = {"none", "watch", "block"}
GUARANTEE_RE = re.compile(r"guaranteed|sure\s+profit|can't\s+lose|must\s+go\s+up", re.I)


def _nonempty(value) -> bool:
    return isinstance(value, str) and bool(value.strip())


def validate_payload(payload: dict) -> list[str]:
    errors: list[str] = []
    for key in REQUIRED:
        if key not in payload:
            errors.append(f"missing required field: {key}")
    if errors:
        return errors

    if payload.get("object_type") != "PGIFinanceDecisionReview":
        errors.append("object_type must be PGIFinanceDecisionReview")
    if payload.get("decision_type") not in VALID_DECISIONS:
        errors.append(f"decision_type must be one of {sorted(VALID_DECISIONS)}")
    if payload.get("decision_posture") not in VALID_POSTURES:
        errors.append(f"decision_posture must be one of {sorted(VALID_POSTURES)}")
    for key in ("fomo_or_gambling_risk", "self_proof_risk"):
        if payload.get(key) not in VALID_RISK:
            errors.append(f"{key} must be one of {sorted(VALID_RISK)}")

    for key in (
        "review_id",
        "thesis",
        "evidence_summary",
        "base_rate_note",
        "max_loss",
        "time_horizon",
        "review_date",
        "freedom_fragility_assessment",
        "broker_write_boundary",
        "authority_boundary",
    ):
        if not _nonempty(payload.get(key)):
            errors.append(f"{key} must be a non-empty string")

    if payload.get("live_trading_no_go") is not True:
        errors.append("live_trading_no_go must remain true in PGI-2.06")

    if payload.get("decision_type") != "no_action" and str(payload.get("max_loss", "")).strip().lower() in {
        "unknown",
        "tbd",
        "none",
    }:
        errors.append("financial action reviews must state a concrete max_loss")

    thesis = str(payload.get("thesis", ""))
    if GUARANTEE_RE.search(thesis):
        errors.append("thesis must not contain guaranteed-profit language")

    if payload.get("fomo_or_gambling_risk") == "block" and payload.get("decision_posture") not in {"hold", "reject"}:
        errors.append("block-level FOMO/gambling risk requires hold or reject posture")
    if payload.get("self_proof_risk") == "block" and payload.get("decision_posture") not in {"hold", "reject"}:
        errors.append("block-level self-proof risk requires hold or reject posture")

    broker = str(payload.get("broker_write_boundary", "")).lower()
    if "no broker write" not in broker:
        errors.append("broker_write_boundary must state no broker write")

    boundary = str(payload.get("authority_boundary", "")).lower()
    if "does not authorize" not in boundary or "not financial advice" not in boundary:
        errors.append("authority_boundary must state this does not authorize action and is not financial advice")

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
        print("Usage: python scripts/validate_pgi_finance_decision_review.py <payload.json> [...]")
        return 2
    failed = False
    results = []
    for raw in args:
        path = Path(raw)
        ok, errors = validate_file(path)
        failed = failed or not ok
        results.append({"path": str(path), "valid": ok, "errors": errors})
    print(json.dumps({"tool": "pgi-finance-decision-review-validator", "results": results}, indent=2))
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
