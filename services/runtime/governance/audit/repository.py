from sqlalchemy.orm import Session

from governance.audit.builders import normalize_audit_event, structured_payload_or_legacy
from governance.audit.models import AuditEvent
from governance.audit.orm import AuditEventORM
from shared.utils.serialization import from_json_text, to_json_text


class AuditEventRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def create(self, event: AuditEvent) -> AuditEventORM:
        event = normalize_audit_event(event)
        row = AuditEventORM(
            id=event.id,
            event_type=event.event_type,
            entity_type=event.entity_type,
            entity_id=event.entity_id,
            analysis_id=event.analysis_id,
            recommendation_id=event.recommendation_id,
            outcome_snapshot_id=event.outcome_snapshot_id,
            review_id=event.review_id,
            payload_json=to_json_text(event.payload),
        )
        self.db.add(row)
        self.db.flush()
        return row

    def list_recent(self, limit: int = 100) -> list[AuditEventORM]:
        return (
            self.db.query(AuditEventORM)
            .order_by(AuditEventORM.created_at.desc())
            .limit(limit)
            .all()
        )

    def list_for_review(self, review_id: str) -> list[AuditEventORM]:
        return (
            self.db.query(AuditEventORM)
            .filter(AuditEventORM.review_id == review_id)
            .order_by(AuditEventORM.created_at.desc())
            .all()
        )

    def to_model(self, row: AuditEventORM) -> AuditEvent:
        parsed_payload = from_json_text(row.payload_json, {})
        structured = structured_payload_or_legacy(
            event_type=row.event_type,
            entity_type=row.entity_type,
            entity_id=row.entity_id,
            payload_json=row.payload_json,
            parsed_payload=parsed_payload,
        )
        return AuditEvent(
            id=row.id,
            event_type=row.event_type,
            entity_type=row.entity_type,
            entity_id=row.entity_id,
            analysis_id=row.analysis_id,
            recommendation_id=row.recommendation_id,
            outcome_snapshot_id=row.outcome_snapshot_id,
            review_id=row.review_id,
            payload=structured.to_payload(),
            created_at=row.created_at.isoformat(),
        )
