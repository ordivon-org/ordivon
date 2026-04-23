from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class ReportResult:
    report_id: str
    symbol: str | None
    title: str | None
    status: str | None
    report_path: str | None
    created_at: str
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class DashboardResult:
    """Composite view aggregate, not a domain object."""

    recommendation_stats: dict[str, int]
    recent_outcomes: list[dict[str, Any]]
    pending_review_count: int
    system_health: str | None
    reasoning_provider: str | None = None
    runtime_status: str | None = None
    hermes_status: str | None = None
    last_agent_action: dict[str, Any] | None = None
    total_balance_estimate: float | None = None


@dataclass(slots=True)
class AuditEventResult:
    event_id: str
    workflow_name: str
    stage: str
    decision: str
    subject_id: str | None
    status: str
    context_summary: str
    details: dict[str, Any] = field(default_factory=dict)
    report_path: str | None = None
    created_at: str = ""
