"""DB-backed Runtime Evidence Audit — integration tests.

Constructs a minimal complete evidence chain in a test database,
then runs the audit checks to verify each one passes or fails correctly.
"""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool

from capabilities.boundary import ActionContext
from domains.candidate_rules.repository import CandidateRuleRepository
from domains.decision_intake.models import DecisionIntake
from domains.decision_intake.repository import DecisionIntakeRepository
from domains.execution_records.orm import ExecutionReceiptORM
from domains.execution_records.repository import ExecutionRecordRepository
from domains.execution_records.service import ExecutionRecordService
from domains.finance_outcome.models import FinanceManualOutcome
from domains.finance_outcome.orm import FinanceManualOutcomeORM
from domains.finance_outcome.repository import FinanceManualOutcomeRepository
from domains.journal.models import Review
from domains.journal.orm import ReviewORM
from domains.journal.repository import ReviewRepository
from domains.journal.lesson_repository import LessonRepository
from domains.journal.lesson_service import LessonService
from domains.journal.service import ReviewService
from governance.risk_engine.engine import RiskEngine
from packs.finance.trading_discipline_policy import TradingDisciplinePolicy
from scripts.audit_runtime_evidence_db import audit_evidence_chain
from shared.enums.domain import ReviewVerdict
from shared.utils.ids import new_id
from state.db.base import Base


# ── Fixtures ──────────────────────────────────────────────────────────


@pytest.fixture
def db() -> Session:
    """Create an in-memory SQLite test database."""
    engine = create_engine("sqlite:///:memory:", poolclass=StaticPool)
    Base.metadata.create_all(engine)
    TestingSession = sessionmaker(bind=engine)
    session = TestingSession()
    # Run migrations for the fresh DB
    from state.db.migrations.runner import run_migrations

    with engine.connect() as conn:
        run_migrations(conn)
    yield session
    session.rollback()
    session.close()


def _action_context() -> ActionContext:
    return ActionContext(
        actor="test_auditor",
        context="wave_e2_audit",
        reason="Testing evidence chain audit",
        idempotency_key=new_id("idem"),
    )


# ── Chain builder ─────────────────────────────────────────────────────


def build_evidence_chain(db: Session) -> dict:
    """Construct a minimal complete evidence chain.

    Returns a dict with IDs of all created objects for verification.
    """
    ctx = _action_context()

    # 1. DecisionIntake — use repository directly
    intake_repo = DecisionIntakeRepository(db)
    intake = DecisionIntake(
        id=new_id("intake"),
        pack_id="finance",
        intake_type="trading_decision",
        payload={
            "symbol": "BTCUSDT",
            "timeframe": "1h",
            "direction": "long",
            "thesis": "Audit test thesis with volume confirmation criteria.",
            "stop_loss": "2%",
            "max_loss_usdt": 200,
            "position_size_usdt": 1000,
            "risk_unit_usdt": 200,
            "is_revenge_trade": False,
            "is_chasing": False,
            "emotional_state": "calm",
            "confidence": 0.7,
        },
        status="validated",
    )
    intake_repo.create(intake)

    # 2. Governance: validate_intake
    engine = RiskEngine()
    decision = engine.validate_intake(intake, pack_policy=TradingDisciplinePolicy())
    assert decision.decision == "execute", f"Expected execute, got {decision.decision}: {decision.reasons}"

    # 3. Plan receipt — use service
    exec_repo = ExecutionRecordRepository(db)
    exec_svc = ExecutionRecordService(exec_repo)
    plan_req = exec_svc.start_request(
        action_id="finance_decision_plan",
        action_context=ctx,
        payload={"decision_intake_id": intake.id},
        entity_type="decision_intake",
        entity_id=intake.id,
    )
    receipt_row = exec_svc.record_success(
        plan_req.id,
        result_ref=plan_req.id,
        detail={
            "broker_execution": False,
            "side_effect_level": "none",
            "receipt_kind": "plan",
            "decision_intake_id": intake.id,
        },
    )

    # 4. FinanceManualOutcome
    outcome_repo = FinanceManualOutcomeRepository(db)
    outcome = FinanceManualOutcome(
        id=new_id("fmout"),
        decision_intake_id=intake.id,
        execution_receipt_id=receipt_row.id,
        observed_outcome="Price reached +4%",
        verdict="validated",
        plan_followed=True,
    )
    outcome_row = outcome_repo.create(outcome)

    # 5. Review (submit)
    review_repo = ReviewRepository(db)
    lesson_repo = LessonRepository(db)
    lesson_svc = LessonService(lesson_repo)
    review_svc = ReviewService(review_repo, lesson_svc)
    review = Review(
        id=new_id("review"),
        review_type="recommendation_postmortem",
        expected_outcome="Trade follows plan",
        observed_outcome="Price reached +4%",
        outcome_ref_type="finance_manual_outcome",
        outcome_ref_id=outcome_row.id,
    )
    review_row = review_svc.create(review)

    # 6. Complete review with a rule_candidate lesson
    review_row2, lesson_rows, _kf = review_svc.complete_review(
        review_id=review_row.id,
        observed_outcome="Price reached +4%",
        verdict=ReviewVerdict.VALIDATED,
        variance_summary="Clean execution",
        cause_tags=["plan_followed"],
        lessons=["Always trust the plan targets."],
        followup_actions=[],
        lesson_types=["rule_candidate"],
    )

    db.flush()

    return {
        "intake_id": intake.id,
        "receipt_id": receipt_row.id,
        "outcome_id": outcome_row.id,
        "review_id": review_row.id,
        "lesson_id": lesson_rows[0].id if lesson_rows else None,
    }


# ═══════════════════════════════════════════════════════════════════════
# Test 1: Valid chain audit passes
# ═══════════════════════════════════════════════════════════════════════


def test_valid_chain_audit_passes(db):
    """A complete, valid evidence chain must pass all audit checks."""
    build_evidence_chain(db)
    db.commit()

    result = audit_evidence_chain(db)
    assert result.passed, f"Audit failed: {result.violations}"
    assert result.checks_run == 8
    assert result.objects_scanned.get("execution_receipts", 0) >= 1
    assert result.objects_scanned.get("finance_manual_outcomes", 0) >= 1
    assert result.objects_scanned.get("reviews", 0) >= 1


# ═══════════════════════════════════════════════════════════════════════
# Test 2: Broken receipt reference detected
# ═══════════════════════════════════════════════════════════════════════


def test_broken_receipt_reference_detected(db):
    """FinanceManualOutcome pointing to non-existent receipt must be flagged."""
    outcome_repo = FinanceManualOutcomeRepository(db)
    outcome = FinanceManualOutcome(
        id=new_id("fmout"),
        decision_intake_id="intake_ghost",
        execution_receipt_id="exrcpt_does_not_exist",
        observed_outcome="Ghost trade",
        verdict="invalidated",
    )
    outcome_repo.create(outcome)
    db.commit()

    result = audit_evidence_chain(db)
    assert not result.passed
    assert any("execution_receipt_id" in v and "not found" in v for v in result.violations)


# ═══════════════════════════════════════════════════════════════════════
# Test 3: Broken outcome_ref detected
# ═══════════════════════════════════════════════════════════════════════


def test_broken_outcome_ref_detected(db):
    """Review pointing to non-existent outcome must be flagged."""
    review_repo = ReviewRepository(db)
    lesson_repo = LessonRepository(db)
    lesson_svc = LessonService(lesson_repo)
    review_svc = ReviewService(review_repo, lesson_svc)
    review = Review(
        id=new_id("review"),
        review_type="recommendation_postmortem",
        expected_outcome="Test",
        outcome_ref_type="finance_manual_outcome",
        outcome_ref_id="fmout_ghost",
    )
    review_svc.create(review)
    db.commit()

    result = audit_evidence_chain(db)
    assert not result.passed
    assert any("outcome_ref_id" in v and "not found" in v for v in result.violations)


# ═══════════════════════════════════════════════════════════════════════
# Test 4: CandidateRule without source_refs detected
# ═══════════════════════════════════════════════════════════════════════


def test_candidate_rule_without_source_refs_detected(db):
    """CandidateRule draft with empty lesson_ids/source_refs must be flagged."""
    from domains.candidate_rules.models import CandidateRule

    repo = CandidateRuleRepository(db)
    draft = CandidateRule(
        id=new_id("crule"),
        issue_key="test_no_refs",
        summary="Draft without source refs",
        status="draft",
        lesson_ids=(),
        source_refs=(),
    )
    repo.create(draft)
    db.commit()

    result = audit_evidence_chain(db)
    assert not result.passed
    assert any("lesson_ids is empty" in v or "source_refs is empty" in v for v in result.violations)


# ═══════════════════════════════════════════════════════════════════════
# Test 5: Audit is read-only
# ═══════════════════════════════════════════════════════════════════════


def test_audit_is_read_only(db):
    """Audit must not modify the database."""
    build_evidence_chain(db)
    db.commit()

    # Count objects before audit
    before_receipts = db.query(ExecutionReceiptORM).count()
    before_outcomes = db.query(FinanceManualOutcomeORM).count()
    before_reviews = db.query(ReviewORM).count()

    # Run audit
    audit_evidence_chain(db)

    # Count objects after audit — must be identical
    after_receipts = db.query(ExecutionReceiptORM).count()
    after_outcomes = db.query(FinanceManualOutcomeORM).count()
    after_reviews = db.query(ReviewORM).count()

    assert before_receipts == after_receipts
    assert before_outcomes == after_outcomes
    assert before_reviews == after_reviews


# ═══════════════════════════════════════════════════════════════════════
# Test 6: No broker/order/trade in audit module
# ═══════════════════════════════════════════════════════════════════════


def test_audit_module_no_broker_imports():
    """The audit script must not import broker/order/trade modules."""
    import inspect
    from scripts import audit_runtime_evidence_db as mod

    src = inspect.getsource(mod)
    import_lines = [l for l in src.splitlines() if l.strip().startswith(("from ", "import "))]
    forbidden = ["broker", "place_order", "execute_trade"]
    for word in forbidden:
        assert word not in "\n".join(import_lines), f"Forbidden import: {word}"
