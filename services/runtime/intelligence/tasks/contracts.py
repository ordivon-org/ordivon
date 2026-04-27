from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any

from intelligence.runtime.hermes_client import HermesTaskError


def _require_str(value: Any, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise HermesTaskError(f"Malformed Hermes payload: {field_name} must be a non-empty string.")
    return value


def _require_optional_str(value: Any, field_name: str) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str):
        raise HermesTaskError(f"Malformed Hermes payload: {field_name} must be a string when present.")
    return value


def _require_str_list(value: Any, field_name: str) -> list[str]:
    if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
        raise HermesTaskError(f"Malformed Hermes payload: {field_name} must be a list of strings.")
    return value


def _require_dict(value: Any, field_name: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise HermesTaskError(f"Malformed Hermes payload: {field_name} must be an object.")
    return value


def _require_list_of_dicts(value: Any, field_name: str) -> list[dict[str, Any]]:
    if value is None:
        return []
    if not isinstance(value, list) or not all(isinstance(item, dict) for item in value):
        raise HermesTaskError(f"Malformed Hermes payload: {field_name} must be a list of objects.")
    return value


@dataclass
class AnalysisTaskInput:
    query: str
    symbol: str
    timeframe: str | None
    market_signals: dict[str, Any]
    memory_lessons: list[Any]
    related_reviews: list[Any]
    active_policies: list[Any]
    risk_mode: str | None
    portfolio_cash_balance: float | int | None
    portfolio_positions: list[dict[str, Any]]


@dataclass
class TaskContextRefs:
    provider: str
    model: str


@dataclass
class TaskLineage:
    query: str
    symbol: str
    timeframe: str | None


@dataclass
class TaskConstraints:
    must_return_fields: list[str]


@dataclass
class TaskExecutionPolicy:
    enable_delegation: bool
    enable_memory: bool
    enable_moa: bool


@dataclass
class IntelligenceTaskRequest:
    task_id: str
    idempotency_key: str
    trace_id: str
    input: AnalysisTaskInput
    context_refs: TaskContextRefs
    lineage: TaskLineage
    constraints: TaskConstraints
    execution_policy: TaskExecutionPolicy
    reason: str
    actor: str
    context: str

    def to_payload(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class IntelligenceTaskMetadata:
    provider: str = "hermes"
    runtime_provider: str | None = None
    runtime_model: str | None = None
    session_id: str | None = None
    task_id: str = ""
    task_type: str = ""
    trace_id: str | None = None
    hermes_status: str = "completed"


@dataclass
class IntelligenceAgentActionPayload:
    task_type: str
    provider: str | None
    model: str | None
    session_id: str | None
    status: str
    reason: str
    idempotency_key: str
    trace_id: str | None
    input_summary: str
    output_summary: str
    tool_trace: list[dict[str, Any]] = field(default_factory=list)
    memory_events: list[dict[str, Any]] = field(default_factory=list)
    delegation_trace: list[dict[str, Any]] = field(default_factory=list)
    usage: dict[str, Any] = field(default_factory=dict)
    error: str | None = None
    started_at: str | None = None
    completed_at: str | None = None


@dataclass
class AnalysisTaskResultBundle:
    summary: str
    thesis: str
    risks: list[str]
    suggested_actions: list[str]
    metadata: IntelligenceTaskMetadata
    agent_action: IntelligenceAgentActionPayload

    @classmethod
    def from_runtime_response(
        cls,
        request: IntelligenceTaskRequest,
        response: dict[str, Any],
    ) -> "AnalysisTaskResultBundle":
        response_obj = _require_dict(response, "response")
        output = _require_dict(response_obj.get("output"), "output")

        task_id = _require_str(response_obj.get("task_id"), "task_id")
        task_type = _require_str(response_obj.get("task_type"), "task_type")
        status = _require_str(response_obj.get("status"), "status")
        if status not in {"completed", "success"}:
            raise HermesTaskError(f"Malformed Hermes payload: unsupported status {status!r}.")

        summary = _require_str(output.get("summary"), "output.summary")
        thesis = _require_str(output.get("thesis"), "output.thesis")
        risks = _require_str_list(output.get("risks"), "output.risks")
        suggested_actions = _require_str_list(output.get("suggested_actions"), "output.suggested_actions")

        metadata = IntelligenceTaskMetadata(
            provider="hermes",
            runtime_provider=_require_optional_str(response_obj.get("provider"), "provider"),
            runtime_model=_require_optional_str(response_obj.get("model"), "model"),
            session_id=_require_optional_str(response_obj.get("session_id"), "session_id"),
            task_id=task_id,
            task_type=task_type,
            trace_id=_require_optional_str(response_obj.get("trace_id"), "trace_id"),
            hermes_status=status,
        )
        agent_action = IntelligenceAgentActionPayload(
            task_type=task_type,
            provider=metadata.runtime_provider,
            model=metadata.runtime_model,
            session_id=metadata.session_id,
            status=status,
            reason=_require_optional_str(response_obj.get("reason"), "reason") or request.reason,
            idempotency_key=_require_optional_str(response_obj.get("idempotency_key"), "idempotency_key")
            or request.idempotency_key,
            trace_id=metadata.trace_id or request.trace_id,
            input_summary=request.input.query,
            output_summary=summary,
            tool_trace=_require_list_of_dicts(response_obj.get("tool_trace"), "tool_trace"),
            memory_events=_require_list_of_dicts(response_obj.get("memory_events"), "memory_events"),
            delegation_trace=_require_list_of_dicts(response_obj.get("delegation_trace"), "delegation_trace"),
            usage=_require_dict(response_obj.get("usage") or {}, "usage"),
            error=_require_optional_str(response_obj.get("error"), "error"),
            started_at=_require_optional_str(response_obj.get("started_at"), "started_at"),
            completed_at=_require_optional_str(response_obj.get("completed_at"), "completed_at"),
        )
        return cls(
            summary=summary,
            thesis=thesis,
            risks=risks,
            suggested_actions=suggested_actions,
            metadata=metadata,
            agent_action=agent_action,
        )
