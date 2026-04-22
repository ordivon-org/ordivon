from pydantic import BaseModel
from typing import Any

class BaseResponse(BaseModel):
    status: str = "success"
    message: str | None = None


class ActionContextInput(BaseModel):
    actor: str
    context: str
    reason: str
    idempotency_key: str

class StatusResponse(BaseModel):
    status: str
    system: str = "PFIOS"
    version: str = "0.1.0"
    reasoning_provider: str | None = None
    hermes_status: str | None = None
    hermes_detail: str | None = None
    hermes_base_url: str | None = None
    runtime_provider: str | None = None
    runtime_model: str | None = None
    monitoring_status: str | None = None
    monitoring_detail: str | None = None
    monitoring_window_hours: int | None = None
    recent_failed_workflow_count: int | None = None
    recent_failed_execution_count: int | None = None
    last_workflow_at: str | None = None
    last_audit_at: str | None = None
    workflow_failures_by_type: dict[str, int] | None = None
    execution_failures_by_family: dict[str, int] | None = None
    stale_or_blocked_run_count: int | None = None
    approval_blocked_count: int | None = None
    top_workflow_failure_type: str | None = None
    top_execution_failure_family: str | None = None
    blocked_run_ids: list[str] | None = None


class AgentActionSummaryResponse(BaseModel):
    id: str
    task_type: str
    status: str
    actor_runtime: str
    provider: str | None = None
    model: str | None = None
    reason: str
    idempotency_key: str
    trace_id: str | None = None
    input_summary: str
    output_summary: str
    input_refs: dict[str, Any]
    output_refs: dict[str, Any]
    usage: dict[str, Any]
    error: str | None = None
    started_at: str | None = None
    completed_at: str | None = None
    created_at: str

class ErrorResponse(BaseModel):
    status: str = "error"
    detail: str
