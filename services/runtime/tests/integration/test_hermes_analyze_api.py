from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient
from shared.utils.serialization import from_json_text

from apps.api.app.deps import get_db
from apps.api.app.main import app
from domains.ai_actions.orm import AgentActionORM
from domains.execution_records.orm import ExecutionProgressRecordORM
from domains.knowledge_feedback.feedback_record_orm import FeedbackRecordORM
from domains.journal.lesson_repository import LessonRepository
from domains.journal.lesson_service import LessonService
from domains.journal.models import Review
from domains.journal.repository import ReviewRepository
from domains.journal.service import ReviewService
from domains.research.orm import AnalysisORM
from domains.research.models import AnalysisResult
from domains.research.repository import AnalysisRepository
from domains.intelligence_runs.orm import IntelligenceRunORM
from domains.strategy.orm import RecommendationORM
from domains.strategy.models import Recommendation
from domains.strategy.outcome_repository import OutcomeRepository
from domains.strategy.outcome_service import OutcomeService
from domains.strategy.repository import RecommendationRepository
from domains.strategy.service import RecommendationService
from governance_engine.audit.orm import AuditEventORM
from intelligence.runtime.hermes_client import HermesUnavailableError
from shared.enums.domain import ReviewVerdict
from shared.config.settings import settings
from state.db.base import Base


def test_analyze_api_persists_agent_action_with_hermes(monkeypatch):
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
    response = client.post(
        "/api/v1/analyze-and-suggest",
        json={"query": "Analyze BTC", "symbols": ["BTC/USDT"]},
    )

    settings.reasoning_provider = original_provider
    app.dependency_overrides.clear()

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "success"
    assert payload["decision"] == "execute"
    assert payload["metadata"]["governance_decision"] == "execute"
    assert payload["metadata"]["agent_action_id"]
    assert payload["metadata"]["intelligence_run_id"]

    db = TestingSessionLocal()
    try:
        assert db.query(AgentActionORM).count() == 1
        assert db.query(IntelligenceRunORM).count() == 1
        run = db.query(IntelligenceRunORM).one()
        assert run.status == "completed"
        assert run.output_summary == "Hermes summary"
        analysis = db.query(AnalysisORM).one()
        analysis_meta = from_json_text(analysis.metadata_json, {})
        assert analysis_meta["governance_decision"] == "execute"
        assert analysis_meta["governance_source"] == "risk_engine.default_validation"
        assert analysis_meta["governance_policy_set_id"] == "governance.default.v1"
        assert analysis_meta["governance_active_policy_ids"] == [
            "forbidden_symbols_policy",
            "trading_discipline_policy",
        ]
        assert analysis_meta["report_write_action_context"]["actor"] == "workflow.analyze"
        assert analysis_meta["metadata_update_action_context"]["context"] == "write_wiki_step"
        event = db.query(AuditEventORM).filter(AuditEventORM.event_type == "analysis_completed").one()
        event_payload = from_json_text(event.payload_json, {})
        assert event_payload["decision"] == "execute"
        assert event_payload["governance_source"] == "risk_engine.default_validation"
        assert event_payload["governance_policy_set_id"] == "governance.default.v1"
        assert "agent_action_id" in event.payload_json
        assert "intelligence_run_id" in event.payload_json
        recommendation_event = (
            db.query(AuditEventORM).filter(AuditEventORM.event_type == "recommendation_generated").one()
        )
        recommendation_payload = from_json_text(recommendation_event.payload_json, {})
        assert recommendation_payload["decision"] == "execute"
        progress_rows = (
            db
            .query(ExecutionProgressRecordORM)
            .filter(ExecutionProgressRecordORM.request_id == analysis_meta["recommendation_generate_request_id"])
            .order_by(ExecutionProgressRecordORM.created_at.asc())
            .all()
        )
        assert [row.progress_state for row in progress_rows] == ["started", "completed"]
        report_event = db.query(AuditEventORM).filter(AuditEventORM.event_type == "analysis_report_written").one()
        report_payload = from_json_text(report_event.payload_json, {})
        assert report_payload["write_action_context"]["actor"] == "workflow.analyze"
        assert report_payload["metadata_action_context"]["reason"]
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


def test_analyze_api_returns_503_when_hermes_is_unavailable(monkeypatch):
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
    assert response.json()["detail"] == "Hermes runtime is unavailable."

    db = TestingSessionLocal()
    try:
        assert db.query(AgentActionORM).count() == 0
        assert db.query(IntelligenceRunORM).count() == 1
        run = db.query(IntelligenceRunORM).one()
        assert run.status == "failed"
        assert run.error == "Hermes runtime is unavailable."
        assert db.query(AuditEventORM).count() == 0
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


def test_analyze_api_escalates_honestly_and_skips_recommendation(monkeypatch):
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
                "suggested_actions": [],
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
    assert payload["decision"] == "escalate"
    assert payload["metadata"]["governance_decision"] == "escalate"
    assert "No suggested actions were produced." in payload["risk_flags"]

    db = TestingSessionLocal()
    try:
        assert db.query(AnalysisORM).count() == 1
        assert db.query(RecommendationORM).count() == 0
        analysis = db.query(AnalysisORM).one()
        analysis_meta = from_json_text(analysis.metadata_json, {})
        assert analysis_meta["governance_decision"] == "escalate"
        assert analysis_meta["governance_policy_set_id"] == "governance.default.v1"

        analysis_event = db.query(AuditEventORM).filter(AuditEventORM.event_type == "analysis_completed").one()
        analysis_payload = from_json_text(analysis_event.payload_json, {})
        assert analysis_payload["decision"] == "escalate"
        assert analysis_payload["governance_source"] == "risk_engine.default_validation"
        assert analysis_payload["governance_policy_set_id"] == "governance.default.v1"
        assert db.query(AuditEventORM).filter(AuditEventORM.event_type == "recommendation_generated").count() == 0
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


def test_analyze_api_fails_honestly_when_boundary_context_is_missing(monkeypatch):
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

    from orchestrator.workflows.analyze import BuildContextStep

    original_execute = BuildContextStep.execute

    def execute_without_context(self, ctx):
        updated = original_execute(self, ctx)
        updated.metadata.pop("side_effect_contexts", None)
        return updated

    monkeypatch.setattr(BuildContextStep, "execute", execute_without_context)

    client = TestClient(app)
    response = client.post(
        "/api/v1/analyze-and-suggest",
        json={"query": "Analyze BTC", "symbols": ["BTC/USDT"]},
    )

    settings.reasoning_provider = original_provider
    app.dependency_overrides.clear()

    assert response.status_code == 500
    assert "requires action context" in response.json()["detail"]

    db = TestingSessionLocal()
    try:
        assert db.query(AuditEventORM).count() == 0
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


def test_analyze_api_consumes_governance_feedback_hints_from_prior_review(monkeypatch):
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

    seed_db = TestingSessionLocal()
    try:
        AnalysisRepository(seed_db).create(
            AnalysisResult(
                id="ana_prior_hint",
                query="Analyze BTC",
                symbol="BTC-USDT",
                timeframe="1h",
                summary="Prior summary",
                thesis="Prior thesis",
                suggested_actions=["BUY"],
            )
        )
        recommendation_repo = RecommendationRepository(seed_db)
        recommendation_repo.create(
            Recommendation(
                id="reco_prior_hint",
                analysis_id="ana_prior_hint",
                title="Buy BTC",
                summary="Prior recommendation",
            )
        )
        review_service = ReviewService(
            ReviewRepository(seed_db),
            LessonService(LessonRepository(seed_db)),
            outcome_service=OutcomeService(OutcomeRepository(seed_db)),
            recommendation_service=RecommendationService(recommendation_repo),
        )
        review_row = review_service.create(
            Review(
                id="review_prior_hint",
                recommendation_id="reco_prior_hint",
                review_type="recommendation_postmortem",
                expected_outcome="Trend holds",
            )
        )
        review_service.complete_review(
            review_id=review_row.id,
            observed_outcome="Trend failed",
            verdict=ReviewVerdict.INVALIDATED,
            variance_summary="Entered too early",
            cause_tags=["timing"],
            lessons=["Wait for confirmation before entry"],
            followup_actions=["Add confirmation rule"],
        )
        seed_db.commit()
    finally:
        seed_db.close()

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
    response = client.post(
        "/api/v1/analyze-and-suggest",
        json={"query": "Analyze BTC again", "symbols": ["BTC-USDT"]},
    )

    settings.reasoning_provider = original_provider
    app.dependency_overrides.clear()

    assert response.status_code == 200
    payload = response.json()
    assert payload["decision"] == "execute"
    assert payload["metadata"]["governance_advisory_hint_status"] == "available"
    assert len(payload["metadata"]["governance_advisory_hints"]) == 1
    assert payload["metadata"]["governance_advisory_hints"][0]["summary"] == "Wait for confirmation before entry"

    db = TestingSessionLocal()
    try:
        event = (
            db
            .query(AuditEventORM)
            .filter(AuditEventORM.event_type == "analysis_completed")
            .order_by(AuditEventORM.created_at.desc())
            .first()
        )
        assert event is not None
        event_payload = from_json_text(event.payload_json, {})
        assert len(event_payload["governance_advisory_hints"]) == 1
        assert event_payload["governance_advisory_hints"][0]["summary"] == "Wait for confirmation before entry"
        feedback_rows = (
            db
            .query(FeedbackRecordORM)
            .filter(
                FeedbackRecordORM.recommendation_id == "reco_prior_hint",
                FeedbackRecordORM.consumer_type == "governance",
            )
            .all()
        )
        assert len(feedback_rows) == 1
        assert feedback_rows[0].subject_key == "BTC-USDT"
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


def test_analyze_api_consumes_intelligence_feedback_hints_into_task_payload(monkeypatch):
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

    seed_db = TestingSessionLocal()
    try:
        AnalysisRepository(seed_db).create(
            AnalysisResult(
                id="ana_prior_intel_hint",
                query="Analyze BTC",
                symbol="BTC-USDT",
                timeframe="1h",
                summary="Prior summary",
                thesis="Prior thesis",
                suggested_actions=["BUY"],
            )
        )
        recommendation_repo = RecommendationRepository(seed_db)
        recommendation_repo.create(
            Recommendation(
                id="reco_prior_intel_hint",
                analysis_id="ana_prior_intel_hint",
                title="Buy BTC",
                summary="Prior recommendation",
            )
        )
        review_service = ReviewService(
            ReviewRepository(seed_db),
            LessonService(LessonRepository(seed_db)),
            outcome_service=OutcomeService(OutcomeRepository(seed_db)),
            recommendation_service=RecommendationService(recommendation_repo),
        )
        review_row = review_service.create(
            Review(
                id="review_prior_intel_hint",
                recommendation_id="reco_prior_intel_hint",
                review_type="recommendation_postmortem",
                expected_outcome="Trend holds",
            )
        )
        review_service.complete_review(
            review_id=review_row.id,
            observed_outcome="Trend failed",
            verdict=ReviewVerdict.INVALIDATED,
            variance_summary="Entered too early",
            cause_tags=["timing"],
            lessons=["Wait for confirmation before entry"],
            followup_actions=["Add confirmation rule"],
        )
        seed_db.commit()
    finally:
        seed_db.close()

    captured_payload = {}
    original_provider = settings.reasoning_provider
    settings.reasoning_provider = "hermes"

    def _capture_run_task(self, task_type, payload):
        captured_payload["payload"] = payload
        return {
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
        }

    monkeypatch.setattr(
        "intelligence.runtime.hermes_client.HermesClient.run_task",
        _capture_run_task,
    )

    client = TestClient(app)
    response = client.post(
        "/api/v1/analyze-and-suggest",
        json={"query": "Analyze BTC again", "symbols": ["BTC-USDT"]},
    )

    settings.reasoning_provider = original_provider
    app.dependency_overrides.clear()

    assert response.status_code == 200
    assert captured_payload["payload"]["input"]["memory_lessons"] == ["Wait for confirmation before entry"]
    assert captured_payload["payload"]["input"]["related_reviews"] == ["review_prior_intel_hint"]
    payload = response.json()
    assert payload["metadata"]["intelligence_feedback_hint_status"] == "available"
    assert payload["metadata"]["intelligence_memory_lesson_count"] == 1
    assert payload["metadata"]["intelligence_related_review_count"] == 1

    db = TestingSessionLocal()
    try:
        analysis = db.query(AnalysisORM).order_by(AnalysisORM.created_at.desc()).first()
        assert analysis is not None
        analysis_meta = from_json_text(analysis.metadata_json, {})
        assert analysis_meta["intelligence_feedback_hint_status"] == "available"
        assert analysis_meta["intelligence_memory_lesson_count"] == 1
        assert analysis_meta["intelligence_related_review_count"] == 1
        feedback_rows = (
            db
            .query(FeedbackRecordORM)
            .filter(
                FeedbackRecordORM.recommendation_id == "reco_prior_intel_hint",
                FeedbackRecordORM.consumer_type == "intelligence",
            )
            .all()
        )
        assert len(feedback_rows) == 1
        assert feedback_rows[0].subject_key == "BTC-USDT"
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


def test_analyze_api_honestly_falls_back_when_governance_feedback_reader_fails(monkeypatch):
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
    monkeypatch.setattr(
        "governance_engine.feedback.GovernanceFeedbackReader.list_hints_for_symbol",
        lambda self, symbol, limit=3: (_ for _ in ()).throw(RuntimeError("feedback store unavailable")),
    )

    client = TestClient(app)
    response = client.post(
        "/api/v1/analyze-and-suggest",
        json={"query": "Analyze BTC", "symbols": ["BTC-USDT"]},
    )

    settings.reasoning_provider = original_provider
    app.dependency_overrides.clear()

    assert response.status_code == 200
    payload = response.json()
    assert payload["decision"] == "execute"
    assert payload["metadata"]["governance_advisory_hint_status"] == "unavailable"
    assert payload["metadata"]["governance_advisory_hints"] == []

    db = TestingSessionLocal()
    try:
        analysis = db.query(AnalysisORM).one()
        analysis_meta = from_json_text(analysis.metadata_json, {})
        assert analysis_meta["governance_advisory_hint_status"] == "unavailable"
        assert analysis_meta["governance_advisory_hints"] == []
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


def test_analyze_api_honestly_falls_back_when_intelligence_feedback_reader_fails(monkeypatch):
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
    monkeypatch.setattr(
        "intelligence.feedback.IntelligenceFeedbackReader.read_for_symbol",
        lambda self, symbol, limit=3: (_ for _ in ()).throw(RuntimeError("intelligence feedback unavailable")),
    )

    client = TestClient(app)
    response = client.post(
        "/api/v1/analyze-and-suggest",
        json={"query": "Analyze BTC", "symbols": ["BTC-USDT"]},
    )

    settings.reasoning_provider = original_provider
    app.dependency_overrides.clear()

    assert response.status_code == 200
    payload = response.json()
    assert payload["metadata"]["intelligence_feedback_hint_status"] == "unavailable"
    assert payload["metadata"]["intelligence_memory_lesson_count"] == 0
    assert payload["metadata"]["intelligence_related_review_count"] == 0

    db = TestingSessionLocal()
    try:
        analysis = db.query(AnalysisORM).one()
        analysis_meta = from_json_text(analysis.metadata_json, {})
        assert analysis_meta["intelligence_feedback_hint_status"] == "unavailable"
        assert analysis_meta["intelligence_memory_lesson_count"] == 0
        assert analysis_meta["intelligence_related_review_count"] == 0
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)
