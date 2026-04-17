from pfios.domain.recommendation.models import Recommendation
from pfios.domain.recommendation.repository import RecommendationRepository
from pfios.domain.recommendation.state_machine import RecommendationStateMachine
from pfios.domain.common.enums import RecommendationStatus
from pfios.domain.common.errors import DomainNotFound


class RecommendationService:
    def __init__(self, repository: RecommendationRepository) -> None:
        self.repository = repository
        self.state_machine = RecommendationStateMachine()

    def create(self, recommendation: Recommendation):
        return self.repository.create(recommendation)

    def get_model(self, recommendation_id: str) -> Recommendation:
        row = self.repository.get(recommendation_id)
        if row is None:
            raise DomainNotFound(f"Recommendation not found: {recommendation_id}")
        return self.repository.to_model(row)

    def transition(
        self,
        recommendation_id: str,
        target_status: RecommendationStatus,
        latest_outcome_snapshot_id: str | None = None,
    ):
        current = self.get_model(recommendation_id)
        self.state_machine.ensure_transition(current.status, target_status)
        return self.repository.update_status(
            recommendation_id=recommendation_id,
            status=target_status,
            latest_outcome_snapshot_id=latest_outcome_snapshot_id,
        )

    def list_recent(self, limit: int = 20):
        return self.repository.list_recent(limit=limit)

    def list_by_status(self, status: RecommendationStatus):
        return self.repository.list_by_status(status)
