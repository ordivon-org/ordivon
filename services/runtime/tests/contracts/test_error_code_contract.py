from __future__ import annotations

import os

import pytest
from fastapi.testclient import TestClient

os.environ["PFIOS_ENV"] = "test"
os.environ["PFIOS_DEBUG"] = "false"
os.environ["PFIOS_REASONING_PROVIDER"] = "mock"
os.environ["PFIOS_DB_URL"] = "duckdb:///:memory:"

from apps.api.app.main import app

KNOWN_ERROR_CODES = {
    "not_found",
    "validation_error",
    "conflict",
    "governance_rejected",
    "governance_escalated",
    "receipt_not_found",
    "plan_not_allowed",
    "internal_error",
    "bad_request",
}


@pytest.fixture(scope="module")
def app_client() -> TestClient:
    with TestClient(app) as client:
        yield client


def _intake_payload(**overrides: object) -> dict:
    """Return a minimal valid intake payload with optional overrides."""
    payload = {
        "symbol": "BTC/USDT",
        "direction": "long",
        "thesis": "A valid thesis with at least 50 characters to pass length checks",
        "stop_loss": "10%",
        "emotional_state": "calm",
        "max_loss_usdt": 100,
        "position_size_usdt": 500,
        "risk_unit_usdt": 100,
        "is_revenge_trade": False,
        "is_chasing": False,
    }
    payload.update(overrides)
    return payload


# ── Test 1: Reject path returns governance error ────────────────────────


def test_reject_path_returns_governance_error(app_client: TestClient) -> None:
    """Low-quality thesis → govern rejects → plan returns structured error."""
    # Step 1: Create intake with a low-quality thesis
    create_resp = app_client.post(
        "/api/v1/finance-decisions/intake",
        json=_intake_payload(thesis="YOLO"),
    )
    assert create_resp.status_code == 200, (
        f"Expected intake creation to succeed, got {create_resp.status_code}: {create_resp.text}"
    )
    intake = create_resp.json()
    intake_id = intake["id"]
    assert intake["status"] == "validated"

    # Step 2: Govern — thesis "YOLO" is banned → should be rejected
    govern_resp = app_client.post(
        f"/api/v1/finance-decisions/intake/{intake_id}/govern",
    )
    assert govern_resp.status_code == 200, (
        f"Expected govern to succeed, got {govern_resp.status_code}: {govern_resp.text}"
    )
    governed = govern_resp.json()
    assert governed["governance_status"] == "reject", (
        f"Expected governance_status='reject', got '{governed['governance_status']}'"
    )

    # Step 3: Plan — should fail because governance_status is "reject"
    plan_resp = app_client.post(
        f"/api/v1/finance-decisions/intake/{intake_id}/plan",
    )
    assert plan_resp.status_code in {400, 403, 409, 422}, (
        f"Expected plan to return a client error (400/403/409/422), got {plan_resp.status_code}: {plan_resp.text}"
    )

    # Assert structured error: must have at least one of detail/error/message
    err_payload = plan_resp.json()
    has_structured_key = "detail" in err_payload or "error" in err_payload or "message" in err_payload
    assert has_structured_key, (
        f"Expected structured error with 'detail', 'error', or 'message' key, got keys: {list(err_payload.keys())}"
    )


# ── Test 2: Not found returns structured error ──────────────────────────


def test_not_found_returns_structured_error(app_client: TestClient) -> None:
    """A nonexistent intake GET returns 404 with a structured error body."""
    response = app_client.get(
        "/api/v1/finance-decisions/intake/nonexistent-intake-id",
    )
    assert response.status_code == 404, (
        f"Expected 404 for nonexistent intake, got {response.status_code}: {response.text}"
    )

    err_payload = response.json()
    has_structured_key = "detail" in err_payload or "error" in err_payload or "message" in err_payload
    assert has_structured_key, (
        f"Expected structured error with 'detail', 'error', or 'message' key, got keys: {list(err_payload.keys())}"
    )
