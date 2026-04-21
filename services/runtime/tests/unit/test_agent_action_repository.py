from domains.ai_actions.models import AgentAction
from domains.ai_actions.repository import AgentActionRepository
from domains.ai_actions.service import AgentActionService
from state.db.bootstrap import init_db
from state.db.session import SessionLocal


def test_agent_action_repository_create_and_get():
    init_db()
    db = SessionLocal()

    try:
        repo = AgentActionRepository(db)
        action = AgentAction(
            task_type="analysis.generate",
            provider="openrouter",
            model="test-model",
            reason="Test analyze task",
            idempotency_key="task_123",
            input_summary="Analyze BTC",
            output_summary="BTC looks stable",
            input_refs={"symbol": "BTC"},
            output_refs={"analysis_id": "analysis_123"},
        )
        row = repo.create(action)
        loaded = repo.get(row.id)

        assert loaded is not None
        assert loaded.task_type == "analysis.generate"
        assert loaded.provider == "openrouter"
    finally:
        db.close()


def test_agent_action_service_reuses_existing_idempotency_key():
    init_db()
    db = SessionLocal()

    try:
        service = AgentActionService(AgentActionRepository(db))
        first = service.create(
            AgentAction(
                task_type="analysis.generate",
                reason="First",
                idempotency_key="same_key",
            )
        )
        second = service.create(
            AgentAction(
                task_type="analysis.generate",
                reason="Second",
                idempotency_key="same_key",
            )
        )

        assert first.id == second.id
    finally:
        db.close()
