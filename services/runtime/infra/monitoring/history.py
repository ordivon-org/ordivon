from __future__ import annotations

from datetime import timedelta

from sqlalchemy.orm import Session

from domains.execution_records.orm import ExecutionRequestORM
from domains.execution_records.orm import ExecutionReceiptORM
from domains.workflow_runs.orm import WorkflowRunORM
from infra.monitoring.models import MonitoringHistorySummary
from shared.time.clock import utc_now
from shared.utils.serialization import from_json_text


def build_monitoring_history_summary(db: Session, *, window_hours: int) -> MonitoringHistorySummary:
    cutoff = utc_now() - timedelta(hours=window_hours)
    workflow_rows = db.query(WorkflowRunORM).filter(WorkflowRunORM.started_at >= cutoff).all()
    execution_rows = db.query(ExecutionReceiptORM).filter(ExecutionReceiptORM.created_at >= cutoff).all()

    workflow_failures_by_type: dict[str, int] = {}
    stale_or_blocked_run_count = 0
    approval_blocked_count = 0
    blocked_run_ids: list[str] = []
    for row in workflow_rows:
        if row.status == "failed":
            key = row.failed_step or "workflow_failed"
            workflow_failures_by_type[key] = workflow_failures_by_type.get(key, 0) + 1
        lineage = from_json_text(row.lineage_refs_json, {})
        blocked_reason = lineage.get("blocked_reason")
        if blocked_reason:
            stale_or_blocked_run_count += 1
            blocked_run_ids.append(row.id)
            if "approval" in str(blocked_reason):
                approval_blocked_count += 1

    execution_failures_by_family: dict[str, int] = {}
    request_family_by_id = {
        row.id: row.family
        for row in db.query(ExecutionRequestORM).all()
    }
    for row in execution_rows:
        if row.status != "failed":
            continue
        family = request_family_by_id.get(row.request_id) or "unknown"
        execution_failures_by_family[family] = execution_failures_by_family.get(family, 0) + 1

    top_workflow_failure_type = None
    if workflow_failures_by_type:
        top_workflow_failure_type = max(workflow_failures_by_type.items(), key=lambda item: item[1])[0]

    top_execution_failure_family = None
    if execution_failures_by_family:
        top_execution_failure_family = max(execution_failures_by_family.items(), key=lambda item: item[1])[0]

    return MonitoringHistorySummary(
        workflow_failures_by_type=workflow_failures_by_type,
        execution_failures_by_family=execution_failures_by_family,
        stale_or_blocked_run_count=stale_or_blocked_run_count,
        approval_blocked_count=approval_blocked_count,
        top_workflow_failure_type=top_workflow_failure_type,
        top_execution_failure_family=top_execution_failure_family,
        blocked_run_ids=tuple(blocked_run_ids[:10]),
    )
