from pfios.core.db.bootstrap import init_db
from pfios.core.db.session import SessionLocal
from pfios.domain.review.models import Review
from pfios.domain.review.repository import ReviewRepository
from pfios.domain.review.service import ReviewService
from pfios.domain.lessons.repository import LessonRepository
from pfios.domain.lessons.service import LessonService
from pfios.domain.common.enums import ReviewStatus, ReviewVerdict


def test_review_completion_creates_lessons():
    init_db()
    db = SessionLocal()

    try:
        lesson_service = LessonService(LessonRepository(db))
        review_service = ReviewService(ReviewRepository(db), lesson_service)

        review = Review(
            recommendation_id="reco_test",
            review_type="recommendation_postmortem",
            status=ReviewStatus.PENDING,
            expected_outcome="Target achieved",
        )
        row = review_service.create(review)

        completed_review, lesson_rows = review_service.complete_review(
            review_id=row.id,
            observed_outcome="Target not achieved",
            verdict=ReviewVerdict.INVALIDATED,
            variance_summary="Execution lagged",
            cause_tags=["execution_failure"],
            lessons=["Execution deadlines must be explicit"],
            followup_actions=["Add stronger tracking"],
        )

        assert completed_review.status == ReviewStatus.COMPLETED.value
        assert len(lesson_rows) == 1
    finally:
        db.close()
