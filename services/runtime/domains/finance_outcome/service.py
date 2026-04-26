from domains.finance_outcome.models import FinanceManualOutcome
from domains.finance_outcome.repository import FinanceManualOutcomeRepository


class FinanceManualOutcomeService:
    def __init__(self, repository: FinanceManualOutcomeRepository) -> None:
        self.repository = repository

    def create(self, outcome: FinanceManualOutcome):
        return self.repository.create(outcome)

    def get_model(self, outcome_id: str) -> FinanceManualOutcome:
        row = self.repository.get(outcome_id)
        if row is None:
            raise ValueError(f"FinanceManualOutcome not found: {outcome_id}")
        return self.repository.to_model(row)

    def find_for_intake(self, decision_intake_id: str) -> FinanceManualOutcome | None:
        row = self.repository.find_for_intake(decision_intake_id)
        if row is None:
            return None
        return self.repository.to_model(row)
