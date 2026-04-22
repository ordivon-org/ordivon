from __future__ import annotations

from dataclasses import dataclass

from domains.journal.orm import ReviewORM
from domains.journal.repository import ReviewRepository
from domains.strategy.orm import RecommendationORM
from domains.strategy.outcome_orm import OutcomeSnapshotORM
from domains.strategy.outcome_repository import OutcomeRepository


@dataclass(frozen=True, slots=True)
class OutcomeGraphNode:
    recommendation_id: str
    latest_review_id: str | None
    latest_outcome_snapshot_id: str | None


class OutcomeGraph:
    def __init__(self, db) -> None:
        self.db = db
        self.review_repository = ReviewRepository(db)
        self.outcome_repository = OutcomeRepository(db)

    def for_recommendation(self, recommendation: RecommendationORM | None) -> OutcomeGraphNode:
        if recommendation is None:
            return OutcomeGraphNode(
                recommendation_id="",
                latest_review_id=None,
                latest_outcome_snapshot_id=None,
            )
        reviews = self.review_repository.list_for_recommendation(recommendation.id)
        latest_review: ReviewORM | None = reviews[0] if reviews else None
        return OutcomeGraphNode(
            recommendation_id=recommendation.id,
            latest_review_id=latest_review.id if latest_review is not None else None,
            latest_outcome_snapshot_id=recommendation.latest_outcome_snapshot_id,
        )

    def latest_outcome_for_recommendation(self, recommendation: RecommendationORM | None) -> OutcomeSnapshotORM | None:
        if recommendation is None or not recommendation.latest_outcome_snapshot_id:
            return None
        return self.db.get(OutcomeSnapshotORM, recommendation.latest_outcome_snapshot_id)
