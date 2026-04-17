from sqlalchemy.orm import Session

from pfios.domain.lessons.models import Lesson
from pfios.domain.lessons.orm import LessonORM
from pfios.core.utils.serialization import to_json_text, from_json_text


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
        self.db.commit()
        self.db.refresh(row)
        return row

    def list_recent(self, limit: int = 50) -> list[LessonORM]:
        return (
            self.db.query(LessonORM)
            .order_by(LessonORM.created_at.desc())
            .limit(limit)
            .all()
        )

    def list_for_recommendation(self, recommendation_id: str) -> list[LessonORM]:
        return (
            self.db.query(LessonORM)
            .filter(LessonORM.recommendation_id == recommendation_id)
            .order_by(LessonORM.created_at.desc())
            .all()
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
