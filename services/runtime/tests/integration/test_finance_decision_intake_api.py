"""H-5: Finance Decision Governance Hard Gate — Integration Tests.

Tests the full API path: create intake → govern → verify decision + audit event.
Also verifies no Recommendation, ExecutionReceipt, PlanReceipt are created.
"""

from contextlib import contextmanager

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from apps.api.app.deps import get_db
from apps.api.app.main import app
from domains.execution_records.orm import ExecutionReceiptORM, ExecutionRequestORM
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


def _valid_request() -> dict:
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


def _create_and_govern(client, payload_override=None):
    """Create an intake, then govern it. Returns (intake_dict, govern_dict)."""
    payload = _valid_request()
    if payload_override:
        payload.update(payload_override)
    resp = client.post("/api/v1/finance-decisions/intake", json=payload)
    assert resp.status_code == 200, resp.text
    intake_id = resp.json()["id"]
    gov_resp = client.post(f"/api/v1/finance-decisions/intake/{intake_id}/govern")
    assert gov_resp.status_code == 200, gov_resp.text
    return resp.json(), gov_resp.json()


# ── Existing tests (kept, updated for H-5) ─────────────────────────────────

def test_valid_request_returns_validated_with_governance_not_started():
    with _client_with_db() as (client, _):
        response = client.post("/api/v1/finance-decisions/intake", json=_valid_request())
        assert response.status_code == 200
        payload = response.json()
        assert payload["status"] == "validated"
        assert payload["governance_status"] == "not_started"
        assert payload["validation_errors"] == []
        assert payload["payload"]["symbol"] == "BTC/USDT"

        intake_id = payload["id"]
        get_response = client.get(f"/api/v1/finance-decisions/intake/{intake_id}")
        assert get_response.status_code == 200
        get_payload = get_response.json()
        assert get_payload["id"] == intake_id
        assert get_payload["payload"]["symbol"] == "BTC/USDT"


def test_invalid_request_returns_invalid_with_structured_validation_errors():
    payload = _valid_request()
    payload["thesis"] = None
    with _client_with_db() as (client, _):
        response = client.post("/api/v1/finance-decisions/intake", json=payload)
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "invalid"
    assert body["governance_status"] == "not_started"
    assert any(error["field"] == "thesis" for error in body["validation_errors"])


def test_transport_type_errors_still_return_422():
    payload = _valid_request()
    payload["max_loss_usdt"] = "not-a-number"
    with _client_with_db() as (client, _):
        response = client.post("/api/v1/finance-decisions/intake", json=payload)
    assert response.status_code == 422


# ── H-5 Rule 1: invalid intake → reject ────────────────────────────────────

def test_h5_govern_invalid_intake_rejected():
    with _client_with_db() as (client, testing_session_local):
        _, gov_resp = _create_and_govern(client, payload_override={
            "thesis": None,  # makes it invalid
        })
        assert gov_resp["governance_status"] == "reject"
        assert gov_resp["governance_decision"] == "reject"
        assert len(gov_resp["governance_reasons"]) >= 1
        assert len(gov_resp["governance_policy_refs"]) >= 1


# ── H-5 Rule 2: missing thesis → reject ────────────────────────────────────

def test_h5_govern_missing_thesis_rejected():
    """When thesis is missing, validation fails → intake is invalid → governance rejects."""
    with _client_with_db() as (client, testing_session_local):
        payload = _valid_request()
        payload["thesis"] = None
        resp = client.post("/api/v1/finance-decisions/intake", json=payload)
        assert resp.status_code == 200
        body = resp.json()
        assert body["status"] == "invalid"
        # Govern the invalid intake → should reject
        intake_id = body["id"]
        gov_resp = client.post(f"/api/v1/finance-decisions/intake/{intake_id}/govern")
        assert gov_resp.status_code == 200
        assert gov_resp.json()["governance_decision"] == "reject"
        assert any("thesis" in r.lower() or "invalid" in r.lower()
                   for r in gov_resp.json()["governance_reasons"])


# ── H-5 Rule 8: revenge_trade=true → escalate ──────────────────────────────

def test_h5_govern_revenge_trade_escalated():
    with _client_with_db() as (client, _):
        _, gov_resp = _create_and_govern(client, payload_override={
            "is_revenge_trade": True,
        })
        assert gov_resp["governance_status"] == "escalate"
        assert gov_resp["governance_decision"] == "escalate"
        assert any("revenge" in r.lower() for r in gov_resp["governance_reasons"])


# ── H-5 Rule 9: chasing=true → escalate ────────────────────────────────────

def test_h5_govern_chasing_escalated():
    with _client_with_db() as (client, _):
        _, gov_resp = _create_and_govern(client, payload_override={
            "is_chasing": True,
        })
        assert gov_resp["governance_status"] == "escalate"
        assert gov_resp["governance_decision"] == "escalate"
        assert any("chasing" in r.lower() for r in gov_resp["governance_reasons"])


# ── H-5 Rule 10: max_loss > 2× risk_unit → reject ──────────────────────────

def test_h5_govern_max_loss_exceeds_limit_rejected():
    with _client_with_db() as (client, _):
        _, gov_resp = _create_and_govern(client, payload_override={
            "max_loss_usdt": 30.0,
            "risk_unit_usdt": 10.0,
        })
        assert gov_resp["governance_status"] == "reject"
        assert gov_resp["governance_decision"] == "reject"


# ── H-5 Rule 11: position_size > 10× risk_unit → reject ────────────────────

def test_h5_govern_position_size_exceeds_limit_rejected():
    with _client_with_db() as (client, _):
        _, gov_resp = _create_and_govern(client, payload_override={
            "position_size_usdt": 200.0,
            "risk_unit_usdt": 10.0,
        })
        assert gov_resp["governance_status"] == "reject"
        assert gov_resp["governance_decision"] == "reject"


# ── H-5 Rule 12: valid intake → execute ────────────────────────────────────

def test_h5_govern_valid_intake_executed():
    with _client_with_db() as (client, _):
        _, gov_resp = _create_and_govern(client)
        assert gov_resp["governance_status"] == "execute"
        assert gov_resp["governance_decision"] == "execute"
        assert len(gov_resp["governance_reasons"]) >= 1
        assert len(gov_resp["governance_policy_refs"]) >= 1


# ── H-5 Priority: reject > escalate > execute ──────────────────────────────

def test_h5_govern_priority_reject_over_escalate():
    """missing emotional_state + is_revenge_trade → invalid intake → governance rejects."""
    with _client_with_db() as (client, _):
        payload = _valid_request()
        payload["emotional_state"] = ""
        payload["is_revenge_trade"] = True
        resp = client.post("/api/v1/finance-decisions/intake", json=payload)
        assert resp.json()["status"] == "invalid"
        intake_id = resp.json()["id"]
        gov_resp = client.post(f"/api/v1/finance-decisions/intake/{intake_id}/govern")
        assert gov_resp.status_code == 200
        assert gov_resp.json()["governance_decision"] == "reject"


# ── Side-effect: governance does NOT create Recommendation ──────────────────

def test_h5_governance_does_not_create_recommendation():
    with _client_with_db() as (client, testing_session_local):
        _, gov_resp = _create_and_govern(client)
        assert gov_resp["governance_decision"] == "execute"
        db = testing_session_local()
        try:
            rec_events = db.query(AuditEventORM).filter(
                AuditEventORM.event_type == "recommendation_generated"
            ).count()
        finally:
            db.close()
        assert rec_events == 0, "H-5 must not generate Recommendation events"


# ── Side-effect: governance does NOT create ExecutionReceipt ────────────────

def test_h5_governance_does_not_create_execution_receipt():
    with _client_with_db() as (client, testing_session_local):
        _, gov_resp = _create_and_govern(client)
        assert gov_resp["governance_decision"] == "execute"
        db = testing_session_local()
        try:
            count = db.query(ExecutionReceiptORM).count()
        finally:
            db.close()
        assert count == 0, "H-5 must not create ExecutionReceipt"


# ── Side-effect: governance does NOT trigger broker/order/execution ─────────

def test_h5_governance_does_not_trigger_broker():
    with _client_with_db() as (client, testing_session_local):
        _, gov_resp = _create_and_govern(client)
        assert gov_resp["governance_decision"] == "execute"
        db = testing_session_local()
        try:
            count = db.query(ExecutionReceiptORM).count()
        finally:
            db.close()
        assert count == 0, "H-5 must not create broker/order execution records"


# ── Governance writes AuditEvent ───────────────────────────────────────────

def test_h5_governance_writes_audit_event():
    with _client_with_db() as (client, testing_session_local):
        _, gov_resp = _create_and_govern(client)
        assert gov_resp["governance_decision"] == "execute"
        db = testing_session_local()
        try:
            events = db.query(AuditEventORM).filter(
                AuditEventORM.event_type == "governance_evaluated"
            ).all()
        finally:
            db.close()
        assert len(events) == 1, "H-5 must write one governance_evaluated AuditEvent"
        event = events[0]
        assert event.entity_type == "decision_intake"


# ── Response includes governance metadata ──────────────────────────────────

def test_h5_govern_response_has_decision_details():
    with _client_with_db() as (client, _):
        _, gov_resp = _create_and_govern(client)
        assert "governance_decision" in gov_resp
        assert "governance_reasons" in gov_resp
        assert "governance_policy_refs" in gov_resp
        assert gov_resp["governance_decision"] in ("execute", "escalate", "reject")
        assert isinstance(gov_resp["governance_reasons"], list)
        assert isinstance(gov_resp["governance_policy_refs"], list)


# ── Original test_route_does_not_create_execution_receipts (kept) ──────────

def test_route_does_not_create_execution_receipts():
    with _client_with_db() as (client, testing_session_local):
        response = client.post("/api/v1/finance-decisions/intake", json=_valid_request())
        db = testing_session_local()
        try:
            receipt_count = db.query(ExecutionReceiptORM).count()
        finally:
            db.close()
    assert response.status_code == 200
    assert receipt_count == 0


# ═══════════════════════════════════════════════════════════════════════════
# H-6: Plan-Only Receipt — Integration Tests
# ═══════════════════════════════════════════════════════════════════════════


def _create_govern_and_plan(client) -> dict:
    """Create intake, govern to execute, create plan receipt. Returns plan response."""
    payload = _valid_request()
    resp = client.post("/api/v1/finance-decisions/intake", json=payload)
    assert resp.status_code == 200, resp.text
    intake_id = resp.json()["id"]

    gov_resp = client.post(f"/api/v1/finance-decisions/intake/{intake_id}/govern")
    assert gov_resp.status_code == 200, gov_resp.text
    assert gov_resp.json()["governance_decision"] == "execute"

    plan_resp = client.post(f"/api/v1/finance-decisions/intake/{intake_id}/plan")
    return plan_resp


# ── H-6 Test 1: execute intake → plan receipt (happy path) ──────────────


def test_h6_execute_intake_creates_plan_receipt():
    with _client_with_db() as (client, _):
        plan_resp = _create_govern_and_plan(client)
        assert plan_resp.status_code == 200, plan_resp.text
        body = plan_resp.json()
        assert body["receipt_kind"] == "plan"
        assert body["broker_execution"] is False
        assert body["side_effect_level"] == "none"
        assert body["decision_intake_id"].startswith("intake_")
        assert body["governance_status"] == "execute"
        assert body["execution_request_id"].startswith("exreq_")
        assert body["execution_receipt_id"].startswith("exrcpt_")


# ── H-6 Test 2: invalid intake → 422 ────────────────────────────────────


def test_h6_invalid_intake_cannot_create_plan_receipt():
    with _client_with_db() as (client, _):
        payload = _valid_request()
        payload["thesis"] = None
        resp = client.post("/api/v1/finance-decisions/intake", json=payload)
        assert resp.status_code == 200
        intake_id = resp.json()["id"]
        assert resp.json()["status"] == "invalid"

        plan_resp = client.post(f"/api/v1/finance-decisions/intake/{intake_id}/plan")
        assert plan_resp.status_code == 422, plan_resp.text
        assert "not_started" in plan_resp.json()["detail"]


# ── H-6 Test 3: rejected intake → 422 ───────────────────────────────────


def test_h6_rejected_intake_cannot_create_plan_receipt():
    with _client_with_db() as (client, _):
        payload = _valid_request()
        payload["thesis"] = None
        resp = client.post("/api/v1/finance-decisions/intake", json=payload)
        intake_id = resp.json()["id"]
        gov_resp = client.post(f"/api/v1/finance-decisions/intake/{intake_id}/govern")
        assert gov_resp.json()["governance_decision"] == "reject"

        plan_resp = client.post(f"/api/v1/finance-decisions/intake/{intake_id}/plan")
        assert plan_resp.status_code == 422, plan_resp.text
        assert "reject" in plan_resp.json()["detail"]


# ── H-6 Test 4: escalated intake → 422 ──────────────────────────────────


def test_h6_escalated_intake_cannot_create_plan_receipt():
    with _client_with_db() as (client, _):
        payload = _valid_request()
        payload["is_revenge_trade"] = True
        resp = client.post("/api/v1/finance-decisions/intake", json=payload)
        intake_id = resp.json()["id"]
        gov_resp = client.post(f"/api/v1/finance-decisions/intake/{intake_id}/govern")
        assert gov_resp.json()["governance_decision"] == "escalate"

        plan_resp = client.post(f"/api/v1/finance-decisions/intake/{intake_id}/plan")
        assert plan_resp.status_code == 422, plan_resp.text
        assert "escalate" in plan_resp.json()["detail"]


# ── H-6 Test 5: repeated plan creation → 409 ────────────────────────────


def test_h6_repeated_plan_creation_conflict():
    with _client_with_db() as (client, _):
        payload = _valid_request()
        resp = client.post("/api/v1/finance-decisions/intake", json=payload)
        intake_id = resp.json()["id"]
        client.post(f"/api/v1/finance-decisions/intake/{intake_id}/govern")

        # First plan — succeeds
        plan1 = client.post(f"/api/v1/finance-decisions/intake/{intake_id}/plan")
        assert plan1.status_code == 200, plan1.text

        # Second plan — conflict
        plan2 = client.post(f"/api/v1/finance-decisions/intake/{intake_id}/plan")
        assert plan2.status_code == 409, plan2.text
        assert "already exists" in plan2.json()["detail"]


# ── H-6 Test 6: plan receipt writes AuditEvent ──────────────────────────


def test_h6_plan_receipt_writes_audit_event():
    with _client_with_db() as (client, testing_session_local):
        plan_resp = _create_govern_and_plan(client)
        assert plan_resp.status_code == 200

        db = testing_session_local()
        try:
            events = db.query(AuditEventORM).filter(
                AuditEventORM.event_type == "plan_receipt_created"
            ).all()
            assert len(events) == 1, "H-6 must write plan_receipt_created AuditEvent"
            assert events[0].entity_type == "decision_intake"
        finally:
            db.close()


# ── H-6 Test 7: plan receipt does NOT create broker/order related records


def test_h6_plan_receipt_does_not_create_broker_records():
    with _client_with_db() as (client, testing_session_local):
        plan_resp = _create_govern_and_plan(client)
        assert plan_resp.status_code == 200

        db = testing_session_local()
        try:
            # No order execution requests
            order_reqs = db.query(ExecutionRequestORM).filter(
                ExecutionRequestORM.action_id.like("%order%")
            ).count()
            assert order_reqs == 0

            # Only one execution request (the plan one)
            total_reqs = db.query(ExecutionRequestORM).count()
            assert total_reqs == 1

            req = db.query(ExecutionRequestORM).one()
            assert req.action_id == "finance_decision_plan"
        finally:
            db.close()
