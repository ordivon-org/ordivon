from domains.journal.lesson_models import Lesson
from domains.journal.lesson_orm import LessonORM
from domains.journal.lesson_repository import LessonRepository
from domains.journal.lesson_service import LessonService
from domains.journal.lesson_models import Lesson as LegacyLesson
from domains.journal.lesson_orm import LessonORM as LegacyLessonORM
from domains.journal.lesson_repository import LessonRepository as LegacyLessonRepository
from domains.journal.lesson_service import LessonService as LegacyLessonService


def test_root_lesson_imports_are_available():
    assert Lesson is not None
    assert LessonORM is not None
    assert LessonRepository is not None
    assert LessonService is not None


def test_legacy_lesson_imports_still_resolve():
    assert LegacyLesson.__name__ == Lesson.__name__
    assert LegacyLessonORM.__name__ == LessonORM.__name__
    assert LegacyLessonRepository.__name__ == LessonRepository.__name__
    assert LegacyLessonService.__name__ == LessonService.__name__
