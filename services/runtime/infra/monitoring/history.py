from __future__ import annotations

from datetime import timedelta

from sqlalchemy.orm import Session

from domains.execution_records.orm import ExecutionRequestORM
from domains.execution_records.orm import ExecutionReceiptORM
from domains.workflow_runs.orm import WorkflowRunORM
from infra.monitoring.models import BlockedRunSummary, MonitoringHistorySummary, SchedulerTriggerHealthSummary
from infra.scheduler.repository import SchedulerRepository
from shared.time.clock import utc_now
from shared.utils.serialization import from_json_text


def build_monitoring_history_summary(db: Session, *, window_hours: int) -> MonitoringHistorySummary:
    cutoff = utc_now() - timedelta(hours=window_hours)
    workflow_rows = db.query(WorkflowRunORM).filter(WorkflowRunORM.started_at >= cutoff).all()
    execution_rows = db.query(ExecutionReceiptORM).filter(ExecutionReceiptORM.created_at >= cutoff).all()

    workflow_failures_by_type: dict[str, int] = {}
    blocked_reason_counts: dict[str, int] = {}
    recovery_action_counts: dict[str, int] = {}
    stale_or_blocked_run_count = 0
    approval_blocked_count = 0
    blocked_run_ids: list[str] = []
    blocked_runs: list[BlockedRunSummary] = []
    approval_blocked_run_ids: list[str] = []
    recent_workflow_failures: list[dict[str, str]] = []
    for row in workflow_rows:
        if row.status == "failed":
            key = row.failed_step or "workflow_failed"
            workflow_failures_by_type[key] = workflow_failures_by_type.get(key, 0) + 1
            recent_workflow_failures.append(
                {
                    "run_id": row.id,
                    "workflow_name": row.workflow_name,
                    "failure_type": key,
                }
            )
        lineage = from_json_text(row.lineage_refs_json, {})
        blocked_reason = lineage.get("blocked_reason")
        if blocked_reason:
            stale_or_blocked_run_count += 1
            reason_key = str(blocked_reason)
            blocked_reason_counts[reason_key] = blocked_reason_counts.get(reason_key, 0) + 1
            blocked_run_ids.append(row.id)
            blocked_runs.append(BlockedRunSummary(run_id=row.id, blocked_reason=reason_key))
            if "approval" in reason_key:
                approval_blocked_count += 1
                approval_blocked_run_ids.append(row.id)
        for step in from_json_text(row.step_statuses_json, []):
            if not isinstance(step, dict):
                continue
            action = step.get("recovery_action")
            if isinstance(action, str) and action:
                recovery_action_counts[action] = recovery_action_counts.get(action, 0) + 1

    execution_failures_by_family: dict[str, int] = {}
    request_family_by_id = {
        row.id: row.family
        for row in db.query(ExecutionRequestORM).all()
    }
    recent_execution_failures: list[dict[str, str]] = []
    for row in execution_rows:
        if row.status != "failed":
            continue
        family = request_family_by_id.get(row.request_id) or "unknown"
        execution_failures_by_family[family] = execution_failures_by_family.get(family, 0) + 1
        recent_execution_failures.append(
            {
                "receipt_id": row.id,
                "request_id": row.request_id,
                "family": family,
            }
        )

    top_workflow_failure_type = None
    if workflow_failures_by_type:
        top_workflow_failure_type = max(workflow_failures_by_type.items(), key=lambda item: item[1])[0]

    top_execution_failure_family = None
    if execution_failures_by_family:
        top_execution_failure_family = max(execution_failures_by_family.items(), key=lambda item: item[1])[0]

    scheduler_rows = SchedulerRepository(db).list_all()
    scheduler_summary = SchedulerTriggerHealthSummary(
        total_trigger_count=len(scheduler_rows),
        enabled_trigger_count=sum(1 for row in scheduler_rows if row.is_enabled),
        disabled_trigger_count=sum(1 for row in scheduler_rows if not row.is_enabled),
        dispatched_trigger_count=sum(1 for row in scheduler_rows if row.dispatch_count > 0),
    )

    return MonitoringHistorySummary(
        workflow_failures_by_type=workflow_failures_by_type,
        execution_failures_by_family=execution_failures_by_family,
        stale_or_blocked_run_count=stale_or_blocked_run_count,
        approval_blocked_count=approval_blocked_count,
        blocked_reason_counts=blocked_reason_counts,
        recovery_action_counts=recovery_action_counts,
        top_workflow_failure_type=top_workflow_failure_type,
        top_execution_failure_family=top_execution_failure_family,
        blocked_run_ids=tuple(blocked_run_ids[:10]),
        recent_workflow_failures=tuple(recent_workflow_failures[:10]),
        recent_execution_failures=tuple(recent_execution_failures[:10]),
        blocked_runs=tuple(blocked_runs[:10]),
        approval_blocked_run_ids=tuple(approval_blocked_run_ids[:10]),
        scheduler=scheduler_summary,
    )
