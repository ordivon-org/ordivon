from dataclasses import dataclass, field
from typing import Any

from shared.utils.ids import new_id
from shared.enums.domain import OutcomeState
from shared.time.clock import utc_now


@dataclass
class OutcomeSnapshot:
    id: str = field(default_factory=lambda: new_id("outcome"))
    recommendation_id: str = ""
    outcome_state: OutcomeState = OutcomeState.UNCHANGED
    observed_metrics: dict[str, Any] = field(default_factory=dict)
    evidence_refs: list[str] = field(default_factory=list)
    trigger_reason: str = ""
    note: str | None = None
    observed_at: str = field(default_factory=lambda: utc_now().isoformat())
