from shared.enums.domain import ReviewStatus
from shared.errors.domain import InvalidStateTransition


ALLOWED_REVIEW_TRANSITIONS: dict[ReviewStatus, set[ReviewStatus]] = {
    ReviewStatus.PENDING: {
        ReviewStatus.GENERATED,
        ReviewStatus.IN_PROGRESS,
        ReviewStatus.COMPLETED,
        ReviewStatus.CANCELLED,
    },
    ReviewStatus.GENERATED: {
        ReviewStatus.IN_PROGRESS,
        ReviewStatus.COMPLETED,
        ReviewStatus.CANCELLED,
    },
    ReviewStatus.IN_PROGRESS: {
        ReviewStatus.COMPLETED,
        ReviewStatus.CANCELLED,
    },
    ReviewStatus.COMPLETED: set(),
    ReviewStatus.CANCELLED: set(),
}


class ReviewStateMachine:
    def can_transition(self, current: ReviewStatus, target: ReviewStatus) -> bool:
        return target in ALLOWED_REVIEW_TRANSITIONS.get(current, set())

    def ensure_transition(self, current: ReviewStatus, target: ReviewStatus) -> None:
        if not self.can_transition(current, target):
            raise InvalidStateTransition(f"Invalid review transition: {current} -> {target}")
