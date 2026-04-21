import os

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from apps.api.app.deps import get_db
from apps.api.app.main import app
from domains.journal.lesson_repository import LessonRepository
from domains.journal.lesson_service import LessonService
from domains.journal.models import Review
from domains.journal.repository import ReviewRepository
from domains.journal.service import ReviewService
from domains.research.models import AnalysisResult
from domains.research.repository import AnalysisRepository
from domains.strategy.models import Recommendation
from domains.strategy.orm import RecommendationORM
from domains.strategy.outcome_repository import OutcomeRepository
from domains.strategy.outcome_service import OutcomeService
from domains.strategy.repository import RecommendationRepository
from domains.strategy.service import RecommendationService
from shared.enums.domain import ReviewStatus, ReviewVerdict
from shared.config.settings import settings
from state.db.base import Base


def _make_client_db():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)
    return engine, TestingSessionLocal


def test_trace_api_returns_linked_main_chain_for_workflow_run(monkeypatch):
    engine, TestingSessionLocal = _make_client_db()

    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    original_provider = settings.reasoning_provider
    settings.reasoning_provider = "hermes"

    monkeypatch.setattr(
        "intelligence.runtime.hermes_client.HermesClient.run_task",
        lambda self, task_type, payload: {
            "task_id": payload["task_id"],
            "task_type": task_type,
            "idempotency_key": payload["idempotency_key"],
            "trace_id": payload["trace_id"],
            "input": payload["input"],
            "status": "completed",
            "provider": "openrouter",
            "model": "test-model",
            "session_id": "sess_123",
            "started_at": "2026-04-19T00:00:00+00:00",
            "completed_at": "2026-04-19T00:00:01+00:00",
            "output": {
                "summary": "Hermes summary",
                "thesis": "Hermes thesis",
                "risks": ["risk_a"],
                "suggested_actions": ["action_a"],
            },
            "tool_trace": [],
            "memory_events": [],
            "delegation_trace": [],
            "usage": {"total_tokens": 42},
            "error": None,
        },
    )

    client = TestClient(app)
    analyze_response = client.post(
        "/api/v1/analyze-and-suggest",
        json={"query": "Analyze BTC", "symbols": ["BTC/USDT"]},
    )

    assert analyze_response.status_code == 200
    workflow_run_id = analyze_response.json()["metadata"]["workflow_run_id"]

    db = TestingSessionLocal()
    try:
        recommendation_id = db.query(RecommendationORM).one().id
    finally:
        db.close()

    trace_response = client.get(f"/api/v1/traces/workflow-runs/{workflow_run_id}")
    recommendation_trace = client.get(f"/api/v1/traces/recommendations/{recommendation_id}")
    legacy_trace = client.get(f"/api/v1/agent-actions/trace/recommendations/{recommendation_id}")

    assert trace_response.status_code == 200
    payload = trace_response.json()
    assert payload["root_type"] == "workflow_run"
    assert payload["workflow_run"]["object_id"] == workflow_run_id
    assert payload["analysis"]["status"] == "present"
    assert payload["recommendation"]["status"] == "present"
    assert payload["intelligence_run"]["status"] == "present"
    assert payload["agent_action"]["status"] == "present"
    assert payload["execution_request"]["status"] == "present"
    assert payload["execution_receipt"]["status"] == "present"
    assert payload["report_artifact"]["status"] == "present"
    assert payload["latest_audit_events"]

    assert recommendation_trace.status_code == 200
    recommendation_payload = recommendation_trace.json()
    assert recommendation_payload["root_type"] == "recommendation"
    assert recommendation_payload["recommendation"]["object_id"] == recommendation_id
    assert recommendation_payload["workflow_run"]["status"] == "present"
    assert recommendation_payload["analysis"]["status"] == "present"

    assert legacy_trace.status_code == 200
    legacy_payload = legacy_trace.json()
    assert legacy_payload["recommendation_id"] == recommendation_id
    assert legacy_payload["analysis_id"] == recommendation_payload["analysis"]["object_id"]
    assert legacy_payload["agent_action_id"] == recommendation_payload["agent_action"]["object_id"]
    assert legacy_payload["report_path"] == recommendation_payload["report_artifact"]["detail"]["path"]
    assert legacy_payload["audit_event_ids"]

    settings.reasoning_provider = original_provider
    app.dependency_overrides.clear()

    if os.path.exists("wiki"):
        import shutil

        shutil.rmtree("wiki")

    Base.metadata.drop_all(bind=engine)


def test_trace_api_does_not_fabricate_missing_metadata_relations():
    engine, TestingSessionLocal = _make_client_db()

    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db

    db = TestingSessionLocal()
    try:
        AnalysisRepository(db).create(
            AnalysisResult(
                id="analysis_trace_missing",
                query="Analyze SOL",
                symbol="SOL/USDT",
                metadata={
                    "agent_action_id": "act_missing_trace",
                    "document_path": "wiki/reports/analysis_trace_missing.md",
                },
            )
        )
        RecommendationRepository(db).create(
            Recommendation(
                id="reco_trace_missing",
                analysis_id="analysis_trace_missing",
                title="Review SOL",
                summary="Review SOL setup",
            )
        )
        db.commit()
    finally:
        db.close()

    client = TestClient(app)
    response = client.get("/api/v1/traces/recommendations/reco_trace_missing")

    app.dependency_overrides.clear()

    assert response.status_code == 200
    payload = response.json()
    assert payload["agent_action"]["object_id"] == "act_missing_trace"
    assert payload["agent_action"]["status"] == "missing"
    assert payload["agent_action"]["relation_source"] == "analysis.metadata"
    assert payload["workflow_run"]["status"] == "unlinked"
    assert payload["report_artifact"]["status"] == "present"
    assert payload["report_artifact"]["relation_source"] == "analysis.metadata"

    Base.metadata.drop_all(bind=engine)


def test_trace_api_returns_outcome_after_review_backfill():
    engine, TestingSessionLocal = _make_client_db()

    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db

    db = TestingSessionLocal()
    try:
        AnalysisRepository(db).create(
            AnalysisResult(
                id="analysis_trace_outcome",
                query="Analyze BTC",
                symbol="BTC/USDT",
            )
        )
        RecommendationRepository(db).create(
            Recommendation(
                id="reco_trace_outcome",
                analysis_id="analysis_trace_outcome",
                title="Track BTC thesis",
                summary="Track BTC setup",
            )
        )
        review_service = ReviewService(
            ReviewRepository(db),
            LessonService(LessonRepository(db)),
            outcome_service=OutcomeService(OutcomeRepository(db)),
            recommendation_service=RecommendationService(RecommendationRepository(db)),
        )
        review = Review(
            recommendation_id="reco_trace_outcome",
            review_type="recommendation_postmortem",
            status=ReviewStatus.PENDING,
            expected_outcome="BTC breakout",
        )
        row = review_service.create(review)
        review_service.complete_review(
            review_id=row.id,
            observed_outcome="BTC breakout failed",
            verdict=ReviewVerdict.INVALIDATED,
            variance_summary="Breakout lost momentum",
            cause_tags=["momentum"],
            lessons=["Wait for confirmation"],
            followup_actions=["Tighten invalidation"],
        )
        db.commit()
    finally:
        db.close()

    client = TestClient(app)
    response = client.get("/api/v1/traces/recommendations/reco_trace_outcome")
    app.dependency_overrides.clear()

    assert response.status_code == 200
    payload = response.json()
    assert payload["outcome"]["status"] == "present"
    assert payload["outcome"]["relation_source"] == "recommendation.latest_outcome_snapshot_id"
    assert payload["review"]["status"] == "present"
    assert payload["review_execution_request"]["status"] == "unlinked"
    assert payload["review_execution_receipt"]["status"] == "unlinked"
    assert payload["knowledge_feedback"]["status"] == "present"
    assert payload["knowledge_feedback"]["relation_source"] == "review.knowledge_feedback_packet_id"

    Base.metadata.drop_all(bind=engine)


def test_trace_api_returns_review_root_with_review_execution_chain():
    engine, TestingSessionLocal = _make_client_db()

    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db

    db = TestingSessionLocal()
    try:
        AnalysisRepository(db).create(
            AnalysisResult(
                id="analysis_review_trace_api",
                query="Analyze BTC",
                symbol="BTC/USDT",
            )
        )
        RecommendationRepository(db).create(
            Recommendation(
                id="reco_review_trace_api",
                analysis_id="analysis_review_trace_api",
                title="Track BTC",
                summary="Track BTC thesis",
            )
        )
        db.commit()
    finally:
        db.close()

    client = TestClient(app)
    submit_response = client.post(
        "/api/v1/reviews/submit",
        json={
            "linked_recommendation_id": "reco_review_trace_api",
            "expected_outcome": "Trend holds",
            "actual_outcome": "Trend failed",
            "deviation": "Late entry",
            "mistake_tags": "timing",
            "lessons": [{"lesson_text": "Use confirmation"}],
            "new_rule_candidate": "Wait for pullback",
        },
    )

    assert submit_response.status_code == 200
    review_id = submit_response.json()["id"]

    complete_response = client.post(
        f"/api/v1/reviews/{review_id}/complete",
        json={
            "observed_outcome": "Loss contained",
            "verdict": "invalidated",
            "variance_summary": "Setup failed quickly",
            "cause_tags": ["timing"],
            "lessons": ["Use confirmation candle"],
            "followup_actions": ["Update checklist"],
        },
    )

    assert complete_response.status_code == 200
    metadata = complete_response.json()["metadata"]
    trace_response = client.get(f"/api/v1/traces/reviews/{review_id}")
    recommendation_trace = client.get("/api/v1/traces/recommendations/reco_review_trace_api")

    app.dependency_overrides.clear()

    assert trace_response.status_code == 200
    payload = trace_response.json()
    assert payload["root_type"] == "review"
    assert payload["review"]["object_id"] == review_id
    assert payload["recommendation"]["object_id"] == "reco_review_trace_api"
    assert payload["review_execution_request"]["object_id"] == metadata["execution_request_id"]
    assert payload["review_execution_request"]["relation_source"] == "review.complete_execution_request_id"
    assert payload["review_execution_request"]["status"] == "present"
    assert payload["review_execution_receipt"]["object_id"] == metadata["execution_receipt_id"]
    assert payload["review_execution_receipt"]["relation_source"] == "review.complete_execution_receipt_id"
    assert payload["review_execution_receipt"]["status"] == "present"
    assert payload["outcome"]["status"] == "present"
    assert payload["knowledge_feedback"]["status"] == "present"
    assert payload["knowledge_feedback"]["relation_source"] == "review.knowledge_feedback_packet_id"
    assert payload["latest_audit_events"]

    assert recommendation_trace.status_code == 200
    recommendation_payload = recommendation_trace.json()
    assert recommendation_payload["review"]["object_id"] == review_id
    assert recommendation_payload["review_execution_request"]["object_id"] == metadata["execution_request_id"]
    assert recommendation_payload["review_execution_receipt"]["object_id"] == metadata["execution_receipt_id"]
    assert recommendation_payload["knowledge_feedback"]["status"] == "present"

    Base.metadata.drop_all(bind=engine)
