from __future__ import annotations

from datetime import datetime

from sqlalchemy.orm import Session

from governance_engine.approval import ApprovalRecord
from governance_engine.approval_orm import ApprovalRecordORM


def _parse_dt(value: str | None) -> datetime | None:
    if not value:
        return None
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


class ApprovalRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def create(self, approval: ApprovalRecord) -> ApprovalRecordORM:
        row = ApprovalRecordORM(
            id=approval.id,
            action_key=approval.action_key,
            entity_type=approval.entity_type,
            entity_id=approval.entity_id,
            status=approval.status,
            requested_by=approval.requested_by,
            reason=approval.reason,
            note=approval.note,
            decided_by=approval.decided_by,
            decided_note=approval.decided_note,
            created_at=_parse_dt(approval.created_at),
            decided_at=_parse_dt(approval.decided_at),
        )
        self.db.add(row)
        self.db.flush()
        return row

    def get(self, approval_id: str) -> ApprovalRecordORM | None:
        return self.db.get(ApprovalRecordORM, approval_id)

    def latest_for_action(self, action_key: str, *, entity_type: str, entity_id: str) -> ApprovalRecordORM | None:
        return (
            self.db.query(ApprovalRecordORM)
            .filter(
                ApprovalRecordORM.action_key == action_key,
                ApprovalRecordORM.entity_type == entity_type,
                ApprovalRecordORM.entity_id == entity_id,
            )
            .order_by(ApprovalRecordORM.created_at.desc())
            .first()
        )

    def update_decision(
        self,
        approval_id: str,
        *,
        status: str,
        decided_by: str,
        decided_note: str | None = None,
    ) -> ApprovalRecordORM | None:
        row = self.get(approval_id)
        if row is None:
            return None
        row.status = status
        row.decided_by = decided_by
        row.decided_note = decided_note
        row.decided_at = datetime.utcnow()
        self.db.flush()
        return row

    def to_model(self, row: ApprovalRecordORM) -> ApprovalRecord:
        return ApprovalRecord(
            id=row.id,
            action_key=row.action_key,
            entity_type=row.entity_type,
            entity_id=row.entity_id,
            status=row.status,
            requested_by=row.requested_by,
            reason=row.reason,
            note=row.note,
            decided_by=row.decided_by,
            decided_note=row.decided_note,
            created_at=row.created_at.isoformat(),
            decided_at=row.decided_at.isoformat() if row.decided_at else None,
        )
