from __future__ import annotations

from domains.journal.lesson_models import Lesson
from domains.strategy.outcome_models import OutcomeSnapshot
from shared.enums.domain import OutcomeState
from knowledge.models import KnowledgeEntry, KnowledgeRef


class KnowledgeEntryBuilder:
    """Builds knowledge-layer representations from persisted lesson facts."""

    @staticmethod
    def from_lesson(lesson: Lesson) -> KnowledgeEntry:
        if not lesson.id:
            raise ValueError("Lesson id is required to derive a KnowledgeEntry")

        evidence_refs: list[KnowledgeRef] = []

        if lesson.review_id:
            evidence_refs.append(
                KnowledgeRef(object_type="review", object_id=lesson.review_id, relation="supports")
            )
        if lesson.recommendation_id:
            evidence_refs.append(
                KnowledgeRef(
                    object_type="recommendation",
                    object_id=lesson.recommendation_id,
                    relation="supports",
                )
            )
        if lesson.wiki_path:
            evidence_refs.append(
                KnowledgeRef(
                    object_type="wiki_document",
                    object_id=lesson.id,
                    relation="narrative_source",
                    path=lesson.wiki_path,
                )
            )
        for ref in lesson.source_refs:
            evidence_refs.append(
                KnowledgeRef(object_type="source_ref", object_id=ref, relation="supports")
            )

        if not evidence_refs:
            raise ValueError(
                "Cannot derive KnowledgeEntry from Lesson without evidence or source relations"
            )

        return KnowledgeEntry(
            title=lesson.title or f"Lesson {lesson.id}",
            narrative=lesson.body,
            knowledge_type="lesson",
            derived_from=KnowledgeRef(
                object_type="lesson",
                object_id=lesson.id,
                relation="derived_from",
            ),
            evidence_refs=tuple(evidence_refs),
            feedback_targets=("governance", "intelligence"),
            confidence=lesson.confidence,
            created_at=lesson.created_at,
        )

    @staticmethod
    def from_lesson_with_outcome(
        lesson: Lesson,
        outcome: OutcomeSnapshot,
    ) -> KnowledgeEntry:
        base_entry = KnowledgeEntryBuilder.from_lesson(lesson)
        outcome_ref = KnowledgeRef(
            object_type="outcome_snapshot",
            object_id=outcome.id,
            relation="supports",
        )
        return KnowledgeEntry(
            title=base_entry.title,
            narrative=base_entry.narrative,
            knowledge_type=base_entry.knowledge_type,
            derived_from=base_entry.derived_from,
            evidence_refs=base_entry.evidence_refs + (outcome_ref,),
            feedback_targets=KnowledgeEntryBuilder._feedback_targets_for_outcome(outcome.outcome_state),
            confidence=base_entry.confidence,
            created_at=base_entry.created_at,
        )

    @staticmethod
    def _feedback_targets_for_outcome(outcome_state: OutcomeState) -> tuple[str, ...]:
        if outcome_state == OutcomeState.FAILED:
            return ("governance", "intelligence")
        if outcome_state == OutcomeState.SATISFIED:
            return ("reporting", "intelligence")
        if outcome_state == OutcomeState.IMPROVING:
            return ("intelligence",)
        return ("knowledge_review",)
