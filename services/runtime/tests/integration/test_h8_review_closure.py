"""H-8: Review Closure on Manual Outcome — Integration Tests.

Tests the full closure path:
  Manual Outcome → Review (with outcome_ref) → complete_review → Lesson / KnowledgeFeedback

Verifies all H-8 rules: outcome ref validation, preservation, Lesson derivation,
KnowledgeFeedback (H-3 path), side-effect isolation (no CandidateRule/Policy/broker).

Uses standard pytest def test_*() convention (NOT pytest-describe).
"""

from contextlib import contextmanager

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from apps.api.app.deps import get_db
from apps.api.app.main import app
from domains.candidate_rules.orm import CandidateRuleORM
from domains.execution_records.orm import ExecutionReceiptORM, ExecutionRequestORM
from domains.finance_outcome.orm import FinanceManualOutcomeORM
from domains.journal.models import Review
from domains.journal.orm import ReviewORM
from domains.journal.lesson_orm import LessonORM
from domains.journal.repository import ReviewRepository
from domains.journal.service import ReviewService
from domains.journal.lesson_service import LessonService
from domains.journal.lesson_repository import LessonRepository
from domains.knowledge_feedback.orm import KnowledgeFeedbackPacketORM
from domains.strategy.models import Recommendation
from domains.strategy.outcome_repository import OutcomeRepository
from domains.strategy.outcome_service import OutcomeService
from domains.strategy.repository import RecommendationRepository
from domains.strategy.service import RecommendationService
from governance_engine.audit.orm import AuditEventORM
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


def _valid_intake_payload() -> dict:
    return {
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
        "notes": "Controlled setup",
    }


def _create_outcome(client) -> dict:
    """Create intake → govern → plan → outcome. Returns outcome response JSON."""
    payload = _valid_intake_payload()
    resp = client.post("/api/v1/finance-decisions/intake", json=payload)
    assert resp.status_code == 200, resp.text
    intake_id = resp.json()["id"]

    gov_resp = client.post(f"/api/v1/finance-decisions/intake/{intake_id}/govern")
    assert gov_resp.status_code == 200, gov_resp.text
    assert gov_resp.json()["governance_decision"] == "execute"

    plan_resp = client.post(f"/api/v1/finance-decisions/intake/{intake_id}/plan")
    assert plan_resp.status_code == 200, plan_resp.text
    plan = plan_resp.json()
    receipt_id = plan["execution_receipt_id"]

    outcome_resp = client.post(
        f"/api/v1/finance-decisions/intake/{intake_id}/outcome",
        json={
            "execution_receipt_id": receipt_id,
            "observed_outcome": "Stop loss hit at -2.5%.",
            "verdict": "validated",
            "variance_summary": "Expected -1%, actual -2.5%.",
            "plan_followed": True,
        },
    )
    assert outcome_resp.status_code == 200, outcome_resp.text
    return outcome_resp.json()


def _create_review_payload(outcome_id: str | None = None, outcome_ref_type: str | None = None) -> dict:
    """Build a minimal review submit payload, optionally with outcome ref."""
    payload: dict = {
        "linked_recommendation_id": "reco_nonexistent",
        "expected_outcome": "Trade follows plan",
        "actual_outcome": "Stop loss hit",
        "deviation": "Momentum faded",
        "mistake_tags": "timing,risk",
        "lessons": [{"lesson_text": "Wait for confirmation"}],
    }
    if outcome_ref_type is not None:
        payload["outcome_ref_type"] = outcome_ref_type
    if outcome_id is not None:
        payload["outcome_ref_id"] = outcome_id
    return payload


# ── Test 1: review can be created with finance manual outcome reference ────


def test_h8_create_review_with_outcome_ref():
    with _client_with_db() as (client, testing_session_local):
        outcome = _create_outcome(client)
        outcome_id = outcome["outcome_id"]

        payload = _create_review_payload(
            outcome_id=outcome_id,
            outcome_ref_type="finance_manual_outcome",
        )
        resp = client.post("/api/v1/reviews/submit", json=payload)
        assert resp.status_code == 200, resp.text
        body = resp.json()
        review_id = body["id"]
        assert review_id.startswith("review_")

        # Verify DB has outcome_ref fields
        db = testing_session_local()
        try:
            row = db.get(ReviewORM, review_id)
            assert row is not None
            assert row.outcome_ref_type == "finance_manual_outcome"
            assert row.outcome_ref_id == outcome_id
        finally:
            db.close()


# ── Test 2: review detail returns outcome_ref_type/outcome_ref_id ─────────


def test_h8_review_detail_returns_outcome_ref():
    with _client_with_db() as (client, testing_session_local):
        outcome = _create_outcome(client)
        outcome_id = outcome["outcome_id"]

        payload = _create_review_payload(
            outcome_id=outcome_id,
            outcome_ref_type="finance_manual_outcome",
        )
        resp = client.post("/api/v1/reviews/submit", json=payload)
        assert resp.status_code == 200, resp.text
        review_id = resp.json()["id"]

        detail_resp = client.get(f"/api/v1/reviews/{review_id}")
        assert detail_resp.status_code == 200, detail_resp.text
        detail = detail_resp.json()
        assert detail["outcome_ref_type"] == "finance_manual_outcome"
        assert detail["outcome_ref_id"] == outcome_id


# ── Test 3: review rejects missing finance manual outcome reference ────────


def test_h8_review_rejects_missing_outcome():
    with _client_with_db() as (client, _):
        payload = _create_review_payload(
            outcome_id="fmout_nonexistent",
            outcome_ref_type="finance_manual_outcome",
        )
        resp = client.post("/api/v1/reviews/submit", json=payload)
        assert resp.status_code == 422, resp.text
        assert "not found" in resp.json()["detail"]


# ── Test 4: review rejects unsupported outcome_ref_type ────────────────────


def test_h8_review_rejects_unsupported_outcome_ref_type():
    with _client_with_db() as (client, _):
        payload = _create_review_payload(
            outcome_id="fmout_x",
            outcome_ref_type="coding_outcome",
        )
        resp = client.post("/api/v1/reviews/submit", json=payload)
        assert resp.status_code == 422, resp.text
        assert "Unsupported outcome_ref_type" in resp.json()["detail"]


# ── Test 5: review rejects partial outcome ref pair ────────────────────────


def test_h8_review_rejects_partial_outcome_ref_pair():
    with _client_with_db() as (client, _):
        # type without id
        resp = client.post(
            "/api/v1/reviews/submit",
            json=_create_review_payload(outcome_ref_type="finance_manual_outcome"),
        )
        assert resp.status_code == 422, resp.text
        assert "outcome_ref_type provided without outcome_ref_id" in resp.json()["detail"]

    with _client_with_db() as (client, _):
        # id without type
        resp = client.post(
            "/api/v1/reviews/submit",
            json=_create_review_payload(outcome_id="fmout_x"),
        )
        assert resp.status_code == 422, resp.text
        assert "outcome_ref_id provided without outcome_ref_type" in resp.json()["detail"]


# ── Test 6: complete_review preserves outcome_ref_type/outcome_ref_id ─────


def test_h8_complete_review_preserves_outcome_ref():
    with _client_with_db() as (client, testing_session_local):
        outcome = _create_outcome(client)
        outcome_id = outcome["outcome_id"]

        # Seed a review with outcome_ref + recommendation for completion path
        db = testing_session_local()
        try:
            # Need a recommendation so complete_review can build knowledge feedback
            RecommendationRepository(db).create(
                Recommendation(
                    id="reco_h8",
                    analysis_id="analysis_h8",
                    title="Test reco H8",
                    summary="Test summary",
                )
            )
            review_service = ReviewService(
                ReviewRepository(db),
                LessonService(LessonRepository(db)),
                outcome_service=OutcomeService(OutcomeRepository(db)),
                recommendation_service=RecommendationService(RecommendationRepository(db)),
            )
            review = Review(
                recommendation_id="reco_h8",
                review_type="recommendation_postmortem",
                expected_outcome="Plan followed",
                outcome_ref_type="finance_manual_outcome",
                outcome_ref_id=outcome_id,
            )
            review_row = review_service.create(review)
            db.commit()
            review_id = review_row.id

            # Complete the review
            completed, lesson_rows, kf = review_service.complete_review(
                review_id=review_id,
                observed_outcome="Plan followed exactly",
                verdict=ReviewVerdict.VALIDATED,
                variance_summary="No variance",
                cause_tags=["discipline"],
                lessons=["Plan adherence works"],
                followup_actions=["Keep following plan"],
            )
            db.commit()

            # Verify outcome_ref preserved
            fetched = db.get(ReviewORM, review_id)
            assert fetched.outcome_ref_type == "finance_manual_outcome"
            assert fetched.outcome_ref_id == outcome_id
            assert fetched.status == "completed"
        finally:
            db.close()


# ── Test 7: complete_review derives lesson rows ────────────────────────────


def test_h8_complete_review_derives_lessons():
    with _client_with_db() as (client, testing_session_local):
        outcome = _create_outcome(client)
        outcome_id = outcome["outcome_id"]

        db = testing_session_local()
        try:
            RecommendationRepository(db).create(
                Recommendation(
                    id="reco_h8_lessons",
                    analysis_id="analysis_h8_lessons",
                    title="Lesson test",
                    summary="Summary",
                )
            )
            review_service = ReviewService(
                ReviewRepository(db),
                LessonService(LessonRepository(db)),
                outcome_service=OutcomeService(OutcomeRepository(db)),
                recommendation_service=RecommendationService(RecommendationRepository(db)),
            )
            review = Review(
                recommendation_id="reco_h8_lessons",
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
                cause_tags=["process"],
                lessons=["Lesson A", "Lesson B"],
                followup_actions=[],
            )
            db.commit()

            assert len(lesson_rows) == 2
            assert lesson_rows[0].body == "Lesson A"
            assert lesson_rows[1].body == "Lesson B"
            # Verify Lesson ORM rows exist
            for lr in lesson_rows:
                orm_row = db.get(LessonORM, lr.id)
                assert orm_row is not None
                assert orm_row.review_id == review_row.id
        finally:
            db.close()


# ── Test 8: lesson source_refs include finance_manual_outcome ──────────────


def test_h8_lesson_source_refs_include_outcome():
    with _client_with_db() as (client, testing_session_local):
        outcome = _create_outcome(client)
        outcome_id = outcome["outcome_id"]

        db = testing_session_local()
        try:
            RecommendationRepository(db).create(
                Recommendation(
                    id="reco_h8_src_refs",
                    analysis_id="analysis_h8_src_refs",
                    title="Source ref test",
                    summary="Summary",
                )
            )
            review_service = ReviewService(
                ReviewRepository(db),
                LessonService(LessonRepository(db)),
                outcome_service=OutcomeService(OutcomeRepository(db)),
                recommendation_service=RecommendationService(RecommendationRepository(db)),
            )
            review = Review(
                recommendation_id="reco_h8_src_refs",
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
                cause_tags=["process"],
                lessons=["Wait for setup confirmation"],
                followup_actions=[],
            )
            db.commit()

            assert len(lesson_rows) == 1
            # Check lesson source_refs via ORM
            lesson_orm = db.get(LessonORM, lesson_rows[0].id)
            import json

            source_refs = json.loads(lesson_orm.source_refs_json or "[]")
            expected_ref = f"finance_manual_outcome:{outcome_id}"
            assert expected_ref in source_refs, f"Expected {expected_ref} in {source_refs}"
            assert f"recommendation:reco_h8_src_refs" in source_refs
        finally:
            db.close()


# ── Test 9: knowledge feedback still derives on recommendation-backed path ─


def test_h8_knowledge_feedback_derives():
    with _client_with_db() as (client, testing_session_local):
        outcome = _create_outcome(client)
        outcome_id = outcome["outcome_id"]

        db = testing_session_local()
        try:
            RecommendationRepository(db).create(
                Recommendation(
                    id="reco_h8_kf",
                    analysis_id="analysis_h8_kf",
                    title="KF test reco",
                    summary="Test summary for KF",
                )
            )
            review_service = ReviewService(
                ReviewRepository(db),
                LessonService(LessonRepository(db)),
                outcome_service=OutcomeService(OutcomeRepository(db)),
                recommendation_service=RecommendationService(RecommendationRepository(db)),
            )
            review = Review(
                recommendation_id="reco_h8_kf",
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
                lessons=["Plan following works well"],
                followup_actions=[],
            )
            db.commit()

            # KnowledgeFeedback should be created (has recommendation_id)
            assert kf is not None, "Knowledge feedback should derive when recommendation_id exists"
            assert kf.id.startswith("kfpkt_")
            assert kf.recommendation_id == "reco_h8_kf"
            assert kf.review_id == review_row.id

            # Verify persisted in DB
            kf_orm = db.get(KnowledgeFeedbackPacketORM, kf.id)
            assert kf_orm is not None
        finally:
            db.close()


# ── Test 10: review completion does NOT create CandidateRule ───────────────


def test_h8_review_completion_does_not_create_candidate_rule():
    with _client_with_db() as (client, testing_session_local):
        outcome = _create_outcome(client)
        outcome_id = outcome["outcome_id"]

        db = testing_session_local()
        try:
            RecommendationRepository(db).create(
                Recommendation(
                    id="reco_h8_no_cr",
                    analysis_id="analysis_h8_no_cr",
                    title="No CR test",
                    summary="Summary",
                )
            )
            review_service = ReviewService(
                ReviewRepository(db),
                LessonService(LessonRepository(db)),
                outcome_service=OutcomeService(OutcomeRepository(db)),
                recommendation_service=RecommendationService(RecommendationRepository(db)),
            )
            review = Review(
                recommendation_id="reco_h8_no_cr",
                review_type="recommendation_postmortem",
                expected_outcome="Test",
            )
            review_row = review_service.create(review)
            db.commit()

            initial_cr_count = db.query(CandidateRuleORM).count()
            assert initial_cr_count == 0

            review_service.complete_review(
                review_id=review_row.id,
                observed_outcome="Test",
                verdict=ReviewVerdict.VALIDATED,
                variance_summary=None,
                cause_tags=["test"],
                lessons=["Test lesson"],
                followup_actions=[],
            )
            db.commit()

            final_cr_count = db.query(CandidateRuleORM).count()
            assert final_cr_count == 0, "Review completion must not create CandidateRule"
        finally:
            db.close()


# ── Test 11: review completion does NOT promote Policy ─────────────────────


def test_h8_review_completion_does_not_promote_policy():
    with _client_with_db() as (client, testing_session_local):
        outcome = _create_outcome(client)
        db = testing_session_local()
        try:
            RecommendationRepository(db).create(
                Recommendation(
                    id="reco_h8_no_policy",
                    analysis_id="analysis_h8_no_policy",
                    title="No policy test",
                    summary="Summary",
                )
            )
            review_service = ReviewService(
                ReviewRepository(db),
                LessonService(LessonRepository(db)),
                outcome_service=OutcomeService(OutcomeRepository(db)),
                recommendation_service=RecommendationService(RecommendationRepository(db)),
            )
            review = Review(
                recommendation_id="reco_h8_no_policy",
                review_type="recommendation_postmortem",
                expected_outcome="Test",
            )
            review_row = review_service.create(review)
            db.commit()

            review_service.complete_review(
                review_id=review_row.id,
                observed_outcome="Test",
                verdict=ReviewVerdict.VALIDATED,
                variance_summary=None,
                cause_tags=["test"],
                lessons=["Test lesson"],
                followup_actions=[],
            )
            db.commit()

            # Check no policy-related audit events
            policy_events = (
                db
                .query(AuditEventORM)
                .filter(AuditEventORM.event_type.like("%policy%") | AuditEventORM.event_type.like("%promote%"))
                .count()
            )
            assert policy_events == 0, "Review completion must not promote Policy"
        finally:
            db.close()


# ── Test 12: review completion does NOT trigger broker/order/trade ─────────


def test_h8_review_completion_does_not_trigger_broker():
    with _client_with_db() as (client, testing_session_local):
        outcome = _create_outcome(client)
        db = testing_session_local()
        try:
            # Count existing execution requests before completion
            initial_count = db.query(ExecutionRequestORM).count()

            RecommendationRepository(db).create(
                Recommendation(
                    id="reco_h8_no_broker",
                    analysis_id="analysis_h8_no_broker",
                    title="No broker test",
                    summary="Summary",
                )
            )
            review_service = ReviewService(
                ReviewRepository(db),
                LessonService(LessonRepository(db)),
                outcome_service=OutcomeService(OutcomeRepository(db)),
                recommendation_service=RecommendationService(RecommendationRepository(db)),
            )
            review = Review(
                recommendation_id="reco_h8_no_broker",
                review_type="recommendation_postmortem",
                expected_outcome="Test",
            )
            review_row = review_service.create(review)
            db.commit()

            review_service.complete_review(
                review_id=review_row.id,
                observed_outcome="Test",
                verdict=ReviewVerdict.VALIDATED,
                variance_summary=None,
                cause_tags=["test"],
                lessons=["Test lesson"],
                followup_actions=[],
            )
            db.commit()

            # Verify no new broker/order/trade execution requests
            broker_reqs = (
                db
                .query(ExecutionRequestORM)
                .filter(
                    ExecutionRequestORM.action_id.like("%order%")
                    | ExecutionRequestORM.action_id.like("%trade%")
                    | ExecutionRequestORM.action_id.like("%broker%")
                )
                .count()
            )
            assert broker_reqs == 0, "Review completion must not trigger broker/order/trade"
        finally:
            db.close()
