from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any


class DecisionRecordError(ValueError):
    pass


def _digest(value: Any) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()
    return "sha256:" + hashlib.sha256(payload).hexdigest()


def build_decision_record(*, context: dict[str, Any], state_projection: dict[str, Any], decision_route: dict[str, Any], authority_refs: dict[str, str]) -> dict[str, Any]:
    """Freeze one decision-support episode without claiming recommendation or effect authority."""

    if not isinstance(context, dict) or not isinstance(state_projection, dict) or not isinstance(decision_route, dict):
        raise DecisionRecordError("context, state_projection and decision_route must be objects")
    if decision_route.get("decisionId") != context.get("decisionId"):
        raise DecisionRecordError("decision identity mismatch")
    if decision_route.get("asOf") != context.get("asOf") or state_projection.get("asOf") != context.get("asOf"):
        raise DecisionRecordError("decision timestamp mismatch")
    if decision_route.get("externalFinancialEffectAllowed") is not False:
        raise DecisionRecordError("decision route violates external-effect boundary")
    if not isinstance(authority_refs, dict) or any(not isinstance(k, str) or not isinstance(v, str) for k, v in authority_refs.items()):
        raise DecisionRecordError("authority_refs must be string mapping")
    body = {
        "schemaVersion": 1,
        "kind": "ordivon.capital.investment-decision-record",
        "truthRole": "FROZEN_DECISION_SUPPORT_EVIDENCE_NOT_INVESTMENT_TRUTH",
        "decisionId": context["decisionId"],
        "asOf": context["asOf"],
        "objective": context["objective"],
        "horizon": context["horizon"],
        "stateProjection": state_projection,
        "decisionRoute": decision_route,
        "authorityRefs": dict(sorted(authority_refs.items())),
        "externalFinancialEffectAllowed": False,
        "recommendationTruthClaimed": False,
        "semanticCompletionEvaluated": False,
    }
    body["recordDigest"] = _digest(body)
    return body


def persist_decision_record(*, record: dict[str, Any], output_dir: Path) -> dict[str, Any]:
    expected = record.get("recordDigest")
    body = dict(record)
    body.pop("recordDigest", None)
    if not isinstance(expected, str) or expected != _digest(body):
        raise DecisionRecordError("record digest mismatch")
    output_dir.mkdir(parents=True, exist_ok=True)
    path = output_dir / f"{expected.removeprefix('sha256:')}.json"
    rendered = json.dumps(record, indent=2, sort_keys=True, ensure_ascii=False) + "\n"
    if path.exists() and path.read_text() != rendered:
        raise DecisionRecordError("content-addressed record collision")
    path.write_text(rendered)
    readback = json.loads(path.read_text())
    if readback != record:
        raise DecisionRecordError("decision record readback mismatch")
    return {
        "schemaVersion": 1,
        "kind": "ordivon.capital.investment-decision-record-persistence",
        "recordDigest": expected,
        "path": str(path),
        "standing": "CONTENT_ADDRESSED_LOCAL_PERSISTENCE_PASS",
        "externalFinancialWriteAttempted": False,
    }
