from __future__ import annotations

from contextlib import contextmanager
from time import perf_counter

from fastapi.testclient import TestClient

from apps.api.app.main import app


@contextmanager
def app_client():
    with TestClient(app) as client:
        yield client


def test_analyze_api_baseline_latency() -> None:
    with app_client() as client:
        started_at = perf_counter()
        response = client.post(
            "/api/v1/analyze-and-suggest",
            json={"query": "Analyze BTC trend", "symbols": ["BTC/USDT"]},
        )
        elapsed = perf_counter() - started_at

    assert response.status_code == 200
    assert elapsed < 3.0


def test_health_api_baseline_latency() -> None:
    with app_client() as client:
        started_at = perf_counter()
        response = client.get("/api/v1/health")
        elapsed = perf_counter() - started_at

    assert response.status_code == 200
    assert elapsed < 1.5


def test_health_history_api_baseline_latency() -> None:
    with app_client() as client:
        started_at = perf_counter()
        response = client.get("/api/v1/health/history")
        elapsed = perf_counter() - started_at

    assert response.status_code == 200
    assert elapsed < 1.5
