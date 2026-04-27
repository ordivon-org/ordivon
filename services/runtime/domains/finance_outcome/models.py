from dataclasses import dataclass, field

from shared.utils.ids import new_id
from shared.time.clock import utc_now

VALID_OUTCOME_SOURCES = {"manual"}
VALID_OUTCOME_VERDICTS = {
    "validated",
    "partially_validated",
    "invalidated",
    "inconclusive",
}


@dataclass
class FinanceManualOutcome:
    id: str = field(default_factory=lambda: new_id("fmout"))
    decision_intake_id: str = ""
    execution_receipt_id: str = ""
    outcome_source: str = "manual"
    observed_outcome: str = ""
    verdict: str = ""
    variance_summary: str | None = None
    plan_followed: bool = False
    created_at: str = field(default_factory=lambda: utc_now().isoformat())

    def __post_init__(self) -> None:
        if not self.decision_intake_id:
            raise ValueError("FinanceManualOutcome requires decision_intake_id.")
        if not self.execution_receipt_id:
            raise ValueError("FinanceManualOutcome requires execution_receipt_id.")
        if self.outcome_source not in VALID_OUTCOME_SOURCES:
            raise ValueError(
                f"Unsupported outcome_source: {self.outcome_source}. Must be one of: {VALID_OUTCOME_SOURCES}"
            )
        if self.verdict not in VALID_OUTCOME_VERDICTS:
            raise ValueError(f"Unsupported verdict: {self.verdict}. Must be one of: {VALID_OUTCOME_VERDICTS}")
