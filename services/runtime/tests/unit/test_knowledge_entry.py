from domains.journal.lesson_models import Lesson
from knowledge import KnowledgeEntry, KnowledgeEntryBuilder, KnowledgeRef


def test_knowledge_entry_builder_requires_evidence_relation():
    lesson = Lesson(
        id="lesson_orphan",
        title="Orphan lesson",
        body="Looks useful but has no source relation",
        confidence=0.8,
    )

    try:
        KnowledgeEntryBuilder.from_lesson(lesson)
        assert False, "Expected ValueError for lesson without evidence relations"
    except ValueError as exc:
        assert "evidence or source relations" in str(exc)


def test_knowledge_entry_rejects_state_truth_object_type():
    try:
        KnowledgeEntry(
            title="Should fail",
            narrative="A narrative must not masquerade as an analysis fact",
            knowledge_type="analysis",
            derived_from=KnowledgeRef(
                object_type="lesson",
                object_id="lesson_1",
                relation="derived_from",
            ),
            evidence_refs=(KnowledgeRef(object_type="review", object_id="review_1", relation="supports"),),
        )
        assert False, "Expected ValueError for state truth masquerade"
    except ValueError as exc:
        assert "cannot masquerade as state truth" in str(exc)


def test_knowledge_entry_builder_maps_lesson_to_structured_knowledge():
    lesson = Lesson(
        id="lesson_1",
        review_id="review_1",
        recommendation_id="reco_1",
        title="Review lesson",
        body="Wait for confirmation candle",
        source_refs=["audit:review_completed"],
        confidence=0.8,
    )

    entry = KnowledgeEntryBuilder.from_lesson(lesson)

    assert entry.knowledge_type == "lesson"
    assert entry.derived_from.object_type == "lesson"
    assert entry.derived_from.object_id == "lesson_1"
    assert {ref.object_type for ref in entry.evidence_refs} == {
        "review",
        "recommendation",
        "source_ref",
    }
    assert entry.feedback_targets == ("governance", "intelligence")
