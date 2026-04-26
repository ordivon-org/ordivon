from __future__ import annotations

from sqlalchemy.orm import Session

from domains.journal.lesson_repository import LessonRepository
from domains.journal.repository import ReviewRepository
from domains.strategy.outcome_repository import OutcomeRepository
from knowledge.adapters import KnowledgeEntryBuilder
from knowledge.models import KnowledgeEntry, KnowledgeRef


class LessonExtractionService:
    """Derives structured knowledge entries from persisted lesson and outcome facts."""

    def __init__(self, db: Session) -> None:
        self.db = db
        self.lesson_repository = LessonRepository(db)
        self.review_repository = ReviewRepository(db)
        self.outcome_repository = OutcomeRepository(db)

    def extract_for_recommendation(self, recommendation_id: str) -> list[KnowledgeEntry]:
        lessons = [
            self.lesson_repository.to_model(row)
            for row in self.lesson_repository.list_for_recommendation(recommendation_id)
        ]
        if not lessons:
            return []

        outcomes = [
            self.outcome_repository.to_model(row)
            for row in self.outcome_repository.list_for_recommendation(recommendation_id)
        ]
        latest_outcome = outcomes[0] if outcomes else None

        entries: list[KnowledgeEntry] = []
        for lesson in lessons:
            if latest_outcome is None:
                entries.append(KnowledgeEntryBuilder.from_lesson(lesson))
            else:
                entries.append(KnowledgeEntryBuilder.from_lesson_with_outcome(lesson, latest_outcome))
        return entries

    def extract_for_review(self, review_id: str) -> list[KnowledgeEntry]:
        review = self.review_repository.get(review_id)
        if review is None or review.recommendation_id is None:
            return []
        return self.extract_for_recommendation(review.recommendation_id)

    def extract_for_review_by_id(self, review_id: str) -> list[KnowledgeEntry]:
        """Derive KnowledgeEntries from lessons linked to a review.

        Works WITHOUT recommendation_id — uses review-scoped lesson
        lookup and outcome_ref linkage to find the associated outcome.
        This is the H-10 generalization path for finance DecisionIntake
        reviews that have no recommendation_id.
        """
        from domains.finance_outcome.repository import (
            FinanceManualOutcomeRepository,
        )

        review_row = self.review_repository.get(review_id)
        if review_row is None:
            return []

        lesson_rows = self.lesson_repository.list_for_review(review_id)
        if not lesson_rows:
            return []

        lessons = [self.lesson_repository.to_model(row) for row in lesson_rows]

        # Try to find the linked outcome via outcome_ref
        latest_outcome = None
        if (
            review_row.outcome_ref_id
            and review_row.outcome_ref_type == "finance_manual_outcome"
        ):
            outcome_repo = FinanceManualOutcomeRepository(self.db)
            outcome_row = outcome_repo.get(review_row.outcome_ref_id)
            if outcome_row:
                latest_outcome = outcome_repo.to_model(outcome_row)

        entries: list[KnowledgeEntry] = []
        for lesson in lessons:
            entry = KnowledgeEntryBuilder.from_lesson(lesson)
            if latest_outcome is not None:
                outcome_ref = KnowledgeRef(
                    object_type="finance_manual_outcome",
                    object_id=latest_outcome.id,
                    relation="supports",
                )
                entry = KnowledgeEntry(
                    title=entry.title,
                    narrative=entry.narrative,
                    knowledge_type=entry.knowledge_type,
                    derived_from=entry.derived_from,
                    evidence_refs=entry.evidence_refs + (outcome_ref,),
                    feedback_targets=entry.feedback_targets,
                    confidence=entry.confidence,
                    created_at=entry.created_at,
                )
            entries.append(entry)
        return entries
