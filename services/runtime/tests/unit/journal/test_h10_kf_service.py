"""H-10: ReviewService._build_knowledge_feedback 回退逻辑测试."""

import pytest
from datetime import datetime, timezone
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from state.db.base import Base
from domains.journal.orm import ReviewORM
from domains.journal.lesson_orm import LessonORM
from domains.journal.repository import ReviewRepository
from domains.journal.lesson_service import LessonService
from domains.journal.service import ReviewService
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


def test_kf_generated_when_recommendation_id_is_none(db):
    """H-10: recommendation_id=None 时，K-F 通过 review 回退路径生成。"""
    now = datetime.now(timezone.utc)

    # Setup: outcome + review + lesson
    outcome = FinanceManualOutcomeORM(
        id="fmout-kf-001",
        decision_intake_id="intake-kf-001",
        execution_receipt_id="exrcpt-kf-001",
        outcome_source="manual",
        observed_outcome="Price went up 5%",
        verdict="validated",
        variance_summary="Clean",
        plan_followed=True,
        created_at=now,
    )
    db.add(outcome)

    review = ReviewORM(
        id="review-kf-001",
        recommendation_id=None,
        review_type="recommendation_postmortem",
        status="completed",
        outcome_ref_type="finance_manual_outcome",
        outcome_ref_id="fmout-kf-001",
        expected_outcome="Price goes up",
        observed_outcome="Price went up 5%",
        verdict="validated",
        cause_tags_json='["plan_execution"]',
        lessons_json='["Good entry timing"]',
        followup_actions_json="[]",
        created_at=now,
        completed_at=now,
    )
    db.add(review)

    lesson = LessonORM(
        id="lesson-kf-001",
        review_id="review-kf-001",
        recommendation_id=None,
        body="Good entry timing on BTC support retest",
        source_refs_json="[]",
        created_at=now,
    )
    db.add(lesson)
    db.commit()

    # Directly call extraction fallback
    extraction = LessonExtractionService(db)
    entries = extraction.extract_for_review_by_id("review-kf-001")
    assert len(entries) >= 1
    assert entries[0].narrative is not None


def test_existing_recommendation_path_still_works(db):
    """H-10: 有 recommendation_id 的 review 不受影响。"""
    now = datetime.now(timezone.utc)

    review = ReviewORM(
        id="review-with-rec",
        recommendation_id="rec-001",
        review_type="recommendation_postmortem",
        status="completed",
        expected_outcome="Price goes up",
        observed_outcome="Price went up",
        verdict="validated",
        cause_tags_json="[]",
        lessons_json="[]",
        followup_actions_json="[]",
        created_at=now,
        completed_at=now,
    )
    db.add(review)

    lesson = LessonORM(
        id="lesson-with-rec",
        review_id="review-with-rec",
        recommendation_id="rec-001",
        body="Lesson for recommendation-backed review",
        source_refs_json="[]",
        created_at=now,
    )
    db.add(lesson)
    db.commit()

    # Existing path should still work
    extraction = LessonExtractionService(db)
    entries = extraction.extract_for_recommendation("rec-001")
    assert len(entries) >= 1
