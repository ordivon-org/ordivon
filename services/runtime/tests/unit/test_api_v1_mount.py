from fastapi.testclient import TestClient

from apps.api.app.main import app


def test_api_v1_health_route_is_mounted():
    with TestClient(app) as client:
        response = client.get("/api/v1/health")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_api_v1_version_route_is_mounted():
    with TestClient(app) as client:
        response = client.get("/api/v1/version")

    assert response.status_code == 200
    assert response.json()["version"] == "0.1.0"
