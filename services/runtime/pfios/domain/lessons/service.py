from pfios.domain.lessons.models import Lesson
from pfios.domain.lessons.repository import LessonRepository


class LessonService:
    def __init__(self, repository: LessonRepository) -> None:
        self.repository = repository

    def create(self, lesson: Lesson):
        return self.repository.create(lesson)

    def list_recent(self, limit: int = 50):
        return self.repository.list_recent(limit=limit)

    def list_for_recommendation(self, recommendation_id: str):
        return self.repository.list_for_recommendation(recommendation_id)
