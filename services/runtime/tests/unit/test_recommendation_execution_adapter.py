from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from capabilities.boundary import ActionContext
from domains.execution_records.orm import ExecutionReceiptORM, ExecutionRequestORM
from domains.strategy.models import Recommendation
from domains.strategy.repository import RecommendationRepository
from domains.strategy.service import RecommendationService
from execution.adapters import RecommendationExecutionAdapter, RecommendationExecutionFailure
from governance.audit.orm import AuditEventORM
from shared.enums.domain import RecommendationStatus
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


def test_recommendation_status_update_adapter_writes_success_request_and_receipt():
    engine, TestingSessionLocal = _make_db()
    db = TestingSessionLocal()
    try:
        RecommendationRepository(db).create(
            Recommendation(
                id="reco_exec_ok",
                analysis_id="ana_1",
                title="Track BTC",
                summary="Track BTC setup",
                status=RecommendationStatus.GENERATED,
            )
        )
        service = RecommendationService(RecommendationRepository(db), None)
        adapter = RecommendationExecutionAdapter(db)

        result = adapter.update_status(
            service=service,
            recommendation_id="reco_exec_ok",
            target_status=RecommendationStatus.ADOPTED,
            action_context=ActionContext(
                actor="test-suite",
                context="recommendation_status_test",
                reason="advance recommendation to adopted",
                idempotency_key="reco_exec_ok:adopted",
            ),
        )

        request_row = db.query(ExecutionRequestORM).one()
        receipt_row = db.query(ExecutionReceiptORM).one()
        recommendation_row = RecommendationRepository(db).get("reco_exec_ok")

        assert result.execution_request_id == request_row.id
        assert result.execution_receipt_id == receipt_row.id
        assert request_row.action_id == "recommendation_status_update"
        assert request_row.status == "succeeded"
        assert receipt_row.status == "succeeded"
        assert receipt_row.result_ref == "reco_exec_ok"
        assert recommendation_row is not None
        assert recommendation_row.status == RecommendationStatus.ADOPTED.value
        success_audits = (
            db.query(AuditEventORM).filter(AuditEventORM.event_type == "recommendation_status_update").all()
        )
        assert len(success_audits) == 1
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


def test_recommendation_transition_can_suppress_success_audit():
    engine, TestingSessionLocal = _make_db()
    db = TestingSessionLocal()
    try:
        RecommendationRepository(db).create(
            Recommendation(
                id="reco_exec_suppress",
                analysis_id="ana_1",
                title="Track BTC",
                summary="Track BTC setup",
                status=RecommendationStatus.GENERATED,
            )
        )
        service = RecommendationService(RecommendationRepository(db))

        recommendation = service.transition(
            recommendation_id="reco_exec_suppress",
            target_status=RecommendationStatus.ADOPTED,
            emit_recommendation_status_audit=False,
        )

        success_audits = (
            db.query(AuditEventORM).filter(AuditEventORM.event_type == "recommendation_status_update").all()
        )
        assert recommendation.status == RecommendationStatus.ADOPTED
        assert len(success_audits) == 0
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


def test_recommendation_status_update_adapter_writes_failed_receipt_without_success_transition():
    engine, TestingSessionLocal = _make_db()
    db = TestingSessionLocal()
    try:
        RecommendationRepository(db).create(
            Recommendation(
                id="reco_exec_fail",
                analysis_id="ana_1",
                title="Track BTC",
                summary="Track BTC setup",
                status=RecommendationStatus.GENERATED,
            )
        )
        service = RecommendationService(RecommendationRepository(db), None)
        adapter = RecommendationExecutionAdapter(db)

        try:
            adapter.update_status(
                service=service,
                recommendation_id="reco_exec_fail",
                target_status=RecommendationStatus.REVIEWED,
                action_context=ActionContext(
                    actor="test-suite",
                    context="recommendation_status_test",
                    reason="force invalid transition",
                    idempotency_key="reco_exec_fail:reviewed",
                ),
            )
        except RecommendationExecutionFailure as exc:
            assert exc.status_code == 409
        else:
            raise AssertionError("Expected RecommendationExecutionFailure")

        request_row = db.query(ExecutionRequestORM).one()
        receipt_row = db.query(ExecutionReceiptORM).one()
        recommendation_row = RecommendationRepository(db).get("reco_exec_fail")

        assert request_row.status == "failed"
        assert receipt_row.status == "failed"
        assert recommendation_row is not None
        assert recommendation_row.status == RecommendationStatus.GENERATED.value
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)
