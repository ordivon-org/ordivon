from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class BlockedRunSummary:
    run_id: str
    blocked_reason: str


@dataclass(frozen=True, slots=True)
class SchedulerTriggerHealthSummary:
    total_trigger_count: int
    enabled_trigger_count: int
    disabled_trigger_count: int
    dispatched_trigger_count: int


@dataclass(frozen=True, slots=True)
class MonitoringHistorySummary:
    workflow_failures_by_type: dict[str, int]
    execution_failures_by_family: dict[str, int]
    stale_or_blocked_run_count: int
    approval_blocked_count: int
    blocked_reason_counts: dict[str, int]
    recovery_action_counts: dict[str, int]
    top_workflow_failure_type: str | None = None
    top_execution_failure_family: str | None = None
    blocked_run_ids: tuple[str, ...] = ()
    recent_workflow_failures: tuple[dict[str, str], ...] = ()
    recent_execution_failures: tuple[dict[str, str], ...] = ()
    blocked_runs: tuple[BlockedRunSummary, ...] = ()
    approval_blocked_run_ids: tuple[str, ...] = ()
    scheduler: SchedulerTriggerHealthSummary | None = None
