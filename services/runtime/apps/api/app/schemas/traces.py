from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class TraceReferenceResponse(BaseModel):
    object_type: str
    object_id: str | None = None
    status: str
    relation_source: str
    detail: dict[str, Any] = Field(default_factory=dict)


class TraceBundleResponse(BaseModel):
    root_type: str
    root_id: str
    analysis: TraceReferenceResponse
    recommendation: TraceReferenceResponse
    review: TraceReferenceResponse
    workflow_run: TraceReferenceResponse
    intelligence_run: TraceReferenceResponse
    agent_action: TraceReferenceResponse
    execution_request: TraceReferenceResponse
    execution_receipt: TraceReferenceResponse
    review_execution_request: TraceReferenceResponse
    review_execution_receipt: TraceReferenceResponse
    latest_audit_events: list[TraceReferenceResponse]
    report_artifact: TraceReferenceResponse
    outcome: TraceReferenceResponse
    knowledge_feedback: TraceReferenceResponse
