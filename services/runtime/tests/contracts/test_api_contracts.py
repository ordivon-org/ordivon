from __future__ import annotations

import json
from contextlib import contextmanager
from pathlib import Path

from fastapi.testclient import TestClient

from apps.api.app.main import app


ROOT_DIR = Path(__file__).resolve().parents[2]
OPENAPI_SNAPSHOT_PATH = ROOT_DIR / "tests" / "contracts" / "openapi.snapshot.json"


@contextmanager
def app_client():
    with TestClient(app) as client:
        yield client


def test_openapi_snapshot_matches_committed_contract() -> None:
    expected = json.loads(OPENAPI_SNAPSHOT_PATH.read_text(encoding="utf-8"))
    actual = app.openapi()
    assert actual == expected


def test_health_contract_surface_is_stable() -> None:
    with app_client() as client:
        response = client.get("/api/v1/health")

    assert response.status_code == 200
    payload = response.json()
    assert "status" in payload
    assert "reasoning_provider" in payload
    assert "monitoring_status" in payload


def test_history_contract_surface_is_stable() -> None:
    with app_client() as client:
        response = client.get("/api/v1/health/history")

    assert response.status_code == 200
    payload = response.json()
    assert set(payload.keys()) >= {
        "workflow_failures_by_type",
        "execution_failures_by_family",
        "stale_or_blocked_run_count",
        "approval_blocked_count",
        "blocked_run_ids",
    }


def test_analyze_response_contract_includes_object_continuation_fields() -> None:
    with app_client() as client:
        response = client.post(
            "/api/v1/analyze-and-suggest",
            json={"query": "Analyze BTC momentum", "symbols": ["BTC/USDT"]},
        )

    assert response.status_code == 200
    payload = response.json()
    assert set(payload.keys()) >= {
        "status",
        "decision",
        "summary",
        "risk_flags",
        "recommendations",
        "analysis_id",
        "recommendation_id",
        "metadata",
        "workflow",
    }
    assert payload["metadata"]["recommendation_id"] == payload["recommendation_id"]
