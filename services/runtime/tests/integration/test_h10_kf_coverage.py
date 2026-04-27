"""H-10: KnowledgeFeedback path coverage expansion — Integration Tests.

Tests the H-10 generalization path where reviews have no recommendation_id
(Finance DecisionIntake reviews) and KF is derived via extract_for_review_by_id.

Gaps covered:
  1. Review without recommendation_id, with outcome_ref → KF generated
  2. Review without recommendation_id, without outcome_ref → KF generated
  3. Review without recommendation_id, without lessons → no KF

Uses standard pytest def test_*() convention (NOT pytest-describe).
"""

from contextlib import contextmanager

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from apps.api.app.deps import get_db
from apps.api.app.main import app
from domains.journal.lesson_repository import LessonRepository
from domains.journal.lesson_service import LessonService
from domains.journal.models import Review
from domains.journal.repository import ReviewRepository
from domains.journal.service import ReviewService
from domains.knowledge_feedback.orm import KnowledgeFeedbackPacketORM
from domains.strategy.outcome_repository import OutcomeRepository
from domains.strategy.outcome_service import OutcomeService
from domains.strategy.repository import RecommendationRepository
from domains.strategy.service import RecommendationService
from shared.enums.domain import ReviewVerdict
from state.db.base import Base


def _make_engine():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    testing_session_local = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)
    return engine, testing_session_local


@contextmanager
def _client_with_db():
    engine, testing_session_local = _make_engine()

    def override_get_db():
        db = testing_session_local()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    try:
        with TestClient(app) as client:
            yield client, testing_session_local
    finally:
        app.dependency_overrides.clear()
        Base.metadata.drop_all(bind=engine)


def _build_review_service(db):
    return ReviewService(
        ReviewRepository(db),
        LessonService(LessonRepository(db)),
        outcome_service=OutcomeService(OutcomeRepository(db)),
        recommendation_service=RecommendationService(RecommendationRepository(db)),
    )


# ── Test 1: KF via H-10 path — review with outcome_ref, no recommendation_id ──


def test_h10_kf_via_outcome_ref_without_recommendation():
    """Review has outcome_ref (finance_manual_outcome) but no recommendation_id.
    KF should still be generated via extract_for_review_by_id (H-10 path)."""
    with _client_with_db() as (client, testing_session_local):
        # Create a real intake → govern → plan → outcome chain
        payload = {
            "symbol": "BTC/USDT",
            "timeframe": "1h",
            "direction": "long",
            "thesis": "BTC breaking above resistance with volume confirmation; invalidated if price closes below 200 EMA.",
            "entry_condition": "Breakout with retest.",
            "invalidation_condition": "Range reclaim fails.",
            "stop_loss": "Below intraday support",
            "target": "Retest local high",
            "position_size_usdt": 100.0,
            "max_loss_usdt": 20.0,
            "risk_unit_usdt": 10.0,
            "is_revenge_trade": False,
            "is_chasing": False,
            "emotional_state": "calm",
            "confidence": 0.5,
            "rule_exceptions": [],
            "notes": "H-10 test",
        }
        resp = client.post("/api/v1/finance-decisions/intake", json=payload)
        assert resp.status_code == 200, resp.text
        intake_id = resp.json()["id"]

        gov_resp = client.post(f"/api/v1/finance-decisions/intake/{intake_id}/govern")
        assert gov_resp.status_code == 200, gov_resp.text
        assert gov_resp.json()["governance_decision"] == "execute"

        plan_resp = client.post(f"/api/v1/finance-decisions/intake/{intake_id}/plan")
        assert plan_resp.status_code == 200, plan_resp.text
        receipt_id = plan_resp.json()["execution_receipt_id"]

        outcome_resp = client.post(
            f"/api/v1/finance-decisions/intake/{intake_id}/outcome",
            json={
                "execution_receipt_id": receipt_id,
                "observed_outcome": "Price rose 3%",
                "verdict": "validated",
                "variance_summary": None,
                "plan_followed": True,
            },
        )
        assert outcome_resp.status_code == 200, outcome_resp.text
        outcome_id = outcome_resp.json()["outcome_id"]

        db = testing_session_local()
        try:
            # Create review WITHOUT recommendation_id, WITH outcome_ref
            review_service = _build_review_service(db)
            review = Review(
                recommendation_id=None,  # H-10: no recommendation
                review_type="recommendation_postmortem",
                expected_outcome="Test",
                outcome_ref_type="finance_manual_outcome",
                outcome_ref_id=outcome_id,
            )
            review_row = review_service.create(review)
            db.commit()

            completed, lesson_rows, kf = review_service.complete_review(
                review_id=review_row.id,
                observed_outcome="Followed plan",
                verdict=ReviewVerdict.VALIDATED,
                variance_summary=None,
                cause_tags=["discipline"],
                lessons=["Plan following works even without recommendation link"],
                followup_actions=[],
            )
            db.commit()

            # KF should be generated via extract_for_review_by_id (H-10 path)
            assert kf is not None, "H-10: KF must be generated when outcome_ref exists, even without recommendation_id"
            assert kf.id.startswith("kfpkt_")
            # KF recommendation_id falls back to review_id when recommendation_id is None
            assert kf.review_id == review_row.id

            # Verify persisted in DB
            kf_orm = db.get(KnowledgeFeedbackPacketORM, kf.id)
            assert kf_orm is not None
        finally:
            db.close()


# ── Test 2: KF via H-10 path — review without outcome_ref, no recommendation_id ──


def test_h10_kf_without_outcome_ref_without_recommendation():
    """Review has neither outcome_ref nor recommendation_id.
    KF should still be generated from lessons alone (from_lesson path)."""
    with _client_with_db() as (client, testing_session_local):
        db = testing_session_local()
        try:
            review_service = _build_review_service(db)
            review = Review(
                recommendation_id=None,
                review_type="recommendation_postmortem",
                expected_outcome="Test",
                outcome_ref_type=None,
                outcome_ref_id=None,
            )
            review_row = review_service.create(review)
            db.commit()

            completed, lesson_rows, kf = review_service.complete_review(
                review_id=review_row.id,
                observed_outcome="Test outcome",
                verdict=ReviewVerdict.VALIDATED,
                variance_summary=None,
                cause_tags=["testing"],
                lessons=["A lesson without any linked outcome"],
                followup_actions=[],
            )
            db.commit()

            # KF should be generated — lessons exist, from_lesson path works
            assert kf is not None, (
                "H-10: KF must be generated from lessons even without "
                "outcome_ref or recommendation_id (from_lesson path)"
            )
            assert kf.id.startswith("kfpkt_")
            assert kf.review_id == review_row.id

            # Verify persisted
            kf_orm = db.get(KnowledgeFeedbackPacketORM, kf.id)
            assert kf_orm is not None
        finally:
            db.close()


# ── Test 3: no KF when review has no lessons (empty extraction) ──


def test_h10_no_kf_without_lessons():
    """Review has no lessons → extract_for_review_by_id returns [] → no KF."""
    with _client_with_db() as (client, testing_session_local):
        # Create outcome via API for realistic setup
        payload = {
            "symbol": "ETH/USDT",
            "timeframe": "15m",
            "direction": "short",
            "thesis": "ETH rejected at resistance, targeting support; invalidated if breaks above resistance.",
            "entry_condition": "Rejection confirmed.",
            "invalidation_condition": "Break above resistance.",
            "stop_loss": "Above resistance",
            "target": "Support level",
            "position_size_usdt": 50.0,
            "max_loss_usdt": 10.0,
            "risk_unit_usdt": 5.0,
            "is_revenge_trade": False,
            "is_chasing": False,
            "emotional_state": "calm",
            "confidence": 0.6,
            "rule_exceptions": [],
            "notes": "H-10 no-lesson test",
        }
        resp = client.post("/api/v1/finance-decisions/intake", json=payload)
        assert resp.status_code == 200, resp.text
        intake_id = resp.json()["id"]

        gov_resp = client.post(f"/api/v1/finance-decisions/intake/{intake_id}/govern")
        assert gov_resp.status_code == 200
        assert gov_resp.json()["governance_decision"] == "execute"

        plan_resp = client.post(f"/api/v1/finance-decisions/intake/{intake_id}/plan")
        assert plan_resp.status_code == 200
        receipt_id = plan_resp.json()["execution_receipt_id"]

        outcome_resp = client.post(
            f"/api/v1/finance-decisions/intake/{intake_id}/outcome",
            json={
                "execution_receipt_id": receipt_id,
                "observed_outcome": "Hit target",
                "verdict": "validated",
                "variance_summary": None,
                "plan_followed": True,
            },
        )
        assert outcome_resp.status_code == 200, outcome_resp.text
        outcome_id = outcome_resp.json()["outcome_id"]

        db = testing_session_local()
        try:
            review_service = _build_review_service(db)
            review = Review(
                recommendation_id=None,
                review_type="recommendation_postmortem",
                expected_outcome="Test",
                outcome_ref_type="finance_manual_outcome",
                outcome_ref_id=outcome_id,
            )
            review_row = review_service.create(review)
            db.commit()

            # Complete with empty lessons list
            completed, lesson_rows, kf = review_service.complete_review(
                review_id=review_row.id,
                observed_outcome="Followed plan",
                verdict=ReviewVerdict.VALIDATED,
                variance_summary=None,
                cause_tags=[],
                lessons=[],  # No lessons
                followup_actions=[],
            )
            db.commit()

            # KF should be None — no lessons to extract from
            assert kf is None, "H-10: KF must be None when no lessons exist for extraction"
        finally:
            db.close()
