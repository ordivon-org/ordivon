from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from domains.journal.lesson_models import Lesson
from domains.journal.lesson_repository import LessonRepository
from domains.strategy.outcome_models import OutcomeSnapshot
from domains.strategy.outcome_repository import OutcomeRepository
from knowledge import LessonExtractionService, KnowledgeEntryBuilder
from state.db.base import Base
from shared.enums.domain import OutcomeState


def _make_db():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    testing_session = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)
    return engine, testing_session


def test_builder_adds_outcome_evidence_and_feedback_targets():
    lesson = Lesson(
        id="lesson_extract_1",
        review_id="review_1",
        recommendation_id="reco_1",
        title="Outcome-aware lesson",
        body="Wait for confirmation",
        source_refs=["audit:review_completed"],
        confidence=0.8,
    )
    outcome = OutcomeSnapshot(
        id="outcome_1",
        recommendation_id="reco_1",
        outcome_state=OutcomeState.FAILED,
        trigger_reason="review_completion_backfill",
    )

    entry = KnowledgeEntryBuilder.from_lesson_with_outcome(lesson, outcome)

    assert any(ref.object_type == "outcome_snapshot" for ref in entry.evidence_refs)
    assert entry.feedback_targets == ("governance", "intelligence")


def test_lesson_extraction_returns_empty_when_no_lessons_exist():
    engine, testing_session = _make_db()
    db = testing_session()
    try:
        service = LessonExtractionService(db)
        assert service.extract_for_recommendation("reco_missing") == []
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


def test_lesson_extraction_uses_latest_outcome_when_present():
    engine, testing_session = _make_db()
    db = testing_session()
    try:
        LessonRepository(db).create(
            Lesson(
                id="lesson_extract_2",
                review_id="review_2",
                recommendation_id="reco_extract_1",
                title="Use confirmation candle",
                body="Wait for confirmation candle",
                source_refs=["audit:review_completed"],
                confidence=0.8,
            )
        )
        OutcomeRepository(db).create(
            OutcomeSnapshot(
                id="outcome_extract_1",
                recommendation_id="reco_extract_1",
                outcome_state=OutcomeState.FAILED,
                trigger_reason="review_completion_backfill",
            )
        )
        service = LessonExtractionService(db)

        entries = service.extract_for_recommendation("reco_extract_1")

        assert len(entries) == 1
        assert any(ref.object_type == "outcome_snapshot" for ref in entries[0].evidence_refs)
        assert entries[0].feedback_targets == ("governance", "intelligence")
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)
