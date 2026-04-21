from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class TraceReference:
    object_type: str
    object_id: str | None
    status: str
    relation_source: str
    detail: dict[str, Any] = field(default_factory=dict)


@dataclass
class TraceBundle:
    root_type: str
    root_id: str
    analysis: TraceReference
    recommendation: TraceReference
    review: TraceReference
    workflow_run: TraceReference
    intelligence_run: TraceReference
    agent_action: TraceReference
    execution_request: TraceReference
    execution_receipt: TraceReference
    review_execution_request: TraceReference
    review_execution_receipt: TraceReference
    latest_audit_events: list[TraceReference]
    report_artifact: TraceReference
    outcome: TraceReference
    knowledge_feedback: TraceReference
