"""H-7: Finance Manual Outcome Capture — Unit Tests.

Tests the FinanceOutcomeCapability.capture_manual_outcome() method
with all plan-receipt validation gates, duplicate detection, and
side-effect isolation.

Uses standard pytest def test_*() convention (NOT pytest-describe).
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from capabilities.domain.finance_decisions import FinanceDecisionCapability
from capabilities.domain.finance_outcome import (
    DecisionIntakeNotFound,
    FinanceOutcomeCapability,
    ManualOutcomeConflict,
    PlanReceiptNotValid,
)
from domains.execution_records.orm import ExecutionReceiptORM, ExecutionRequestORM
from domains.finance_outcome.orm import FinanceManualOutcomeORM
from governance.audit.orm import AuditEventORM
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


# ── Test 1: execute intake + plan receipt can create manual outcome ──────


def test_execute_intake_with_plan_can_create_manual_outcome():
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

        assert result.outcome_id.startswith("fmout_")
        assert result.outcome_source == "manual"
        assert result.decision_intake_id == intake_id
        assert result.execution_receipt_id == receipt_id
        assert result.observed_outcome == "Trade hit stop loss at -2%."
        assert result.verdict == "validated"
        assert result.variance_summary == "Expected -1%, actual -2%."
        assert result.plan_followed is True
        assert result.created_at
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


# ── Test 2: outcome requires existing plan receipt ────────────────────────


def test_outcome_requires_existing_plan_receipt():
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


# ── Test 3: outcome cannot use non-plan receipt ──────────────────────────


def test_outcome_cannot_use_non_plan_receipt():
    engine, testing_session_local = _make_db()
    db = testing_session_local()
    try:
        intake_id, receipt_id = _create_and_plan(db)

        # Tamper with the receipt to change receipt_kind
        receipt = db.get(ExecutionReceiptORM, receipt_id)
        import json

        detail = json.loads(receipt.detail_json) if receipt.detail_json else {}
        detail["receipt_kind"] = "execution"
        receipt.detail_json = json.dumps(detail)
        db.flush()

        cap = FinanceOutcomeCapability()
        try:
            cap.capture_manual_outcome(
                decision_intake_id=intake_id,
                execution_receipt_id=receipt_id,
                observed_outcome="Test.",
                verdict="validated",
                db=db,
            )
            assert False, "Should have raised PlanReceiptNotValid"
        except PlanReceiptNotValid as exc:
            assert "receipt_kind" in str(exc)
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


# ── Test 4: outcome cannot be created when receipt decision_intake_id
#            mismatches path intake_id ────────────────────────────────────


def test_outcome_mismatched_decision_intake_id_rejected():
    engine, testing_session_local = _make_db()
    db = testing_session_local()
    try:
        # Create two intakes, plan only the first
        intake_id_a, receipt_id_a = _create_and_plan(db)
        intake_id_b = _create_and_govern(db)

        cap = FinanceOutcomeCapability()
        try:
            # Try to create outcome for intake_b using receipt from intake_a
            cap.capture_manual_outcome(
                decision_intake_id=intake_id_b,
                execution_receipt_id=receipt_id_a,
                observed_outcome="Test.",
                verdict="validated",
                db=db,
            )
            assert False, "Should have raised PlanReceiptNotValid"
        except PlanReceiptNotValid as exc:
            assert "does not match" in str(exc)
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


# ── Test 5: outcome_source is always "manual" ────────────────────────────


def test_outcome_source_is_manual():
    engine, testing_session_local = _make_db()
    db = testing_session_local()
    try:
        intake_id, receipt_id = _create_and_plan(db)

        cap = FinanceOutcomeCapability()
        result = cap.capture_manual_outcome(
            decision_intake_id=intake_id,
            execution_receipt_id=receipt_id,
            observed_outcome="Observed.",
            verdict="validated",
            db=db,
        )
        db.commit()
        assert result.outcome_source == "manual"

        # Verify at ORM level
        row = db.get(FinanceManualOutcomeORM, result.outcome_id)
        assert row.outcome_source == "manual"
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


# ── Test 6: observed_outcome persisted ───────────────────────────────────


def test_observed_outcome_persisted():
    engine, testing_session_local = _make_db()
    db = testing_session_local()
    try:
        intake_id, receipt_id = _create_and_plan(db)

        cap = FinanceOutcomeCapability()
        result = cap.capture_manual_outcome(
            decision_intake_id=intake_id,
            execution_receipt_id=receipt_id,
            observed_outcome="Target hit, +3% profit.",
            verdict="validated",
            db=db,
        )
        db.commit()

        row = db.get(FinanceManualOutcomeORM, result.outcome_id)
        assert row.observed_outcome == "Target hit, +3% profit."
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


# ── Test 7: verdict persisted ────────────────────────────────────────────


def test_verdict_persisted():
    engine, testing_session_local = _make_db()
    db = testing_session_local()
    try:
        intake_id, receipt_id = _create_and_plan(db)

        cap = FinanceOutcomeCapability()
        result = cap.capture_manual_outcome(
            decision_intake_id=intake_id,
            execution_receipt_id=receipt_id,
            observed_outcome="Test.",
            verdict="partially_validated",
            db=db,
        )
        db.commit()

        row = db.get(FinanceManualOutcomeORM, result.outcome_id)
        assert row.verdict == "partially_validated"
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


# ── Test 8: variance_summary persisted ───────────────────────────────────


def test_variance_summary_persisted():
    engine, testing_session_local = _make_db()
    db = testing_session_local()
    try:
        intake_id, receipt_id = _create_and_plan(db)

        cap = FinanceOutcomeCapability()
        result = cap.capture_manual_outcome(
            decision_intake_id=intake_id,
            execution_receipt_id=receipt_id,
            observed_outcome="Test.",
            verdict="validated",
            variance_summary="Expected +2%, got +5%.",
            db=db,
        )
        db.commit()

        row = db.get(FinanceManualOutcomeORM, result.outcome_id)
        assert row.variance_summary == "Expected +2%, got +5%."
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


# ── Test 9: plan_followed persisted ──────────────────────────────────────


def test_plan_followed_persisted():
    engine, testing_session_local = _make_db()
    db = testing_session_local()
    try:
        intake_id, receipt_id = _create_and_plan(db)

        cap = FinanceOutcomeCapability()
        result = cap.capture_manual_outcome(
            decision_intake_id=intake_id,
            execution_receipt_id=receipt_id,
            observed_outcome="Test.",
            verdict="validated",
            plan_followed=True,
            db=db,
        )
        db.commit()

        row = db.get(FinanceManualOutcomeORM, result.outcome_id)
        assert row.plan_followed is True

        # Also verify False case
        intake_id2, receipt_id2 = _create_and_plan(db)
        result2 = cap.capture_manual_outcome(
            decision_intake_id=intake_id2,
            execution_receipt_id=receipt_id2,
            observed_outcome="Test 2.",
            verdict="invalidated",
            plan_followed=False,
            db=db,
        )
        db.commit()
        row2 = db.get(FinanceManualOutcomeORM, result2.outcome_id)
        assert row2.plan_followed is False
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


# ── Test 10: duplicate outcome returns 409 conflict ──────────────────────


def test_duplicate_outcome_returns_conflict():
    engine, testing_session_local = _make_db()
    db = testing_session_local()
    try:
        intake_id, receipt_id = _create_and_plan(db)

        cap = FinanceOutcomeCapability()
        result1 = cap.capture_manual_outcome(
            decision_intake_id=intake_id,
            execution_receipt_id=receipt_id,
            observed_outcome="First outcome.",
            verdict="validated",
            db=db,
        )
        db.commit()

        try:
            cap.capture_manual_outcome(
                decision_intake_id=intake_id,
                execution_receipt_id=receipt_id,
                observed_outcome="Second outcome.",
                verdict="invalidated",
                db=db,
            )
            assert False, "Should have raised ManualOutcomeConflict"
        except ManualOutcomeConflict as exc:
            assert intake_id in str(exc)
            assert result1.outcome_id in str(exc)

        # Only one outcome row
        count = db.query(FinanceManualOutcomeORM).count()
        assert count == 1
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


# ── Test 11: outcome creation does NOT create broker/order/trade ──────────


def test_outcome_creation_does_not_create_broker_order_trade():
    from domains.candidate_rules.orm import CandidateRuleORM

    engine, testing_session_local = _make_db()
    db = testing_session_local()
    try:
        intake_id, receipt_id = _create_and_plan(db)

        cap = FinanceOutcomeCapability()
        cap.capture_manual_outcome(
            decision_intake_id=intake_id,
            execution_receipt_id=receipt_id,
            observed_outcome="Test.",
            verdict="validated",
            db=db,
        )
        db.commit()

        # No broker/order/trade execution requests
        broker_requests = (
            db.query(ExecutionRequestORM)
            .filter(
                ExecutionRequestORM.action_id.like("%order%")
                | ExecutionRequestORM.action_id.like("%trade%")
                | ExecutionRequestORM.action_id.like("%broker%")
            )
            .count()
        )
        assert broker_requests == 0, "Outcome must not create broker/order/trade"

        # Only one execution request: the plan receipt
        total = db.query(ExecutionRequestORM).count()
        assert total == 1
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


# ── Test 12: outcome creation does NOT create CandidateRule ───────────────


def test_outcome_creation_does_not_create_candidate_rule():
    from domains.candidate_rules.orm import CandidateRuleORM

    engine, testing_session_local = _make_db()
    db = testing_session_local()
    try:
        intake_id, receipt_id = _create_and_plan(db)

        cap = FinanceOutcomeCapability()
        cap.capture_manual_outcome(
            decision_intake_id=intake_id,
            execution_receipt_id=receipt_id,
            observed_outcome="Test.",
            verdict="validated",
            db=db,
        )
        db.commit()

        count = db.query(CandidateRuleORM).count()
        assert count == 0, "H-7 must not create CandidateRule"
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


# ── Test 13: outcome creation does NOT promote Policy ────────────────────


def test_outcome_creation_does_not_promote_policy():
    engine, testing_session_local = _make_db()
    db = testing_session_local()
    try:
        intake_id, receipt_id = _create_and_plan(db)

        cap = FinanceOutcomeCapability()
        cap.capture_manual_outcome(
            decision_intake_id=intake_id,
            execution_receipt_id=receipt_id,
            observed_outcome="Test.",
            verdict="validated",
            db=db,
        )
        db.commit()

        # No policy-related audit events
        policy_events = (
            db.query(AuditEventORM)
            .filter(AuditEventORM.event_type.like("%policy%") | AuditEventORM.event_type.like("%promote%"))
            .count()
        )
        assert policy_events == 0, "H-7 must not promote Policy"

        # The only audit events: governance_evaluated, plan_receipt_created, outcome_captured
        all_events = db.query(AuditEventORM).all()
        event_types = {e.event_type for e in all_events}
        assert event_types == {"governance_evaluated", "plan_receipt_created", "outcome_captured"}
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


# ── Test 14: outcome writes audit event with correct metadata ────────────


def test_outcome_writes_audit_event():
    engine, testing_session_local = _make_db()
    db = testing_session_local()
    try:
        intake_id, receipt_id = _create_and_plan(db)

        cap = FinanceOutcomeCapability()
        result = cap.capture_manual_outcome(
            decision_intake_id=intake_id,
            execution_receipt_id=receipt_id,
            observed_outcome="Test.",
            verdict="validated",
            variance_summary="variance",
            plan_followed=True,
            db=db,
        )
        db.commit()

        events = db.query(AuditEventORM).filter(AuditEventORM.event_type == "outcome_captured").all()
        assert len(events) == 1
        event = events[0]
        assert event.entity_type == "decision_intake"
        assert event.entity_id == intake_id

        import json

        payload = json.loads(event.payload_json) if event.payload_json else {}
        assert payload["outcome_id"] == result.outcome_id
        assert payload["outcome_source"] == "manual"
        assert payload["verdict"] == "validated"
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


# ── Test: result has all required fields ─────────────────────────────────


def test_outcome_result_has_all_required_fields():
    engine, testing_session_local = _make_db()
    db = testing_session_local()
    try:
        intake_id, receipt_id = _create_and_plan(db)

        cap = FinanceOutcomeCapability()
        result = cap.capture_manual_outcome(
            decision_intake_id=intake_id,
            execution_receipt_id=receipt_id,
            observed_outcome="All fields test.",
            verdict="inconclusive",
            variance_summary="Inconclusive.",
            plan_followed=False,
            db=db,
        )
        db.commit()

        assert result.outcome_id.startswith("fmout_")
        assert result.decision_intake_id == intake_id
        assert result.execution_receipt_id == receipt_id
        assert result.outcome_source == "manual"
        assert result.observed_outcome == "All fields test."
        assert result.verdict == "inconclusive"
        assert result.variance_summary == "Inconclusive."
        assert result.plan_followed is False
        assert result.created_at
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


# ── Test: non-existent intake returns 404 ────────────────────────────────


def test_nonexistent_intake_returns_not_found():
    engine, testing_session_local = _make_db()
    db = testing_session_local()
    try:
        cap = FinanceOutcomeCapability()
        try:
            cap.capture_manual_outcome(
                decision_intake_id="nonexistent_id",
                execution_receipt_id="exrcpt_any",
                observed_outcome="Test.",
                verdict="validated",
                db=db,
            )
            assert False, "Should have raised DecisionIntakeNotFound"
        except DecisionIntakeNotFound as exc:
            assert "nonexistent_id" in str(exc)
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)
