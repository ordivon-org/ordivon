from domains.journal.lesson_models import Lesson
from domains.strategy.outcome_models import OutcomeSnapshot
from knowledge import KnowledgeEntryBuilder, KnowledgeFeedbackService
from shared.enums.domain import OutcomeState


def test_knowledge_feedback_service_builds_governance_and_intelligence_hints():
    lesson = Lesson(
        id="lesson_feedback_1",
        review_id="review_1",
        recommendation_id="reco_1",
        title="Feedback lesson",
        body="Wait for confirmation before entry",
        source_refs=["audit:review_completed"],
        confidence=0.8,
    )
    outcome = OutcomeSnapshot(
        id="outcome_feedback_1",
        recommendation_id="reco_1",
        outcome_state=OutcomeState.FAILED,
        trigger_reason="review_completion_backfill",
    )
    entry = KnowledgeEntryBuilder.from_lesson_with_outcome(lesson, outcome)

    packet = KnowledgeFeedbackService().build_packet("reco_1", [entry])

    assert packet.recommendation_id == "reco_1"
    assert len(packet.governance_hints) == 1
    assert len(packet.intelligence_hints) == 1
    assert packet.governance_hints[0].summary == "Wait for confirmation before entry"
