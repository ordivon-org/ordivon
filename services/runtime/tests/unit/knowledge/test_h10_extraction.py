"""H-10: LessonExtractionService.extract_for_review_by_id 单元测试."""

import pytest
from datetime import datetime, timezone
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from state.db.base import Base
from domains.journal.lesson_orm import LessonORM
from domains.journal.orm import ReviewORM
from domains.finance_outcome.orm import FinanceManualOutcomeORM
from knowledge.extraction import LessonExtractionService


@pytest.fixture
def db():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()


def test_extract_for_review_by_id_returns_entries(db):
    """有 lesson + outcome_ref 的 review → 返回 KnowledgeEntry 列表。"""
    now = datetime.now(timezone.utc)

    outcome = FinanceManualOutcomeORM(
        id="fmout-h10-001",
        decision_intake_id="intake-h10-001",
        execution_receipt_id="exrcpt-h10-001",
        outcome_source="manual",
        observed_outcome="Price went up 5%",
        verdict="validated",
        variance_summary="Clean execution",
        plan_followed=True,
        created_at=now,
    )
    db.add(outcome)

    review = ReviewORM(
        id="review-h10-001",
        recommendation_id=None,
        review_type="recommendation_postmortem",
        status="completed",
        outcome_ref_type="finance_manual_outcome",
        outcome_ref_id="fmout-h10-001",
        created_at=now,
    )
    db.add(review)

    lesson = LessonORM(
        id="lesson-h10-001",
        review_id="review-h10-001",
        recommendation_id=None,
        body="Stop loss should be wider on volatile pairs",
        source_refs_json="[]",
        created_at=now,
    )
    db.add(lesson)
    db.commit()

    service = LessonExtractionService(db)
    entries = service.extract_for_review_by_id("review-h10-001")

    assert len(entries) >= 1
    assert entries[0].narrative is not None


def test_extract_for_review_by_id_returns_empty_for_no_lessons(db):
    """没有 lesson → 返回空列表。"""
    now = datetime.now(timezone.utc)
    review = ReviewORM(
        id="review-empty",
        recommendation_id=None,
        review_type="recommendation_postmortem",
        status="completed",
        outcome_ref_type="finance_manual_outcome",
        outcome_ref_id="fmout-xxx",
        created_at=now,
    )
    db.add(review)
    db.commit()

    service = LessonExtractionService(db)
    entries = service.extract_for_review_by_id("review-empty")
    assert entries == []


def test_extract_for_review_by_id_returns_empty_for_unknown_review(db):
    """不存在的 review_id → 返回空列表。"""
    service = LessonExtractionService(db)
    entries = service.extract_for_review_by_id("nonexistent")
    assert entries == []


def test_extract_for_review_by_id_works_without_outcome_ref(db):
    """review 没有 outcome_ref → 仍返回 KnowledgeEntry（from_lesson 路径）。"""
    now = datetime.now(timezone.utc)

    review = ReviewORM(
        id="review-no-outcome",
        recommendation_id=None,
        review_type="recommendation_postmortem",
        status="completed",
        outcome_ref_type=None,
        outcome_ref_id=None,
        created_at=now,
    )
    db.add(review)

    lesson = LessonORM(
        id="lesson-no-outcome",
        review_id="review-no-outcome",
        recommendation_id=None,
        body="A lesson without linked outcome",
        source_refs_json="[]",
        created_at=now,
    )
    db.add(lesson)
    db.commit()

    service = LessonExtractionService(db)
    entries = service.extract_for_review_by_id("review-no-outcome")

    assert len(entries) >= 1
    # Without outcome, uses from_lesson (not from_lesson_with_outcome)
    assert entries[0].narrative is not None
