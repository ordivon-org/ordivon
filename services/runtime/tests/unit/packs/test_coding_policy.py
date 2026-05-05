"""Coding Pack policy tests — verify CodingDisciplinePolicy gate rules.

Tests all five gates and integration with RiskEngine.
"""

import pytest

from domains.decision_intake.models import DecisionIntake
from governance_engine.risk_engine.engine import RiskEngine
from packs.coding.policy import (
    CodingDisciplinePolicy,
    CodingRejectReason,
    CodingEscalateReason,
)


# ── Helpers ──────────────────────────────────────────────────────────


def _valid_payload(**overrides):
    """Build a valid coding payload with sensible defaults."""
    p = {
        "task_description": "Add input validation to the user registration form",
        "file_paths": ["apps/web/src/components/RegisterForm.tsx"],
        "estimated_impact": "low",
        "reasoning": "The form currently accepts empty strings for required fields.",
        "test_plan": "Add unit tests for empty input, boundary values, and SQL injection.",
    }
    p.update(overrides)
    return p


def _valid_intake(payload=None):
    """Build a DecisionIntake for coding pack."""
    return DecisionIntake(
        id="intake-test-coding",
        pack_id="coding",
        intake_type="code_change",
        payload=payload or _valid_payload(),
        status="validated",
    )


# ═══════════════════════════════════════════════════════════════════════
# Test 1: missing task_description → reject
# ═══════════════════════════════════════════════════════════════════════


def test_missing_task_description_rejects():
    """Empty task_description must reject."""
    policy = CodingDisciplinePolicy()
    reasons = policy.validate_fields(_valid_payload(task_description=""))
    assert len(reasons) == 1
    assert reasons[0].severity == "reject"
    assert "task_description" in reasons[0].message.lower()


# ═══════════════════════════════════════════════════════════════════════
# Test 2: missing file_paths → reject
# ═══════════════════════════════════════════════════════════════════════


def test_missing_file_paths_rejects():
    """Empty file_paths must reject."""
    policy = CodingDisciplinePolicy()
    reasons = policy.validate_fields(_valid_payload(file_paths=[]))
    assert len(reasons) == 1
    assert reasons[0].severity == "reject"
    assert "file_paths" in reasons[0].message.lower()


# ═══════════════════════════════════════════════════════════════════════
# Test 3: forbidden file path → reject
# ═══════════════════════════════════════════════════════════════════════


@pytest.mark.parametrize(
    "bad_path",
    [
        ".env",
        "config/secrets.yaml",
        "keys/private_key.pem",
        "state/db/migrations/runner.py",
        "pyproject.toml",
        "uv.lock",
        "package.json",
        "pnpm-lock.yaml",
    ],
)
def test_forbidden_file_path_rejects(bad_path):
    """Each forbidden path pattern must trigger reject."""
    policy = CodingDisciplinePolicy()
    reasons = policy.validate_limits(_valid_payload(file_paths=[bad_path]))
    assert len(reasons) >= 1
    assert all(r.severity == "reject" for r in reasons)
    assert any(bad_path in r.message for r in reasons)


# ═══════════════════════════════════════════════════════════════════════
# Test 4: high impact → escalate
# ═══════════════════════════════════════════════════════════════════════


def test_high_impact_escalates():
    """estimated_impact='high' must escalate."""
    policy = CodingDisciplinePolicy()
    reasons = policy.validate_behavioral(_valid_payload(estimated_impact="high"))
    assert len(reasons) >= 1
    assert any(r.severity == "escalate" and "high" in r.message.lower() for r in reasons)


# ═══════════════════════════════════════════════════════════════════════
# Test 5: missing test_plan → escalate
# ═══════════════════════════════════════════════════════════════════════


@pytest.mark.parametrize("bad_test_plan", [None, "", "   "])
def test_missing_test_plan_escalates(bad_test_plan):
    """Missing or whitespace-only test_plan must escalate."""
    policy = CodingDisciplinePolicy()
    reasons = policy.validate_behavioral(_valid_payload(test_plan=bad_test_plan))
    assert any(r.severity == "escalate" and "test_plan" in r.message.lower() for r in reasons)


# ═══════════════════════════════════════════════════════════════════════
# Test 6: valid payload → execute through RiskEngine
# ═══════════════════════════════════════════════════════════════════════


def test_valid_coding_payload_executes_through_risk_engine():
    """A fully valid coding payload must pass RiskEngine with execute verdict."""
    engine = RiskEngine()
    intake = _valid_intake()
    policy = CodingDisciplinePolicy()
    decision = engine.validate_intake(intake, pack_policy=policy)
    assert decision.decision == "execute"
    assert "Passed all governance gates" in decision.reasons[0]


# ═══════════════════════════════════════════════════════════════════════
# Test 7: multiple violations accumulate
# ═══════════════════════════════════════════════════════════════════════


def test_multiple_violations_accumulate():
    """Empty task + empty file_paths + high impact + missing test_plan → all collected."""
    engine = RiskEngine()
    intake = _valid_intake(
        _valid_payload(
            task_description="",
            file_paths=[],
            estimated_impact="high",
            test_plan=None,
        )
    )
    policy = CodingDisciplinePolicy()
    decision = engine.validate_intake(intake, pack_policy=policy)
    # reject beats escalate → must be reject
    assert decision.decision == "reject"
    # At least 2 reject reasons (missing task + missing file_paths)
    reject_count = sum(1 for r in decision.reasons if "task_description" in r.lower() or "file_paths" in r.lower())
    assert reject_count >= 2


# ═══════════════════════════════════════════════════════════════════════
# Test 8: severity protocol compliance
# ═══════════════════════════════════════════════════════════════════════


def test_coding_reasons_have_severity_and_message():
    """All coding reasons must have .severity and .message attributes."""
    reject = CodingRejectReason("test")
    escalate = CodingEscalateReason("test")
    assert reject.severity == "reject"
    assert reject.message == "test"
    assert escalate.severity == "escalate"
    assert escalate.message == "test"


def test_coding_reason_severity_only_reject_or_escalate():
    """No other severity values allowed."""
    reject = CodingRejectReason("x")
    escalate = CodingEscalateReason("x")
    assert reject.severity in ("reject", "escalate")
    assert escalate.severity in ("reject", "escalate")
    assert reject.severity != escalate.severity


# ═══════════════════════════════════════════════════════════════════════
# Test 9: valid payload with all optional fields
# ═══════════════════════════════════════════════════════════════════════


def test_valid_payload_all_fields():
    """A fully populated payload must produce no reasons."""
    policy = CodingDisciplinePolicy()
    p = _valid_payload(
        task_description="Refactor the authentication middleware",
        file_paths=["apps/api/app/middleware/auth.py", "tests/unit/test_auth.py"],
        estimated_impact="medium",
        reasoning="Extract duplicate logic, no behavioral change.",
        test_plan="Run existing auth test suite, add edge case for expired tokens.",
    )
    reasons = (
        policy.validate_fields(p)
        + policy.validate_numeric(p)
        + policy.validate_limits(p)
        + policy.validate_behavioral(p)
    )
    assert len(reasons) == 0


# ═══════════════════════════════════════════════════════════════════════
# Test 10: CodingDecisionPayload model validation
# ═══════════════════════════════════════════════════════════════════════


def test_coding_decision_payload_invalid_impact_raises():
    """Invalid estimated_impact must raise ValueError."""
    from packs.coding.models import CodingDecisionPayload

    with pytest.raises(ValueError, match="estimated_impact"):
        CodingDecisionPayload(
            task_description="test",
            file_paths=("a.py",),
            estimated_impact="critical",  # invalid
        )
