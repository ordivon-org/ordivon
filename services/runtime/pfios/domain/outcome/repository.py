from sqlalchemy.orm import Session

from pfios.domain.outcome.models import OutcomeSnapshot
from pfios.domain.outcome.orm import OutcomeSnapshotORM
from pfios.domain.common.enums import OutcomeState
from pfios.core.utils.serialization import to_json_text, from_json_text


class OutcomeRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def create(self, outcome: OutcomeSnapshot) -> OutcomeSnapshotORM:
        row = OutcomeSnapshotORM(
            id=outcome.id,
            recommendation_id=outcome.recommendation_id,
            outcome_state=outcome.outcome_state.value,
            observed_metrics_json=to_json_text(outcome.observed_metrics),
            evidence_refs_json=to_json_text(outcome.evidence_refs),
            trigger_reason=outcome.trigger_reason,
            note=outcome.note,
        )
        self.db.add(row)
        self.db.commit()
        self.db.refresh(row)
        return row

    def list_for_recommendation(self, recommendation_id: str) -> list[OutcomeSnapshotORM]:
        return (
            self.db.query(OutcomeSnapshotORM)
            .filter(OutcomeSnapshotORM.recommendation_id == recommendation_id)
            .order_by(OutcomeSnapshotORM.observed_at.desc())
            .all()
        )

    def to_model(self, row: OutcomeSnapshotORM) -> OutcomeSnapshot:
        return OutcomeSnapshot(
            id=row.id,
            recommendation_id=row.recommendation_id,
            outcome_state=OutcomeState(row.outcome_state),
            observed_metrics=from_json_text(row.observed_metrics_json, {}),
            evidence_refs=from_json_text(row.evidence_refs_json, []),
            trigger_reason=row.trigger_reason,
            note=row.note,
            observed_at=row.observed_at.isoformat(),
        )
