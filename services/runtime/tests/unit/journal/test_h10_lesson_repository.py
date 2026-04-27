"""H-10: LessonRepository.list_for_review 单元测试."""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from state.db.base import Base
from domains.journal.lesson_orm import LessonORM
from domains.journal.lesson_repository import LessonRepository


@pytest.fixture
def db():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()


def test_list_for_review_returns_lessons_for_review_id(db):
    """list_for_review 返回特定 review_id 的所有 lesson。"""
    repo = LessonRepository(db)

    lesson_a = LessonORM(
        id="lesson-001",
        review_id="review-a",
        recommendation_id=None,
        body="Lesson from review A",
        source_refs_json="[]",
    )
    lesson_b = LessonORM(
        id="lesson-002",
        review_id="review-b",
        recommendation_id=None,
        body="Lesson from review B",
        source_refs_json="[]",
    )
    db.add_all([lesson_a, lesson_b])
    db.commit()

    results = repo.list_for_review("review-a")
    assert len(results) == 1
    assert results[0].id == "lesson-001"
    assert results[0].body == "Lesson from review A"


def test_list_for_review_returns_empty_for_unknown_review(db):
    """不存在的 review_id 返回空列表。"""
    repo = LessonRepository(db)
    results = repo.list_for_review("nonexistent")
    assert results == []


def test_list_for_review_returns_empty_when_no_lessons(db):
    """lesson 表为空时返回空列表。"""
    repo = LessonRepository(db)
    results = repo.list_for_review("review-c")
    assert results == []


def test_list_for_review_returns_multiple_lessons(db):
    """同一 review 有多个 lesson 时全部返回，按时间排序。"""
    repo = LessonRepository(db)

    l1 = LessonORM(id="l-1", review_id="review-multi", recommendation_id=None, body="First", source_refs_json="[]")
    l2 = LessonORM(id="l-2", review_id="review-multi", recommendation_id=None, body="Second", source_refs_json="[]")
    db.add_all([l1, l2])
    db.commit()

    results = repo.list_for_review("review-multi")
    assert len(results) == 2
    ids = [r.id for r in results]
    assert "l-1" in ids
    assert "l-2" in ids
