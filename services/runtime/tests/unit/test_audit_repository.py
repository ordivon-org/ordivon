from governance_engine.audit.models import AuditEvent
from governance_engine.audit.repository import AuditEventRepository
from state.db.bootstrap import init_db
from state.db.session import SessionLocal


def test_audit_repository_create_and_list_recent():
    init_db()
    db = SessionLocal()

    try:
        repo = AuditEventRepository(db)
        repo.create(
            AuditEvent(
                event_type="analysis_completed",
                entity_type="analysis",
                entity_id="analysis-123",
                payload={"summary": "done"},
            )
        )

        rows = repo.list_recent(limit=5)

        assert rows
        assert rows[0].event_type == "analysis_completed"
        assert rows[0].entity_type == "analysis"
    finally:
        db.close()
