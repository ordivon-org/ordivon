from __future__ import annotations

from datetime import datetime

from sqlalchemy.orm import Session

from domains.workflow_runs.models import WorkflowRun
from domains.workflow_runs.orm import WorkflowRunORM
from shared.utils.serialization import from_json_text, to_json_text


def _parse_dt(value: str | None) -> datetime | None:
    if not value:
        return None
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


class WorkflowRunRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def create(self, run: WorkflowRun) -> WorkflowRunORM:
        row = WorkflowRunORM(
            id=run.id,
            workflow_name=run.workflow_name,
            status=run.status,
            request_summary=run.request_summary,
            trigger=run.trigger,
            analysis_id=run.analysis_id,
            recommendation_id=run.recommendation_id,
            intelligence_run_id=run.intelligence_run_id,
            agent_action_id=run.agent_action_id,
            execution_request_id=run.execution_request_id,
            execution_receipt_id=run.execution_receipt_id,
            failed_step=run.failed_step,
            failure_reason=run.failure_reason,
            step_statuses_json=to_json_text(run.step_statuses),
            lineage_refs_json=to_json_text(run.lineage_refs),
            started_at=_parse_dt(run.started_at),
            completed_at=_parse_dt(run.completed_at),
        )
        self.db.add(row)
        self.db.flush()
        return row

    def get(self, run_id: str) -> WorkflowRunORM | None:
        return self.db.get(WorkflowRunORM, run_id)

    def upsert(self, run: WorkflowRun) -> WorkflowRunORM:
        row = self.get(run.id)
        if row is None:
            return self.create(run)
        row.workflow_name = run.workflow_name
        row.status = run.status
        row.request_summary = run.request_summary
        row.trigger = run.trigger
        row.analysis_id = run.analysis_id
        row.recommendation_id = run.recommendation_id
        row.intelligence_run_id = run.intelligence_run_id
        row.agent_action_id = run.agent_action_id
        row.execution_request_id = run.execution_request_id
        row.execution_receipt_id = run.execution_receipt_id
        row.failed_step = run.failed_step
        row.failure_reason = run.failure_reason
        row.step_statuses_json = to_json_text(run.step_statuses)
        row.lineage_refs_json = to_json_text(run.lineage_refs)
        row.started_at = _parse_dt(run.started_at)
        row.completed_at = _parse_dt(run.completed_at)
        self.db.flush()
        return row

    def to_model(self, row: WorkflowRunORM) -> WorkflowRun:
        return WorkflowRun(
            id=row.id,
            workflow_name=row.workflow_name,
            status=row.status,
            request_summary=row.request_summary,
            trigger=row.trigger,
            analysis_id=row.analysis_id,
            recommendation_id=row.recommendation_id,
            intelligence_run_id=row.intelligence_run_id,
            agent_action_id=row.agent_action_id,
            execution_request_id=row.execution_request_id,
            execution_receipt_id=row.execution_receipt_id,
            failed_step=row.failed_step,
            failure_reason=row.failure_reason,
            step_statuses=from_json_text(row.step_statuses_json, []),
            lineage_refs=from_json_text(row.lineage_refs_json, {}),
            started_at=row.started_at.isoformat(),
            completed_at=row.completed_at.isoformat() if row.completed_at else None,
        )
