from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from apps.api.app.deps import get_db
from apps.api.app.main import app
from domains.workflow_runs.models import WorkflowRun
from domains.workflow_runs.repository import WorkflowRunRepository
from state.db.base import Base


def test_health_api_exposes_monitoring_history_summary():
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
                id="wfrun_monitor_history_1",
                workflow_name="analyze",
                status="failed",
                request_summary="Analyze BTC",
                failed_step="ReasonStep",
                lineage_refs={"blocked_reason": "approval_required"},
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
    assert "workflow_failures_by_type" in payload
    assert "approval_blocked_count" in payload
    assert payload["approval_blocked_count"] == 1
    assert payload["blocked_run_ids"] == ["wfrun_monitor_history_1"]
