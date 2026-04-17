from enum import StrEnum


class RecommendationStatus(StrEnum):
    GENERATED = "generated"
    ADOPTED = "adopted"
    TRACKING = "tracking"
    SATISFIED = "satisfied"
    FAILED = "failed"
    EXPIRED = "expired"
    SUPERSEDED = "superseded"
    REVIEW_PENDING = "review_pending"
    REVIEWED = "reviewed"
    ARCHIVED = "archived"


class OutcomeState(StrEnum):
    UNCHANGED = "unchanged"
    IMPROVING = "improving"
    SATISFIED = "satisfied"
    FAILED = "failed"
    EXPIRED = "expired"
    INCONCLUSIVE = "inconclusive"


class ReviewStatus(StrEnum):
    PENDING = "pending"
    GENERATED = "generated"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class ReviewVerdict(StrEnum):
    VALIDATED = "validated"
    PARTIALLY_VALIDATED = "partially_validated"
    INVALIDATED = "invalidated"
    INCONCLUSIVE = "inconclusive"
