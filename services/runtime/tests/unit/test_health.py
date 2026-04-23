from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from apps.api.app.deps import get_db
from apps.api.app.main import app
from domains.execution_records.models import ExecutionReceipt, ExecutionRequest
from domains.execution_records.repository import ExecutionRecordRepository
from domains.workflow_runs.models import WorkflowRun
from domains.workflow_runs.repository import WorkflowRunRepository
from governance.audit.models import AuditEvent
from governance.audit.repository import AuditEventRepository
from shared.config.settings import settings
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


def test_health_is_served_from_api_v1_only():
    original_provider = settings.reasoning_provider
    settings.reasoning_provider = "mock"
    client = TestClient(app)
    response = client.get("/api/v1/health")
    settings.reasoning_provider = original_provider
    assert response.status_code == 200
    assert response.json()["status"] in {"ok", "degraded"}
    assert response.json()["monitoring_status"] in {"nominal", "attention", "unavailable"}


def test_health_reports_degraded_when_hermes_is_unavailable(monkeypatch):
    original_provider = settings.reasoning_provider
    settings.reasoning_provider = "hermes"
    monkeypatch.setattr(
        "apps.api.app.api.v1.health.resolve_runtime",
        lambda: type("UnavailableRuntime", (), {"health": lambda self: (_ for _ in ()).throw(Exception("unavailable"))})(),
    )
    client = TestClient(app)
    response = client.get("/api/v1/health")
    settings.reasoning_provider = original_provider

    assert response.status_code == 200
    assert response.json()["status"] == "degraded"
    assert response.json()["runtime_status"] == "unavailable"
    assert response.json()["hermes_detail"] == "Hermes health check failed unexpectedly."


def test_health_returns_monitoring_snapshot_from_real_rows():
    engine, TestingSessionLocal = _make_db()

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
                id="wfrun_health_1",
                workflow_name="analyze",
                status="failed",
                request_summary="Analyze BTC",
                failed_step="reason",
                failure_reason="Hermes unavailable",
            )
        )
        execution_repo = ExecutionRecordRepository(db)
        execution_repo.create_request(
            ExecutionRequest(
                id="exreq_health_1",
                action_id="review_complete",
                family="review",
                side_effect_level="state_mutation",
                status="failed",
                actor="test",
                context="health_test",
                reason="test",
                idempotency_key="health-test-1",
            )
        )
        execution_repo.create_receipt(
            ExecutionReceipt(
                id="exrcpt_health_1",
                request_id="exreq_health_1",
                action_id="review_complete",
                status="failed",
                error="review failed",
            )
        )
        AuditEventRepository(db).create(
            AuditEvent(
                id="audit_health_1",
                event_type="review_completed_failed",
                entity_type="review",
                entity_id="review_health_1",
                payload={"detail": "failed"},
            )
        )
        db.commit()
    finally:
        db.close()

    client = TestClient(app)
    response = client.get("/api/v1/health")

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
    assert payload["workflow_failures_by_type"].get("reason", 0) + payload["workflow_failures_by_type"].get("workflow_failed", 0) == 1
    assert payload["execution_failures_by_family"]["review"] == 1
    assert payload["top_execution_failure_family"] == "review"


def test_health_reports_monitoring_unavailable_when_snapshot_fails(monkeypatch):
    monkeypatch.setattr(
        "apps.api.app.api.v1.health.MonitoringService.get_snapshot",
        lambda self: (_ for _ in ()).throw(RuntimeError("db unavailable")),
    )
    client = TestClient(app)
    response = client.get("/api/v1/health")

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "degraded"
    assert payload["monitoring_status"] == "unavailable"
    assert payload["monitoring_detail"] == "Monitoring snapshot could not be confirmed."
    assert payload["recent_failed_workflow_count"] is None
    assert payload["recent_failed_execution_count"] is None


def test_legacy_top_level_health_route_is_not_exposed():
    client = TestClient(app)
    response = client.get("/health")
    assert response.status_code == 404
