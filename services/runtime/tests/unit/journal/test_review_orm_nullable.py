"""ReviewORM outcome_ref nullable field invariant tests.

Ensures that outcome_ref_type and outcome_ref_id are nullable columns
that survive the DB round-trip correctly, both when omitted and when
populated with known values.
"""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from state.db.base import Base
from domains.journal.orm import ReviewORM


@pytest.fixture
def db():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()


def test_review_orm_has_outcome_ref_columns():
    """ReviewORM exposes outcome_ref_type and outcome_ref_id attributes."""
    assert hasattr(ReviewORM, "outcome_ref_type")
    assert hasattr(ReviewORM, "outcome_ref_id")


def test_review_orm_without_outcome_ref_defaults_to_none(db):
    """Create ReviewORM without outcome_ref_* → flush → read back → both are None."""
    review = ReviewORM(
        id="review-null-001",
        review_type="recommendation_postmortem",
        status="pending",
        expected_outcome="price moves up",
    )
    db.add(review)
    db.flush()

    row = db.query(ReviewORM).filter_by(id="review-null-001").one()

    assert row.outcome_ref_type is None
    assert row.outcome_ref_id is None


def test_review_orm_with_outcome_ref_preserves_values(db):
    """Create ReviewORM with outcome_ref_type and outcome_ref_id → flush
    → read back → both values are preserved."""
    review = ReviewORM(
        id="review-outcome-001",
        review_type="recommendation_postmortem",
        status="pending",
        expected_outcome="price moves up",
        outcome_ref_type="finance_manual_outcome",
        outcome_ref_id="outcome_abc_123",
    )
    db.add(review)
    db.flush()

    row = db.query(ReviewORM).filter_by(id="review-outcome-001").one()

    assert row.outcome_ref_type == "finance_manual_outcome"
    assert row.outcome_ref_id == "outcome_abc_123"
