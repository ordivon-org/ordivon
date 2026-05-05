from domains.strategy.models import Recommendation
from domains.strategy.repository import RecommendationRepository
from domains.strategy.state_machine import RecommendationStateMachine
from shared.enums.domain import RecommendationStatus
from shared.errors.domain import DomainNotFound


from governance_engine.audit.auditor import RiskAuditor


class RecommendationService:
    def __init__(self, repository: RecommendationRepository, auditor: RiskAuditor | None = None) -> None:
        self.repository = repository
        self.state_machine = RecommendationStateMachine()
        self.auditor = auditor

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
        *,
        emit_recommendation_status_audit: bool = True,
    ):
        current = self.get_model(recommendation_id)
        self.state_machine.ensure_transition(current.status, target_status)
        row = self.repository.update_status(
            recommendation_id=recommendation_id,
            status=target_status,
            latest_outcome_snapshot_id=latest_outcome_snapshot_id,
        )

        if self.auditor and emit_recommendation_status_audit:
            self.auditor.record_event(
                event_type="recommendation_status_update",
                payload={"new_status": target_status.value},
                entity_type="recommendation",
                entity_id=recommendation_id,
                recommendation_id=recommendation_id,
                db=self.repository.db,
            )

            # Dedicated audit event for adoption — a key lifecycle signal
            # indicating the user decided to act on the AI recommendation.
            if target_status == RecommendationStatus.ADOPTED:
                self.auditor.record_event(
                    event_type="recommendation_adopted",
                    payload={
                        "recommendation_id": recommendation_id,
                        "adopted_status": target_status.value,
                    },
                    entity_type="recommendation",
                    entity_id=recommendation_id,
                    recommendation_id=recommendation_id,
                    db=self.repository.db,
                )

        return self.repository.to_model(row)

    def list_recent(self, limit: int = 20):
        return self.repository.list_recent(limit=limit)

    def list_by_status(self, status: RecommendationStatus):
        return self.repository.list_by_status(status)

    def attach_latest_outcome_snapshot(self, recommendation_id: str, outcome_snapshot_id: str):
        row = self.repository.attach_latest_outcome_snapshot(recommendation_id, outcome_snapshot_id)
        if row is None:
            raise DomainNotFound(f"Recommendation not found: {recommendation_id}")
        return self.repository.to_model(row)
