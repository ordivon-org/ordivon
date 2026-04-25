from __future__ import annotations

from sqlalchemy.orm import Session

from domains.decision_intake.models import DecisionIntake
from domains.decision_intake.orm import DecisionIntakeORM
from shared.utils.serialization import from_json_text, to_json_text


class DecisionIntakeRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def create(self, intake: DecisionIntake) -> DecisionIntakeORM:
        row = DecisionIntakeORM(
            id=intake.id,
            pack_id=intake.pack_id,
            intake_type=intake.intake_type,
            status=intake.status,
            payload_json=to_json_text(intake.payload),
            validation_errors_json=to_json_text(intake.validation_errors),
            governance_status=intake.governance_status,
        )
        self.db.add(row)
        self.db.flush()
        return row

    def get(self, intake_id: str) -> DecisionIntakeORM | None:
        return self.db.get(DecisionIntakeORM, intake_id)

    def list_recent(self, limit: int = 20) -> list[DecisionIntakeORM]:
        return (
            self.db.query(DecisionIntakeORM)
            .order_by(DecisionIntakeORM.created_at.desc())
            .limit(limit)
            .all()
        )

    def update_governance_status(self, intake_id: str, governance_status: str) -> DecisionIntakeORM | None:
        row = self.get(intake_id)
        if row:
            row.governance_status = governance_status
            self.db.flush()
        return row

    def to_model(self, row: DecisionIntakeORM) -> DecisionIntake:
        return DecisionIntake(
            id=row.id,
            pack_id=row.pack_id,
            intake_type=row.intake_type,
            status=row.status,
            payload=from_json_text(row.payload_json, {}),
            validation_errors=from_json_text(row.validation_errors_json, []),
            governance_status=row.governance_status,
            created_at=row.created_at.isoformat(),
        )
