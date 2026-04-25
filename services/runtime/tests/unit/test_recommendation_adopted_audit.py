"""Verify that recommendation_adopted audit event is emitted on adoption."""

from unittest.mock import MagicMock

from domains.strategy.models import Recommendation
from domains.strategy.service import RecommendationService
from shared.enums.domain import RecommendationStatus


def _build_service(*, initial_status=RecommendationStatus.GENERATED):
    repo = MagicMock()
    auditor = MagicMock()
    svc = RecommendationService(repo, auditor=auditor)

    model = Recommendation(
        analysis_id="a1",
        title="Test recommendation",
        confidence=0.8,
        status=initial_status,
    )
    row = MagicMock()
    row.id = "rec_1"
    repo.get.return_value = row
    repo.to_model.return_value = model
    repo.update_status.return_value = row
    return svc, repo, auditor


def test_transition_to_adopted_emits_adopted_audit_event():
    svc, _, auditor = _build_service()

    svc.transition("rec_1", RecommendationStatus.ADOPTED)

    event_types = [c.kwargs["event_type"] for c in auditor.record_event.call_args_list]
    assert "recommendation_status_update" in event_types
    assert "recommendation_adopted" in event_types


def test_transition_to_non_adopted_does_not_emit_adopted_event():
    svc, _, auditor = _build_service()

    svc.transition("rec_1", RecommendationStatus.ARCHIVED)

    event_types = [c.kwargs["event_type"] for c in auditor.record_event.call_args_list]
    assert "recommendation_status_update" in event_types
    assert "recommendation_adopted" not in event_types


def test_transition_without_auditor_does_not_fail():
    repo = MagicMock()
    svc = RecommendationService(repo, auditor=None)

    model = Recommendation(
        analysis_id="a1",
        title="Test recommendation",
        confidence=0.8,
        status=RecommendationStatus.GENERATED,
    )
    row = MagicMock()
    row.id = "rec_1"
    repo.get.return_value = row
    repo.to_model.return_value = model
    repo.update_status.return_value = row

    result = svc.transition("rec_1", RecommendationStatus.ADOPTED)
    assert result is not None
