"""H-5: Finance Decision Governance Hard Gate — Unit Tests.

Covers all 12 hard-gate rules plus side-effect and priority verification.
Test names use standard pytest def test_*() convention (NOT pytest-describe).
"""

from domains.decision_intake.models import DecisionIntake
from governance_engine.risk_engine.engine import RiskEngine
from packs.finance.trading_discipline_policy import TradingDisciplinePolicy


# ── Helpers ────────────────────────────────────────────────────────────────


def _make_intake(*, status="validated", payload=None) -> DecisionIntake:
    """Create a DecisionIntake for testing."""
    p = {
        "symbol": "BTC/USDT",
        "timeframe": "1h",
        "direction": "long",
        "thesis": "BTC breaking above resistance with volume confirmation; invalidated if price closes below 200 EMA.",
        "entry_condition": "Breakout confirmed.",
        "invalidation_condition": "Range reclaim.",
        "stop_loss": "Below support",
        "target": "Local high",
        "position_size_usdt": 100.0,
        "max_loss_usdt": 20.0,
        "risk_unit_usdt": 10.0,
        "is_revenge_trade": False,
        "is_chasing": False,
        "emotional_state": "calm",
        "confidence": 0.5,
        "rule_exceptions": [],
        "notes": "Controlled",
    }
    if payload is not None:
        p.update(payload)
    return DecisionIntake(
        pack_id="finance",
        intake_type="controlled_decision",
        status=status,
        payload=p,
    )


def _valid_intake() -> DecisionIntake:
    return _make_intake()


# ── Rule 1: invalid intake → reject ────────────────────────────────────────


def test_h5_invalid_intake_rejected():
    engine = RiskEngine()
    intake = _make_intake(status="invalid")
    decision = engine.validate_intake(intake, pack_policy=TradingDisciplinePolicy())
    assert decision.decision == "reject"
    assert any("invalid" in r.lower() for r in decision.reasons)


# ── Rule 2: missing thesis → reject ────────────────────────────────────────


def test_h5_missing_thesis_rejected():
    engine = RiskEngine()
    intake = _make_intake(payload={"thesis": None})
    decision = engine.validate_intake(intake, pack_policy=TradingDisciplinePolicy())
    assert decision.decision == "reject"
    assert any("thesis" in r.lower() for r in decision.reasons)


def test_h5_empty_thesis_rejected():
    engine = RiskEngine()
    intake = _make_intake(payload={"thesis": "   "})
    decision = engine.validate_intake(intake, pack_policy=TradingDisciplinePolicy())
    assert decision.decision == "reject"
    assert any("thesis" in r.lower() for r in decision.reasons)


# ── Rule 3: missing stop_loss → reject ─────────────────────────────────────


def test_h5_missing_stop_loss_rejected():
    engine = RiskEngine()
    intake = _make_intake(payload={"stop_loss": None})
    decision = engine.validate_intake(intake, pack_policy=TradingDisciplinePolicy())
    assert decision.decision == "reject"
    assert any("stop_loss" in r.lower() for r in decision.reasons)


# ── Rule 4: missing max_loss_usdt → reject ─────────────────────────────────


def test_h5_missing_max_loss_rejected():
    engine = RiskEngine()
    intake = _make_intake(payload={"max_loss_usdt": None})
    decision = engine.validate_intake(intake, pack_policy=TradingDisciplinePolicy())
    assert decision.decision == "reject"
    assert any("max_loss" in r.lower() for r in decision.reasons)


def test_h5_zero_max_loss_rejected():
    engine = RiskEngine()
    intake = _make_intake(payload={"max_loss_usdt": 0.0})
    decision = engine.validate_intake(intake, pack_policy=TradingDisciplinePolicy())
    assert decision.decision == "reject"
    assert any("max_loss" in r.lower() for r in decision.reasons)


# ── Rule 5: missing position_size_usdt → reject ────────────────────────────


def test_h5_missing_position_size_rejected():
    engine = RiskEngine()
    intake = _make_intake(payload={"position_size_usdt": None})
    decision = engine.validate_intake(intake, pack_policy=TradingDisciplinePolicy())
    assert decision.decision == "reject"
    assert any("position_size" in r.lower() for r in decision.reasons)


# ── Rule 6: missing risk_unit_usdt → reject ────────────────────────────────


def test_h5_missing_risk_unit_rejected():
    engine = RiskEngine()
    intake = _make_intake(payload={"risk_unit_usdt": None})
    decision = engine.validate_intake(intake, pack_policy=TradingDisciplinePolicy())
    assert decision.decision == "reject"
    assert any("risk_unit" in r.lower() for r in decision.reasons)


# ── Rule 7: missing emotional_state → reject ───────────────────────────────


def test_h5_missing_emotional_state_rejected():
    engine = RiskEngine()
    intake = _make_intake(payload={"emotional_state": None})
    decision = engine.validate_intake(intake, pack_policy=TradingDisciplinePolicy())
    assert decision.decision == "reject"
    assert any("emotional_state" in r.lower() for r in decision.reasons)


def test_h5_empty_emotional_state_rejected():
    engine = RiskEngine()
    intake = _make_intake(payload={"emotional_state": ""})
    decision = engine.validate_intake(intake, pack_policy=TradingDisciplinePolicy())
    assert decision.decision == "reject"
    assert any("emotional_state" in r.lower() for r in decision.reasons)


# ── Rule 8: is_revenge_trade=true → escalate ───────────────────────────────


def test_h5_revenge_trade_escalated():
    engine = RiskEngine()
    intake = _make_intake(payload={"is_revenge_trade": True})
    decision = engine.validate_intake(intake, pack_policy=TradingDisciplinePolicy())
    assert decision.decision == "escalate"
    assert any("revenge" in r.lower() for r in decision.reasons)


# ── Rule 9: is_chasing=true → escalate ─────────────────────────────────────


def test_h5_chasing_escalated():
    engine = RiskEngine()
    intake = _make_intake(payload={"is_chasing": True})
    decision = engine.validate_intake(intake, pack_policy=TradingDisciplinePolicy())
    assert decision.decision == "escalate"
    assert any("chasing" in r.lower() for r in decision.reasons)


# ── Rule 10: max_loss_usdt exceeds 2× risk_unit → reject ──────────────────


def test_h5_max_loss_exceeds_risk_unit_rejected():
    engine = RiskEngine()
    # max_loss = 25 > 2 * 10 = 20
    intake = _make_intake(payload={"max_loss_usdt": 25.0, "risk_unit_usdt": 10.0})
    decision = engine.validate_intake(intake, pack_policy=TradingDisciplinePolicy())
    assert decision.decision == "reject"
    assert any("max_loss" in r.lower() for r in decision.reasons)
    assert any("exceeds" in r.lower() for r in decision.reasons)


def test_h5_max_loss_equal_to_2x_risk_unit_allowed():
    engine = RiskEngine()
    # max_loss = 20 == 2 * 10 → boundary, not rejected
    intake = _make_intake(payload={"max_loss_usdt": 20.0, "risk_unit_usdt": 10.0})
    decision = engine.validate_intake(intake, pack_policy=TradingDisciplinePolicy())
    # Should not reject for max_loss; may escalate if other flags present
    if decision.decision == "reject":
        assert not any("max_loss" in r.lower() for r in decision.reasons)


# ── Rule 11: position_size exceeds 10× risk_unit → reject ──────────────────


def test_h5_position_size_exceeds_risk_unit_rejected():
    engine = RiskEngine()
    # position_size = 120 > 10 * 10 = 100
    intake = _make_intake(payload={"position_size_usdt": 120.0, "risk_unit_usdt": 10.0})
    decision = engine.validate_intake(intake, pack_policy=TradingDisciplinePolicy())
    assert decision.decision == "reject"
    assert any("position_size" in r.lower() for r in decision.reasons)
    assert any("exceeds" in r.lower() for r in decision.reasons)


# ── Rule 12: valid intake → execute ────────────────────────────────────────


def test_h5_valid_intake_executed():
    engine = RiskEngine()
    intake = _valid_intake()
    decision = engine.validate_intake(intake, pack_policy=TradingDisciplinePolicy())
    assert decision.decision == "execute"
    assert any("passed" in r.lower() for r in decision.reasons)


# ── Priority: reject > escalate > execute ──────────────────────────────────


def test_h5_priority_reject_over_escalate_when_missing_field_and_revenge():
    """missing stop_loss + is_revenge_trade → reject (not escalate)."""
    engine = RiskEngine()
    intake = _make_intake(
        payload={
            "stop_loss": None,
            "is_revenge_trade": True,
        }
    )
    decision = engine.validate_intake(intake, pack_policy=TradingDisciplinePolicy())
    assert decision.decision == "reject"
    assert any("stop_loss" in r.lower() for r in decision.reasons)


def test_h5_priority_reject_over_escalate_when_limit_and_chasing():
    """max_loss exceeds limit + is_chasing → reject (not escalate)."""
    engine = RiskEngine()
    intake = _make_intake(
        payload={
            "max_loss_usdt": 30.0,
            "risk_unit_usdt": 10.0,
            "is_chasing": True,
        }
    )
    decision = engine.validate_intake(intake, pack_policy=TradingDisciplinePolicy())
    assert decision.decision == "reject"


# ── GovernanceDecision metadata ────────────────────────────────────────────


def test_h5_governance_decision_has_reasons():
    engine = RiskEngine()
    intake = _valid_intake()
    decision = engine.validate_intake(intake, pack_policy=TradingDisciplinePolicy())
    assert len(decision.reasons) >= 1
    assert isinstance(decision.reasons[0], str)


def test_h5_governance_decision_has_policy_refs():
    engine = RiskEngine()
    intake = _valid_intake()
    decision = engine.validate_intake(intake, pack_policy=TradingDisciplinePolicy())
    assert len(decision.active_policy_ids) >= 1
    assert decision.policy_set_id != "governance.unknown"


def test_h5_governance_decision_source_is_hard_gate():
    engine = RiskEngine()
    intake = _valid_intake()
    decision = engine.validate_intake(intake, pack_policy=TradingDisciplinePolicy())
    assert "hard_gate" in decision.source or "finance_governance" in decision.source


# ── validate_analysis unchanged ────────────────────────────────────────────


def test_h5_validate_analysis_still_works():
    """H-5 must not break the existing validate_analysis path."""
    from datetime import datetime
    from domains.research.models import AnalysisResult

    engine = RiskEngine()
    analysis = AnalysisResult(
        id="ana_h5_test",
        query="Test BTC",
        symbol="BTC-USDT",
        timeframe="4h",
        summary="Good",
        thesis="Breakout",
        suggested_actions=["BUY"],
        metadata={},
        created_at=datetime.now(),
    )
    decision = engine.validate_analysis(analysis)
    assert decision.decision == "execute"


# ── validate_analysis still rejects forbidden symbols ──────────────────────


def test_h5_validate_analysis_still_rejects_forbidden():
    from datetime import datetime
    from domains.research.models import AnalysisResult

    engine = RiskEngine()
    analysis = AnalysisResult(
        id="ana_h5_test2",
        query="Test PEPE",
        symbol="PEPE/USDT",
        timeframe="1h",
        summary="Moon",
        thesis="Speculation",
        suggested_actions=["BUY"],
        metadata={},
        created_at=datetime.now(),
    )
    decision = engine.validate_analysis(analysis)
    assert decision.decision == "reject"
