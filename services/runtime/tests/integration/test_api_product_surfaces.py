from contextlib import contextmanager

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
from domains.execution_records.models import ExecutionReceipt, ExecutionRequest
from domains.execution_records.repository import ExecutionRecordRepository
from domains.research.models import AnalysisResult
from domains.research.repository import AnalysisRepository
from domains.strategy.models import Recommendation
from domains.strategy.outcome_repository import OutcomeRepository
from domains.strategy.outcome_service import OutcomeService
from domains.strategy.repository import RecommendationRepository
from domains.strategy.service import RecommendationService
from domains.workflow_runs.models import WorkflowRun
from domains.workflow_runs.repository import WorkflowRunRepository
from governance.audit.models import AuditEvent
from governance.audit.repository import AuditEventRepository
from shared.enums.domain import ReviewStatus, ReviewVerdict
from state.db.base import Base

@contextmanager
def _app_client():
    with TestClient(app) as client:
        yield client


def test_dashboard_summary_surface_exposes_real_sparse_fields():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)

    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    local_client = TestClient(app)
    response = local_client.get("/api/v1/dashboard/summary")
    app.dependency_overrides.clear()
    Base.metadata.drop_all(bind=engine)

    assert response.status_code == 200

    payload = response.json()
    assert set(payload.keys()) == {
        "recommendation_stats",
        "recent_outcomes",
        "pending_review_count",
        "system_health",
        "reasoning_provider",
        "hermes_status",
        "last_agent_action",
        "total_balance_estimate",
    }
    assert isinstance(payload["recommendation_stats"], dict)
    assert isinstance(payload["recent_outcomes"], list)
    assert isinstance(payload["pending_review_count"], int)
    assert payload["system_health"] is None or isinstance(payload["system_health"], str)
    assert payload["reasoning_provider"] is None or isinstance(payload["reasoning_provider"], str)
    assert payload["hermes_status"] is None or isinstance(payload["hermes_status"], str)
    assert payload["last_agent_action"] is None or isinstance(payload["last_agent_action"], dict)
    assert payload["total_balance_estimate"] is None or isinstance(payload["total_balance_estimate"], (int, float))

    for outcome in payload["recent_outcomes"]:
        assert set(outcome.keys()) == {"state", "reason", "symbol", "timestamp"}


def test_health_surface_exposes_monitoring_snapshot_fields():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)

    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db

    db = TestingSessionLocal()
    try:
        WorkflowRunRepository(db).create(
            WorkflowRun(
                id="wfrun_health_surface_1",
                workflow_name="analyze",
                status="failed",
                request_summary="Analyze BTC",
            )
        )
        execution_repo = ExecutionRecordRepository(db)
        execution_repo.create_request(
            ExecutionRequest(
                id="exreq_health_surface_1",
                action_id="validation_issue_report",
                family="validation",
                side_effect_level="state_mutation",
                status="failed",
                actor="test",
                context="health_surface",
                reason="test",
                idempotency_key="health-surface-1",
            )
        )
        execution_repo.create_receipt(
            ExecutionReceipt(
                id="exrcpt_health_surface_1",
                request_id="exreq_health_surface_1",
                action_id="validation_issue_report",
                status="failed",
                error="failed",
            )
        )
        AuditEventRepository(db).create(
            AuditEvent(
                id="audit_health_surface_1",
                event_type="validation_issue_report_failed",
                entity_type="issue",
                entity_id="issue_health_surface_1",
                payload={"detail": "failed"},
            )
        )
        db.commit()
    finally:
        db.close()

    local_client = TestClient(app)
    response = local_client.get("/api/v1/health")

    app.dependency_overrides.clear()
    Base.metadata.drop_all(bind=engine)

    assert response.status_code == 200
    payload = response.json()
    assert payload["monitoring_status"] == "attention"
    assert payload["recent_failed_workflow_count"] == 1
    assert payload["recent_failed_execution_count"] == 1
    assert payload["last_workflow_at"] is not None
    assert payload["last_audit_at"] is not None
    assert payload["monitoring_window_hours"] == 24
    assert payload["workflow_failures_by_type"] is not None
    assert payload["execution_failures_by_family"] is not None


def test_analyze_and_suggest_api_success_contract_is_real():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)

    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    local_client = TestClient(app)
    response = local_client.post(
        "/api/v1/analyze-and-suggest",
        json={"query": "Analyze BTC momentum", "symbols": ["BTC-USDT"]},
    )
    app.dependency_overrides.clear()
    Base.metadata.drop_all(bind=engine)
    assert response.status_code == 200

    payload = response.json()
    assert payload["status"] == "success"
    assert payload["workflow"] == "analyze_and_suggest"
    assert payload["decision"] in {"execute", "escalate", "reject"}
    assert isinstance(payload["summary"], str)
    assert isinstance(payload["risk_flags"], list)
    assert isinstance(payload["recommendations"], list)
    assert isinstance(payload["metadata"], dict)
    assert "governance_decision" in payload["metadata"]
    assert "governance_source" in payload["metadata"]
    assert "governance_policy_set_id" in payload["metadata"]
    assert "governance_active_policy_ids" in payload["metadata"]
    assert "agent_action_id" in payload["metadata"]
    assert payload["metadata"].get("symbol") == "BTC-USDT"
    assert "thesis" not in payload
    assert "action_plan" not in payload
    assert payload["audit_event_id"] is None or isinstance(payload["audit_event_id"], str)
    assert payload["report_path"] is None or isinstance(payload["report_path"], str)


def test_audits_recent_surface_contains_real_event_fields():
    with _app_client() as client:
        response = client.get("/api/v1/audits/recent?limit=5")
    assert response.status_code == 200

    payload = response.json()
    assert set(payload.keys()) == {"status", "message", "audits"}
    assert payload["status"] == "success"
    assert isinstance(payload["audits"], list)

    for event in payload["audits"]:
        assert set(event.keys()) == {
            "event_id",
            "workflow_name",
            "stage",
            "decision",
            "subject_id",
            "status",
            "context_summary",
            "details",
            "report_path",
            "created_at",
        }
        assert isinstance(event["workflow_name"], str)
        assert isinstance(event["stage"], str)
        assert isinstance(event["decision"], str)
        assert isinstance(event["status"], str)
        assert isinstance(event["context_summary"], str)
        assert isinstance(event["details"], dict)
        assert event["report_path"] is None or isinstance(event["report_path"], str)


def test_recommendation_surface_exposes_trace_outcome_and_derived_knowledge_refs():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)

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
                id="analysis_surface_1",
                query="Analyze BTC trend",
                symbol="BTC-USDT",
                metadata={
                    "workflow_run_id": "wfrun_surface_1",
                    "intelligence_run_id": "irun_surface_1",
                    "execution_receipt_id": "exrcpt_report_surface_1",
                    "recommendation_generate_receipt_id": "exrcpt_reco_surface_1",
                },
            )
        )
        RecommendationRepository(db).create(
            Recommendation(
                id="reco_surface_1",
                analysis_id="analysis_surface_1",
                title="Track BTC breakout",
                summary="Track BTC breakout setup",
            )
        )
        review_service = ReviewService(
            ReviewRepository(db),
            LessonService(LessonRepository(db)),
            outcome_service=OutcomeService(OutcomeRepository(db)),
            recommendation_service=RecommendationService(RecommendationRepository(db)),
        )
        review = Review(
            recommendation_id="reco_surface_1",
            review_type="recommendation_postmortem",
            status=ReviewStatus.PENDING,
            expected_outcome="BTC breakout confirmation",
        )
        row = review_service.create(review)
        review_service.complete_review(
            review_id=row.id,
            observed_outcome="BTC breakout failed",
            verdict=ReviewVerdict.INVALIDATED,
            variance_summary="Breakout rejected",
            cause_tags=["momentum"],
            lessons=["Wait for stronger confirmation"],
            followup_actions=["Tighten invalidation"],
        )
        db.commit()
    finally:
        db.close()

    local_client = TestClient(app)
    response = local_client.get("/api/v1/recommendations/recent")
    app.dependency_overrides.clear()
    Base.metadata.drop_all(bind=engine)

    assert response.status_code == 200
    payload = response.json()
    recommendation = next(item for item in payload["recommendations"] if item["id"] == "reco_surface_1")
    assert recommendation["outcome_status"] == "failed"
    assert recommendation["metadata"]["workflow_run_id"] == "wfrun_surface_1"
    assert recommendation["metadata"]["intelligence_run_id"] == "irun_surface_1"
    assert recommendation["metadata"]["execution_receipt_id"] == "exrcpt_report_surface_1"
    assert recommendation["metadata"]["recommendation_generate_receipt_id"] == "exrcpt_reco_surface_1"
    assert recommendation["metadata"]["latest_outcome_reason"] == "review_completion_backfill"
    assert recommendation["metadata"]["knowledge_hint_count"] == 1
    assert recommendation["metadata"]["knowledge_hint_status"] == "prepared"
    assert recommendation["metadata"]["knowledge_hint_summaries"] == ["Wait for stronger confirmation"]
    assert recommendation["metadata"]["governance"] is None


def test_recommendation_surface_returns_honest_missing_fields_when_not_linked():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)

    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db

    db = TestingSessionLocal()
    try:
        RecommendationRepository(db).create(
            Recommendation(
                id="reco_surface_missing",
                analysis_id=None,
                title="Track ETH setup",
                summary="Track ETH setup",
            )
        )
        db.commit()
    finally:
        db.close()

    local_client = TestClient(app)
    response = local_client.get("/api/v1/recommendations/recent")
    app.dependency_overrides.clear()
    Base.metadata.drop_all(bind=engine)

    assert response.status_code == 200
    payload = response.json()
    recommendation = next(item for item in payload["recommendations"] if item["id"] == "reco_surface_missing")
    assert recommendation["outcome_status"] is None
    assert recommendation["metadata"]["workflow_run_id"] is None
    assert recommendation["metadata"]["intelligence_run_id"] is None
    assert recommendation["metadata"]["execution_receipt_id"] is None
    assert recommendation["metadata"]["recommendation_generate_receipt_id"] is None
    assert recommendation["metadata"]["latest_outcome_reason"] is None
    assert recommendation["metadata"]["knowledge_hint_count"] == 0
    assert recommendation["metadata"]["knowledge_hint_status"] == "not_linked_yet"
    assert recommendation["metadata"]["knowledge_hint_summaries"] == []
    assert recommendation["metadata"]["governance"] is None


def test_recommendation_detail_surface_returns_real_object_by_id():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)

    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db

    db = TestingSessionLocal()
    try:
        RecommendationRepository(db).create(
            Recommendation(
                id="reco_surface_detail",
                analysis_id=None,
                title="Track SOL breakout",
                summary="Track SOL breakout setup",
            )
        )
        db.commit()
    finally:
        db.close()

    local_client = TestClient(app)
    response = local_client.get("/api/v1/recommendations/reco_surface_detail")
    app.dependency_overrides.clear()
    Base.metadata.drop_all(bind=engine)

    assert response.status_code == 200
    payload = response.json()
    assert payload["id"] == "reco_surface_detail"
    assert payload["status"] == "generated"
    assert payload["metadata"]["knowledge_hint_status"] == "not_linked_yet"


def test_recommendation_surface_reuses_governance_decision_shape():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)

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
                id="analysis_surface_governance",
                query="Analyze BTC trend",
                symbol="BTC-USDT",
                metadata={"governance_source": "risk_engine.default_validation"},
            )
        )
        RecommendationRepository(db).create(
            Recommendation(
                id="reco_surface_governance",
                analysis_id="analysis_surface_governance",
                title="Track BTC breakout",
                summary="Track BTC breakout setup",
                decision="execute",
                decision_reason="Passed default Step 1 governance validation.",
            )
        )
        db.commit()
    finally:
        db.close()

    local_client = TestClient(app)
    response = local_client.get("/api/v1/recommendations/recent")
    app.dependency_overrides.clear()
    Base.metadata.drop_all(bind=engine)

    assert response.status_code == 200
    payload = response.json()
    recommendation = next(item for item in payload["recommendations"] if item["id"] == "reco_surface_governance")
    assert recommendation["decision"] == "execute"
    assert recommendation["metadata"]["governance"] == {
        "decision": "execute",
        "reasons": ["Passed default Step 1 governance validation."],
        "source": "risk_engine.default_validation",
        "advisory_hints": [],
        "policy_set_id": "governance.default.v1",
        "active_policy_ids": ["forbidden_symbols_policy"],
        "default_decision_rule_ids": ["default_no_actions_escalate", "default_pass_execute"],
        "evidence": [],
        "actor": {
            "actor_type": "system",
            "actor_id": "risk_engine.default_validation",
        },
        "scope": {
            "scope_type": "entity",
        },
    }
