from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from domains.knowledge_feedback.repository import KnowledgeFeedbackPacketRepository
from domains.knowledge_feedback.service import KnowledgeFeedbackPacketService
from knowledge.feedback import KnowledgeFeedbackPacket, KnowledgeHint
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


def test_feedback_packet_repository_persists_packet_and_hints():
    engine, testing_session_local = _make_db()
    db = testing_session_local()
    try:
        service = KnowledgeFeedbackPacketService(KnowledgeFeedbackPacketRepository(db))
        packet = service.persist_packet(
            KnowledgeFeedbackPacket(
                recommendation_id="reco_packet_1",
                knowledge_entry_ids=("ke_1", "ke_2"),
                review_id="review_packet_1",
                governance_hints=(
                    KnowledgeHint(
                        target="governance",
                        hint_type="lesson_caution",
                        summary="Wait for confirmation",
                        evidence_object_ids=("review_packet_1", "outcome_packet_1"),
                    ),
                ),
                intelligence_hints=(
                    KnowledgeHint(
                        target="intelligence",
                        hint_type="memory_lesson",
                        summary="Avoid early entries",
                        evidence_object_ids=("review_packet_1",),
                    ),
                ),
            )
        )

        latest = service.latest_for_recommendation("reco_packet_1")

        assert latest is not None
        assert latest.id == packet.id
        assert latest.review_id == "review_packet_1"
        assert latest.knowledge_entry_ids == ("ke_1", "ke_2")
        assert latest.governance_hints[0].summary == "Wait for confirmation"
        assert latest.intelligence_hints[0].summary == "Avoid early entries"
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)
