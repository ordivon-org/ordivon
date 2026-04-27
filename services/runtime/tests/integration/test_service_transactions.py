import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from unittest.mock import MagicMock, patch

from state.db.base import Base
from domains.strategy.models import Recommendation
from domains.strategy.orm import RecommendationORM
from domains.strategy.service import RecommendationService
from domains.strategy.repository import RecommendationRepository
from shared.enums.domain import RecommendationStatus
from governance.audit.auditor import RiskAuditor
from governance.audit.orm import AuditEventORM

# Setup in-memory SQLite
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


class TestServiceTransactions:
    """
    Verifies that services no longer commit by themselves and
    require an external commit for persistence.
    """

    def test_recommendation_transition_rollback_if_no_commit(self, db: Session):
        # 1. Setup
        repo = RecommendationRepository(db)
        # Create a real record
        reco_row = repo.create(
            Recommendation(
                analysis_id="ana_1",
                title="Test",
                summary="Test",
                rationale="Test",
                expected_outcome="Test",
                status=RecommendationStatus.GENERATED,
            )
        )
        db.commit()  # Initial setup commit

        service = RecommendationService(repo, RiskAuditor())

        # 2. Action: Transition without external commit
        service.transition(reco_row.id, RecommendationStatus.ADOPTED)

        # 3. Verification: Data in session but not in DB (if we were to rollback/close)
        db.rollback()
        fresh_row = repo.get(reco_row.id)
        assert fresh_row.status == RecommendationStatus.GENERATED.value  # Still old status!

    def test_audit_consistency_in_transaction(self, db: Session):
        # 1. Setup
        repo = RecommendationRepository(db)
        reco_row = repo.create(
            Recommendation(
                analysis_id="ana_1",
                title="Test",
                summary="Test",
                rationale="Test",
                expected_outcome="Test",
                status=RecommendationStatus.GENERATED,
            )
        )
        db.commit()

        service = RecommendationService(repo, RiskAuditor())

        # 2. Action: Successful transition + Audit, then commit
        service.transition(reco_row.id, RecommendationStatus.ADOPTED)
        db.commit()

        # 3. Verification
        assert db.query(RecommendationORM).filter_by(status=RecommendationStatus.ADOPTED.value).count() == 1
        assert db.query(AuditEventORM).filter_by(event_type="recommendation_status_update").count() == 1

    def test_atomic_rollback_on_audit_failure(self, db: Session):
        # 1. Setup
        repo = RecommendationRepository(db)
        reco_row = repo.create(
            Recommendation(
                analysis_id="ana_1",
                title="Test",
                summary="Test",
                rationale="Test",
                expected_outcome="Test",
                status=RecommendationStatus.GENERATED,
            )
        )
        db.commit()

        auditor = RiskAuditor()
        service = RecommendationService(repo, auditor)

        # 2. Action: Inject failure in auditor
        with patch.object(auditor, "record_event", side_effect=Exception("Audit crash")):
            try:
                service.transition(reco_row.id, RecommendationStatus.ADOPTED)
                db.commit()
            except Exception:
                db.rollback()

        # 3. Verification: Business status should NOT have changed in DB
        db.expire_all()
        fresh_row = repo.get(reco_row.id)
        assert fresh_row.status == RecommendationStatus.GENERATED.value
        assert db.query(AuditEventORM).count() == 0
