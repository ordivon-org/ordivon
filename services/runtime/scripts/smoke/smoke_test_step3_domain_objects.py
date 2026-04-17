from pfios.core.db.bootstrap import init_db
from pfios.core.db.session import SessionLocal
from pfios.domain.recommendation.models import Recommendation
from pfios.domain.recommendation.repository import RecommendationRepository
from pfios.domain.recommendation.service import RecommendationService
from pfios.domain.review.models import Review
from pfios.domain.review.repository import ReviewRepository
from pfios.domain.review.service import ReviewService
from pfios.domain.lessons.repository import LessonRepository
from pfios.domain.lessons.service import LessonService
from pfios.domain.issue.models import Issue
from pfios.domain.issue.repository import IssueRepository
from pfios.domain.common.enums import (
    RecommendationStatus,
    ReviewStatus,
    ReviewVerdict,
)


def main():
    print("[START] Step 3 domain object smoke test")
    init_db()
    db = SessionLocal()

    try:
        reco_service = RecommendationService(RecommendationRepository(db))
        lesson_service = LessonService(LessonRepository(db))
        review_service = ReviewService(ReviewRepository(db), lesson_service)
        issue_repo = IssueRepository(db)

        reco = Recommendation(
            title="Reduce BTC exposure",
            summary="Trim BTC position if concentration is too high",
            rationale="Concentration risk too high",
            expected_outcome="Exposure below 25%",
            confidence=0.77,
        )
        reco_service.create(reco)

        reco_service.transition(reco.id, RecommendationStatus.ADOPTED)
        reco_service.transition(reco.id, RecommendationStatus.TRACKING)
        reco_service.transition(reco.id, RecommendationStatus.FAILED)
        reco_service.transition(reco.id, RecommendationStatus.REVIEW_PENDING)

        review = Review(
            recommendation_id=reco.id,
            review_type="recommendation_postmortem",
            status=ReviewStatus.PENDING,
            expected_outcome=reco.expected_outcome,
        )
        review_row = review_service.create(review)

        completed_review, lesson_rows = review_service.complete_review(
            review_id=review_row.id,
            observed_outcome="Exposure remained above threshold",
            verdict=ReviewVerdict.INVALIDATED,
            variance_summary="Execution did not reduce exposure in time",
            cause_tags=["execution_failure", "timing_mismatch"],
            lessons=[
                "Risk reduction recommendations need explicit execution deadlines.",
                "Concentration controls should create earlier alerts."
            ],
            followup_actions=[
                "Introduce exposure rule alerts.",
                "Add execution confirmation check."
            ],
        )

        issue_repo.create(
            Issue(
                title="Review backlog detected",
                summary="Review was created only after terminal outcome",
                severity="p2",
                category="workflow",
                source_type="review",
                source_id=completed_review.id,
                detail={"note": "Step 3 smoke test issue example"},
            )
        )

        lessons = lesson_service.list_recent(limit=10)
        open_issues = issue_repo.list_open()

        print("[OK] Recommendation lifecycle reached REVIEW_PENDING")
        print("[OK] Review completed:", completed_review.id)
        print("[OK] Lessons created:", len(lesson_rows))
        print("[OK] Recent lessons count:", len(lessons))
        print("[OK] Open issues count:", len(open_issues))

        assert len(lesson_rows) == 2
        assert len(lessons) >= 2
        assert len(open_issues) >= 1

        print("[WIN] Step 3 domain object smoke test passed.")
    finally:
        db.close()


if __name__ == "__main__":
    main()
