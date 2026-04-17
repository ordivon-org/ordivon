from pfios.domain.review.models import Review
from pfios.domain.review.repository import ReviewRepository
from pfios.domain.common.enums import ReviewStatus, ReviewVerdict
from pfios.domain.lessons.models import Lesson
from pfios.domain.lessons.service import LessonService
from pfios.domain.common.errors import DomainNotFound
from pfios.audit.auditor import RiskAuditor


class ReviewService:
    def __init__(
        self,
        review_repository: ReviewRepository,
        lesson_service: LessonService,
        auditor: RiskAuditor,
    ) -> None:
        self.review_repository = review_repository
        self.lesson_service = lesson_service
        self.auditor = auditor

    def create(self, review: Review):
        return self.review_repository.create(review)

    def get_model(self, review_id: str) -> Review:
        row = self.review_repository.get(review_id)
        if row is None:
            raise DomainNotFound(f"Review not found: {review_id}")
        return self.review_repository.to_model(row)

    def complete_review(
        self,
        review_id: str,
        observed_outcome: str,
        verdict: ReviewVerdict,
        variance_summary: str | None,
        cause_tags: list[str],
        lessons: list[str],
        followup_actions: list[str],
    ):
        row = self.review_repository.get(review_id)
        if row is None:
            raise DomainNotFound(f"Review not found: {review_id}")

        row.status = ReviewStatus.COMPLETED.value
        row.observed_outcome = observed_outcome
        row.verdict = verdict.value
        row.variance_summary = variance_summary
        row.cause_tags_json = self.review_repository.encode_list(cause_tags)
        row.lessons_json = self.review_repository.encode_list(lessons)
        row.followup_actions_json = self.review_repository.encode_list(followup_actions)

        self.review_repository.db.commit()
        self.review_repository.db.refresh(row)

        lesson_rows = []
        for idx, lesson_text in enumerate(lessons, start=1):
            lesson_model = Lesson(
                review_id=row.id,
                recommendation_id=row.recommendation_id,
                title=f"Lesson {idx} from review {row.id}",
                body=lesson_text,
                lesson_type="review_learning",
                tags=cause_tags,
                confidence=0.8,
            )
            lesson_row = self.lesson_service.create(lesson_model)
            lesson_rows.append(lesson_row)

            # Audit Lesson (Wired!)
            self.auditor.record_event(
                "lesson_persisted",
                {
                    "lesson_id": lesson_row.id,
                    "review_id": row.id,
                    "recommendation_id": row.recommendation_id,
                },
                entity_type="lesson",
                entity_id=lesson_row.id,
                review_id=row.id,
                recommendation_id=row.recommendation_id,
            )

        return row, lesson_rows
