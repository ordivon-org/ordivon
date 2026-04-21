from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from shared.time.clock import utc_now
from shared.utils.ids import new_id


@dataclass
class IntelligenceRun:
    id: str = field(default_factory=lambda: new_id("irun"))
    task_type: str = ""
    actor_runtime: str = "hermes"
    provider: str | None = None
    model: str | None = None
    task_id: str = ""
    trace_id: str | None = None
    idempotency_key: str = ""
    status: str = "pending"
    reason: str = ""
    actor: str = ""
    context: str = ""
    input_summary: str = ""
    request_payload: dict[str, Any] = field(default_factory=dict)
    lineage_refs: dict[str, Any] = field(default_factory=dict)
    output_summary: str = ""
    error: str | None = None
    started_at: str | None = None
    completed_at: str | None = None
    created_at: str = field(default_factory=lambda: utc_now().isoformat())
