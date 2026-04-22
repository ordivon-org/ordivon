from datetime import datetime, timezone
from types import SimpleNamespace

from capabilities.workflow.reviews import ReviewCapability


def test_review_capability_list_pending_maps_rows_to_contract():
    capability = ReviewCapability()
    service = SimpleNamespace(
        review_repository=SimpleNamespace(db=None),
        recommendation_service=None,
        list_pending=lambda limit=10: [
            SimpleNamespace(
                id="review_1",
                recommendation_id="reco_1",
                review_type="recommendation_postmortem",
                status="pending",
                expected_outcome="Target holds",
                created_at=datetime(2026, 4, 20, tzinfo=timezone.utc),
            )
        ]
    )

    result = capability.list_pending(service, limit=5)

    assert len(result.reviews) == 1
    assert result.reviews[0].id == "review_1"
    assert result.reviews[0].recommendation_id == "reco_1"
    assert result.reviews[0].status == "pending"
    assert result.reviews[0].created_at.startswith("2026-04-20")
