"""H-9C3: Thesis quality gate — unit tests.

Verifies deterministic thesis quality checks: minimum length,
banned patterns, missing invalidation wording.
"""

import pytest

from domains.decision_intake.models import DecisionIntake
from governance.risk_engine.engine import RiskEngine


def _make_intake(*, status="validated", payload=None) -> DecisionIntake:
    p = {
        "symbol": "BTC/USDT",
        "timeframe": "1h",
        "direction": "long",
        "thesis": "BTC is breaking out above the 4h resistance with volume confirmation "
                 "and the 200 EMA is sloping upward, targeting the range high of 72k.",
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


# ── Thesis too short (< 50 chars) → escalate ──────────────────────────

def test_h9c3_thesis_too_short_escalated():
    engine = RiskEngine()
    intake = _make_intake(payload={"thesis": "Short thesis statement"})
    decision = engine.validate_intake(intake)
    assert decision.decision == "escalate"
    assert any("thesis" in r.lower() for r in decision.reasons)


def test_h9c3_thesis_boundary_short_escalated():
    """49 chars → escalate (below 50 threshold)."""
    engine = RiskEngine()
    intake = _make_intake(payload={"thesis": "B" * 49})
    decision = engine.validate_intake(intake)
    assert decision.decision == "escalate"


def test_h9c3_thesis_boundary_ok_not_escalated():
    """50 chars → not escalated for length."""
    engine = RiskEngine()
    intake = _make_intake(payload={"thesis": "B" * 50})
    decision = engine.validate_intake(intake)
    # Length is OK — decision depends on other factors (might be execute or 
    # escalate for lack of verifiability, but NOT for length)
    if decision.decision == "escalate":
        assert not any("shorter than 50" in r.lower() for r in decision.reasons)
        assert not any("too short" in r.lower() for r in decision.reasons)


# ── Banned patterns → reject ──────────────────────────────────────────

@pytest.mark.parametrize("bad_thesis", [
    "No specific thesis, just feels right",
    "It just feels right to buy here",
    "Looks good, should pump",
    "No specific thesis provided",
    "Vibes are good, trust me",
    "YOLO all in",
    "Because I said so",
    "I think so, let's see what happens",
])
def test_h9c3_banned_pattern_rejected(bad_thesis):
    engine = RiskEngine()
    intake = _make_intake(payload={"thesis": bad_thesis})
    decision = engine.validate_intake(intake)
    assert decision.decision == "reject"
    assert any("thesis" in r.lower() for r in decision.reasons)
    assert any(("quality" in r.lower() or "pattern" in r.lower() or "generic" in r.lower())
               for r in decision.reasons)


def test_h9c3_banned_pattern_case_insensitive():
    engine = RiskEngine()
    intake = _make_intake(payload={"thesis": "JUST FEELS RIGHT"})
    decision = engine.validate_intake(intake)
    assert decision.decision == "reject"


# ── Missing invalidation/confirmation wording → escalate ──────────────

def test_h9c3_no_invalidation_wording_escalated():
    """Thesis has no invalidation or confirmation language → escalate."""
    engine = RiskEngine()
    # Long enough but purely directional, no "if"/"unless"/"invalid"/"confirm"
    intake = _make_intake(payload={
        "thesis": "BTC is going up because the trend is strong and volume is high "
                  "and the market sentiment is bullish across all timeframes."
    })
    decision = engine.validate_intake(intake)
    assert decision.decision == "escalate"
    assert any(
        w in str(decision.reasons).lower()
        for w in ("invalidation", "verifiable", "confirmation", "falsifiable")
    )


def test_h9c3_has_invalidation_wording_not_escalated():
    """Thesis with 'unless' or 'if not' — acceptable."""
    engine = RiskEngine()
    intake = _make_intake(payload={
        "thesis": "BTC is going up because the trend is strong, "
                  "invalidated if price closes below the 200 EMA."
    })
    decision = engine.validate_intake(intake)
    # Should NOT escalate for invalidation wording
    if decision.decision == "escalate":
        assert not any("invalidation" in r.lower() for r in decision.reasons)


def test_h9c3_has_confirmation_wording_not_escalated():
    """Thesis with 'confirmed when' — acceptable."""
    engine = RiskEngine()
    intake = _make_intake(payload={
        "thesis": "ETH breakout target is 2500, confirmed when 4h candle "
                  "closes above resistance with volume > 2x average."
    })
    decision = engine.validate_intake(intake)
    if decision.decision == "escalate":
        assert not any("invalidation" in r.lower() for r in decision.reasons)


def test_h9c3_has_unless_not_escalated():
    engine = RiskEngine()
    intake = _make_intake(payload={
        "thesis": "SOL will continue its uptrend unless it loses the 100 level "
                  "on daily close, which would invalidate the momentum thesis."
    })
    decision = engine.validate_intake(intake)
    if decision.decision == "escalate":
        assert not any("invalidation" in r.lower() for r in decision.reasons)


# ── Valid thesis still passes ──────────────────────────────────────────

def test_h9c3_valid_thesis_executed():
    engine = RiskEngine()
    intake = _make_intake()
    decision = engine.validate_intake(intake)
    assert decision.decision == "execute"
