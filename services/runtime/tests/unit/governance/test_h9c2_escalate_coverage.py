"""H-9C2: Escalation path coverage — unit tests.

Verifies that emotional state, rule exceptions, and low confidence
trigger escalate (not reject, not execute).
"""

from domains.decision_intake.models import DecisionIntake
from governance.risk_engine.engine import RiskEngine
from packs.finance.trading_discipline_policy import TradingDisciplinePolicy


def _make_intake(*, status="validated", payload=None) -> DecisionIntake:
    """Create a valid DecisionIntake for testing."""
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
        "confidence": 0.7,
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


# ── H-9C2 Rule 1: emotional_state stress → escalate ─────────────────────


def test_h9c2_emotional_stress_escalated():
    engine = RiskEngine()
    intake = _make_intake(payload={"emotional_state": "stressed"})
    decision = engine.validate_intake(intake, pack_policy=TradingDisciplinePolicy())
    assert decision.decision == "escalate"
    assert any("emotional_state" in r.lower() for r in decision.reasons)


def test_h9c2_emotional_fear_escalated():
    engine = RiskEngine()
    intake = _make_intake(payload={"emotional_state": "fearful"})
    decision = engine.validate_intake(intake, pack_policy=TradingDisciplinePolicy())
    assert decision.decision == "escalate"


def test_h9c2_emotional_anger_escalated():
    engine = RiskEngine()
    intake = _make_intake(payload={"emotional_state": "angry"})
    decision = engine.validate_intake(intake, pack_policy=TradingDisciplinePolicy())
    assert decision.decision == "escalate"


def test_h9c2_emotional_fomo_escalated():
    engine = RiskEngine()
    intake = _make_intake(payload={"emotional_state": "FOMO"})
    decision = engine.validate_intake(intake, pack_policy=TradingDisciplinePolicy())
    assert decision.decision == "escalate"


def test_h9c2_emotional_calm_not_escalated():
    """calm emotional_state should NOT trigger escalate on its own."""
    engine = RiskEngine()
    intake = _make_intake(payload={"emotional_state": "calm"})
    decision = engine.validate_intake(intake, pack_policy=TradingDisciplinePolicy())
    assert decision.decision == "execute"


def test_h9c2_emotional_neutral_not_escalated():
    engine = RiskEngine()
    intake = _make_intake(payload={"emotional_state": "neutral"})
    decision = engine.validate_intake(intake, pack_policy=TradingDisciplinePolicy())
    assert decision.decision == "execute"


# ── H-9C2 Rule 2: rule_exceptions not empty → escalate ────────────────


def test_h9c2_rule_exceptions_not_empty_escalated():
    engine = RiskEngine()
    intake = _make_intake(payload={"rule_exceptions": ["override position limit"]})
    decision = engine.validate_intake(intake, pack_policy=TradingDisciplinePolicy())
    assert decision.decision == "escalate"
    assert any("rule_exceptions" in r.lower() for r in decision.reasons)


def test_h9c2_rule_exceptions_empty_not_escalated():
    engine = RiskEngine()
    intake = _make_intake(payload={"rule_exceptions": []})
    decision = engine.validate_intake(intake, pack_policy=TradingDisciplinePolicy())
    assert decision.decision == "execute"


def test_h9c2_rule_exceptions_none_not_escalated():
    engine = RiskEngine()
    intake = _make_intake(payload={"rule_exceptions": None})
    decision = engine.validate_intake(intake, pack_policy=TradingDisciplinePolicy())
    # None → treat as empty, no escalate
    assert decision.decision == "execute"


# ── H-9C2 Rule 3: confidence < 0.3 → escalate ─────────────────────────


def test_h9c2_confidence_too_low_escalated():
    engine = RiskEngine()
    intake = _make_intake(payload={"confidence": 0.2})
    decision = engine.validate_intake(intake, pack_policy=TradingDisciplinePolicy())
    assert decision.decision == "escalate"
    assert any("confidence" in r.lower() for r in decision.reasons)


def test_h9c2_confidence_low_boundary_escalated():
    engine = RiskEngine()
    intake = _make_intake(payload={"confidence": 0.299})
    decision = engine.validate_intake(intake, pack_policy=TradingDisciplinePolicy())
    assert decision.decision == "escalate"


def test_h9c2_confidence_acceptable_not_escalated():
    engine = RiskEngine()
    intake = _make_intake(payload={"confidence": 0.5})
    decision = engine.validate_intake(intake, pack_policy=TradingDisciplinePolicy())
    assert decision.decision == "execute"


def test_h9c2_confidence_high_not_escalated():
    engine = RiskEngine()
    intake = _make_intake(payload={"confidence": 0.9})
    decision = engine.validate_intake(intake, pack_policy=TradingDisciplinePolicy())
    assert decision.decision == "execute"


# ── Priority: reject still beats escalate ──────────────────────────────


def test_h9c2_priority_reject_over_escalate_emotion():
    """missing stop_loss + stressed → reject (not escalate)."""
    engine = RiskEngine()
    intake = _make_intake(
        payload={
            "stop_loss": None,
            "emotional_state": "stressed",
        }
    )
    decision = engine.validate_intake(intake, pack_policy=TradingDisciplinePolicy())
    assert decision.decision == "reject"


def test_h9c2_priority_reject_over_escalate_low_confidence():
    """missing thesis + low confidence → reject (not escalate)."""
    engine = RiskEngine()
    intake = _make_intake(
        payload={
            "thesis": None,
            "confidence": 0.2,
        }
    )
    decision = engine.validate_intake(intake, pack_policy=TradingDisciplinePolicy())
    assert decision.decision == "reject"


# ── Existing triggers still work ───────────────────────────────────────


def test_h9c2_existing_revenge_trade_still_escalates():
    engine = RiskEngine()
    intake = _make_intake(payload={"is_revenge_trade": True})
    decision = engine.validate_intake(intake, pack_policy=TradingDisciplinePolicy())
    assert decision.decision == "escalate"


def test_h9c2_existing_chasing_still_escalates():
    engine = RiskEngine()
    intake = _make_intake(payload={"is_chasing": True})
    decision = engine.validate_intake(intake, pack_policy=TradingDisciplinePolicy())
    assert decision.decision == "escalate"
