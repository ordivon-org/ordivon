from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from domains.journal.lesson_repository import LessonRepository
from domains.journal.lesson_service import LessonService
from domains.journal.models import Review
from domains.journal.repository import ReviewRepository
from domains.journal.service import ReviewService
from domains.strategy.models import Recommendation
from domains.strategy.outcome_repository import OutcomeRepository
from domains.strategy.outcome_service import OutcomeService
from domains.strategy.repository import RecommendationRepository
from domains.strategy.service import RecommendationService
from knowledge import LessonExtractionService
from state.db.base import Base
from shared.enums.domain import ReviewStatus, ReviewVerdict


def _make_db():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    testing_session = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)
    return engine, testing_session


def test_review_completion_materializes_extractable_knowledge_entries():
    engine, testing_session = _make_db()
    db = testing_session()
    try:
        recommendation_repo = RecommendationRepository(db)
        recommendation_repo.create(
            Recommendation(
                id="reco_extract_2",
                analysis_id="analysis_extract_2",
                title="Track breakout",
                summary="Track breakout setup",
            )
        )
        review_service = ReviewService(
            ReviewRepository(db),
            LessonService(LessonRepository(db)),
            outcome_service=OutcomeService(OutcomeRepository(db)),
            recommendation_service=RecommendationService(recommendation_repo),
        )
        review_row = review_service.create(
            Review(
                recommendation_id="reco_extract_2",
                review_type="recommendation_postmortem",
                status=ReviewStatus.PENDING,
                expected_outcome="Breakout continues",
            )
        )
        review_service.complete_review(
            review_id=review_row.id,
            observed_outcome="Breakout failed",
            verdict=ReviewVerdict.INVALIDATED,
            variance_summary="Breakout lost momentum",
            cause_tags=["momentum"],
            lessons=["Wait for confirmation candle before entry"],
            followup_actions=["Tighten invalidation"],
        )

        entries = LessonExtractionService(db).extract_for_recommendation("reco_extract_2")

        assert len(entries) == 1
        assert entries[0].derived_from.object_type == "lesson"
        assert any(ref.object_type == "outcome_snapshot" for ref in entries[0].evidence_refs)
        assert entries[0].feedback_targets == ("governance", "intelligence")
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)
