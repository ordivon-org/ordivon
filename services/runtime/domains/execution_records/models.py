from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from shared.time.clock import utc_now
from shared.utils.ids import new_id

VALID_EXECUTION_REQUEST_STATUSES = {"pending", "blocked", "succeeded", "failed", "cancelled"}
VALID_EXECUTION_RECEIPT_STATUSES = {"pending", "succeeded", "failed"}
VALID_EXECUTION_PROGRESS_STATES = {"started", "heartbeat", "completed", "failed"}


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

    def __post_init__(self) -> None:
        if not self.action_id:
            raise ValueError("ExecutionRequest requires action_id.")
        if not self.family:
            raise ValueError("ExecutionRequest requires family.")
        if self.status not in VALID_EXECUTION_REQUEST_STATUSES:
            raise ValueError(f"Unsupported execution request status: {self.status}")
        if not self.actor:
            raise ValueError("ExecutionRequest requires actor.")
        if not self.context:
            raise ValueError("ExecutionRequest requires context.")
        if not self.idempotency_key:
            raise ValueError("ExecutionRequest requires idempotency_key.")

    @property
    def is_terminal(self) -> bool:
        return self.status in {"succeeded", "failed", "cancelled"}


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

    def __post_init__(self) -> None:
        if not self.request_id:
            raise ValueError("ExecutionReceipt requires request_id.")
        if not self.action_id:
            raise ValueError("ExecutionReceipt requires action_id.")
        if self.status not in VALID_EXECUTION_RECEIPT_STATUSES:
            raise ValueError(f"Unsupported execution receipt status: {self.status}")
        if self.status == "succeeded" and self.error is not None:
            raise ValueError("Succeeded execution receipt cannot carry error.")
        if self.status == "failed" and not self.error:
            raise ValueError("Failed execution receipt requires error.")

    @property
    def is_success(self) -> bool:
        return self.status == "succeeded"


@dataclass
class ExecutionProgressRecord:
    id: str = field(default_factory=lambda: new_id("exprg"))
    request_id: str = ""
    progress_state: str = "started"
    progress_message: str = ""
    heartbeat_at: str = field(default_factory=lambda: utc_now().isoformat())
    created_at: str = field(default_factory=lambda: utc_now().isoformat())

    def __post_init__(self) -> None:
        if not self.request_id:
            raise ValueError("ExecutionProgressRecord requires request_id.")
        if self.progress_state not in VALID_EXECUTION_PROGRESS_STATES:
            raise ValueError(f"Unsupported execution progress state: {self.progress_state}")
