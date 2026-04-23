from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from apps.api.app.schemas.common import BlockedRunResponse, HealthHistoryResponse, SchedulerTriggerHealthResponse, StatusResponse
from apps.api.app.deps import get_db
from adapters.runtimes.factory import resolve_runtime
from infra.monitoring import MonitoringService
from shared.config.settings import settings
from shared.observability import span

router = APIRouter()

@router.get("/health", response_model=StatusResponse)
async def health_check(db: Session = Depends(get_db)):
    with span("api.health"):
        runtime_status = None
        runtime_detail = None
        runtime_base_url = None
        hermes_status = None
        hermes_detail = None
        runtime_provider = None
        runtime_model = None
        monitoring_status = None
        monitoring_detail = None
        monitoring_window_hours = None
        recent_failed_workflow_count = None
        recent_failed_execution_count = None
        last_workflow_at = None
        last_audit_at = None
        workflow_failures_by_type = None
        execution_failures_by_family = None
        stale_or_blocked_run_count = None
        approval_blocked_count = None
        top_workflow_failure_type = None
        top_execution_failure_family = None
        blocked_run_ids = None

        try:
            health = resolve_runtime().health()
            runtime_status = health.get("status", "ok")
            runtime_detail = health.get("detail")
            runtime_base_url = health.get("base_url")
            runtime_provider = health.get("provider")
            runtime_model = health.get("model")
            if settings.reasoning_provider == "hermes":
                hermes_status = runtime_status
                hermes_detail = runtime_detail
        except Exception:
            runtime_status = "unavailable"
            runtime_detail = f"{settings.reasoning_provider} runtime health check failed unexpectedly."
            if settings.reasoning_provider == "hermes":
                hermes_status = "unavailable"
                hermes_detail = "Hermes health check failed unexpectedly."

        try:
            snapshot = MonitoringService(db).get_snapshot()
            monitoring_status = snapshot.monitoring_status
            monitoring_window_hours = snapshot.monitoring_window_hours
            recent_failed_workflow_count = snapshot.recent_failed_workflow_count
            recent_failed_execution_count = snapshot.recent_failed_execution_count
            last_workflow_at = snapshot.last_workflow_at
            last_audit_at = snapshot.last_audit_at
            if snapshot.history is not None:
                workflow_failures_by_type = snapshot.history.workflow_failures_by_type
                execution_failures_by_family = snapshot.history.execution_failures_by_family
                stale_or_blocked_run_count = snapshot.history.stale_or_blocked_run_count
                approval_blocked_count = snapshot.history.approval_blocked_count
                top_workflow_failure_type = snapshot.history.top_workflow_failure_type
                top_execution_failure_family = snapshot.history.top_execution_failure_family
                blocked_run_ids = list(snapshot.history.blocked_run_ids)
        except Exception:
            monitoring_status = "unavailable"
            monitoring_detail = "Monitoring snapshot could not be confirmed."

        return StatusResponse(
            status=(
                "degraded"
                if runtime_status == "unavailable"
                or monitoring_status == "unavailable"
                else "ok"
            ),
            reasoning_provider=settings.reasoning_provider,
            runtime_status=runtime_status,
            runtime_detail=runtime_detail,
            runtime_base_url=runtime_base_url or (settings.hermes_base_url if settings.reasoning_provider == "hermes" else None),
            hermes_status=hermes_status,
            hermes_detail=hermes_detail,
            hermes_base_url=settings.hermes_base_url if settings.reasoning_provider == "hermes" else None,
            runtime_provider=runtime_provider,
            runtime_model=runtime_model,
            monitoring_status=monitoring_status,
            monitoring_detail=monitoring_detail,
            monitoring_window_hours=monitoring_window_hours,
            recent_failed_workflow_count=recent_failed_workflow_count,
            recent_failed_execution_count=recent_failed_execution_count,
            last_workflow_at=last_workflow_at,
            last_audit_at=last_audit_at,
            workflow_failures_by_type=workflow_failures_by_type,
            execution_failures_by_family=execution_failures_by_family,
            stale_or_blocked_run_count=stale_or_blocked_run_count,
            approval_blocked_count=approval_blocked_count,
            top_workflow_failure_type=top_workflow_failure_type,
            top_execution_failure_family=top_execution_failure_family,
            blocked_run_ids=blocked_run_ids,
        )


@router.get("/health/history", response_model=HealthHistoryResponse)
async def health_history(db: Session = Depends(get_db)):
    with span("api.health_history"):
        summary = MonitoringService(db).get_snapshot().history
        if summary is None:
            return HealthHistoryResponse(
                workflow_failures_by_type={},
                execution_failures_by_family={},
                stale_or_blocked_run_count=0,
                approval_blocked_count=0,
                blocked_reason_counts={},
                recovery_action_counts={},
                blocked_run_ids=[],
                recent_workflow_failures=[],
                recent_execution_failures=[],
                blocked_runs=[],
                approval_blocked_run_ids=[],
                scheduler=SchedulerTriggerHealthResponse(
                    total_trigger_count=0,
                    enabled_trigger_count=0,
                    disabled_trigger_count=0,
                    dispatched_trigger_count=0,
                ),
            )
        return HealthHistoryResponse(
            workflow_failures_by_type=summary.workflow_failures_by_type,
            execution_failures_by_family=summary.execution_failures_by_family,
            stale_or_blocked_run_count=summary.stale_or_blocked_run_count,
            approval_blocked_count=summary.approval_blocked_count,
            blocked_reason_counts=summary.blocked_reason_counts,
            recovery_action_counts=summary.recovery_action_counts,
            top_workflow_failure_type=summary.top_workflow_failure_type,
            top_execution_failure_family=summary.top_execution_failure_family,
            blocked_run_ids=list(summary.blocked_run_ids),
            recent_workflow_failures=list(summary.recent_workflow_failures),
            recent_execution_failures=list(summary.recent_execution_failures),
            blocked_runs=[
                BlockedRunResponse(run_id=item.run_id, blocked_reason=item.blocked_reason)
                for item in summary.blocked_runs
            ],
            approval_blocked_run_ids=list(summary.approval_blocked_run_ids),
            scheduler=(
                SchedulerTriggerHealthResponse(
                    total_trigger_count=summary.scheduler.total_trigger_count,
                    enabled_trigger_count=summary.scheduler.enabled_trigger_count,
                    disabled_trigger_count=summary.scheduler.disabled_trigger_count,
                    dispatched_trigger_count=summary.scheduler.dispatched_trigger_count,
                )
                if summary.scheduler is not None
                else None
            ),
        )

@router.get("/version", response_model=StatusResponse)
async def get_version():
    return StatusResponse(status="ok", version="0.1.0", reasoning_provider=settings.reasoning_provider)
