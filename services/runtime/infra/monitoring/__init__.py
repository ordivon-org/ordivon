from __future__ import annotations

from dataclasses import dataclass
from datetime import timedelta

from sqlalchemy import func
from sqlalchemy.orm import Session

from domains.execution_records.orm import ExecutionReceiptORM
from domains.workflow_runs.orm import WorkflowRunORM
from governance_engine.audit.orm import AuditEventORM
from infra.monitoring.history import build_monitoring_history_summary
from infra.monitoring.models import MonitoringHistorySummary
from shared.observability import increment_counter, span
from shared.time.clock import utc_now


@dataclass(frozen=True, slots=True)
class MonitoringSnapshot:
    recent_failed_workflow_count: int
    recent_failed_execution_count: int
    last_workflow_at: str | None
    last_audit_at: str | None
    monitoring_status: str
    monitoring_window_hours: int
    history: MonitoringHistorySummary | None = None


class MonitoringService:
    def __init__(self, db: Session, *, window_hours: int = 24) -> None:
        self.db = db
        self.window_hours = window_hours

    def get_snapshot(self) -> MonitoringSnapshot:
        with span("monitoring.snapshot", attributes={"monitoring.window_hours": self.window_hours}):
            cutoff = utc_now() - timedelta(hours=self.window_hours)

            failed_workflows = (
                self.db.query(func.count(WorkflowRunORM.id))
                .filter(
                    WorkflowRunORM.status == "failed",
                    WorkflowRunORM.started_at >= cutoff,
                )
                .scalar()
            ) or 0

            failed_executions = (
                self.db.query(func.count(ExecutionReceiptORM.id))
                .filter(
                    ExecutionReceiptORM.status == "failed",
                    ExecutionReceiptORM.created_at >= cutoff,
                )
                .scalar()
            ) or 0

            last_workflow_at = self.db.query(func.max(WorkflowRunORM.started_at)).scalar()
            last_audit_at = self.db.query(func.max(AuditEventORM.created_at)).scalar()

            monitoring_status = "attention" if failed_workflows or failed_executions else "nominal"
            increment_counter(
                "health_snapshot_total",
                attributes={"monitoring_status": monitoring_status},
            )

            return MonitoringSnapshot(
                recent_failed_workflow_count=int(failed_workflows),
                recent_failed_execution_count=int(failed_executions),
                last_workflow_at=last_workflow_at.isoformat() if last_workflow_at else None,
                last_audit_at=last_audit_at.isoformat() if last_audit_at else None,
                monitoring_status=monitoring_status,
                monitoring_window_hours=self.window_hours,
                history=build_monitoring_history_summary(self.db, window_hours=self.window_hours),
            )


__all__ = ["MonitoringService", "MonitoringSnapshot", "MonitoringHistorySummary"]
