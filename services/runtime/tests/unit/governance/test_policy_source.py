from governance_engine.policy_source import GovernancePolicySource
from governance_engine.risk_engine.engine import RiskEngine
from domains.research.models import AnalysisResult


def test_governance_policy_source_returns_active_snapshot():
    snapshot = GovernancePolicySource().get_active_snapshot()

    assert snapshot.policy_set_id == "governance.default.v1"
    assert snapshot.active_policy_ids == ("forbidden_symbols_policy", "trading_discipline_policy")
    assert snapshot.default_decision_rule_ids == (
        "default_no_actions_escalate",
        "default_pass_execute",
    )


def test_risk_engine_emits_policy_source_in_decision():
    decision = RiskEngine().validate_analysis(
        AnalysisResult(
            id="ana_policy_1",
            query="Analyze BTC",
            symbol="BTC-USDT",
            summary="Bullish",
            thesis="trend",
            suggested_actions=["BUY"],
        )
    )

    assert decision.policy_set_id == "governance.default.v1"
    assert decision.active_policy_ids == ("forbidden_symbols_policy", "trading_discipline_policy")
    assert decision.default_decision_rule_ids == (
        "default_no_actions_escalate",
        "default_pass_execute",
    )
