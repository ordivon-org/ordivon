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

    @property
    def blocked_reason(self) -> str | None:
        value = self.lineage_refs.get("blocked_reason")
        return str(value) if value else None

    @property
    def wake_reason(self) -> str | None:
        value = self.lineage_refs.get("wake_reason")
        return str(value) if value else None

    @property
    def resume_marker(self) -> str | None:
        value = self.lineage_refs.get("resume_marker")
        return str(value) if value else None

    @property
    def handoff_artifact_ref(self) -> str | None:
        value = self.lineage_refs.get("handoff_artifact_ref")
        return str(value) if value else None

    @property
    def resume_from_ref(self) -> str | None:
        value = self.lineage_refs.get("resume_from_ref")
        return str(value) if value else None

    @property
    def resume_reason(self) -> str | None:
        value = self.lineage_refs.get("resume_reason")
        return str(value) if value else None

    @property
    def resume_count(self) -> int:
        value = self.lineage_refs.get("resume_count")
        if value is None:
            return 0
        try:
            return int(value)
        except (TypeError, ValueError):
            return 0
