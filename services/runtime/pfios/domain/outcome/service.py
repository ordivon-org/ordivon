from pfios.domain.outcome.models import OutcomeSnapshot
from pfios.domain.outcome.repository import OutcomeRepository
from pfios.domain.common.enums import OutcomeState


class OutcomeService:
    def __init__(self, repository: OutcomeRepository) -> None:
        self.repository = repository

    def create_snapshot(self, snapshot: OutcomeSnapshot):
        return self.repository.create(snapshot)

    def classify_terminal_state(self, outcome_state: OutcomeState) -> bool:
        return outcome_state in {
            OutcomeState.SATISFIED,
            OutcomeState.FAILED,
            OutcomeState.EXPIRED,
        }

    def list_for_recommendation(self, recommendation_id: str):
        return self.repository.list_for_recommendation(recommendation_id)
