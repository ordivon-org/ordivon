"""extract_for_review 单元测试 — 验证通过 review_id 委托到 extract_for_recommendation.

extract_for_review(review_id) 是 H-3 路径:
  1. 查找 review → 获取 recommendation_id
  2. 如果有 recommendation_id → 委托 extract_for_recommendation
  3. 如果没有 recommendation_id → 返回空列表
"""

from datetime import datetime, timezone

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from domains.journal.lesson_orm import LessonORM
from domains.journal.orm import ReviewORM
from domains.strategy.orm import RecommendationORM
from knowledge.extraction import LessonExtractionService
from state.db.base import Base


@pytest.fixture
def db():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()


def test_extract_for_review_delegates_to_extract_for_recommendation(db):
    """有 recommendation_id 的 review → 委托到 extract_for_recommendation 路径。"""
    now = datetime.now(timezone.utc)

    rec = RecommendationORM(
        id="reco-er-001",
        analysis_id="analysis-er-001",
        title="Test Recommendation",
        summary="Summary",
        created_at=now,
    )
    db.add(rec)

    review = ReviewORM(
        id="review-er-001",
        recommendation_id="reco-er-001",
        review_type="recommendation_postmortem",
        status="completed",
        created_at=now,
    )
    db.add(review)

    lesson = LessonORM(
        id="lesson-er-001",
        review_id="review-er-001",
        recommendation_id="reco-er-001",
        body="A lesson from this review",
        source_refs_json="[]",
        created_at=now,
    )
    db.add(lesson)
    db.commit()

    service = LessonExtractionService(db)
    entries = service.extract_for_review("review-er-001")

    assert len(entries) >= 1
    assert entries[0].narrative is not None


def test_extract_for_review_returns_empty_for_missing_review(db):
    """不存在的 review_id → 返回空列表。"""
    service = LessonExtractionService(db)
    entries = service.extract_for_review("nonexistent-review")
    assert entries == []


def test_extract_for_review_returns_empty_when_no_recommendation_id(db):
    """review 存在但没有 recommendation_id → 返回空列表（不尝试 extract_for_review_by_id）。"""
    now = datetime.now(timezone.utc)

    review = ReviewORM(
        id="review-er-no-reco",
        recommendation_id=None,
        review_type="recommendation_postmortem",
        status="completed",
        created_at=now,
    )
    db.add(review)
    db.commit()

    service = LessonExtractionService(db)
    entries = service.extract_for_review("review-er-no-reco")
    assert entries == []


def test_extract_for_review_returns_empty_when_no_lessons(db):
    """有 recommendation_id 但没有 lessons → 返回空列表。"""
    now = datetime.now(timezone.utc)

    rec = RecommendationORM(
        id="reco-er-no-lessons",
        analysis_id="analysis-er-no-lessons",
        title="No Lessons",
        summary="Summary",
        created_at=now,
    )
    db.add(rec)

    review = ReviewORM(
        id="review-er-no-lessons",
        recommendation_id="reco-er-no-lessons",
        review_type="recommendation_postmortem",
        status="completed",
        created_at=now,
    )
    db.add(review)
    db.commit()

    service = LessonExtractionService(db)
    entries = service.extract_for_review("review-er-no-lessons")
    assert entries == []
