from __future__ import annotations

from sqlalchemy.orm import Session

from infra.scheduler.models import ScheduledTrigger
from infra.scheduler.orm import ScheduledTriggerORM
from shared.utils.serialization import from_json_text, to_json_text


class SchedulerRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def upsert(self, trigger: ScheduledTrigger) -> ScheduledTriggerORM:
        row = self.db.get(ScheduledTriggerORM, trigger.id)
        if row is None:
            row = ScheduledTriggerORM(id=trigger.id)
            self.db.add(row)
        row.trigger_type = trigger.trigger_type
        row.cron_or_interval = trigger.cron_or_interval
        row.target_capability = trigger.target_capability
        row.payload_json = to_json_text(dict(trigger.payload))
        row.is_enabled = trigger.is_enabled
        row.last_dispatched_at = trigger.last_dispatched_at
        row.dispatch_count = trigger.dispatch_count
        self.db.flush()
        return row

    def list_all(self) -> list[ScheduledTriggerORM]:
        return self.db.query(ScheduledTriggerORM).order_by(ScheduledTriggerORM.created_at.asc()).all()

    def to_model(self, row: ScheduledTriggerORM) -> ScheduledTrigger:
        return ScheduledTrigger(
            id=row.id,
            trigger_type=row.trigger_type,
            cron_or_interval=row.cron_or_interval,
            target_capability=row.target_capability,
            payload=dict(from_json_text(row.payload_json, {})),
            is_enabled=row.is_enabled,
            last_dispatched_at=row.last_dispatched_at,
            dispatch_count=row.dispatch_count,
        )
