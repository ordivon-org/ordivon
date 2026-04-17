from pfios.core.db.bootstrap import init_db
from pfios.core.db.session import SessionLocal
from pfios.domain.lessons.models import Lesson
from pfios.domain.lessons.repository import LessonRepository


def test_lesson_repository_create():
    init_db()
    db = SessionLocal()

    try:
        repo = LessonRepository(db)
        row = repo.create(
            Lesson(
                review_id="review_x",
                recommendation_id="reco_x",
                title="Test lesson",
                body="This is a lesson",
                tags=["risk", "timing"],
                confidence=0.9,
            )
        )
        assert row.title == "Test lesson"
    finally:
        db.close()
