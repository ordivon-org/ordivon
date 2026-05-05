import os

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from apps.api.app.deps import get_db
from apps.api.app.main import app
from domains.execution_records.orm import ExecutionReceiptORM, ExecutionRequestORM
from domains.research.orm import AnalysisORM
from domains.strategy.orm import RecommendationORM
from governance_engine.audit.orm import AuditEventORM
from shared.config.settings import settings
from shared.utils.serialization import from_json_text
from state.db.base import Base


def test_analyze_api_writes_execution_request_and_receipt(monkeypatch):
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
    body = response.json()
    assert body["metadata"]["execution_request_id"].startswith("exreq_")
    assert body["metadata"]["execution_receipt_id"].startswith("exrcpt_")
    assert body["metadata"]["recommendation_generate_request_id"].startswith("exreq_")
    assert body["metadata"]["recommendation_generate_receipt_id"].startswith("exrcpt_")

    db = TestingSessionLocal()
    try:
        request_rows = db.query(ExecutionRequestORM).order_by(ExecutionRequestORM.action_id.asc()).all()
        receipt_rows = db.query(ExecutionReceiptORM).order_by(ExecutionReceiptORM.action_id.asc()).all()
        analysis_row = db.query(AnalysisORM).one()
        recommendation_row = db.query(RecommendationORM).one()
        audit_row = db.query(AuditEventORM).filter(AuditEventORM.event_type == "analysis_report_written").one()
        recommendation_audit_row = (
            db.query(AuditEventORM).filter(AuditEventORM.event_type == "recommendation_generated").one()
        )

        assert len(request_rows) == 2
        assert len(receipt_rows) == 2

        request_by_action = {row.action_id: row for row in request_rows}
        receipt_by_action = {row.action_id: row for row in receipt_rows}

        report_request = request_by_action["analysis_report_write"]
        report_receipt = receipt_by_action["analysis_report_write"]
        recommendation_request = request_by_action["recommendation_generate"]
        recommendation_receipt = receipt_by_action["recommendation_generate"]

        assert report_request.status == "succeeded"
        assert report_receipt.request_id == report_request.id
        assert report_receipt.status == "succeeded"
        assert report_receipt.result_ref is not None
        assert analysis_row.id == report_request.analysis_id

        assert recommendation_request.status == "succeeded"
        assert recommendation_request.analysis_id == analysis_row.id
        assert recommendation_request.recommendation_id == recommendation_row.id
        assert recommendation_request.entity_type == "recommendation"
        assert recommendation_request.entity_id == recommendation_row.id
        assert recommendation_receipt.request_id == recommendation_request.id
        assert recommendation_receipt.status == "succeeded"
        assert recommendation_receipt.result_ref == recommendation_row.id

        metadata = from_json_text(analysis_row.metadata_json, {})
        assert metadata["execution_request_id"] == report_request.id
        assert metadata["execution_receipt_id"] == report_receipt.id
        assert metadata["recommendation_generate_request_id"] == recommendation_request.id
        assert metadata["recommendation_generate_receipt_id"] == recommendation_receipt.id

        payload = from_json_text(audit_row.payload_json, {})
        assert payload["execution_request_id"] == report_request.id
        assert payload["execution_receipt_id"] == report_receipt.id

        recommendation_payload = from_json_text(recommendation_audit_row.payload_json, {})
        assert recommendation_payload["recommendation_generate_request_id"] == recommendation_request.id
        assert recommendation_payload["recommendation_generate_receipt_id"] == recommendation_receipt.id
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)
        if os.path.exists("wiki"):
            import shutil

            shutil.rmtree("wiki")
