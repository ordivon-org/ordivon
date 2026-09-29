from __future__ import annotations

import json
from pathlib import Path

import pytest

from ordivon_capital.portfolio.decision_record import (
    build_decision_record,
    persist_decision_record,
)
from ordivon_capital.research.decision_attribution import (
    DecisionAttributionError,
    attribute_decision_outcome,
)
from ordivon_capital.research.state_projection import project_decision_state

ROOT = Path(__file__).resolve().parents[1]


def _registry() -> dict:
    return json.loads((ROOT / "config/decision_state_claim_registry.json").read_text())


def _claim(*, claim_id: str = "claim:value:r1", observed: str = "2026-09-27T01:00:00+08:00", valid: str = "2026-09-27T02:00:00+08:00") -> dict:
    return {
        "claimId": claim_id,
        "claimKey": "valuation-signal-available",
        "producerId": "valuation:test:r1",
        "producerClass": "REGISTERED_MODEL_OUTPUT",
        "evidenceKind": "VALUATION_MODEL_OUTPUT",
        "evidenceDigest": "sha256:" + "a" * 64,
        "observedAt": observed,
        "validUntil": valid,
        "standing": "ACTIVE",
    }


def test_state_projection_accepts_only_current_registered_claims() -> None:
    out = project_decision_state(
        as_of="2026-09-27T01:30:00+08:00",
        claims=[_claim()],
        registry=_registry(),
    )
    assert out["stateTags"] == ["VALUATION_SIGNAL_AVAILABLE"]
    assert len(out["acceptedClaims"]) == 1
    assert out["rejectedClaims"] == []
    assert out["executionAuthorityGranted"] is False


def test_state_projection_rejects_expired_and_unknown_claims() -> None:
    expired = _claim(valid="2026-09-27T01:15:00+08:00")
    unknown = dict(_claim(claim_id="claim:unknown:r1"))
    unknown["claimKey"] = "magic-regime"
    out = project_decision_state(
        as_of="2026-09-27T01:30:00+08:00",
        claims=[expired, unknown],
        registry=_registry(),
    )
    assert out["stateTags"] == []
    assert {row["reason"] for row in out["rejectedClaims"]} == {"CLAIM_EXPIRED", "UNREGISTERED_CLAIM_KEY"}


def test_decision_record_is_content_addressed_and_idempotently_persisted(tmp_path: Path) -> None:
    state = project_decision_state(
        as_of="2026-09-27T01:30:00+08:00",
        claims=[_claim()],
        registry=_registry(),
    )
    route = {
        "decisionId": "decision:test:r2",
        "asOf": "2026-09-27T01:30:00+08:00",
        "decisionStanding": "RESEARCH_ONLY_RISK_BUDGET_UNSET",
        "modelRoutes": [{"modelKey": "value-valuation", "route": "ELIGIBLE"}],
        "externalFinancialEffectAllowed": False,
    }
    record = build_decision_record(
        context={
            "decisionId": "decision:test:r2",
            "asOf": "2026-09-27T01:30:00+08:00",
            "objective": "test",
            "horizon": "months",
        },
        state_projection=state,
        decision_route=route,
        authority_refs={"atlas": "sha256:" + "b" * 64},
    )
    first = persist_decision_record(record=record, output_dir=tmp_path)
    second = persist_decision_record(record=record, output_dir=tmp_path)
    assert first == second
    assert first["standing"] == "CONTENT_ADDRESSED_LOCAL_PERSISTENCE_PASS"


def test_outcome_attribution_is_measurement_not_skill_or_causality(tmp_path: Path) -> None:
    state = project_decision_state(
        as_of="2026-09-27T01:30:00+08:00",
        claims=[_claim()],
        registry=_registry(),
    )
    route = {
        "decisionId": "decision:test:r2",
        "asOf": "2026-09-27T01:30:00+08:00",
        "decisionStanding": "RESEARCH_ONLY_RISK_BUDGET_UNSET",
        "modelRoutes": [
            {"modelKey": "value-valuation", "route": "ELIGIBLE"},
            {"modelKey": "factor-timing", "route": "RESEARCH_ONLY"},
        ],
        "externalFinancialEffectAllowed": False,
    }
    record = build_decision_record(
        context={
            "decisionId": "decision:test:r2",
            "asOf": "2026-09-27T01:30:00+08:00",
            "objective": "test",
            "horizon": "months",
        },
        state_projection=state,
        decision_route=route,
        authority_refs={"atlas": "sha256:" + "b" * 64},
    )
    out = attribute_decision_outcome(
        decision_record=record,
        outcome={
            "observedAt": "2026-10-27T01:30:00+08:00",
            "realizedReturn": "0.10",
            "benchmarkReturn": "0.07",
        },
    )
    assert out["excessReturn"] == "0.03"
    assert out["causalAttributionClaimed"] is False
    assert out["skillClaimed"] is False
    assert out["modelValidatedByOutcome"] is False
    with pytest.raises(DecisionAttributionError):
        attribute_decision_outcome(
            decision_record=record,
            outcome={"observedAt": "2026-09-27T01:00:00+08:00", "realizedReturn": "0.01"},
        )
