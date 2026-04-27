"""Prove review completion creates no CandidateRule or Policy side effects."""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from state.db.base import Base
from domains.candidate_rules.orm import CandidateRuleORM
from domains.journal.models import Review
from domains.journal.repository import ReviewRepository
from domains.journal.service import ReviewService
from domains.journal.lesson_service import LessonService
from domains.journal.lesson_repository import LessonRepository
from shared.enums.domain import ReviewVerdict


@pytest.fixture
def db() -> Session:
    engine = create_engine("sqlite:///:memory:", poolclass=StaticPool)
    Base.metadata.create_all(bind=engine)
    with Session(engine) as session:
        yield session
    Base.metadata.drop_all(bind=engine)


def test_complete_review_does_not_create_candidate_rule(db: Session):
    """After complete_review, CandidateRuleORM count must not increase."""
    service = ReviewService(
        review_repository=ReviewRepository(db),
        lesson_service=LessonService(LessonRepository(db)),
    )

    review = Review(
        recommendation_id="reco_no_side",
        review_type="recommendation_postmortem",
        expected_outcome="Test expected",
    )
    row = service.create(review)
    db.flush()

    before_count = db.query(CandidateRuleORM).count()

    service.complete_review(
        review_id=row.id,
        observed_outcome="Test observed",
        verdict=ReviewVerdict.VALIDATED,
        variance_summary=None,
        cause_tags=["test"],
        lessons=["Test lesson"],
        followup_actions=[],
        emit_review_completed_audit=False,
    )
    db.flush()

    after_count = db.query(CandidateRuleORM).count()
    assert after_count == before_count, (
        f"complete_review auto-created CandidateRule: before={before_count}, after={after_count}"
    )


def test_complete_review_does_not_create_policy_audit_events(db: Session):
    """After complete_review, no audit events with 'policy' or 'promote' type."""
    from governance.audit.orm import AuditEventORM

    service = ReviewService(
        review_repository=ReviewRepository(db),
        lesson_service=LessonService(LessonRepository(db)),
    )
    review = Review(
        recommendation_id="reco_no_policy_audit",
        review_type="recommendation_postmortem",
        expected_outcome="Test",
    )
    row = service.create(review)
    db.flush()

    service.complete_review(
        review_id=row.id,
        observed_outcome="Test",
        verdict=ReviewVerdict.VALIDATED,
        variance_summary=None,
        cause_tags=["test"],
        lessons=["Test"],
        followup_actions=[],
        emit_review_completed_audit=False,
    )
    db.flush()

    policy_events = (
        db.query(AuditEventORM)
        .filter(AuditEventORM.event_type.like("%policy%") | AuditEventORM.event_type.like("%promote%"))
        .count()
    )

    assert policy_events == 0, f"complete_review generated policy-related audit events: {policy_events}"
