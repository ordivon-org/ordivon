from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from fastapi.testclient import TestClient

from apps.api.app.deps import get_db
from apps.api.app.main import app
from execution.catalog import get_execution_action
from governance_engine.audit.orm import AuditEventORM
from shared.config.settings import settings
from state.db.base import Base


def test_execution_action_catalog_aligns_with_analyze_side_effects(monkeypatch):
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

    original_provider = settings.reasoning_provider
    settings.reasoning_provider = "hermes"

    monkeypatch.setattr(
        "intelligence.runtime.hermes_client.HermesClient.run_task",
        lambda self, task_type, payload: {
            "task_id": payload["task_id"],
            "task_type": task_type,
            "idempotency_key": payload["idempotency_key"],
            "trace_id": payload["trace_id"],
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
    response = client.post(
        "/api/v1/analyze-and-suggest",
        json={"query": "Analyze BTC", "symbols": ["BTC/USDT"]},
    )

    settings.reasoning_provider = original_provider
    app.dependency_overrides.clear()

    assert response.status_code == 200

    db = TestingSessionLocal()
    try:
        report_write = get_execution_action("analysis_report_write")
        metadata_update = get_execution_action("analysis_metadata_update")
        recommendation_generate = get_execution_action("recommendation_generate")

        assert report_write.boundary_status == "covered"
        assert metadata_update.primary_receipt_candidate is True
        assert recommendation_generate.side_effect_level == "state_mutation"

        event_types = {row.event_type for row in db.query(AuditEventORM).all()}
        assert "analysis_report_written" in event_types
        assert "recommendation_generated" in event_types
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)
