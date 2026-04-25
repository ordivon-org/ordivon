from contextlib import contextmanager

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from apps.api.app.deps import get_db
from apps.api.app.main import app
from domains.execution_records.orm import ExecutionReceiptORM
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
        "thesis": "Momentum and structure are aligned.",
        "entry_condition": "Breakout with retest.",
        "invalidation_condition": "Range reclaim fails.",
        "stop_loss": "Below intraday support",
        "target": "Retest local high",
        "position_size_usdt": 150.0,
        "max_loss_usdt": 25.0,
        "risk_unit_usdt": 10.0,
        "is_revenge_trade": False,
        "is_chasing": False,
        "emotional_state": "calm",
        "confidence": 0.5,
        "rule_exceptions": [],
        "notes": "Controlled setup",
    }


def test_valid_request_returns_validated_with_governance_not_started():
    with _client_with_db() as (client, _):
        response = client.post("/api/v1/finance-decisions/intake", json=_valid_request())

        assert response.status_code == 200
        payload = response.json()
        assert payload["status"] == "validated"
        assert payload["governance_status"] == "not_started"
        assert payload["validation_errors"] == []
        assert payload["payload"]["symbol"] == "BTC/USDT"
        
        # Test GET endpoint within the same DB context
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


def test_govern_endpoint_evaluates_policy():
    with _client_with_db() as (client, _):
        # Create an intake with a revenge trade to trigger rejection
        payload = _valid_request()
        payload["is_revenge_trade"] = True
        
        response = client.post("/api/v1/finance-decisions/intake", json=payload)
        assert response.status_code == 200
        intake_id = response.json()["id"]
        
        # Govern the intake
        govern_response = client.post(f"/api/v1/finance-decisions/intake/{intake_id}/govern")
        assert govern_response.status_code == 200
        govern_payload = govern_response.json()
        
        assert govern_payload["governance_status"] == "reject"
        
        # Check an escalated one (chasing but not revenge)
        payload2 = _valid_request()
        payload2["is_revenge_trade"] = False
        payload2["is_chasing"] = True
        payload2["confidence"] = 0.9
        
        response2 = client.post("/api/v1/finance-decisions/intake", json=payload2)
        intake_id2 = response2.json()["id"]
        
        govern_response2 = client.post(f"/api/v1/finance-decisions/intake/{intake_id2}/govern")
        assert govern_response2.status_code == 200
        assert govern_response2.json()["governance_status"] == "escalate"
