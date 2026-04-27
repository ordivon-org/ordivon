"""FinanceOutcomeCapability receipt validation guard tests.

Tests the capture_manual_outcome() receipt validation invariants:
- Reject nonexistent execution receipt (PlanReceiptNotValid)
- Succeed with valid plan receipt
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from capabilities.domain.finance_decisions import FinanceDecisionCapability
from capabilities.domain.finance_outcome import (
    FinanceOutcomeCapability,
    PlanReceiptNotValid,
)
from state.db.base import Base


def _make_db():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    testing_session_local = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)
    return engine, testing_session_local


def _create_and_govern(db, payload_override=None) -> str:
    """Create a validated intake, run governance to execute, returns intake_id."""
    payload = {
        "symbol": "BTC/USDT",
        "timeframe": "1h",
        "direction": "long",
        "thesis": "BTC breaking above resistance with volume confirmation.",
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
    if payload_override:
        payload.update(payload_override)

    cap = FinanceDecisionCapability()
    model = cap.create_intake(payload, db)
    db.commit()

    updated, decision = cap.govern_intake(model.id, db)
    db.commit()
    return model.id


def _create_and_plan(db) -> tuple[str, str]:
    """Create intake, govern, plan — returns (intake_id, execution_receipt_id)."""
    intake_id = _create_and_govern(db)
    cap = FinanceDecisionCapability()
    result = cap.plan_intake(intake_id, db)
    db.commit()
    return intake_id, result.execution_receipt_id


# ── Test 1: reject nonexistent receipt ────────────────────────────────


def test_capture_outcome_rejects_nonexistent_receipt():
    """capture_manual_outcome with nonexistent execution_receipt_id raises PlanReceiptNotValid."""
    engine, testing_session_local = _make_db()
    db = testing_session_local()
    try:
        intake_id = _create_and_govern(db)

        cap = FinanceOutcomeCapability()
        try:
            cap.capture_manual_outcome(
                decision_intake_id=intake_id,
                execution_receipt_id="exrcpt_nonexistent",
                observed_outcome="Test.",
                verdict="validated",
                db=db,
            )
            assert False, "Should have raised PlanReceiptNotValid"
        except PlanReceiptNotValid as exc:
            assert "not found" in str(exc)
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


# ── Test 2: succeed with valid receipt ────────────────────────────────


def test_capture_outcome_succeeds_with_valid_receipt():
    """Create intake → govern → plan → capture_manual_outcome with valid receipt."""
    engine, testing_session_local = _make_db()
    db = testing_session_local()
    try:
        intake_id, receipt_id = _create_and_plan(db)

        cap = FinanceOutcomeCapability()
        result = cap.capture_manual_outcome(
            decision_intake_id=intake_id,
            execution_receipt_id=receipt_id,
            observed_outcome="Trade hit stop loss at -2%.",
            verdict="validated",
            variance_summary="Expected -1%, actual -2%.",
            plan_followed=True,
            db=db,
        )
        db.commit()

        assert result.outcome_id is not None
        assert result.outcome_source == "manual"
        assert result.decision_intake_id == intake_id
        assert result.execution_receipt_id == receipt_id
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)
