from contextlib import contextmanager

from fastapi.testclient import TestClient

from apps.api.app.main import app

@contextmanager
def _app_client():
    with TestClient(app) as client:
        yield client


def test_recommendations_recent_uses_honest_semantic_fields():
    with _app_client() as client:
        response = client.get("/api/v1/recommendations/recent")
    assert response.status_code == 200

    payload = response.json()
    assert "recommendations" in payload

    for recommendation in payload["recommendations"]:
        assert recommendation["symbol"] is not None
        assert recommendation["outcome_status"] is None or isinstance(recommendation["outcome_status"], str)
        assert "workflow_run_id" in recommendation["metadata"]
        assert "intelligence_run_id" in recommendation["metadata"]
        assert "execution_receipt_id" in recommendation["metadata"]
        assert "recommendation_generate_receipt_id" in recommendation["metadata"]
        assert "knowledge_hint_count" in recommendation["metadata"]
        assert "knowledge_hint_status" in recommendation["metadata"]
        assert "governance" in recommendation["metadata"]
        assert "governance_policy_set_id" in recommendation["metadata"]
        assert "governance_active_policy_ids" in recommendation["metadata"]
        if recommendation["confidence"] is None:
            assert recommendation["metadata"]["confidence_status"] == "not_recorded"


def test_validation_summary_period_id_is_real_or_none():
    with _app_client() as client:
        response = client.get("/api/v1/validation/summary")
    assert response.status_code == 200

    payload = response.json()
    assert payload["period_id"] != "latest_period"


def test_evals_latest_filters_dirty_notes():
    with _app_client() as client:
        response = client.get("/api/v1/evals/latest")
    assert response.status_code == 200

    payload = response.json()
    for case in payload["cases"]:
        assert "notes: []" not in case["notes"]


def test_reports_latest_uses_consistent_status_and_report_path():
    with _app_client() as client:
        response = client.get("/api/v1/reports/latest?limit=10")
    assert response.status_code == 200

    payload = response.json()
    for report in payload["reports"]:
        if report["report_path"] is None:
            assert report["status"] == "not_generated"
        else:
            assert report["status"] == "generated"


def test_review_generate_skeleton_has_single_sections_source():
    with _app_client() as client:
        response = client.post("/api/v1/reviews/generate-skeleton?report_id=rep_semantic&reco_id=reco_semantic")
    assert response.status_code == 200

    payload = response.json()
    assert payload["sections"] == [
        "expected_outcome",
        "actual_outcome",
        "deviation",
        "mistake_tags",
        "lessons",
        "new_rule_candidate",
    ]
    assert "sections" not in payload["metadata"]
