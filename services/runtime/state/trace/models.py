from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


VALID_TRACE_LINK_STATUSES = {"present", "missing", "unlinked"}


@dataclass
class TraceLink:
    object_type: str
    object_id: str | None
    status: str
    relation_source: str
    detail: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.object_type:
            raise ValueError("TraceLink requires object_type.")
        if self.status not in VALID_TRACE_LINK_STATUSES:
            raise ValueError(f"Unsupported trace link status: {self.status}")
        if not self.relation_source:
            raise ValueError("TraceLink requires relation_source.")

    @property
    def is_resolved(self) -> bool:
        return self.status == "present"


TraceReference = TraceLink


@dataclass
class TraceBundle:
    root_type: str
    root_id: str
    analysis: TraceLink
    recommendation: TraceLink
    review: TraceLink
    workflow_run: TraceLink
    intelligence_run: TraceLink
    agent_action: TraceLink
    execution_request: TraceLink
    execution_receipt: TraceLink
    review_execution_request: TraceLink
    review_execution_receipt: TraceLink
    latest_audit_events: list[TraceLink]
    report_artifact: TraceLink
    outcome: TraceLink
    knowledge_feedback: TraceLink
