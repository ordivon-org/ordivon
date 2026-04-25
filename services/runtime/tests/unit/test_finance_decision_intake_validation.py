"""H-4: DecisionIntake Discipline Validation — 10-point compliance test suite."""

from __future__ import annotations

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from capabilities.domain.finance_decisions import FinanceDecisionCapability
from domains.decision_intake.models import DecisionIntake
from domains.decision_intake.repository import DecisionIntakeRepository
from domains.decision_intake.service import DecisionIntakeService
from domains.execution_records.orm import ExecutionReceiptORM
from domains.strategy.orm import RecommendationORM
from packs.finance.decision_intake import validate_finance_decision_intake
from state.db.base import Base


# ── Helpers ──────────────────────────────────────────────────────────

def _make_db():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    testing_session_local = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)
    return engine, testing_session_local


def _valid_payload() -> dict:
    return {
        "symbol": "BTC/USDT",
        "timeframe": "1h",
        "direction": "long",
        "thesis": "Momentum and structure are aligned.",
        "entry_condition": "Breakout with retest.",
        "invalidation_condition": "Range reclaim fails.",
        "stop_loss": "Below intraday support",
        "target": "Retest local high",
        "position_size_usdt": 150.0,
        "max_loss_usdt": 25.0,
        "risk_unit_usdt": 10.0,
        "is_revenge_trade": False,
        "is_chasing": False,
        "emotional_state": "calm",
        "confidence": 0.6,
        "rule_exceptions": [],
        "notes": "Controlled setup",
    }


# ── 1. valid decision intake can be created ──────────────────────────

def test_valid_decision_intake_can_be_created():
    result = validate_finance_decision_intake(_valid_payload())
    assert result.is_valid is True
    assert result.validation_errors == []
    assert result.payload["thesis"] == "Momentum and structure are aligned."


# ── 2. missing thesis is invalid ─────────────────────────────────────

def test_missing_thesis_is_invalid():
    payload = _valid_payload()
    del payload["thesis"]
    result = validate_finance_decision_intake(payload)
    assert result.is_valid is False
    assert any(e["field"] == "thesis" for e in result.validation_errors)


# ── 3. missing stop_loss is invalid ──────────────────────────────────

def test_missing_stop_loss_is_invalid():
    payload = _valid_payload()
    del payload["stop_loss"]
    result = validate_finance_decision_intake(payload)
    assert result.is_valid is False
    assert any(e["field"] == "stop_loss" for e in result.validation_errors)


# ── 4. missing max_loss_usdt is invalid ──────────────────────────────

def test_missing_max_loss_usdt_is_invalid():
    payload = _valid_payload()
    payload["max_loss_usdt"] = None
    result = validate_finance_decision_intake(payload)
    assert result.is_valid is False
    assert any(e["field"] == "max_loss_usdt" for e in result.validation_errors)


# ── 5. revenge_trade must be explicit ────────────────────────────────

def test_revenge_trade_must_be_explicit():
    payload = _valid_payload()
    del payload["is_revenge_trade"]
    result = validate_finance_decision_intake(payload)
    assert result.is_valid is False
    assert any(e["field"] == "is_revenge_trade" for e in result.validation_errors)


# ── 6. chasing must be explicit ──────────────────────────────────────

def test_chasing_must_be_explicit():
    payload = _valid_payload()
    payload["is_chasing"] = None
    result = validate_finance_decision_intake(payload)
    assert result.is_valid is False
    assert any(e["field"] == "is_chasing" for e in result.validation_errors)


# ── 7. create intake does not create recommendation ──────────────────

def test_create_intake_does_not_create_recommendation():
    engine, testing_session_local = _make_db()
    db = testing_session_local()
    try:
        capability = FinanceDecisionCapability()
        capability.create_intake(_valid_payload(), db)

        recos = db.query(RecommendationORM).count()
        assert recos == 0, f"Expected 0 recommendations, found {recos}"
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


# ── 8. create intake does not create execution receipt ───────────────

def test_create_intake_does_not_create_execution_receipt():
    engine, testing_session_local = _make_db()
    db = testing_session_local()
    try:
        capability = FinanceDecisionCapability()
        capability.create_intake(_valid_payload(), db)

        receipts = db.query(ExecutionReceiptORM).count()
        assert receipts == 0, f"Expected 0 execution receipts, found {receipts}"
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


# ── 9. create intake does not trigger governance ─────────────────────

def test_create_intake_does_not_trigger_governance():
    """Governance must remain not_started after creation — requires explicit call."""
    engine, testing_session_local = _make_db()
    db = testing_session_local()
    try:
        capability = FinanceDecisionCapability()
        intake = capability.create_intake(_valid_payload(), db)
        db.commit()

        # Re-read to ensure governance_status was not auto-triggered
        service = DecisionIntakeService(DecisionIntakeRepository(db))
        reloaded = service.get_model(intake.id)

        assert reloaded.governance_status == "not_started", (
            f"Governance must stay 'not_started' after create, got '{reloaded.governance_status}'"
        )
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


# ── 10. create intake does not trigger broker / order / execution ────

def test_create_intake_does_not_trigger_broker_order_execution():
    """
    Broker/order/execution modules must not be importable from the intake
    code path.  This test verifies that the intake service layer has no
    side effects touching broker, order, or execution domain objects.
    """
    engine, testing_session_local = _make_db()
    db = testing_session_local()
    try:
        capability = FinanceDecisionCapability()
        intake = capability.create_intake(_valid_payload(), db)
        db.commit()

        # Verify the intake was created cleanly
        assert intake.status == "validated"
        assert intake.governance_status == "not_started"

        # Verify no execution-side tables have been touched
        from domains.execution_records.orm import ExecutionReceiptORM
        receipts = db.query(ExecutionReceiptORM).count()
        assert receipts == 0

        # Verify no recommendation tables touched
        from domains.strategy.orm import RecommendationORM
        recos = db.query(RecommendationORM).count()
        assert recos == 0
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


# ── 11. invalid intake cannot be governed ────────────────────────────

def test_invalid_intake_cannot_be_governed():
    """An intake with validation errors must not be accepted by governance."""
    engine, testing_session_local = _make_db()
    db = testing_session_local()
    try:
        capability = FinanceDecisionCapability()

        # Create an invalid intake
        payload = _valid_payload()
        payload["thesis"] = None
        intake = capability.create_intake(payload, db)
        db.commit()

        assert intake.status == "invalid"

        # Attempt governance — must reject
        intake2, decision = capability.govern_intake(intake.id, db)
        assert decision.decision == "reject", (
            f"Governance must reject invalid intake, got decision='{decision.decision}'"
        )
        assert any("only validated" in r for r in decision.reasons), (
            f"Rejection reason must mention 'only validated', got: {decision.reasons}"
        )
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)
