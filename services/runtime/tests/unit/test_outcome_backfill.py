import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from domains.journal.lesson_repository import LessonRepository
from domains.journal.lesson_service import LessonService
from domains.journal.models import Review
from domains.journal.repository import ReviewRepository
from domains.journal.service import ReviewService
from domains.strategy.models import Recommendation
from domains.strategy.outcome_repository import OutcomeRepository
from domains.strategy.outcome_service import OutcomeService
from domains.strategy.repository import RecommendationRepository
from domains.strategy.service import RecommendationService
from governance_engine.audit.auditor import RiskAuditor
from governance_engine.audit.orm import AuditEventORM
from shared.enums.domain import OutcomeState, ReviewStatus, ReviewVerdict
from state.db.base import Base


def _make_db():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    testing_session = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)
    return engine, testing_session


def test_review_completion_backfills_outcome_and_updates_recommendation():
    engine, testing_session = _make_db()
    db = testing_session()

    try:
        recommendation_repo = RecommendationRepository(db)
        recommendation_repo.create(
            Recommendation(
                id="reco_outcome_1",
                analysis_id="analysis_1",
                title="Track BTC",
                summary="Track BTC thesis",
            )
        )

        review_service = ReviewService(
            ReviewRepository(db),
            LessonService(LessonRepository(db)),
            RiskAuditor(),
            outcome_service=OutcomeService(OutcomeRepository(db)),
            recommendation_service=RecommendationService(recommendation_repo),
        )
        review = Review(
            recommendation_id="reco_outcome_1",
            review_type="recommendation_postmortem",
            status=ReviewStatus.PENDING,
            expected_outcome="Target hit",
        )
        row = review_service.create(review)

        review_service.complete_review(
            review_id=row.id,
            observed_outcome="Target failed",
            verdict=ReviewVerdict.INVALIDATED,
            variance_summary="Momentum broke down",
            cause_tags=["momentum"],
            lessons=["Wait for confirmation"],
            followup_actions=["Tighten invalidation"],
        )

        recommendation = recommendation_repo.get("reco_outcome_1")
        outcomes = OutcomeRepository(db).list_for_recommendation("reco_outcome_1")
        outcome_audits = db.query(AuditEventORM).filter(AuditEventORM.event_type == "outcome_backfilled").all()

        assert recommendation is not None
        assert recommendation.latest_outcome_snapshot_id is not None
        assert len(outcomes) == 1
        assert outcomes[0].id == recommendation.latest_outcome_snapshot_id
        assert outcomes[0].outcome_state == OutcomeState.FAILED.value
        assert len(outcome_audits) == 1
        assert outcome_audits[0].entity_id == outcomes[0].id
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


def test_outcome_backfill_failure_does_not_attach_snapshot_id():
    engine, testing_session = _make_db()
    db = testing_session()

    class FailingOutcomeService(OutcomeService):
        def create_snapshot(self, snapshot):
            raise RuntimeError("Outcome persistence failed")

    try:
        recommendation_repo = RecommendationRepository(db)
        recommendation_repo.create(
            Recommendation(
                id="reco_outcome_fail",
                analysis_id="analysis_1",
                title="Track ETH",
                summary="Track ETH thesis",
            )
        )
        db.commit()

        review_service = ReviewService(
            ReviewRepository(db),
            LessonService(LessonRepository(db)),
            RiskAuditor(),
            outcome_service=FailingOutcomeService(OutcomeRepository(db)),
            recommendation_service=RecommendationService(recommendation_repo),
        )
        row = review_service.create(
            Review(
                recommendation_id="reco_outcome_fail",
                review_type="recommendation_postmortem",
                status=ReviewStatus.PENDING,
                expected_outcome="Trend holds",
            )
        )

        with pytest.raises(RuntimeError, match="Outcome persistence failed"):
            review_service.complete_review(
                review_id=row.id,
                observed_outcome="Trend failed",
                verdict=ReviewVerdict.INVALIDATED,
                variance_summary="No follow-through",
                cause_tags=["trend"],
                lessons=["Wait for confirmation"],
                followup_actions=["Reduce exposure"],
            )
        db.rollback()

        recommendation = recommendation_repo.get("reco_outcome_fail")
        outcomes = OutcomeRepository(db).list_for_recommendation("reco_outcome_fail")
        outcome_audits = db.query(AuditEventORM).filter(AuditEventORM.event_type == "outcome_backfilled").all()

        assert recommendation is not None
        assert recommendation.latest_outcome_snapshot_id is None
        assert outcomes == []
        assert outcome_audits == []
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)
