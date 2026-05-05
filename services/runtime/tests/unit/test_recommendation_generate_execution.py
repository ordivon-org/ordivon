from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from capabilities.boundary import ActionContext
from domains.execution_records.orm import ExecutionReceiptORM, ExecutionRequestORM
from domains.research.models import AnalysisRequest, AnalysisResult
from domains.strategy.orm import RecommendationORM
from governance_engine.risk_engine.engine import GovernanceDecision
from orchestrator.contracts.workflow import WorkflowContext
from orchestrator.workflows.analyze import GenerateRecommendationStep
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


def _make_context(db):
    ctx = WorkflowContext(
        request=AnalysisRequest(query="Analyze BTC", symbol="BTC/USDT", timeframe="1h"),
        db=db,
    )
    ctx.analysis_id = "analysis_test_123"
    ctx.analysis = AnalysisResult(
        id="analysis_test_123",
        query="Analyze BTC",
        symbol="BTC/USDT",
        summary="summary",
        thesis="thesis",
    )
    ctx.governance = GovernanceDecision(
        decision="execute",
        reasons=["Passed default Step 1 governance validation."],
        source="risk_engine.default_validation",
    )
    ctx.metadata["side_effect_contexts"] = {
        "generate_recommendation": ActionContext(
            actor="workflow.analyze",
            context="generate_recommendation_step",
            reason="generate recommendation for BTC/USDT",
            idempotency_key="recommendation:Analyze BTC:BTC/USDT",
        )
    }
    return ctx


def test_generate_recommendation_creates_request_receipt_and_row():
    engine, TestingSessionLocal = _make_db()
    db = TestingSessionLocal()
    try:
        step = GenerateRecommendationStep()
        ctx = _make_context(db)

        updated = step.execute(ctx)

        assert updated.recommendation_id is not None
        assert updated.metadata["recommendation_generate_request_id"].startswith("exreq_")
        assert updated.metadata["recommendation_generate_receipt_id"].startswith("exrcpt_")

        request_row = db.query(ExecutionRequestORM).one()
        receipt_row = db.query(ExecutionReceiptORM).one()
        recommendation_row = db.query(RecommendationORM).one()

        assert request_row.action_id == "recommendation_generate"
        assert request_row.status == "succeeded"
        assert request_row.analysis_id == "analysis_test_123"
        assert request_row.recommendation_id == recommendation_row.id
        assert request_row.entity_type == "recommendation"
        assert request_row.entity_id == recommendation_row.id

        assert receipt_row.request_id == request_row.id
        assert receipt_row.status == "succeeded"
        assert receipt_row.result_ref == recommendation_row.id
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


def test_generate_recommendation_records_failed_receipt_when_creation_fails(monkeypatch):
    engine, TestingSessionLocal = _make_db()
    db = TestingSessionLocal()
    try:
        step = GenerateRecommendationStep()
        ctx = _make_context(db)

        monkeypatch.setattr(
            "orchestrator.workflows.analyze.RecommendationService.create",
            lambda self, recommendation: (_ for _ in ()).throw(Exception("recommendation create failed")),
        )

        try:
            step.execute(ctx)
            raise AssertionError("expected recommendation creation failure")
        except Exception as exc:
            assert str(exc) == "recommendation create failed"

        request_row = db.query(ExecutionRequestORM).one()
        receipt_row = db.query(ExecutionReceiptORM).one()

        assert request_row.action_id == "recommendation_generate"
        assert request_row.status == "failed"
        assert request_row.recommendation_id is None
        assert receipt_row.request_id == request_row.id
        assert receipt_row.status == "failed"
        assert receipt_row.error == "recommendation create failed"
        assert db.query(RecommendationORM).count() == 0
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)
