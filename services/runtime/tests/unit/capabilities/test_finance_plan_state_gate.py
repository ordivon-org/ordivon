"""Task 4.1+4.2: plan_intake governance gate + duplicate rejection tests.

Tests the governance_status gate in FinanceDecisionCapability.plan_intake():
- Rejects "reject" and "escalate" governance_status values
- Allows "execute" governance_status
- Rejects duplicate plan receipts (idempotency guard)
"""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from capabilities.domain.finance_decisions import (
    FinanceDecisionCapability,
    PlanReceiptConflict,
    PlanReceiptNotAllowed,
)
from domains.decision_intake.repository import DecisionIntakeRepository
from domains.decision_intake.service import DecisionIntakeService
from state.db.base import Base


@pytest.fixture
def db() -> Session:
    engine = create_engine("sqlite:///:memory:", poolclass=StaticPool)
    Base.metadata.create_all(bind=engine)
    with Session(engine) as session:
        yield session
    Base.metadata.drop_all(bind=engine)


# ── Helper: valid payload for intake creation ──────────────────────────


def _valid_payload() -> dict:
    return {
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
        "notes": "Controlled setup",
    }


# ═════════════════════════════════════════════════════════════════════════
# Test 1: plan_intake rejects "reject" governance_status
# ═════════════════════════════════════════════════════════════════════════


def test_plan_intake_rejects_rejected_status(db: Session):
    """plan_intake raises PlanReceiptNotAllowed when governance_status is 'reject'."""
    service = DecisionIntakeService(DecisionIntakeRepository(db))
    intake = service.record_intake(
        pack_id="finance",
        intake_type="controlled_decision",
        payload=_valid_payload(),
        validation_errors=[],
    )
    db.commit()

    # Directly set governance_status to "reject" via service
    updated = service.update_governance_status(intake.id, "reject")
    db.commit()
    assert updated.governance_status == "reject"

    cap = FinanceDecisionCapability()
    with pytest.raises(PlanReceiptNotAllowed) as exc_info:
        cap.plan_intake(intake.id, db)

    msg = str(exc_info.value)
    assert "execute" in msg.lower()
    assert "reject" in msg.lower()
    assert intake.id in msg


# ═════════════════════════════════════════════════════════════════════════
# Test 2: plan_intake rejects "escalate" governance_status
# ═════════════════════════════════════════════════════════════════════════


def test_plan_intake_rejects_escalated_status(db: Session):
    """plan_intake raises PlanReceiptNotAllowed when governance_status is 'escalate'."""
    service = DecisionIntakeService(DecisionIntakeRepository(db))
    intake = service.record_intake(
        pack_id="finance",
        intake_type="controlled_decision",
        payload=_valid_payload(),
        validation_errors=[],
    )
    db.commit()

    # Directly set governance_status to "escalate" via service
    updated = service.update_governance_status(intake.id, "escalate")
    db.commit()
    assert updated.governance_status == "escalate"

    cap = FinanceDecisionCapability()
    with pytest.raises(PlanReceiptNotAllowed) as exc_info:
        cap.plan_intake(intake.id, db)

    msg = str(exc_info.value)
    assert "execute" in msg.lower()
    assert "escalate" in msg.lower()
    assert intake.id in msg


# ═════════════════════════════════════════════════════════════════════════
# Test 3: plan_intake allows "execute" governance_status
# ═════════════════════════════════════════════════════════════════════════


def test_plan_intake_allows_execute_status(db: Session):
    """plan_intake succeeds when governance_status is 'execute' (happy path)."""
    cap = FinanceDecisionCapability()
    intake = cap.create_intake(_valid_payload(), db)
    db.commit()

    updated, decision = cap.govern_intake(intake.id, db)
    db.commit()
    assert decision.decision == "execute"
    assert updated.governance_status == "execute"

    result = cap.plan_intake(intake.id, db)
    db.commit()

    assert result.execution_receipt_id is not None
    assert result.execution_receipt_id.startswith("exrcpt_")
    assert result.broker_execution is False


# ═════════════════════════════════════════════════════════════════════════
# Test 4: plan_intake rejects duplicate plan receipts
# ═════════════════════════════════════════════════════════════════════════


def test_plan_intake_rejects_duplicate(db: Session):
    """Second plan_intake call raises PlanReceiptConflict (idempotency guard)."""
    cap = FinanceDecisionCapability()
    intake = cap.create_intake(_valid_payload(), db)
    db.commit()

    updated, decision = cap.govern_intake(intake.id, db)
    db.commit()
    assert decision.decision == "execute"

    # First plan — succeeds
    result1 = cap.plan_intake(intake.id, db)
    db.commit()
    assert result1.receipt_kind == "plan"

    # Second plan — must raise PlanReceiptConflict
    with pytest.raises(PlanReceiptConflict) as exc_info:
        cap.plan_intake(intake.id, db)

    msg = str(exc_info.value)
    assert intake.id in msg
    assert result1.execution_request_id in msg
    assert "already exists" in msg.lower()

    db.rollback()
