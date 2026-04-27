from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from domains.journal.lesson_repository import LessonRepository
from domains.journal.lesson_service import LessonService
from domains.journal.models import Review
from domains.journal.repository import ReviewRepository
from domains.journal.service import ReviewService
from domains.research.models import AnalysisResult
from domains.research.repository import AnalysisRepository
from domains.strategy.models import Recommendation
from domains.strategy.outcome_repository import OutcomeRepository
from domains.strategy.outcome_service import OutcomeService
from domains.strategy.repository import RecommendationRepository
from domains.strategy.service import RecommendationService
from knowledge.retrieval import KnowledgeRetrievalService
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


def test_completed_reviews_create_retrievable_knowledge_and_packets():
    engine, TestingSessionLocal = _make_db()
    db = TestingSessionLocal()
    try:
        AnalysisRepository(db).create(
            AnalysisResult(id="analysis_knowledge_integration", query="Analyze BTC", symbol="BTC/USDT")
        )
        RecommendationRepository(db).create(
            Recommendation(
                id="reco_knowledge_integration",
                analysis_id="analysis_knowledge_integration",
                title="Track BTC",
                summary="summary",
            )
        )
        review_service = ReviewService(
            ReviewRepository(db),
            LessonService(LessonRepository(db)),
            outcome_service=OutcomeService(OutcomeRepository(db)),
            recommendation_service=RecommendationService(RecommendationRepository(db)),
        )
        review = Review(
            recommendation_id="reco_knowledge_integration",
            review_type="recommendation_postmortem",
            status=ReviewStatus.PENDING,
            expected_outcome="Trend holds",
        )
        row = review_service.create(review)
        review_service.complete_review(
            review_id=row.id,
            observed_outcome="Trend failed",
            verdict=ReviewVerdict.INVALIDATED,
            variance_summary="Entry lacked confirmation",
            cause_tags=["confirmation"],
            lessons=["Wait for confirmation candle before entry"],
            followup_actions=["Tighten checklist"],
        )

        result = KnowledgeRetrievalService(db).retrieve_for_recommendation("reco_knowledge_integration")

        assert len(result.entries) == 1
        assert len(result.packets) == 1
        assert result.packets[0].review_id == row.id
        assert result.entries[0].derived_from.object_type == "lesson"
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


def test_repeated_review_lessons_aggregate_into_recurring_issues():
    engine, TestingSessionLocal = _make_db()
    db = TestingSessionLocal()
    try:
        analysis_repo = AnalysisRepository(db)
        recommendation_repo = RecommendationRepository(db)
        review_service = ReviewService(
            ReviewRepository(db),
            LessonService(LessonRepository(db)),
            outcome_service=OutcomeService(OutcomeRepository(db)),
            recommendation_service=RecommendationService(recommendation_repo),
        )

        analysis_repo.create(AnalysisResult(id="analysis_agg_1", query="Analyze BTC", symbol="BTC/USDT"))
        analysis_repo.create(AnalysisResult(id="analysis_agg_2", query="Analyze BTC again", symbol="BTC/USDT"))
        recommendation_repo.create(
            Recommendation(id="reco_agg_1", analysis_id="analysis_agg_1", title="A", summary="A")
        )
        recommendation_repo.create(
            Recommendation(id="reco_agg_2", analysis_id="analysis_agg_2", title="B", summary="B")
        )

        review_1 = review_service.create(
            Review(recommendation_id="reco_agg_1", status=ReviewStatus.PENDING, expected_outcome="Trend holds")
        )
        review_2 = review_service.create(
            Review(recommendation_id="reco_agg_2", status=ReviewStatus.PENDING, expected_outcome="Trend holds")
        )

        review_service.complete_review(
            review_id=review_1.id,
            observed_outcome="Trend failed",
            verdict=ReviewVerdict.INVALIDATED,
            variance_summary="No confirmation",
            cause_tags=["confirmation"],
            lessons=["Wait for confirmation candle"],
            followup_actions=["Tighten checklist"],
        )
        review_service.complete_review(
            review_id=review_2.id,
            observed_outcome="Trend failed",
            verdict=ReviewVerdict.INVALIDATED,
            variance_summary="Late entry",
            cause_tags=["confirmation"],
            lessons=["Wait for confirmation candle!"],
            followup_actions=["Tighten checklist"],
        )

        summaries = KnowledgeRetrievalService(db).aggregate_recurring_issues_for_symbol("BTC/USDT")

        assert len(summaries) == 1
        assert summaries[0].issue_key == "wait for confirmation candle"
        assert summaries[0].occurrence_count == 2
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)
