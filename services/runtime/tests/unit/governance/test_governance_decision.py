import pytest

from governance_engine.decision import (
    GovernanceAdvisoryHint,
    GovernanceDecision,
    build_governance_decision,
    recommendation_governance_view,
)


def test_governance_decision_accepts_supported_values():
    decision = build_governance_decision(
        decision="execute",
        reasons=["passed"],
        source="risk_engine.default_validation",
    )

    assert isinstance(decision, GovernanceDecision)
    assert decision.decision == "execute"
    assert decision.allowed is True
    assert decision.to_payload()["source"] == "risk_engine.default_validation"
    assert decision.to_payload()["policy_set_id"] == "governance.unknown"


def test_governance_decision_rejects_unknown_values():
    with pytest.raises(ValueError):
        GovernanceDecision(decision="allow")


def test_recommendation_governance_view_returns_none_when_decision_missing():
    assert recommendation_governance_view(decision=None, reason=None, source=None) is None


def test_recommendation_governance_view_normalizes_reason_and_source():
    payload = recommendation_governance_view(
        decision="escalate",
        reason="Needs manual review",
        source="recommendation.recorded_decision",
    )

    assert payload["decision"] == "escalate"
    assert payload["reasons"] == ["Needs manual review"]
    assert payload["source"] == "recommendation.recorded_decision"
    assert payload["advisory_hints"] == []
    assert payload["policy_set_id"] == "recommendation.recorded_policy_source"


def test_governance_decision_serializes_advisory_hints():
    decision = GovernanceDecision(
        decision="execute",
        reasons=["passed"],
        source="risk_engine.default_validation",
        advisory_hints=(
            GovernanceAdvisoryHint(
                target="governance",
                hint_type="lesson_caution",
                summary="Wait for confirmation",
                evidence_object_ids=("lesson_1", "outcome_1"),
            ),
        ),
    )

    assert decision.to_payload()["advisory_hints"] == [
        {
            "target": "governance",
            "hint_type": "lesson_caution",
            "summary": "Wait for confirmation",
            "evidence_object_ids": ["lesson_1", "outcome_1"],
        }
    ]
