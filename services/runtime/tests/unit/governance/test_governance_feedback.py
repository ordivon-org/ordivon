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
from governance_engine.decision import GovernanceAdvisoryHint
from governance_engine.feedback import GovernanceFeedbackReader
from governance_engine.risk_engine.engine import RiskEngine
from knowledge.feedback import KnowledgeFeedbackPacket, KnowledgeHint
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


def test_governance_feedback_reader_returns_symbol_backed_hints():
    engine, TestingSessionLocal = _make_db()
    db = TestingSessionLocal()
    try:
        AnalysisRepository(db).create(
            AnalysisResult(
                id="ana_hint_1",
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
                id="reco_hint_1",
                analysis_id="ana_hint_1",
                title="Buy BTC",
                summary="summary",
            )
        )
        LessonRepository(db).create(
            Lesson(
                id="lesson_hint_1",
                review_id="review_hint_1",
                recommendation_id="reco_hint_1",
                title="Lesson",
                body="Wait for confirmation before entry",
                lesson_type="review_learning",
            )
        )
        OutcomeRepository(db).create(
            OutcomeSnapshot(
                id="outcome_hint_1",
                recommendation_id="reco_hint_1",
                outcome_state=OutcomeState.FAILED,
                evidence_refs=["review:review_hint_1", "recommendation:reco_hint_1"],
                trigger_reason="review_completion_backfill",
                note="Setup failed",
            )
        )
        db.commit()

        hints = GovernanceFeedbackReader(db).list_hints_for_symbol("BTC-USDT")

        assert len(hints) == 1
        assert hints[0].target == "governance"
        assert hints[0].hint_type == "lesson_caution"
        assert hints[0].summary == "Wait for confirmation before entry"
        assert "outcome_hint_1" in hints[0].evidence_object_ids
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


def test_risk_engine_preserves_advisory_hints_without_overriding_decision():
    hint = GovernanceAdvisoryHint(
        target="governance",
        hint_type="lesson_caution",
        summary="Wait for confirmation before entry",
        evidence_object_ids=("lesson_hint_1", "outcome_hint_1"),
    )
    decision = RiskEngine().validate_analysis(
        AnalysisResult(
            id="ana_hint_2",
            query="Analyze BTC",
            symbol="BTC-USDT",
            timeframe="1h",
            summary="Bullish",
            thesis="trend",
            suggested_actions=["BUY"],
        ),
        advisory_hints=[hint],
    )

    assert decision.decision == "execute"
    assert decision.advisory_hints == (hint,)


def test_governance_feedback_reader_prefers_persisted_packet_when_available(monkeypatch):
    engine, TestingSessionLocal = _make_db()
    db = TestingSessionLocal()
    try:
        AnalysisRepository(db).create(
            AnalysisResult(
                id="ana_hint_packet_1",
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
                id="reco_hint_packet_1",
                analysis_id="ana_hint_packet_1",
                title="Buy BTC",
                summary="summary",
            )
        )
        KnowledgeFeedbackPacketService(KnowledgeFeedbackPacketRepository(db)).persist_packet(
            KnowledgeFeedbackPacket(
                recommendation_id="reco_hint_packet_1",
                knowledge_entry_ids=("ke_packet_1",),
                review_id="review_hint_packet_1",
                governance_hints=(
                    KnowledgeHint(
                        target="governance",
                        hint_type="lesson_caution",
                        summary="Persisted governance hint",
                        evidence_object_ids=("ke_packet_1", "outcome_packet_1"),
                    ),
                ),
            )
        )
        db.commit()

        monkeypatch.setattr(
            "knowledge.extraction.LessonExtractionService.extract_for_recommendation",
            lambda self, recommendation_id: (_ for _ in ()).throw(RuntimeError("should not extract")),
        )

        hints = GovernanceFeedbackReader(db).list_hints_for_symbol("BTC-USDT")

        assert len(hints) == 1
        assert hints[0].summary == "Persisted governance hint"
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)
