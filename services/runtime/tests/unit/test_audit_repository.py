from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from governance_engine.audit.models import AuditEvent
from governance_engine.audit.repository import AuditEventRepository
from state.db.base import Base


def _make_db():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    testing_session = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)
    return engine, testing_session


def test_audit_repository_create_and_list_recent():
    engine, testing_session = _make_db()
    db = testing_session()

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
        Base.metadata.drop_all(bind=engine)
