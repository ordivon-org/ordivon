from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from domains.journal.lesson_models import Lesson
from domains.journal.lesson_repository import LessonRepository
from domains.knowledge_feedback.models import KnowledgeFeedbackPacketRecord
from domains.knowledge_feedback.repository import KnowledgeFeedbackPacketRepository
from domains.research.models import AnalysisResult
from domains.research.repository import AnalysisRepository
from domains.strategy.models import Recommendation
from domains.strategy.outcome_models import OutcomeSnapshot
from domains.strategy.outcome_repository import OutcomeRepository
from domains.strategy.repository import RecommendationRepository
from knowledge.feedback import KnowledgeHint
from knowledge.retrieval import KnowledgeRetrievalService
from shared.enums.domain import OutcomeState
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


def test_knowledge_retrieval_by_recommendation_returns_entries_and_packets():
    engine, TestingSessionLocal = _make_db()
    db = TestingSessionLocal()
    try:
        AnalysisRepository(db).create(AnalysisResult(id="analysis_retrieval_1", query="Analyze BTC", symbol="BTC/USDT"))
        RecommendationRepository(db).create(
            Recommendation(
                id="reco_retrieval_1",
                analysis_id="analysis_retrieval_1",
                title="Track BTC",
                summary="summary",
            )
        )
        LessonRepository(db).create(
            Lesson(
                id="lesson_retrieval_1",
                review_id="review_retrieval_1",
                recommendation_id="reco_retrieval_1",
                title="Lesson",
                body="Wait for confirmation candle before entry",
                source_refs=["src:1"],
            )
        )
        OutcomeRepository(db).create(
            OutcomeSnapshot(
                id="outcome_retrieval_1",
                recommendation_id="reco_retrieval_1",
                outcome_state=OutcomeState.FAILED,
                observed_metrics={},
                evidence_refs=["review:review_retrieval_1"],
                trigger_reason="review_completion_backfill",
                note="failed",
            )
        )
        KnowledgeFeedbackPacketRepository(db).create(
            KnowledgeFeedbackPacketRecord(
                id="kfpkt_retrieval_1",
                recommendation_id="reco_retrieval_1",
                review_id="review_retrieval_1",
                knowledge_entry_ids=("know_retrieval_1",),
                governance_hints=(
                    KnowledgeHint(
                        target="governance",
                        hint_type="lesson_caution",
                        summary="Wait for confirmation candle before entry",
                        evidence_object_ids=("lesson_retrieval_1",),
                    ),
                ),
                intelligence_hints=(),
            )
        )

        result = KnowledgeRetrievalService(db).retrieve_for_recommendation("reco_retrieval_1")

        assert len(result.entries) == 1
        assert result.entries[0].narrative == "Wait for confirmation candle before entry"
        assert len(result.packets) == 1
        assert result.packets[0].id == "kfpkt_retrieval_1"
        assert result.packets[0].governance_hint_count == 1
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


def test_knowledge_retrieval_by_review_filters_packets_to_review():
    engine, TestingSessionLocal = _make_db()
    db = TestingSessionLocal()
    try:
        AnalysisRepository(db).create(AnalysisResult(id="analysis_retrieval_2", query="Analyze BTC", symbol="BTC/USDT"))
        RecommendationRepository(db).create(
            Recommendation(
                id="reco_retrieval_2",
                analysis_id="analysis_retrieval_2",
                title="Track BTC",
                summary="summary",
            )
        )
        from domains.journal.models import Review
        from domains.journal.repository import ReviewRepository

        ReviewRepository(db).create(
            Review(
                id="review_retrieval_2",
                recommendation_id="reco_retrieval_2",
                expected_outcome="Trend holds",
            )
        )
        LessonRepository(db).create(
            Lesson(
                id="lesson_retrieval_2",
                review_id="review_retrieval_2",
                recommendation_id="reco_retrieval_2",
                title="Lesson",
                body="Wait for pullback confirmation",
                source_refs=["src:2"],
            )
        )
        KnowledgeFeedbackPacketRepository(db).create(
            KnowledgeFeedbackPacketRecord(
                id="kfpkt_retrieval_2",
                recommendation_id="reco_retrieval_2",
                review_id="review_retrieval_2",
                knowledge_entry_ids=("know_retrieval_2",),
                governance_hints=(),
                intelligence_hints=(),
            )
        )

        result = KnowledgeRetrievalService(db).retrieve_for_review("review_retrieval_2")

        assert len(result.entries) == 1
        assert len(result.packets) == 1
        assert result.packets[0].review_id == "review_retrieval_2"
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


def test_knowledge_retrieval_by_symbol_returns_entries_across_recommendations():
    engine, TestingSessionLocal = _make_db()
    db = TestingSessionLocal()
    try:
        analysis_repo = AnalysisRepository(db)
        recommendation_repo = RecommendationRepository(db)
        lesson_repo = LessonRepository(db)
        outcome_repo = OutcomeRepository(db)

        analysis_repo.create(AnalysisResult(id="analysis_symbol_1", query="Analyze BTC", symbol="BTC/USDT"))
        analysis_repo.create(AnalysisResult(id="analysis_symbol_2", query="Analyze BTC again", symbol="BTC/USDT"))
        recommendation_repo.create(
            Recommendation(id="reco_symbol_1", analysis_id="analysis_symbol_1", title="A", summary="A")
        )
        recommendation_repo.create(
            Recommendation(id="reco_symbol_2", analysis_id="analysis_symbol_2", title="B", summary="B")
        )
        lesson_repo.create(
            Lesson(
                id="lesson_symbol_1",
                review_id="review_symbol_1",
                recommendation_id="reco_symbol_1",
                title="L1",
                body="Wait for confirmation",
                source_refs=["src:1"],
            )
        )
        lesson_repo.create(
            Lesson(
                id="lesson_symbol_2",
                review_id="review_symbol_2",
                recommendation_id="reco_symbol_2",
                title="L2",
                body="Size smaller on breakout",
                source_refs=["src:2"],
            )
        )
        outcome_repo.create(
            OutcomeSnapshot(
                id="outcome_symbol_1",
                recommendation_id="reco_symbol_1",
                outcome_state=OutcomeState.FAILED,
                observed_metrics={},
                evidence_refs=["review:review_symbol_1"],
                trigger_reason="review",
                note="n1",
            )
        )
        outcome_repo.create(
            OutcomeSnapshot(
                id="outcome_symbol_2",
                recommendation_id="reco_symbol_2",
                outcome_state=OutcomeState.FAILED,
                observed_metrics={},
                evidence_refs=["review:review_symbol_2"],
                trigger_reason="review",
                note="n2",
            )
        )

        result = KnowledgeRetrievalService(db).retrieve_for_symbol("BTC/USDT")

        assert len(result.entries) == 2
        narratives = {entry.narrative for entry in result.entries}
        assert "Wait for confirmation" in narratives
        assert "Size smaller on breakout" in narratives
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


def test_recurring_issue_aggregation_normalizes_and_counts_repeated_lessons():
    engine, TestingSessionLocal = _make_db()
    db = TestingSessionLocal()
    try:
        analysis_repo = AnalysisRepository(db)
        recommendation_repo = RecommendationRepository(db)
        lesson_repo = LessonRepository(db)
        outcome_repo = OutcomeRepository(db)

        analysis_repo.create(AnalysisResult(id="analysis_issue_1", query="Analyze BTC", symbol="BTC/USDT"))
        analysis_repo.create(AnalysisResult(id="analysis_issue_2", query="Analyze BTC again", symbol="BTC/USDT"))
        recommendation_repo.create(
            Recommendation(id="reco_issue_1", analysis_id="analysis_issue_1", title="A", summary="A")
        )
        recommendation_repo.create(
            Recommendation(id="reco_issue_2", analysis_id="analysis_issue_2", title="B", summary="B")
        )
        lesson_repo.create(
            Lesson(
                id="lesson_issue_1",
                review_id="review_issue_1",
                recommendation_id="reco_issue_1",
                title="L1",
                body="Wait for confirmation candle!",
                source_refs=["src:1"],
            )
        )
        lesson_repo.create(
            Lesson(
                id="lesson_issue_2",
                review_id="review_issue_2",
                recommendation_id="reco_issue_2",
                title="L2",
                body="Wait for confirmation candle",
                source_refs=["src:2"],
            )
        )
        outcome_repo.create(
            OutcomeSnapshot(
                id="outcome_issue_1",
                recommendation_id="reco_issue_1",
                outcome_state=OutcomeState.FAILED,
                observed_metrics={},
                evidence_refs=["review:review_issue_1"],
                trigger_reason="review",
                note="n1",
            )
        )
        outcome_repo.create(
            OutcomeSnapshot(
                id="outcome_issue_2",
                recommendation_id="reco_issue_2",
                outcome_state=OutcomeState.FAILED,
                observed_metrics={},
                evidence_refs=["review:review_issue_2"],
                trigger_reason="review",
                note="n2",
            )
        )

        summaries = KnowledgeRetrievalService(db).aggregate_recurring_issues_for_symbol("BTC/USDT")

        assert len(summaries) == 1
        assert summaries[0].issue_key == "wait for confirmation candle"
        assert summaries[0].occurrence_count == 2
        assert set(summaries[0].recommendation_ids) == {"reco_issue_1", "reco_issue_2"}
        assert set(summaries[0].review_ids) == {"review_issue_1", "review_issue_2"}
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


def test_knowledge_retrieval_returns_empty_results_honestly():
    engine, TestingSessionLocal = _make_db()
    db = TestingSessionLocal()
    try:
        service = KnowledgeRetrievalService(db)
        assert service.retrieve_for_recommendation("reco_missing").entries == ()
        assert service.retrieve_for_review("review_missing").packets == ()
        assert service.retrieve_for_symbol("DOGE/USDT").entries == ()
        assert service.aggregate_recurring_issues_for_symbol("DOGE/USDT") == ()
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)
