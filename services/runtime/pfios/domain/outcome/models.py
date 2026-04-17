from dataclasses import dataclass, field
from typing import Any

from pfios.core.utils.ids import new_id
from pfios.core.utils.time import utc_now
from pfios.domain.common.enums import OutcomeState


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
