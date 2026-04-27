from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from domains.journal.lesson_repository import LessonRepository
from domains.journal.lesson_service import LessonService
from domains.journal.models import Review
from domains.journal.repository import ReviewRepository
from domains.journal.service import ReviewService
from knowledge import KnowledgeEntryBuilder
from shared.enums.domain import ReviewStatus, ReviewVerdict
from state.db.base import Base


def _make_db():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    testing_session = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)
    return engine, testing_session


def test_completed_review_lessons_can_be_derived_into_knowledge_entries():
    engine, testing_session = _make_db()
    db = testing_session()

    try:
        lesson_repo = LessonRepository(db)
        lesson_service = LessonService(lesson_repo)
        review_service = ReviewService(ReviewRepository(db), lesson_service)

        review = Review(
            recommendation_id="reco_knowledge",
            review_type="recommendation_postmortem",
            status=ReviewStatus.PENDING,
            expected_outcome="Trend continuation",
        )
        row = review_service.create(review)

        review_row, lesson_rows, knowledge_feedback = review_service.complete_review(
            review_id=row.id,
            observed_outcome="Trend failed",
            verdict=ReviewVerdict.INVALIDATED,
            variance_summary="Entry lacked confirmation",
            cause_tags=["confirmation"],
            lessons=["Wait for confirmation candle before entry"],
            followup_actions=["Tighten checklist"],
        )

        assert lesson_rows
        assert knowledge_feedback is not None
        assert review_row.id == row.id

        lesson_model = lesson_repo.to_model(lesson_rows[0])
        knowledge_entry = KnowledgeEntryBuilder.from_lesson(lesson_model)

        assert knowledge_entry.derived_from.object_type == "lesson"
        assert knowledge_entry.derived_from.object_id == lesson_rows[0].id
        assert {ref.object_type for ref in knowledge_entry.evidence_refs} == {
            "review",
            "recommendation",
            "source_ref",
        }
        assert knowledge_entry.narrative == "Wait for confirmation candle before entry"
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)
