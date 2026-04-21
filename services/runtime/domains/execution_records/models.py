from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from shared.time.clock import utc_now
from shared.utils.ids import new_id


@dataclass
class ExecutionRequest:
    id: str = field(default_factory=lambda: new_id("exreq"))
    action_id: str = ""
    family: str = ""
    side_effect_level: str = ""
    status: str = "pending"
    actor: str = ""
    context: str = ""
    reason: str = ""
    idempotency_key: str = ""
    entity_type: str | None = None
    entity_id: str | None = None
    analysis_id: str | None = None
    recommendation_id: str | None = None
    payload: dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=lambda: utc_now().isoformat())


@dataclass
class ExecutionReceipt:
    id: str = field(default_factory=lambda: new_id("exrcpt"))
    request_id: str = ""
    action_id: str = ""
    status: str = "succeeded"
    result_ref: str | None = None
    external_reference: str | None = None
    detail: dict[str, Any] = field(default_factory=dict)
    error: str | None = None
    created_at: str = field(default_factory=lambda: utc_now().isoformat())
