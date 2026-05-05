import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from unittest.mock import MagicMock

from state.db.base import Base
from domains.strategy.repository import RecommendationRepository
from domains.strategy.service import RecommendationService
from domains.strategy.models import Recommendation
from domains.journal.repository import ReviewRepository
from domains.journal.service import ReviewService
from domains.journal.models import Review
from domains.journal.lesson_repository import LessonRepository
from domains.journal.lesson_service import LessonService
from domains.journal.issue_repository import IssueRepository
from domains.journal.issue_service import IssueService
from domains.journal.issue_models import Issue
from governance_engine.audit.auditor import RiskAuditor
from governance_engine.audit.orm import AuditEventORM
from shared.enums.domain import RecommendationStatus, ReviewVerdict

# Setup in-memory SQLite for transaction testing
engine = create_engine("sqlite:///:memory:")
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture
def db():
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


class TestAuditEvents:
    """
    Ensures that domain service actions trigger audit events in the same transaction.
    """

    def test_recommendation_transition_audit(self, db: Session):
        # 1. Setup
        repo = RecommendationRepository(db)
        # Create initial reco
        reco_model = Recommendation(
            id="reco_update",
            analysis_id="ana_1",
            title="Update test",
            summary="testing",
            status=RecommendationStatus.GENERATED,
        )
        repo.create(reco_model)
        db.commit()

        auditor = RiskAuditor()
        service = RecommendationService(repo, auditor)

        # 2. Action
        service.transition("reco_update", RecommendationStatus.ADOPTED)

        # 3. Verification
        # Check Business State
        updated = repo.get("reco_update")
        assert updated.status == RecommendationStatus.ADOPTED.value

        # Check Audit State
        audit_repo = db.query(AuditEventORM).filter(AuditEventORM.event_type == "recommendation_status_update").first()
        assert audit_repo is not None
        assert audit_repo.entity_id == "reco_update"

    def test_review_creation_audit(self, db: Session):
        # 1. Setup
        rev_repo = ReviewRepository(db)
        lesson_repo = LessonRepository(db)
        lesson_service = LessonService(lesson_repo)
        auditor = RiskAuditor()
        service = ReviewService(rev_repo, lesson_service, auditor)

        # 2. Action
        review = Review(id="rev_test", recommendation_id="reco_1", review_type="postmortem")
        service.create(review)

        # 3. Verification
        audit = db.query(AuditEventORM).filter(AuditEventORM.event_type == "review_submitted").first()
        assert audit is not None
        assert audit.review_id == "rev_test"

    def test_issue_creation_audit(self, db: Session):
        # 1. Setup
        repo = IssueRepository(db)
        auditor = RiskAuditor()
        service = IssueService(repo, auditor)

        # 2. Action
        issue = Issue(id="iss_test", title="Broken", severity="p0", category="test")
        service.create(issue)

        # 3. Verification
        audit = db.query(AuditEventORM).filter(AuditEventORM.event_type == "validation_issue_reported").first()
        assert audit is not None
        assert audit.entity_id == "iss_test"

    def test_audit_transaction_integrity_rollback(self, db: Session):
        """
        Verify that if we force a failure before commit, everything rolls back.
        """
        repo = IssueRepository(db)
        auditor = MagicMock()
        # Mock auditor to throw an error when called
        auditor.record_event.side_effect = Exception("Audit failure")
        service = IssueService(repo, auditor)

        # 2. Action
        issue = Issue(id="iss_rollback", title="Should vanish", severity="p1", category="test")

        with pytest.raises(Exception, match="Audit failure"):
            service.create(issue)

        # 3. Verification
        # Business row should NOT exist in DB because commit was never reached
        # (Note: create() calls repo.create which calls flush, but not commit if we errored in service)
        db.rollback()  # Ensure session state is clean for query
        exists = repo.db.get(AuditEventORM, "iss_rollback")  # Check via raw query if you prefer
        from domains.journal.issue_orm import IssueORM

        check_issue = db.get(IssueORM, "iss_rollback")
        assert check_issue is None

        check_audit = db.query(AuditEventORM).count()
        assert check_audit == 0

    def test_review_completion_audit_lessons(self, db: Session):
        # 1. Setup
        rev_repo = ReviewRepository(db)
        lesson_repo = LessonRepository(db)
        lesson_service = LessonService(lesson_repo)
        auditor = RiskAuditor()
        service = ReviewService(rev_repo, lesson_service, auditor)

        # Create a review first
        review = Review(
            id="rev_to_complete", recommendation_id="reco_1", review_type="postmortem", expected_outcome="win"
        )
        rev_repo.create(review)
        db.commit()

        # 2. Action
        service.complete_review(
            review_id="rev_to_complete",
            observed_outcome="lose",
            verdict=ReviewVerdict.INVALIDATED,
            variance_summary="Bad luck",
            cause_tags=["market"],
            lessons=["Don't gamble", "Watch trends"],
            followup_actions=[],
        )

        # 3. Verification
        # Check that 2 lessons were created and 2 audit events for lessons were recorded
        from domains.journal.lesson_orm import LessonORM

        lesson_count = db.query(LessonORM).count()
        assert lesson_count == 2

        audit_events = db.query(AuditEventORM).filter(AuditEventORM.event_type == "lesson_persisted").all()
        review_completed = db.query(AuditEventORM).filter(AuditEventORM.event_type == "review_completed").all()
        assert len(review_completed) == 1
        assert review_completed[0].review_id == "rev_to_complete"
        assert len(audit_events) == 2
        assert audit_events[0].review_id == "rev_to_complete"
