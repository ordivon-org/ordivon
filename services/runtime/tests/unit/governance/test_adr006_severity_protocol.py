"""ADR-006 Severity Protocol 边界测试。

验证 RiskEngine 的 severity 协议在不同边界情况下的行为:
  1. Pack policy 返回 .severity == "reject" → 加入 reject_reasons
  2. Pack policy 返回 .severity == "escalate" → 加入 escalate_reasons
  3. Pack policy 返回未知 .severity → 不加入任何列表（安全忽略）
  4. Pack policy 返回的对象没有 .severity → AttributeError（这是期望行为 — 调用者必须遵守协议）
  5. pack_policy=None → 所有 gate 通过（向后兼容）
"""

import pytest

from domains.decision_intake.models import DecisionIntake
from governance_engine.risk_engine.engine import RiskEngine
from packs.finance.trading_discipline_policy import EscalateReason, RejectReason

# ── Minimal Pack policy for protocol testing ─────────────────────────


class _TestRejectPolicy:
    """A policy that returns only reject reasons."""

    def validate_fields(self, payload):
        return [RejectReason("test reject")]

    def validate_numeric(self, payload):
        return [RejectReason("numeric reject")]

    def validate_limits(self, payload):
        return []

    def validate_behavioral(self, payload):
        return []


class _TestEscalatePolicy:
    """A policy that returns only escalate reasons."""

    def validate_fields(self, payload):
        return [EscalateReason("test escalate")]

    def validate_numeric(self, payload):
        return []

    def validate_limits(self, payload):
        return []

    def validate_behavioral(self, payload):
        return []


class _TestMixedPolicy:
    """A policy that returns both reject and escalate reasons."""

    def validate_fields(self, payload):
        return [RejectReason("reject first")]

    def validate_numeric(self, payload):
        return [EscalateReason("escalate second")]

    def validate_limits(self, payload):
        return []

    def validate_behavioral(self, payload):
        return []


class _TestUnknownSeverityReason:
    """A reason with an unknown severity value."""

    def __init__(self, message):
        self.message = message
        self.severity = "unknown"


class _TestNoSeverityReason:
    """A reason WITHOUT a .severity attribute — violates protocol."""

    def __init__(self, message):
        self.message = message


class _TestUnknownSeverityPolicy:
    """A policy returning reasons with unknown severity."""

    def validate_fields(self, payload):
        return [_TestUnknownSeverityReason("unknown")]

    def validate_numeric(self, payload):
        return []

    def validate_limits(self, payload):
        return []

    def validate_behavioral(self, payload):
        return []


class _TestNoSeverityPolicy:
    """A policy returning reasons without .severity attribute."""

    def validate_fields(self, payload):
        return [_TestNoSeverityReason("no severity")]

    def validate_numeric(self, payload):
        return []

    def validate_limits(self, payload):
        return []

    def validate_behavioral(self, payload):
        return []


# ── Helpers ──────────────────────────────────────────────────────────


def _valid_intake() -> DecisionIntake:
    return DecisionIntake(
        id="intake-test-severity",
        pack_id="test",
        intake_type="controlled_decision",
        payload={
            "thesis": "Valid test thesis with confirmation criteria.",
            "stop_loss": "2%",
            "emotional_state": "calm",
        },
        status="validated",
    )


# ── Tests ────────────────────────────────────────────────────────────


def test_severity_reject_returns_reject_decision():
    """severity == 'reject' → GovernanceDecision with decision='reject'."""
    engine = RiskEngine()
    intake = _valid_intake()
    decision = engine.validate_intake(intake, pack_policy=_TestRejectPolicy())
    assert decision.decision == "reject"
    assert "test reject" in decision.reasons
    assert "numeric reject" in decision.reasons


def test_severity_escalate_returns_escalate_decision():
    """severity == 'escalate' → GovernanceDecision with decision='escalate'."""
    engine = RiskEngine()
    intake = _valid_intake()
    decision = engine.validate_intake(intake, pack_policy=_TestEscalatePolicy())
    assert decision.decision == "escalate"
    assert "test escalate" in decision.reasons


def test_severity_mixed_returns_reject_priority():
    """reject 和 escalate 混合时 → reject 优先。"""
    engine = RiskEngine()
    intake = _valid_intake()
    decision = engine.validate_intake(intake, pack_policy=_TestMixedPolicy())
    assert decision.decision == "reject", "Reject must take priority over escalate when both are present"


def test_severity_unknown_is_silently_ignored():
    """未知 severity → 不加入任何列表，退化为 execute。"""
    engine = RiskEngine()
    intake = _valid_intake()
    decision = engine.validate_intake(intake, pack_policy=_TestUnknownSeverityPolicy())
    # Unknown severity is neither "reject" nor "escalate" → no reasons collected
    # → falls through to execute
    assert decision.decision == "execute"


def test_missing_severity_raises_attribute_error():
    """缺少 .severity 属性 → AttributeError（协议违规）。"""
    engine = RiskEngine()
    intake = _valid_intake()
    with pytest.raises(AttributeError, match="severity"):
        engine.validate_intake(intake, pack_policy=_TestNoSeverityPolicy())


def test_null_pack_policy_returns_execute():
    """pack_policy=None → 所有 gate 通过，返回 execute。"""
    engine = RiskEngine()
    intake = _valid_intake()
    decision = engine.validate_intake(intake, pack_policy=None)
    assert decision.decision == "execute"
