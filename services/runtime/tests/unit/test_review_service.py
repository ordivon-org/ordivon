from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from domains.journal.models import Review
from domains.journal.repository import ReviewRepository
from domains.journal.service import ReviewService
from domains.journal.lesson_repository import LessonRepository
from domains.journal.lesson_service import LessonService
from domains.strategy.models import Recommendation
from domains.strategy.outcome_repository import OutcomeRepository
from domains.strategy.outcome_service import OutcomeService
from domains.strategy.repository import RecommendationRepository
from domains.strategy.service import RecommendationService
from shared.enums.domain import ReviewStatus, ReviewVerdict
from state.db.base import Base


def _make_db():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)
    return engine, TestingSessionLocal


def test_review_completion_creates_lessons():
    engine, TestingSessionLocal = _make_db()
    db = TestingSessionLocal()

    try:
        recommendation_repo = RecommendationRepository(db)
        recommendation_repo.create(
            Recommendation(
                id="reco_test",
                analysis_id="analysis_test",
                title="Test reco",
                summary="summary",
            )
        )
        lesson_service = LessonService(LessonRepository(db))
        review_service = ReviewService(
            ReviewRepository(db),
            lesson_service,
            outcome_service=OutcomeService(OutcomeRepository(db)),
            recommendation_service=RecommendationService(recommendation_repo),
        )

        review = Review(
            recommendation_id="reco_test",
            review_type="recommendation_postmortem",
            status=ReviewStatus.PENDING,
            expected_outcome="Target achieved",
        )
        row = review_service.create(review)

        completed_review, lesson_rows, knowledge_feedback = review_service.complete_review(
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
        # third return value is covered in dedicated audit/integration tests
        recommendation_row = recommendation_repo.get("reco_test")
        outcomes = OutcomeRepository(db).list_for_recommendation("reco_test")
        assert recommendation_row is not None
        assert recommendation_row.latest_outcome_snapshot_id is not None
        assert len(outcomes) == 1
        assert knowledge_feedback is not None
        assert knowledge_feedback.id.startswith("kfpkt_")
        assert knowledge_feedback.review_id == row.id
        assert len(knowledge_feedback.governance_hints) == 1
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)
