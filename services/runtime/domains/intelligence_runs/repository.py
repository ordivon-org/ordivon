from __future__ import annotations

from datetime import datetime

from sqlalchemy.orm import Session

from domains.intelligence_runs.models import IntelligenceRun
from domains.intelligence_runs.orm import IntelligenceRunORM
from shared.utils.serialization import from_json_text, to_json_text


def _parse_dt(value: str | None) -> datetime | None:
    if not value:
        return None
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


class IntelligenceRunRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def create(self, run: IntelligenceRun) -> IntelligenceRunORM:
        row = IntelligenceRunORM(
            id=run.id,
            task_type=run.task_type,
            actor_runtime=run.actor_runtime,
            provider=run.provider,
            model=run.model,
            task_id=run.task_id,
            trace_id=run.trace_id,
            idempotency_key=run.idempotency_key,
            status=run.status,
            reason=run.reason,
            actor=run.actor,
            context=run.context,
            input_summary=run.input_summary,
            request_payload_json=to_json_text(run.request_payload),
            lineage_refs_json=to_json_text(run.lineage_refs),
            output_summary=run.output_summary,
            error=run.error,
            started_at=_parse_dt(run.started_at),
            completed_at=_parse_dt(run.completed_at),
        )
        self.db.add(row)
        self.db.flush()
        return row

    def get(self, run_id: str) -> IntelligenceRunORM | None:
        return self.db.get(IntelligenceRunORM, run_id)

    def get_by_task_id(self, task_id: str) -> IntelligenceRunORM | None:
        return self.db.query(IntelligenceRunORM).filter(IntelligenceRunORM.task_id == task_id).first()

    def list_recent(self, limit: int = 20) -> list[IntelligenceRunORM]:
        return self.db.query(IntelligenceRunORM).order_by(IntelligenceRunORM.created_at.desc()).limit(limit).all()

    def update_status(
        self,
        task_id: str,
        *,
        status: str,
        provider: str | None = None,
        model: str | None = None,
        output_summary: str | None = None,
        error: str | None = None,
        started_at: str | None = None,
        completed_at: str | None = None,
    ) -> IntelligenceRunORM | None:
        row = self.get_by_task_id(task_id)
        if row is None:
            return None
        row.status = status
        row.provider = provider or row.provider
        row.model = model or row.model
        if output_summary is not None:
            row.output_summary = output_summary
        row.error = error
        if started_at is not None:
            row.started_at = _parse_dt(started_at)
        if completed_at is not None:
            row.completed_at = _parse_dt(completed_at)
        self.db.flush()
        return row

    def to_model(self, row: IntelligenceRunORM) -> IntelligenceRun:
        return IntelligenceRun(
            id=row.id,
            task_type=row.task_type,
            actor_runtime=row.actor_runtime,
            provider=row.provider,
            model=row.model,
            task_id=row.task_id,
            trace_id=row.trace_id,
            idempotency_key=row.idempotency_key,
            status=row.status,
            reason=row.reason,
            actor=row.actor,
            context=row.context,
            input_summary=row.input_summary,
            request_payload=from_json_text(row.request_payload_json, {}),
            lineage_refs=from_json_text(row.lineage_refs_json, {}),
            output_summary=row.output_summary,
            error=row.error,
            started_at=row.started_at.isoformat() if row.started_at else None,
            completed_at=row.completed_at.isoformat() if row.completed_at else None,
            created_at=row.created_at.isoformat(),
        )
