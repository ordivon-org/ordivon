from sqlalchemy.orm import Session

from shared.utils.serialization import from_json_text, to_json_text
from state.usage.models import UsageSnapshot
from state.usage.orm import UsageSnapshotORM


class UsageSnapshotRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def create(self, snapshot: UsageSnapshot) -> UsageSnapshotORM:
        from datetime import datetime

        row = UsageSnapshotORM(
            id=snapshot.id,
            snapshot_date=datetime.fromisoformat(snapshot.created_at)
            if isinstance(snapshot.created_at, str)
            else snapshot.created_at,
            analyses_count=snapshot.analyses_count,
            recommendations_generated_count=snapshot.recommendations_generated_count,
            recommendations_adopted_count=snapshot.recommendations_adopted_count,
            recommendations_tracking_count=snapshot.recommendations_tracking_count,
            reviews_generated_count=snapshot.reviews_generated_count,
            reviews_completed_count=snapshot.reviews_completed_count,
            issues_opened_count=snapshot.issues_opened_count,
            metadata_json=to_json_text(snapshot.metadata),
        )
        self.db.add(row)
        self.db.flush()
        return row

    def list_recent(self, limit: int = 30) -> list[UsageSnapshotORM]:
        return self.db.query(UsageSnapshotORM).order_by(UsageSnapshotORM.snapshot_date.desc()).limit(limit).all()

    def to_model(self, row: UsageSnapshotORM) -> UsageSnapshot:
        return UsageSnapshot(
            id=row.id,
            snapshot_date=row.snapshot_date.isoformat(),
            analyses_count=row.analyses_count,
            recommendations_generated_count=row.recommendations_generated_count,
            recommendations_adopted_count=row.recommendations_adopted_count,
            recommendations_tracking_count=row.recommendations_tracking_count,
            reviews_generated_count=row.reviews_generated_count,
            reviews_completed_count=row.reviews_completed_count,
            issues_opened_count=row.issues_opened_count,
            metadata=from_json_text(row.metadata_json, {}),
            created_at=row.created_at.isoformat(),
        )
