"""H-6: Finance Plan-Only Receipt — Unit Tests.

Tests the FinanceDecisionCapability.plan_intake() method with all
governance gates, idempotency, and side-effect isolation.

Uses standard pytest def test_*() convention (NOT pytest-describe).
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from capabilities.domain.finance_decisions import (
    FinanceDecisionCapability,
    PlanReceiptConflict,
    PlanReceiptNotAllowed,
)
from domains.decision_intake.repository import DecisionIntakeRepository
from domains.decision_intake.service import DecisionIntakeService
from domains.execution_records.orm import ExecutionReceiptORM, ExecutionRequestORM
from governance.audit.orm import AuditEventORM
from governance.risk_engine.engine import RiskEngine
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
    """Create a validated intake, run governance to execute. Returns intake_id."""
    payload = {
        "symbol": "BTC/USDT",
        "timeframe": "1h",
        "direction": "long",
        "thesis": "Momentum and structure aligned.",
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
    return model.id, decision


# ── Test 1: execute intake can create plan-only receipt ──────────────────


def test_execute_intake_creates_plan_receipt():
    engine, testing_session_local = _make_db()
    db = testing_session_local()
    try:
        intake_id, decision = _create_and_govern(db)
        assert decision.decision == "execute"

        cap = FinanceDecisionCapability()
        result = cap.plan_intake(intake_id, db)
        db.commit()

        assert result.receipt_kind == "plan"
        assert result.broker_execution is False
        assert result.side_effect_level == "none"
        assert result.decision_intake_id == intake_id
        assert result.governance_status == "execute"
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


# ── Test 2: invalid intake cannot create plan receipt ─────────────────────


def test_invalid_intake_cannot_create_plan_receipt():
    engine, testing_session_local = _make_db()
    db = testing_session_local()
    try:
        cap = FinanceDecisionCapability()
        model = cap.create_intake({
            "symbol": "BTC/USDT",
            "direction": "long",
            "thesis": None,
        }, db)
        db.commit()
        assert model.status == "invalid"

        # Cannot plan an invalid intake even before governance
        try:
            cap.plan_intake(model.id, db)
            assert False, "Should have raised PlanReceiptNotAllowed"
        except PlanReceiptNotAllowed as exc:
            assert "got 'not_started'" in str(exc)
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


# ── Test 3: reject governance intake cannot create plan receipt ───────────


def test_rejected_intake_cannot_create_plan_receipt():
    engine, testing_session_local = _make_db()
    db = testing_session_local()
    try:
        cap = FinanceDecisionCapability()
        model = cap.create_intake({
            "symbol": "BTC/USDT",
            "direction": "long",
            "thesis": None,
        }, db)
        db.commit()

        updated, decision = cap.govern_intake(model.id, db)
        db.commit()
        assert decision.decision == "reject"

        try:
            cap.plan_intake(model.id, db)
            assert False, "Should have raised PlanReceiptNotAllowed"
        except PlanReceiptNotAllowed as exc:
            assert "got 'reject'" in str(exc)
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


# ── Test 4: escalate governance intake cannot create plan receipt ─────────


def test_escalated_intake_cannot_create_plan_receipt():
    engine, testing_session_local = _make_db()
    db = testing_session_local()
    try:
        intake_id, decision = _create_and_govern(db, payload_override={
            "is_revenge_trade": True,
        })
        assert decision.decision == "escalate"

        cap = FinanceDecisionCapability()
        try:
            cap.plan_intake(intake_id, db)
            assert False, "Should have raised PlanReceiptNotAllowed"
        except PlanReceiptNotAllowed as exc:
            assert "got 'escalate'" in str(exc)
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


# ── Test 5: plan receipt includes receipt_kind=plan ─────────────────────


def test_plan_receipt_has_receipt_kind_plan():
    engine, testing_session_local = _make_db()
    db = testing_session_local()
    try:
        intake_id, _ = _create_and_govern(db)
        cap = FinanceDecisionCapability()
        result = cap.plan_intake(intake_id, db)
        db.commit()
        assert result.receipt_kind == "plan"
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


# ── Test 6: plan receipt includes broker_execution=false ─────────────────


def test_plan_receipt_has_broker_execution_false():
    engine, testing_session_local = _make_db()
    db = testing_session_local()
    try:
        intake_id, _ = _create_and_govern(db)
        cap = FinanceDecisionCapability()
        result = cap.plan_intake(intake_id, db)
        db.commit()
        assert result.broker_execution is False
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


# ── Test 7: plan receipt includes side_effect_level=none ─────────────────


def test_plan_receipt_has_side_effect_level_none():
    engine, testing_session_local = _make_db()
    db = testing_session_local()
    try:
        intake_id, _ = _create_and_govern(db)
        cap = FinanceDecisionCapability()
        result = cap.plan_intake(intake_id, db)
        db.commit()
        assert result.side_effect_level == "none"
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


# ── Test 8: plan creation creates ExecutionRequestORM ────────────────────


def test_plan_creation_creates_execution_request_orm():
    engine, testing_session_local = _make_db()
    db = testing_session_local()
    try:
        intake_id, _ = _create_and_govern(db)
        cap = FinanceDecisionCapability()
        result = cap.plan_intake(intake_id, db)
        db.commit()

        request = db.query(ExecutionRequestORM).filter(
            ExecutionRequestORM.id == result.execution_request_id
        ).one()
        assert request.action_id == "finance_decision_plan"
        assert request.family == "finance"
        assert request.status == "succeeded"
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


# ── Test 9: plan creation creates ExecutionReceiptORM ────────────────────


def test_plan_creation_creates_execution_receipt_orm():
    engine, testing_session_local = _make_db()
    db = testing_session_local()
    try:
        intake_id, _ = _create_and_govern(db)
        cap = FinanceDecisionCapability()
        result = cap.plan_intake(intake_id, db)
        db.commit()

        receipt = db.query(ExecutionReceiptORM).filter(
            ExecutionReceiptORM.id == result.execution_receipt_id
        ).one()
        assert receipt.status == "succeeded"
        assert receipt.request_id == result.execution_request_id
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


# ── Test 10: plan creation writes AuditEvent ─────────────────────────────


def test_plan_creation_writes_audit_event():
    engine, testing_session_local = _make_db()
    db = testing_session_local()
    try:
        intake_id, _ = _create_and_govern(db)
        cap = FinanceDecisionCapability()
        cap.plan_intake(intake_id, db)
        db.commit()

        events = db.query(AuditEventORM).filter(
            AuditEventORM.event_type == "plan_receipt_created"
        ).all()
        assert len(events) == 1
        assert events[0].entity_type == "decision_intake"
        assert events[0].entity_id == intake_id
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


# ── Test 11: plan creation does NOT create Recommendation ────────────────


def test_plan_creation_does_not_create_recommendation():
    from domains.strategy.orm import RecommendationORM
    engine, testing_session_local = _make_db()
    db = testing_session_local()
    try:
        intake_id, _ = _create_and_govern(db)
        cap = FinanceDecisionCapability()
        cap.plan_intake(intake_id, db)
        db.commit()

        count = db.query(RecommendationORM).count()
        assert count == 0, "H-6 must not create Recommendation"
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


# ── Test 12: plan creation does NOT create Outcome ───────────────────────


def test_plan_creation_does_not_create_outcome():
    engine, testing_session_local = _make_db()
    db = testing_session_local()
    try:
        intake_id, _ = _create_and_govern(db)
        cap = FinanceDecisionCapability()
        cap.plan_intake(intake_id, db)
        db.commit()

        # No Outcome model exists yet — verify no outcome-related audit events
        outcome_events = db.query(AuditEventORM).filter(
            AuditEventORM.event_type.like("%outcome%")
        ).count()
        assert outcome_events == 0, "H-6 must not create outcome events"

        # No broker-execution audit events
        broker_events = db.query(AuditEventORM).filter(
            AuditEventORM.event_type.like("%broker%")
        ).count()
        assert broker_events == 0, "H-6 must not create broker events"
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


# ── Test 13: plan creation does NOT trigger broker/order/execution ───────


def test_plan_creation_does_not_trigger_broker_order_trade():
    engine, testing_session_local = _make_db()
    db = testing_session_local()
    try:
        intake_id, _ = _create_and_govern(db)
        cap = FinanceDecisionCapability()
        cap.plan_intake(intake_id, db)
        db.commit()

        # Verify no broker-related execution requests
        broker_requests = db.query(ExecutionRequestORM).filter(
            ExecutionRequestORM.action_id.like("%order%")
        ).count()
        assert broker_requests == 0

        # Only one execution request: finance_decision_plan
        total_requests = db.query(ExecutionRequestORM).count()
        assert total_requests == 1

        req = db.query(ExecutionRequestORM).one()
        assert req.action_id == "finance_decision_plan"
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


# ── Test 14: repeated plan creation is explicitly rejected ───────────────


def test_repeated_plan_creation_rejected():
    engine, testing_session_local = _make_db()
    db = testing_session_local()
    try:
        intake_id, _ = _create_and_govern(db)
        cap = FinanceDecisionCapability()

        # First plan — succeeds
        result1 = cap.plan_intake(intake_id, db)
        db.commit()
        assert result1.receipt_kind == "plan"

        # Second plan — must raise PlanReceiptConflict
        try:
            cap.plan_intake(intake_id, db)
            assert False, "Should have raised PlanReceiptConflict"
        except PlanReceiptConflict as exc:
            assert intake_id in str(exc)
            assert result1.execution_request_id in str(exc)

        db.rollback()

        # Verify only one execution request exists
        count = db.query(ExecutionRequestORM).count()
        assert count == 1, "Duplicate plan must not create second request"
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


# ── Test: plan receipt result has all required metadata fields ──────────


def test_plan_receipt_result_has_all_required_metadata():
    engine, testing_session_local = _make_db()
    db = testing_session_local()
    try:
        intake_id, _ = _create_and_govern(db)
        cap = FinanceDecisionCapability()
        result = cap.plan_intake(intake_id, db)
        db.commit()

        assert result.execution_request_id.startswith("exreq_")
        assert result.execution_receipt_id.startswith("exrcpt_")
        assert result.receipt_kind == "plan"
        assert result.broker_execution is False
        assert result.side_effect_level == "none"
        assert result.decision_intake_id == intake_id
        assert result.governance_status == "execute"
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)
