import json

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from capabilities.view.audits import AuditCapability
from governance.audit.models import AuditEvent
from governance.audit.orm import AuditEventORM
from governance.audit.repository import AuditEventRepository
from governance.audit.service import AuditService
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


def test_audit_repository_writes_structured_envelope_for_new_events():
    engine, testing_session = _make_db()
    db = testing_session()

    try:
        repo = AuditEventRepository(db)
        row = repo.create(
            AuditEvent(
                event_type="analysis_completed",
                entity_type="analysis",
                entity_id="analysis-123",
                payload={"summary": "Analysis completed.", "decision": "execute", "analysis_id": "analysis-123"},
            )
        )
        db.commit()

        payload = json.loads(row.payload_json)
        assert payload["schema_version"] == "audit.v1"
        assert payload["workflow_name"] == "analysis_completed"
        assert payload["stage"] == "analysis"
        assert payload["decision"] == "execute"
        assert payload["status"] == "persisted"
        assert payload["context_summary"] == "Analysis completed."
        assert payload["subject_id"] == "analysis-123"
        assert payload["details"]["analysis_id"] == "analysis-123"
        assert payload["analysis_id"] == "analysis-123"
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


def test_audit_capability_marks_legacy_rows_without_guessing():
    engine, testing_session = _make_db()
    db = testing_session()

    try:
        db.add(
            AuditEventORM(
                id="audit_legacy_1",
                event_type="legacy_event",
                entity_type="legacy_subject",
                entity_id="legacy-123",
                payload_json='{"detail":"legacy"}',
            )
        )
        db.commit()

        records = AuditCapability().list_recent(AuditService(AuditEventRepository(db)), limit=10)
        legacy = next(item for item in records if item["event_id"] == "audit_legacy_1")

        assert legacy["workflow_name"] == "legacy_event"
        assert legacy["stage"] == "legacy_subject"
        assert legacy["decision"] == "legacy_unstructured"
        assert legacy["status"] == "legacy_unstructured"
        assert legacy["context_summary"] == "Legacy audit record without structured envelope."
        assert legacy["details"] == {"detail": "legacy"}
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)
