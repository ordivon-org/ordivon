from dataclasses import dataclass, field
from typing import Any

from shared.utils.ids import new_id
from shared.enums.domain import OutcomeState
from shared.time.clock import utc_now

VALID_OUTCOME_SUBJECT_TYPES = {"recommendation", "review", "workflow_run", "task_run"}


@dataclass
class OutcomeSnapshot:
    id: str = field(default_factory=lambda: new_id("outcome"))
    recommendation_id: str = ""
    outcome_state: OutcomeState = OutcomeState.UNCHANGED
    observed_metrics: dict[str, Any] = field(default_factory=dict)
    evidence_refs: list[str] = field(default_factory=list)
    trigger_reason: str = ""
    note: str | None = None
    subject_type: str = "recommendation"
    source_of_truth: str = "derived_outcome_observation"
    observed_at: str = field(default_factory=lambda: utc_now().isoformat())

    def __post_init__(self) -> None:
        if not self.recommendation_id:
            raise ValueError("OutcomeSnapshot requires recommendation_id.")
        if self.subject_type not in VALID_OUTCOME_SUBJECT_TYPES:
            raise ValueError(f"Unsupported outcome subject_type: {self.subject_type}")
        if not self.trigger_reason:
            raise ValueError("OutcomeSnapshot requires trigger_reason.")

    @property
    def subject_id(self) -> str:
        return self.recommendation_id
