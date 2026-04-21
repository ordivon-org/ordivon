from __future__ import annotations

from sqlalchemy.orm import Session

from domains.journal.lesson_repository import LessonRepository
from domains.journal.repository import ReviewRepository
from domains.strategy.outcome_repository import OutcomeRepository
from knowledge.adapters import KnowledgeEntryBuilder
from knowledge.models import KnowledgeEntry


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
