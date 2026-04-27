"""ADR-006: TradingDisciplinePolicy 单元测试 — 16 个测试覆盖全部 Gate 1-4。"""

import pytest
from packs.finance.trading_discipline_policy import (
    TradingDisciplinePolicy,
    RejectReason,
    EscalateReason,
)


@pytest.fixture
def policy():
    return TradingDisciplinePolicy()


# ═══ Gate 1: Field existence + Thesis quality ═══


def test_reject_missing_thesis(policy):
    reasons = policy.validate_fields({"stop_loss": "2%", "emotional_state": "calm"})
    assert any("thesis" in r.message.lower() for r in reasons if isinstance(r, RejectReason))


def test_reject_missing_stop_loss(policy):
    reasons = policy.validate_fields({"thesis": "valid thesis with invalidation condition", "emotional_state": "calm"})
    assert any("stop_loss" in r.message.lower() for r in reasons if isinstance(r, RejectReason))


def test_reject_missing_emotional_state(policy):
    reasons = policy.validate_fields({"thesis": "valid thesis with invalidation condition", "stop_loss": "2%"})
    assert any("emotional_state" in r.message.lower() for r in reasons if isinstance(r, RejectReason))


def test_reject_banned_thesis(policy):
    reasons = policy.validate_fields(
        {"thesis": "no specific thesis, just feels right", "stop_loss": "2%", "emotional_state": "calm"}
    )
    assert any("rejected" in r.message.lower() for r in reasons if isinstance(r, RejectReason))


def test_escalate_short_thesis(policy):
    reasons = policy.validate_fields({"thesis": "Short", "stop_loss": "2%", "emotional_state": "calm"})
    assert any("too short" in r.message.lower() for r in reasons if isinstance(r, EscalateReason))


def test_escalate_no_verifiability(policy):
    reasons = policy.validate_fields(
        {
            "thesis": "BTC is going up because trend is strong and volume is high",
            "stop_loss": "2%",
            "emotional_state": "calm",
        }
    )
    assert any("verifiability" in r.message.lower() for r in reasons if isinstance(r, EscalateReason))


def test_valid_thesis_passes(policy):
    payload = {
        "thesis": "BTC breaking resistance with volume; invalidated if closes below 200 EMA.",
        "stop_loss": "2%",
        "emotional_state": "calm",
    }
    reasons = policy.validate_fields(payload)
    assert not any(isinstance(r, RejectReason) for r in reasons)
    assert not any(isinstance(r, EscalateReason) for r in reasons)


# ═══ Gate 2: Numeric fields ═══


def test_reject_missing_max_loss(policy):
    reasons = policy.validate_numeric({"position_size_usdt": 100.0, "risk_unit_usdt": 10.0})
    assert any("max_loss_usdt" in r.message for r in reasons)


def test_reject_missing_position_size(policy):
    reasons = policy.validate_numeric({"max_loss_usdt": 20.0, "risk_unit_usdt": 10.0})
    assert any("position_size_usdt" in r.message for r in reasons)


def test_reject_missing_risk_unit(policy):
    reasons = policy.validate_numeric({"max_loss_usdt": 20.0, "position_size_usdt": 100.0})
    assert any("risk_unit_usdt" in r.message for r in reasons)


# ═══ Gate 3: Risk limits ═══


def test_reject_max_loss_exceeds_ratio(policy):
    reasons = policy.validate_limits({"max_loss_usdt": 500.0, "position_size_usdt": 100.0, "risk_unit_usdt": 100.0})
    assert any("exceeds" in r.message for r in reasons)


def test_reject_position_size_exceeds_ratio(policy):
    reasons = policy.validate_limits({"max_loss_usdt": 100.0, "position_size_usdt": 5000.0, "risk_unit_usdt": 100.0})
    assert any("exceeds" in r.message for r in reasons)


def test_valid_limits_pass(policy):
    reasons = policy.validate_limits({"max_loss_usdt": 200.0, "position_size_usdt": 1000.0, "risk_unit_usdt": 100.0})
    assert len(reasons) == 0


# ═══ Gate 4: Behavioral ═══


def test_escalate_revenge_trade(policy):
    reasons = policy.validate_behavioral({"is_revenge_trade": True})
    assert any("is_revenge_trade" in r.message for r in reasons)


def test_escalate_chasing(policy):
    reasons = policy.validate_behavioral({"is_chasing": True})
    assert any("is_chasing" in r.message for r in reasons)


def test_calm_no_flags_passes(policy):
    reasons = policy.validate_behavioral(
        {
            "is_revenge_trade": False,
            "is_chasing": False,
            "emotional_state": "calm",
            "confidence": 0.7,
            "rule_exceptions": [],
        }
    )
    assert len(reasons) == 0
