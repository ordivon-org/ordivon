from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from domains.knowledge_feedback.repository import KnowledgeFeedbackPacketRepository
from domains.knowledge_feedback.service import KnowledgeFeedbackPacketService
from domains.journal.lesson_models import Lesson
from domains.journal.lesson_repository import LessonRepository
from domains.research.models import AnalysisResult
from domains.research.repository import AnalysisRepository
from domains.strategy.models import Recommendation
from domains.strategy.outcome_models import OutcomeSnapshot
from domains.strategy.outcome_repository import OutcomeRepository
from domains.strategy.repository import RecommendationRepository
from intelligence.feedback import IntelligenceFeedbackReader
from knowledge.feedback import KnowledgeFeedbackPacket, KnowledgeHint
from shared.enums.domain import OutcomeState
from state.db.base import Base


def _make_db():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    testing_session_local = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)
    return engine, testing_session_local


def test_intelligence_feedback_reader_returns_symbol_backed_memory_lessons_and_related_reviews():
    engine, testing_session_local = _make_db()
    db = testing_session_local()
    try:
        AnalysisRepository(db).create(
            AnalysisResult(
                id="ana_intel_hint_1",
                query="Analyze BTC",
                symbol="BTC-USDT",
                timeframe="1h",
                summary="summary",
                thesis="thesis",
                suggested_actions=["BUY"],
            )
        )
        RecommendationRepository(db).create(
            Recommendation(
                id="reco_intel_hint_1",
                analysis_id="ana_intel_hint_1",
                title="Buy BTC",
                summary="summary",
            )
        )
        LessonRepository(db).create(
            Lesson(
                id="lesson_intel_hint_1",
                review_id="review_intel_hint_1",
                recommendation_id="reco_intel_hint_1",
                title="Lesson",
                body="Wait for confirmation before entry",
                lesson_type="review_learning",
            )
        )
        OutcomeRepository(db).create(
            OutcomeSnapshot(
                id="outcome_intel_hint_1",
                recommendation_id="reco_intel_hint_1",
                outcome_state=OutcomeState.FAILED,
                evidence_refs=["review:review_intel_hint_1", "recommendation:reco_intel_hint_1"],
                trigger_reason="review_completion_backfill",
                note="Setup failed",
            )
        )
        db.commit()

        context = IntelligenceFeedbackReader(db).read_for_symbol("BTC-USDT")

        assert context.memory_lessons == ("Wait for confirmation before entry",)
        assert context.related_reviews == ("review_intel_hint_1",)
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


def test_intelligence_feedback_reader_returns_empty_when_symbol_has_no_feedback():
    engine, testing_session_local = _make_db()
    db = testing_session_local()
    try:
        context = IntelligenceFeedbackReader(db).read_for_symbol("ETH-USDT")
        assert context.memory_lessons == ()
        assert context.related_reviews == ()
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


def test_intelligence_feedback_reader_prefers_persisted_packet_when_available(monkeypatch):
    engine, testing_session_local = _make_db()
    db = testing_session_local()
    try:
        AnalysisRepository(db).create(
            AnalysisResult(
                id="ana_intel_packet_1",
                query="Analyze BTC",
                symbol="BTC-USDT",
                timeframe="1h",
                summary="summary",
                thesis="thesis",
                suggested_actions=["BUY"],
            )
        )
        RecommendationRepository(db).create(
            Recommendation(
                id="reco_intel_packet_1",
                analysis_id="ana_intel_packet_1",
                title="Buy BTC",
                summary="summary",
            )
        )
        KnowledgeFeedbackPacketService(KnowledgeFeedbackPacketRepository(db)).persist_packet(
            KnowledgeFeedbackPacket(
                recommendation_id="reco_intel_packet_1",
                knowledge_entry_ids=("ke_intel_packet_1",),
                review_id="review_intel_packet_1",
                intelligence_hints=(
                    KnowledgeHint(
                        target="intelligence",
                        hint_type="memory_lesson",
                        summary="Persisted intelligence hint",
                        evidence_object_ids=("review_intel_packet_1",),
                    ),
                ),
            )
        )
        db.commit()

        monkeypatch.setattr(
            "knowledge.extraction.LessonExtractionService.extract_for_recommendation",
            lambda self, recommendation_id: (_ for _ in ()).throw(RuntimeError("should not extract")),
        )

        context = IntelligenceFeedbackReader(db).read_for_symbol("BTC-USDT")

        assert context.memory_lessons == ("Persisted intelligence hint",)
        assert context.related_reviews == ("review_intel_packet_1",)
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)
