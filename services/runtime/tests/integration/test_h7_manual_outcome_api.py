"""H-7: Manual Outcome Capture — Integration Tests.

Tests the full API path:
  intake → govern → plan → outcome
Verifies all H-7 rules: plan receipt validation, duplicate detection,
side-effect isolation, review outcome_ref_type/outcome_ref_id.

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
from domains.journal.repository import ReviewRepository
from domains.journal.service import ReviewService
from domains.journal.lesson_service import LessonService
from domains.journal.lesson_repository import LessonRepository
from governance.audit.orm import AuditEventORM
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
        "thesis": "Momentum and structure aligned.",
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


def _create_govern_and_plan(client) -> dict:
    """Create intake, govern to execute, create plan receipt. Returns plan response JSON."""
    payload = _valid_intake_payload()
    resp = client.post("/api/v1/finance-decisions/intake", json=payload)
    assert resp.status_code == 200, resp.text
    intake_id = resp.json()["id"]

    gov_resp = client.post(f"/api/v1/finance-decisions/intake/{intake_id}/govern")
    assert gov_resp.status_code == 200, gov_resp.text
    assert gov_resp.json()["governance_decision"] == "execute"

    plan_resp = client.post(f"/api/v1/finance-decisions/intake/{intake_id}/plan")
    assert plan_resp.status_code == 200, plan_resp.text
    return plan_resp.json()


def _valid_outcome_payload(execution_receipt_id: str) -> dict:
    return {
        "execution_receipt_id": execution_receipt_id,
        "observed_outcome": "Stop loss hit at -2.5%.",
        "verdict": "validated",
        "variance_summary": "Expected -1%, actual -2.5%.",
        "plan_followed": True,
    }


# ── Test 1: execute intake + plan receipt can create manual outcome ──────


def test_h7_execute_intake_with_plan_creates_outcome():
    with _client_with_db() as (client, _):
        plan = _create_govern_and_plan(client)
        intake_id = plan["decision_intake_id"]
        receipt_id = plan["execution_receipt_id"]

        outcome_payload = _valid_outcome_payload(receipt_id)
        resp = client.post(
            f"/api/v1/finance-decisions/intake/{intake_id}/outcome",
            json=outcome_payload,
        )
        assert resp.status_code == 200, resp.text
        body = resp.json()

        assert body["outcome_id"].startswith("fmout_")
        assert body["outcome_source"] == "manual"
        assert body["decision_intake_id"] == intake_id
        assert body["execution_receipt_id"] == receipt_id
        assert body["observed_outcome"] == outcome_payload["observed_outcome"]
        assert body["verdict"] == outcome_payload["verdict"]
        assert body["variance_summary"] == outcome_payload["variance_summary"]
        assert body["plan_followed"] is True
        assert body["created_at"]


# ── Test 2: outcome requires existing plan receipt ────────────────────────


def test_h7_outcome_requires_existing_plan_receipt():
    with _client_with_db() as (client, _):
        plan = _create_govern_and_plan(client)
        intake_id = plan["decision_intake_id"]

        resp = client.post(
            f"/api/v1/finance-decisions/intake/{intake_id}/outcome",
            json={
                "execution_receipt_id": "exrcpt_nonexistent",
                "observed_outcome": "Test.",
                "verdict": "validated",
            },
        )
        assert resp.status_code == 422, resp.text
        assert "not found" in resp.json()["detail"]


# ── Test 3: outcome cannot be created for non-plan receipt ────────────────


def test_h7_outcome_rejects_non_plan_receipt():
    with _client_with_db() as (client, testing_session_local):
        plan = _create_govern_and_plan(client)
        intake_id = plan["decision_intake_id"]
        receipt_id = plan["execution_receipt_id"]

        # Tamper receipt detail to change receipt_kind
        db = testing_session_local()
        try:
            import json
            receipt = db.get(ExecutionReceiptORM, receipt_id)
            detail = json.loads(receipt.detail_json) if receipt.detail_json else {}
            detail["receipt_kind"] = "execution"
            receipt.detail_json = json.dumps(detail)
            db.commit()
        finally:
            db.close()

        resp = client.post(
            f"/api/v1/finance-decisions/intake/{intake_id}/outcome",
            json={
                "execution_receipt_id": receipt_id,
                "observed_outcome": "Test.",
                "verdict": "validated",
            },
        )
        assert resp.status_code == 422, resp.text
        assert "receipt_kind" in resp.json()["detail"]


# ── Test 4: outcome cannot be created when receipt decision_intake_id
#            mismatches path intake_id ────────────────────────────────────


def test_h7_outcome_mismatched_decision_intake_id_rejected():
    with _client_with_db() as (client, _):
        plan_a = _create_govern_and_plan(client)
        plan_b = _create_govern_and_plan(client)

        intake_id_b = plan_b["decision_intake_id"]
        receipt_id_a = plan_a["execution_receipt_id"]

        resp = client.post(
            f"/api/v1/finance-decisions/intake/{intake_id_b}/outcome",
            json={
                "execution_receipt_id": receipt_id_a,
                "observed_outcome": "Test.",
                "verdict": "validated",
            },
        )
        assert resp.status_code == 422, resp.text
        assert "does not match" in resp.json()["detail"]


# ── Test 5: outcome_source is always "manual" ─────────────────────────────


def test_h7_outcome_source_is_manual():
    with _client_with_db() as (client, _):
        plan = _create_govern_and_plan(client)
        intake_id = plan["decision_intake_id"]
        receipt_id = plan["execution_receipt_id"]

        resp = client.post(
            f"/api/v1/finance-decisions/intake/{intake_id}/outcome",
            json=_valid_outcome_payload(receipt_id),
        )
        assert resp.status_code == 200
        assert resp.json()["outcome_source"] == "manual"


# ── Test 6: observed_outcome persisted ────────────────────────────────────


def test_h7_observed_outcome_persisted():
    with _client_with_db() as (client, testing_session_local):
        plan = _create_govern_and_plan(client)
        intake_id = plan["decision_intake_id"]
        receipt_id = plan["execution_receipt_id"]

        resp = client.post(
            f"/api/v1/finance-decisions/intake/{intake_id}/outcome",
            json={
                "execution_receipt_id": receipt_id,
                "observed_outcome": "Target hit at +3%.",
                "verdict": "validated",
                "plan_followed": True,
            },
        )
        assert resp.status_code == 200
        outcome_id = resp.json()["outcome_id"]

        db = testing_session_local()
        try:
            row = db.get(FinanceManualOutcomeORM, outcome_id)
            assert row.observed_outcome == "Target hit at +3%."
        finally:
            db.close()


# ── Test 7: verdict persisted ─────────────────────────────────────────────


def test_h7_verdict_persisted():
    with _client_with_db() as (client, testing_session_local):
        plan = _create_govern_and_plan(client)
        intake_id = plan["decision_intake_id"]
        receipt_id = plan["execution_receipt_id"]

        resp = client.post(
            f"/api/v1/finance-decisions/intake/{intake_id}/outcome",
            json={
                "execution_receipt_id": receipt_id,
                "observed_outcome": "Test.",
                "verdict": "partially_validated",
            },
        )
        assert resp.status_code == 200
        outcome_id = resp.json()["outcome_id"]

        db = testing_session_local()
        try:
            row = db.get(FinanceManualOutcomeORM, outcome_id)
            assert row.verdict == "partially_validated"
        finally:
            db.close()


# ── Test 8: variance_summary persisted ────────────────────────────────────


def test_h7_variance_summary_persisted():
    with _client_with_db() as (client, testing_session_local):
        plan = _create_govern_and_plan(client)
        intake_id = plan["decision_intake_id"]
        receipt_id = plan["execution_receipt_id"]

        resp = client.post(
            f"/api/v1/finance-decisions/intake/{intake_id}/outcome",
            json={
                "execution_receipt_id": receipt_id,
                "observed_outcome": "Test.",
                "verdict": "validated",
                "variance_summary": "Expected +2%, actual +5%.",
            },
        )
        assert resp.status_code == 200
        outcome_id = resp.json()["outcome_id"]

        db = testing_session_local()
        try:
            row = db.get(FinanceManualOutcomeORM, outcome_id)
            assert row.variance_summary == "Expected +2%, actual +5%."
        finally:
            db.close()


# ── Test 9: plan_followed persisted ──────────────────────────────────────


def test_h7_plan_followed_persisted():
    with _client_with_db() as (client, testing_session_local):
        plan = _create_govern_and_plan(client)
        intake_id = plan["decision_intake_id"]
        receipt_id = plan["execution_receipt_id"]

        resp = client.post(
            f"/api/v1/finance-decisions/intake/{intake_id}/outcome",
            json={
                "execution_receipt_id": receipt_id,
                "observed_outcome": "Test.",
                "verdict": "invalidated",
                "plan_followed": True,
            },
        )
        assert resp.status_code == 200
        outcome_id = resp.json()["outcome_id"]

        db = testing_session_local()
        try:
            row = db.get(FinanceManualOutcomeORM, outcome_id)
            assert row.plan_followed is True
        finally:
            db.close()


# ── Test 10: duplicate outcome returns 409 ────────────────────────────────


def test_h7_duplicate_outcome_returns_409():
    with _client_with_db() as (client, _):
        plan = _create_govern_and_plan(client)
        intake_id = plan["decision_intake_id"]
        receipt_id = plan["execution_receipt_id"]

        # First outcome — succeeds
        resp1 = client.post(
            f"/api/v1/finance-decisions/intake/{intake_id}/outcome",
            json=_valid_outcome_payload(receipt_id),
        )
        assert resp1.status_code == 200, resp1.text

        # Second outcome — conflict
        resp2 = client.post(
            f"/api/v1/finance-decisions/intake/{intake_id}/outcome",
            json=_valid_outcome_payload(receipt_id),
        )
        assert resp2.status_code == 409, resp2.text
        assert "already exists" in resp2.json()["detail"]


# ── Test 11: Review can reference outcome via outcome_ref_type/outcome_ref_id


def test_h7_review_can_reference_outcome():
    with _client_with_db() as (client, testing_session_local):
        plan = _create_govern_and_plan(client)
        intake_id = plan["decision_intake_id"]
        receipt_id = plan["execution_receipt_id"]

        # Create outcome
        resp = client.post(
            f"/api/v1/finance-decisions/intake/{intake_id}/outcome",
            json=_valid_outcome_payload(receipt_id),
        )
        assert resp.status_code == 200, resp.text
        outcome_id = resp.json()["outcome_id"]

        # Manually attach outcome_ref to a Review
        db = testing_session_local()
        try:
            review = Review(
                recommendation_id=None,
                review_type="recommendation_postmortem",
                outcome_ref_type="finance_manual_outcome",
                outcome_ref_id=outcome_id,
            )
            review_row = ReviewRepository(db).create(review)
            db.commit()

            # Verify the Review has the outcome_ref fields
            fetched = ReviewRepository(db).get(review_row.id)
            assert fetched.outcome_ref_type == "finance_manual_outcome"
            assert fetched.outcome_ref_id == outcome_id
        finally:
            db.close()

        # Verify outcome still exists
        resp_get = client.get(f"/api/v1/finance-decisions/intake/{intake_id}")
        assert resp_get.status_code == 200


# ── Test 12: outcome creation does NOT create broker/order/trade ──────────


def test_h7_outcome_does_not_create_broker_order_trade():
    with _client_with_db() as (client, testing_session_local):
        plan = _create_govern_and_plan(client)
        intake_id = plan["decision_intake_id"]
        receipt_id = plan["execution_receipt_id"]

        resp = client.post(
            f"/api/v1/finance-decisions/intake/{intake_id}/outcome",
            json=_valid_outcome_payload(receipt_id),
        )
        assert resp.status_code == 200

        db = testing_session_local()
        try:
            broker_reqs = db.query(ExecutionRequestORM).filter(
                ExecutionRequestORM.action_id.like("%order%")
                | ExecutionRequestORM.action_id.like("%trade%")
                | ExecutionRequestORM.action_id.like("%broker%")
            ).count()
            assert broker_reqs == 0, "Outcome must not create broker/order/trade"

            # Only one execution request: the plan receipt
            total = db.query(ExecutionRequestORM).count()
            assert total == 1
        finally:
            db.close()


# ── Test 13: outcome creation does NOT create CandidateRule ───────────────


def test_h7_outcome_does_not_create_candidate_rule():
    with _client_with_db() as (client, testing_session_local):
        plan = _create_govern_and_plan(client)
        intake_id = plan["decision_intake_id"]
        receipt_id = plan["execution_receipt_id"]

        resp = client.post(
            f"/api/v1/finance-decisions/intake/{intake_id}/outcome",
            json=_valid_outcome_payload(receipt_id),
        )
        assert resp.status_code == 200

        db = testing_session_local()
        try:
            count = db.query(CandidateRuleORM).count()
            assert count == 0, "H-7 must not create CandidateRule"
        finally:
            db.close()


# ── Test 14: outcome creation does NOT promote Policy ─────────────────────


def test_h7_outcome_does_not_promote_policy():
    with _client_with_db() as (client, testing_session_local):
        plan = _create_govern_and_plan(client)
        intake_id = plan["decision_intake_id"]
        receipt_id = plan["execution_receipt_id"]

        resp = client.post(
            f"/api/v1/finance-decisions/intake/{intake_id}/outcome",
            json=_valid_outcome_payload(receipt_id),
        )
        assert resp.status_code == 200

        db = testing_session_local()
        try:
            policy_events = db.query(AuditEventORM).filter(
                AuditEventORM.event_type.like("%policy%")
                | AuditEventORM.event_type.like("%promote%")
            ).count()
            assert policy_events == 0, "H-7 must not promote Policy"

            all_events = db.query(AuditEventORM).all()
            event_types = {e.event_type for e in all_events}
            assert event_types == {"governance_evaluated", "plan_receipt_created", "outcome_captured"}
        finally:
            db.close()


# ── Test: outcome writes audit event with correct metadata ────────────────


def test_h7_outcome_writes_audit_event():
    with _client_with_db() as (client, testing_session_local):
        plan = _create_govern_and_plan(client)
        intake_id = plan["decision_intake_id"]
        receipt_id = plan["execution_receipt_id"]

        resp = client.post(
            f"/api/v1/finance-decisions/intake/{intake_id}/outcome",
            json=_valid_outcome_payload(receipt_id),
        )
        assert resp.status_code == 200
        outcome_id = resp.json()["outcome_id"]

        db = testing_session_local()
        try:
            events = db.query(AuditEventORM).filter(
                AuditEventORM.event_type == "outcome_captured"
            ).all()
            assert len(events) == 1, "H-7 must write outcome_captured AuditEvent"
            event = events[0]
            assert event.entity_type == "decision_intake"
            assert event.entity_id == intake_id

            import json
            payload = json.loads(event.payload_json) if event.payload_json else {}
            assert payload["outcome_id"] == outcome_id
            assert payload["outcome_source"] == "manual"
            assert payload["verdict"] == "validated"
        finally:
            db.close()


# ── Test: non-existent intake returns 404 ─────────────────────────────────


def test_h7_nonexistent_intake_returns_404():
    with _client_with_db() as (client, _):
        resp = client.post(
            "/api/v1/finance-decisions/intake/nonexistent/outcome",
            json={
                "execution_receipt_id": "exrcpt_any",
                "observed_outcome": "Test.",
                "verdict": "validated",
            },
        )
        assert resp.status_code == 404, resp.text
