from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from shared.time.clock import utc_now
from shared.utils.ids import new_id


@dataclass
class AgentAction:
    id: str = field(default_factory=lambda: new_id("act"))
    task_type: str = ""
    actor_type: str = "ai"
    actor_runtime: str = "hermes"
    provider: str | None = None
    model: str | None = None
    session_id: str | None = None
    status: str = "completed"
    reason: str = ""
    idempotency_key: str = ""
    trace_id: str | None = None
    input_summary: str = ""
    output_summary: str = ""
    input_refs: dict[str, Any] = field(default_factory=dict)
    output_refs: dict[str, Any] = field(default_factory=dict)
    tool_trace: list[dict[str, Any]] = field(default_factory=list)
    memory_events: list[dict[str, Any]] = field(default_factory=list)
    delegation_trace: list[dict[str, Any]] = field(default_factory=list)
    usage: dict[str, Any] = field(default_factory=dict)
    error: str | None = None
    started_at: str | None = None
    completed_at: str | None = None
    created_at: str = field(default_factory=lambda: utc_now().isoformat())
