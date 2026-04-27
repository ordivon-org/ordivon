"""Lesson.source_refs_json round-trip invariant tests.

Ensures that source_refs (a list of strings) serialised into
source_refs_json and deserialised back survive the DB round-trip
without loss or corruption.
"""

import json

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from state.db.base import Base
from domains.journal.lesson_orm import LessonORM


@pytest.fixture
def db():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()


def test_source_refs_roundtrip_multiple_refs(db):
    """Create LessonORM with source_refs_json containing three refs,
    read back, parse, and verify all three survive."""
    source_refs = [
        "recommendation:reco_001",
        "finance_manual_outcome:out_001",
        "review:review_001",
    ]

    lesson = LessonORM(
        id="lesson-rt-001",
        review_id="review-001",
        recommendation_id="reco_001",
        title="Round-trip test",
        body="Testing source_refs_json serialisation",
        source_refs_json=json.dumps(source_refs),
    )
    db.add(lesson)
    db.commit()

    # Read back from DB
    row = db.query(LessonORM).filter_by(id="lesson-rt-001").one()
    parsed = json.loads(row.source_refs_json)

    assert parsed == source_refs
    assert len(parsed) == 3
    assert "recommendation:reco_001" in parsed
    assert "finance_manual_outcome:out_001" in parsed
    assert "review:review_001" in parsed


def test_source_refs_empty_list_survives_roundtrip(db):
    """Empty source_refs list survives as [] not None/null."""
    lesson = LessonORM(
        id="lesson-rt-empty",
        review_id="review-001",
        recommendation_id=None,
        title="Empty refs",
        body="Should keep empty list",
    )
    db.add(lesson)
    db.commit()

    row = db.query(LessonORM).filter_by(id="lesson-rt-empty").one()

    # Must not be None
    assert row.source_refs_json is not None
    # Must parse to an empty list
    parsed = json.loads(row.source_refs_json)
    assert parsed == []
    assert isinstance(parsed, list)


def test_source_refs_default_is_empty_list(db):
    """The ORM default for source_refs_json is '[]' — verify it behaves."""
    lesson = LessonORM(
        id="lesson-rt-default",
        review_id="review-002",
        title="Default test",
    )
    db.add(lesson)
    db.commit()

    row = db.query(LessonORM).filter_by(id="lesson-rt-default").one()

    assert row.source_refs_json == "[]"
    parsed = json.loads(row.source_refs_json)
    assert parsed == []
    assert isinstance(parsed, list)
