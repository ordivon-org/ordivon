from shared.enums.domain import RecommendationStatus
from shared.errors.domain import InvalidStateTransition


ALLOWED_TRANSITIONS: dict[RecommendationStatus, set[RecommendationStatus]] = {
    RecommendationStatus.GENERATED: {
        RecommendationStatus.ADOPTED,
        RecommendationStatus.ARCHIVED,
    },
    RecommendationStatus.ADOPTED: {
        RecommendationStatus.TRACKING,
        RecommendationStatus.SUPERSEDED,
        RecommendationStatus.ARCHIVED,
    },
    RecommendationStatus.TRACKING: {
        RecommendationStatus.SATISFIED,
        RecommendationStatus.FAILED,
        RecommendationStatus.EXPIRED,
        RecommendationStatus.SUPERSEDED,
    },
    RecommendationStatus.SATISFIED: {
        RecommendationStatus.REVIEW_PENDING,
    },
    RecommendationStatus.FAILED: {
        RecommendationStatus.REVIEW_PENDING,
    },
    RecommendationStatus.EXPIRED: {
        RecommendationStatus.REVIEW_PENDING,
    },
    RecommendationStatus.REVIEW_PENDING: {
        RecommendationStatus.REVIEWED,
    },
    RecommendationStatus.REVIEWED: {
        RecommendationStatus.ARCHIVED,
    },
    RecommendationStatus.SUPERSEDED: {
        RecommendationStatus.ARCHIVED,
    },
    RecommendationStatus.ARCHIVED: set(),
}


class RecommendationStateMachine:
    def can_transition(
        self,
        current: RecommendationStatus,
        target: RecommendationStatus,
    ) -> bool:
        return target in ALLOWED_TRANSITIONS.get(current, set())

    def ensure_transition(
        self,
        current: RecommendationStatus,
        target: RecommendationStatus,
    ) -> None:
        if not self.can_transition(current, target):
            raise InvalidStateTransition(f"Invalid recommendation transition: {current} -> {target}")
