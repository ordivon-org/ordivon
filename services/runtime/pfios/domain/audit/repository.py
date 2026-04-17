from sqlalchemy.orm import Session

from pfios.domain.audit.models import AuditEvent
from pfios.domain.audit.orm import AuditEventORM
from pfios.core.utils.serialization import to_json_text, from_json_text


class AuditEventRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def create(self, event: AuditEvent) -> AuditEventORM:
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
        self.db.commit()
        self.db.refresh(row)
        return row

    def list_recent(self, limit: int = 100) -> list[AuditEventORM]:
        return (
            self.db.query(AuditEventORM)
            .order_by(AuditEventORM.created_at.desc())
            .limit(limit)
            .all()
        )

    def to_model(self, row: AuditEventORM) -> AuditEvent:
        return AuditEvent(
            id=row.id,
            event_type=row.event_type,
            entity_type=row.entity_type,
            entity_id=row.entity_id,
            analysis_id=row.analysis_id,
            recommendation_id=row.recommendation_id,
            outcome_snapshot_id=row.outcome_snapshot_id,
            review_id=row.review_id,
            payload=from_json_text(row.payload_json, {}),
            created_at=row.created_at.isoformat(),
        )
