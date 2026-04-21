from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from capabilities.boundary import ActionContext
from domains.execution_records.orm import ExecutionReceiptORM, ExecutionRequestORM
from domains.journal.lesson_repository import LessonRepository
from domains.journal.lesson_service import LessonService
from domains.journal.models import Review
from domains.journal.repository import ReviewRepository
from domains.journal.service import ReviewService
from domains.strategy.models import Recommendation
from domains.strategy.outcome_repository import OutcomeRepository
from domains.strategy.outcome_service import OutcomeService
from domains.strategy.repository import RecommendationRepository
from domains.strategy.service import RecommendationService
from execution.adapters import ReviewExecutionAdapter, ReviewExecutionFailure
from shared.enums.domain import ReviewStatus, ReviewVerdict
from state.db.base import Base


def _make_db():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)
    return engine, TestingSessionLocal


def test_review_complete_adapter_writes_success_request_and_receipt():
    engine, TestingSessionLocal = _make_db()
    db = TestingSessionLocal()
    try:
        recommendation_repo = RecommendationRepository(db)
        recommendation_repo.create(
            Recommendation(
                id="reco_review_exec_ok",
                analysis_id="analysis_ok",
                title="Trend setup",
                summary="summary",
            )
        )
        review_service = ReviewService(
            ReviewRepository(db),
            LessonService(LessonRepository(db)),
            outcome_service=OutcomeService(OutcomeRepository(db)),
            recommendation_service=RecommendationService(recommendation_repo),
        )
        review_row = review_service.create(
            Review(
                id="review_exec_ok",
                recommendation_id="reco_review_exec_ok",
                status=ReviewStatus.PENDING,
                expected_outcome="Trend holds",
            )
        )
        adapter = ReviewExecutionAdapter(db)

        result = adapter.complete(
            service=review_service,
            review_id=review_row.id,
            observed_outcome="Loss contained",
            verdict=ReviewVerdict.INVALIDATED,
            variance_summary="Setup failed quickly",
            cause_tags=["timing"],
            lessons=["Use confirmation candle"],
            followup_actions=["Update checklist"],
            action_context=ActionContext(
                actor="test-suite",
                context="review_complete_test",
                reason="complete review execution path",
                idempotency_key="review_exec_ok:complete",
            ),
        )

        request_row = db.query(ExecutionRequestORM).one()
        receipt_row = db.query(ExecutionReceiptORM).one()
        persisted_review = ReviewRepository(db).get("review_exec_ok")

        assert result.execution_request_id == request_row.id
        assert result.execution_receipt_id == receipt_row.id
        assert request_row.action_id == "review_complete"
        assert request_row.status == "succeeded"
        assert request_row.entity_type == "review"
        assert request_row.entity_id == "review_exec_ok"
        assert receipt_row.status == "succeeded"
        assert receipt_row.result_ref == "review_exec_ok"
        assert persisted_review is not None
        assert persisted_review.status == ReviewStatus.COMPLETED.value
        assert persisted_review.complete_execution_request_id == request_row.id
        assert persisted_review.complete_execution_receipt_id == receipt_row.id
        assert persisted_review.knowledge_feedback_packet_id is not None
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


def test_review_submit_adapter_writes_success_request_and_receipt():
    engine, TestingSessionLocal = _make_db()
    db = TestingSessionLocal()
    try:
        review_service = ReviewService(
            ReviewRepository(db),
            LessonService(LessonRepository(db)),
        )
        adapter = ReviewExecutionAdapter(db)
        review = Review(
            id="review_submit_exec_ok",
            recommendation_id="reco_submit_exec_ok",
            status=ReviewStatus.PENDING,
            expected_outcome="Trend holds",
        )

        result = adapter.submit(
            service=review_service,
            review=review,
            action_context=ActionContext(
                actor="test-suite",
                context="review_submit_test",
                reason="submit review execution path",
                idempotency_key="review_submit_exec_ok:submit",
            ),
        )

        request_row = db.query(ExecutionRequestORM).one()
        receipt_row = db.query(ExecutionReceiptORM).one()
        persisted_review = ReviewRepository(db).get("review_submit_exec_ok")

        assert result.execution_request_id == request_row.id
        assert result.execution_receipt_id == receipt_row.id
        assert request_row.action_id == "review_submit"
        assert request_row.status == "succeeded"
        assert request_row.entity_type == "review"
        assert request_row.entity_id == "review_submit_exec_ok"
        assert receipt_row.status == "succeeded"
        assert receipt_row.result_ref == "review_submit_exec_ok"
        assert persisted_review is not None
        assert persisted_review.status == ReviewStatus.PENDING.value
        assert persisted_review.submit_execution_request_id == request_row.id
        assert persisted_review.submit_execution_receipt_id == receipt_row.id
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


def test_review_submit_adapter_writes_failed_receipt_without_success_row():
    engine, TestingSessionLocal = _make_db()
    db = TestingSessionLocal()
    try:
        review_service = ReviewService(
            ReviewRepository(db),
            LessonService(LessonRepository(db)),
        )
        adapter = ReviewExecutionAdapter(db)

        original_create = review_service.create_with_options

        def _boom(*args, **kwargs):
            raise RuntimeError("submit exploded")

        review_service.create_with_options = _boom  # type: ignore[assignment]
        try:
            adapter.submit(
                service=review_service,
                review=Review(
                    id="review_submit_exec_fail",
                    recommendation_id="reco_submit_exec_fail",
                    status=ReviewStatus.PENDING,
                    expected_outcome="Trend holds",
                ),
                action_context=ActionContext(
                    actor="test-suite",
                    context="review_submit_test",
                    reason="force review submit failure",
                    idempotency_key="review_submit_exec_fail:submit",
                ),
            )
        except ReviewExecutionFailure as exc:
            assert exc.status_code == 500
        else:
            raise AssertionError("Expected ReviewExecutionFailure")
        finally:
            review_service.create_with_options = original_create  # type: ignore[assignment]

        request_row = db.query(ExecutionRequestORM).one()
        receipt_row = db.query(ExecutionReceiptORM).one()
        persisted_review = ReviewRepository(db).get("review_submit_exec_fail")

        assert request_row.status == "failed"
        assert receipt_row.status == "failed"
        assert persisted_review is None
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


def test_review_complete_adapter_writes_failed_receipt_without_success_transition():
    engine, TestingSessionLocal = _make_db()
    db = TestingSessionLocal()
    try:
        recommendation_repo = RecommendationRepository(db)
        recommendation_repo.create(
            Recommendation(
                id="reco_review_exec_fail",
                analysis_id="analysis_fail",
                title="Trend setup",
                summary="summary",
            )
        )
        review_service = ReviewService(
            ReviewRepository(db),
            LessonService(LessonRepository(db)),
            outcome_service=OutcomeService(OutcomeRepository(db)),
            recommendation_service=RecommendationService(recommendation_repo),
        )
        review_service.create(
            Review(
                id="review_exec_fail",
                recommendation_id="reco_review_exec_fail",
                status=ReviewStatus.COMPLETED,
                expected_outcome="Trend holds",
            )
        )
        adapter = ReviewExecutionAdapter(db)

        try:
            adapter.complete(
                service=review_service,
                review_id="review_exec_fail",
                observed_outcome="Still bad",
                verdict=ReviewVerdict.INVALIDATED,
                variance_summary="Already completed",
                cause_tags=["timing"],
                lessons=["Do not reopen implicitly"],
                followup_actions=["Keep review immutable"],
                action_context=ActionContext(
                    actor="test-suite",
                    context="review_complete_test",
                    reason="force invalid review completion",
                    idempotency_key="review_exec_fail:complete",
                ),
            )
        except ReviewExecutionFailure as exc:
            assert exc.status_code == 409
        else:
            raise AssertionError("Expected ReviewExecutionFailure")

        request_row = db.query(ExecutionRequestORM).one()
        receipt_row = db.query(ExecutionReceiptORM).one()
        persisted_review = ReviewRepository(db).get("review_exec_fail")

        assert request_row.status == "failed"
        assert receipt_row.status == "failed"
        assert persisted_review is not None
        assert persisted_review.status == ReviewStatus.COMPLETED.value
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


def test_review_submit_adapter_avoids_begin_nested_for_duckdb_compatibility(monkeypatch):
    engine, TestingSessionLocal = _make_db()
    db = TestingSessionLocal()
    try:
        review_service = ReviewService(
            ReviewRepository(db),
            LessonService(LessonRepository(db)),
        )
        adapter = ReviewExecutionAdapter(db)

        def _no_nested_transactions():
            raise AssertionError("begin_nested should not be called in review submit adapter")

        monkeypatch.setattr(db, "begin_nested", _no_nested_transactions)

        result = adapter.submit(
            service=review_service,
            review=Review(
                id="review_submit_no_nested",
                recommendation_id="reco_submit_no_nested",
                status=ReviewStatus.PENDING,
                expected_outcome="Trend holds",
            ),
            action_context=ActionContext(
                actor="test-suite",
                context="review_submit_test",
                reason="assert duckdb compatibility without savepoints",
                idempotency_key="review_submit_no_nested:submit",
            ),
        )

        persisted_review = ReviewRepository(db).get("review_submit_no_nested")
        assert result.execution_request_id
        assert result.execution_receipt_id
        assert persisted_review is not None
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


def test_review_complete_adapter_avoids_begin_nested_for_duckdb_compatibility(monkeypatch):
    engine, TestingSessionLocal = _make_db()
    db = TestingSessionLocal()
    try:
        recommendation_repo = RecommendationRepository(db)
        recommendation_repo.create(
            Recommendation(
                id="reco_complete_no_nested",
                analysis_id="analysis_no_nested",
                title="Trend setup",
                summary="summary",
            )
        )
        review_service = ReviewService(
            ReviewRepository(db),
            LessonService(LessonRepository(db)),
            outcome_service=OutcomeService(OutcomeRepository(db)),
            recommendation_service=RecommendationService(recommendation_repo),
        )
        review_service.create(
            Review(
                id="review_complete_no_nested",
                recommendation_id="reco_complete_no_nested",
                status=ReviewStatus.PENDING,
                expected_outcome="Trend holds",
            )
        )
        adapter = ReviewExecutionAdapter(db)

        def _no_nested_transactions():
            raise AssertionError("begin_nested should not be called in review complete adapter")

        monkeypatch.setattr(db, "begin_nested", _no_nested_transactions)

        result = adapter.complete(
            service=review_service,
            review_id="review_complete_no_nested",
            observed_outcome="Loss contained",
            verdict=ReviewVerdict.INVALIDATED,
            variance_summary="Setup failed quickly",
            cause_tags=["timing"],
            lessons=["Use confirmation candle"],
            followup_actions=["Update checklist"],
            action_context=ActionContext(
                actor="test-suite",
                context="review_complete_test",
                reason="assert duckdb compatibility without savepoints",
                idempotency_key="review_complete_no_nested:complete",
            ),
        )

        persisted_review = ReviewRepository(db).get("review_complete_no_nested")
        assert result.execution_request_id
        assert result.execution_receipt_id
        assert persisted_review is not None
        assert persisted_review.complete_execution_request_id == result.execution_request_id
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)
