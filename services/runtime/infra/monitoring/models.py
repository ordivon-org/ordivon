from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class MonitoringHistorySummary:
    workflow_failures_by_type: dict[str, int]
    execution_failures_by_family: dict[str, int]
    stale_or_blocked_run_count: int
    approval_blocked_count: int
    top_workflow_failure_type: str | None = None
    top_execution_failure_family: str | None = None
    blocked_run_ids: tuple[str, ...] = ()
