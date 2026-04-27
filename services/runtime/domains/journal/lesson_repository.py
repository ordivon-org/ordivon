from sqlalchemy.orm import Session

from domains.journal.lesson_models import Lesson
from domains.journal.lesson_orm import LessonORM
from shared.utils.serialization import from_json_text, to_json_text


class LessonRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def create(self, lesson: Lesson) -> LessonORM:
        row = LessonORM(
            id=lesson.id,
            review_id=lesson.review_id,
            recommendation_id=lesson.recommendation_id,
            title=lesson.title,
            body=lesson.body,
            lesson_type=lesson.lesson_type,
            tags_json=to_json_text(lesson.tags),
            confidence=lesson.confidence,
            source_refs_json=to_json_text(lesson.source_refs),
            wiki_path=lesson.wiki_path,
        )
        self.db.add(row)
        self.db.flush()
        return row

    def list_recent(self, limit: int = 50) -> list[LessonORM]:
        return self.db.query(LessonORM).order_by(LessonORM.created_at.desc()).limit(limit).all()

    def list_for_recommendation(self, recommendation_id: str) -> list[LessonORM]:
        return (
            self.db.query(LessonORM)
            .filter(LessonORM.recommendation_id == recommendation_id)
            .order_by(LessonORM.created_at.desc())
            .all()
        )

    def list_for_review(self, review_id: str) -> list[LessonORM]:
        """Return all lessons linked to a specific review_id.

        Unlike list_for_recommendation(), this does NOT require
        recommendation_id — it queries directly by review_id.
        Used by H-10 KF generalization for finance DecisionIntake reviews
        that have no recommendation_id.
        """
        return (
            self.db.query(LessonORM).filter(LessonORM.review_id == review_id).order_by(LessonORM.created_at.asc()).all()
        )

    def to_model(self, row: LessonORM) -> Lesson:
        return Lesson(
            id=row.id,
            review_id=row.review_id,
            recommendation_id=row.recommendation_id,
            title=row.title,
            body=row.body,
            lesson_type=row.lesson_type,
            tags=from_json_text(row.tags_json, []),
            confidence=row.confidence,
            source_refs=from_json_text(row.source_refs_json, []),
            wiki_path=row.wiki_path,
            created_at=row.created_at.isoformat(),
        )
