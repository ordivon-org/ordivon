from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from shared.time.clock import utc_now
from shared.utils.ids import new_id


@dataclass
class WorkflowRun:
    id: str = field(default_factory=lambda: new_id("wfrun"))
    workflow_name: str = ""
    status: str = "pending"
    request_summary: str = ""
    trigger: str = "api"
    analysis_id: str | None = None
    recommendation_id: str | None = None
    intelligence_run_id: str | None = None
    agent_action_id: str | None = None
    execution_request_id: str | None = None
    execution_receipt_id: str | None = None
    failed_step: str | None = None
    failure_reason: str | None = None
    step_statuses: list[dict[str, Any]] = field(default_factory=list)
    lineage_refs: dict[str, Any] = field(default_factory=dict)
    started_at: str = field(default_factory=lambda: utc_now().isoformat())
    completed_at: str | None = None
