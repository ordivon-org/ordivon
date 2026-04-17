from sqlalchemy.orm import Session

from pfios.domain.review.models import Review
from pfios.domain.review.orm import ReviewORM
from pfios.domain.common.enums import ReviewStatus, ReviewVerdict
from pfios.core.utils.serialization import to_json_text, from_json_text


class ReviewRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def encode_list(self, value: list[str]) -> str:
        return to_json_text(value)

    def decode_list(self, value: str | None) -> list[str]:
        return from_json_text(value, [])

    def create(self, review: Review) -> ReviewORM:
        row = ReviewORM(
            id=review.id,
            recommendation_id=review.recommendation_id,
            analysis_id=review.analysis_id,
            review_type=review.review_type,
            status=review.status.value,
            expected_outcome=review.expected_outcome,
            observed_outcome=review.observed_outcome,
            verdict=review.verdict.value if review.verdict else None,
            variance_summary=review.variance_summary,
            cause_tags_json=to_json_text(review.cause_tags),
            lessons_json=to_json_text(review.lessons),
            followup_actions_json=to_json_text(review.followup_actions),
            wiki_path=review.wiki_path,
        )
        self.db.add(row)
        self.db.commit()
        self.db.refresh(row)
        return row

    def get(self, review_id: str) -> ReviewORM | None:
        return self.db.get(ReviewORM, review_id)

    def list_pending(self) -> list[ReviewORM]:
        return (
            self.db.query(ReviewORM)
            .filter(ReviewORM.status.in_(["pending", "generated", "in_progress"]))
            .order_by(ReviewORM.created_at.desc())
            .all()
        )

    def list_for_recommendation(self, recommendation_id: str) -> list[ReviewORM]:
        return (
            self.db.query(ReviewORM)
            .filter(ReviewORM.recommendation_id == recommendation_id)
            .order_by(ReviewORM.created_at.desc())
            .all()
        )

    def to_model(self, row: ReviewORM) -> Review:
        return Review(
            id=row.id,
            recommendation_id=row.recommendation_id,
            analysis_id=row.analysis_id,
            review_type=row.review_type,
            status=ReviewStatus(row.status),
            expected_outcome=row.expected_outcome,
            observed_outcome=row.observed_outcome,
            verdict=ReviewVerdict(row.verdict) if row.verdict else None,
            variance_summary=row.variance_summary,
            cause_tags=from_json_text(row.cause_tags_json, []),
            lessons=from_json_text(row.lessons_json, []),
            followup_actions=from_json_text(row.followup_actions_json, []),
            wiki_path=row.wiki_path,
            scheduled_at=row.scheduled_at.isoformat(),
            started_at=row.started_at.isoformat() if row.started_at else None,
            completed_at=row.completed_at.isoformat() if row.completed_at else None,
            created_at=row.created_at.isoformat(),
        )
