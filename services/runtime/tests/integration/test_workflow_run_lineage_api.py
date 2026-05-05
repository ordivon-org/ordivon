from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from apps.api.app.deps import get_db
from apps.api.app.main import app
from domains.research.orm import AnalysisORM
from domains.workflow_runs.orm import WorkflowRunORM
from governance_engine.audit.orm import AuditEventORM
from intelligence.runtime.hermes_client import HermesUnavailableError
from shared.config.settings import settings
from shared.utils.serialization import from_json_text
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


def test_analyze_api_persists_completed_workflow_run(monkeypatch):
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
    payload = response.json()
    assert payload["metadata"]["workflow_run_id"].startswith("wfrun_")

    db = TestingSessionLocal()
    try:
        run = db.query(WorkflowRunORM).one()
        assert run.status == "completed"
        assert run.workflow_name == "analyze"
        steps = from_json_text(run.step_statuses_json, [])
        assert steps[0]["step"] == "BuildContextStep"
        assert steps[-1]["step"] == "WriteWikiStep"
        assert all(step["status"] == "completed" for step in steps)

        analysis = db.query(AnalysisORM).one()
        metadata = from_json_text(analysis.metadata_json, {})
        assert metadata["workflow_run_id"] == run.id

        analysis_event = db.query(AuditEventORM).filter(AuditEventORM.event_type == "analysis_completed").one()
        event_payload = from_json_text(analysis_event.payload_json, {})
        assert event_payload["workflow_run_id"] == run.id
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


def test_analyze_api_persists_failed_workflow_run(monkeypatch):
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

    def raise_unavailable(self, task_type, payload):
        raise HermesUnavailableError("Hermes runtime is unavailable.")

    monkeypatch.setattr(
        "intelligence.runtime.hermes_client.HermesClient.run_task",
        raise_unavailable,
    )

    client = TestClient(app)
    response = client.post(
        "/api/v1/analyze-and-suggest",
        json={"query": "Analyze BTC", "symbols": ["BTC/USDT"]},
    )

    settings.reasoning_provider = original_provider
    app.dependency_overrides.clear()

    assert response.status_code == 503

    db = TestingSessionLocal()
    try:
        run = db.query(WorkflowRunORM).one()
        assert run.status == "failed"
        assert run.failed_step == "ReasonStep"
        assert run.failure_reason == "Hermes runtime is unavailable."
        steps = from_json_text(run.step_statuses_json, [])
        assert steps[0]["step"] == "BuildContextStep"
        assert steps[0]["status"] == "completed"
        assert steps[1]["step"] == "ReasonStep"
        assert steps[1]["status"] == "failed"
        assert steps[1]["attempt"] == 1
        assert steps[1]["recovery_action"] == "none"
        assert db.query(AnalysisORM).count() == 0
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


def test_analyze_api_retries_reason_step_once_before_success(monkeypatch):
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

    calls = {"count": 0}

    def flaky_run_task(self, task_type, payload):
        calls["count"] += 1
        if calls["count"] == 1:
            raise HermesUnavailableError("Hermes runtime is unavailable.", retryable=True)
        return {
            "task_id": payload["task_id"],
            "task_type": task_type,
            "idempotency_key": payload["idempotency_key"],
            "trace_id": payload["trace_id"],
            "status": "completed",
            "provider": "openrouter",
            "model": "test-model",
            "session_id": "sess_retry",
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
        }

    monkeypatch.setattr(
        "intelligence.runtime.hermes_client.HermesClient.run_task",
        flaky_run_task,
    )

    client = TestClient(app)
    response = client.post(
        "/api/v1/analyze-and-suggest",
        json={"query": "Analyze BTC", "symbols": ["BTC/USDT"]},
    )

    settings.reasoning_provider = original_provider
    app.dependency_overrides.clear()

    assert response.status_code == 200
    assert calls["count"] == 2

    db = TestingSessionLocal()
    try:
        run = db.query(WorkflowRunORM).one()
        steps = from_json_text(run.step_statuses_json, [])
        reason_retry = [step for step in steps if step["step"] == "ReasonStep"]
        assert reason_retry[0]["status"] == "retrying"
        assert reason_retry[0]["attempt"] == 1
        assert reason_retry[1]["status"] == "completed"
        assert reason_retry[1]["attempt"] == 2
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


def test_analyze_api_uses_degraded_fallback_after_retry_exhaustion(monkeypatch):
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

    def always_retryable(self, task_type, payload):
        raise HermesUnavailableError("Hermes runtime is unavailable.", retryable=True)

    monkeypatch.setattr(
        "intelligence.runtime.hermes_client.HermesClient.run_task",
        always_retryable,
    )

    client = TestClient(app)
    response = client.post(
        "/api/v1/analyze-and-suggest",
        json={"query": "Analyze BTC", "symbols": ["BTC/USDT"]},
    )

    settings.reasoning_provider = original_provider
    app.dependency_overrides.clear()

    assert response.status_code == 200
    payload = response.json()
    assert payload["summary"] == "Degraded analysis: runtime failed after retries."

    db = TestingSessionLocal()
    try:
        run = db.query(WorkflowRunORM).one()
        steps = from_json_text(run.step_statuses_json, [])
        reason_steps = [step for step in steps if step["step"] == "ReasonStep"]
        assert reason_steps[0]["status"] == "retrying"
        assert reason_steps[1]["status"] == "completed"
        assert reason_steps[1]["recovery_action"] == "fallback"
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


def test_failed_workflow_run_keeps_compensation_detail(monkeypatch):
    engine, TestingSessionLocal = _make_client_db()

    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    original_provider = settings.reasoning_provider
    settings.reasoning_provider = "mock"

    monkeypatch.setattr(
        "orchestrator.workflows.analyze.MarkdownWikiService.write_document",
        lambda self, section, doc_id, content: "wiki/reports/test.md",
    )
    monkeypatch.setattr(
        "orchestrator.workflows.analyze.AnalysisService.update_metadata",
        lambda self, analysis_id, metadata: (_ for _ in ()).throw(Exception("DB update fail")),
    )

    client = TestClient(app)
    response = client.post(
        "/api/v1/analyze-and-suggest",
        json={"query": "Analyze BTC", "symbols": ["BTC/USDT"]},
    )

    settings.reasoning_provider = original_provider
    app.dependency_overrides.clear()

    assert response.status_code == 500

    db = TestingSessionLocal()
    try:
        run = db.query(WorkflowRunORM).one()
        assert run.status == "failed"
        assert run.failed_step == "WriteWikiStep"
        steps = from_json_text(run.step_statuses_json, [])
        failed_step = next(step for step in steps if step["step"] == "WriteWikiStep")
        assert failed_step["status"] == "failed"
        assert failed_step["recovery_action"] == "compensation"
        assert failed_step["recovery_detail"]["compensation_applied"] is False
        assert failed_step["recovery_detail"]["document_path"] == "wiki/reports/test.md"
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


def test_governance_block_persists_handoff_and_resume_refs():
    engine, TestingSessionLocal = _make_client_db()

    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    original_provider = settings.reasoning_provider
    settings.reasoning_provider = "mock"

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
        run = db.query(WorkflowRunORM).one()
        lineage = from_json_text(run.lineage_refs_json, {})
        assert lineage.get("handoff_artifact_ref") is None or isinstance(lineage.get("handoff_artifact_ref"), str)
        if lineage.get("handoff_artifact_ref") is not None:
            assert lineage.get("blocked_reason", "").startswith("governance_")
            assert str(lineage.get("resume_marker", "")).startswith("handoff:")
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)
