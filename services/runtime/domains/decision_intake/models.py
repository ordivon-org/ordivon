from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from shared.time.clock import utc_now
from shared.utils.ids import new_id

VALID_DECISION_INTAKE_STATUSES = {"draft", "validated", "invalid"}
VALID_DECISION_INTAKE_GOVERNANCE_STATUSES = {"not_started", "execute", "escalate", "reject"}


@dataclass(slots=True)
class DecisionIntake:
    id: str = field(default_factory=lambda: new_id("intake"))
    pack_id: str = ""
    intake_type: str = ""
    status: str = "draft"
    payload: dict[str, Any] = field(default_factory=dict)
    validation_errors: list[dict[str, str]] = field(default_factory=list)
    governance_status: str = "not_started"
    created_at: str = field(default_factory=lambda: utc_now().isoformat())

    def __post_init__(self) -> None:
        if not self.pack_id:
            raise ValueError("DecisionIntake requires pack_id.")
        if not self.intake_type:
            raise ValueError("DecisionIntake requires intake_type.")
        if self.status not in VALID_DECISION_INTAKE_STATUSES:
            raise ValueError(f"Unsupported decision intake status: {self.status}")
        if self.governance_status not in VALID_DECISION_INTAKE_GOVERNANCE_STATUSES:
            raise ValueError(f"Unsupported decision intake governance status: {self.governance_status}")
