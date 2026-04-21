from state.db.bootstrap import init_db
from state.db.session import SessionLocal
from shared.enums.domain import RecommendationStatus
from domains.strategy.models import Recommendation
from domains.strategy.repository import RecommendationRepository


def test_recommendation_repository_create_and_get():
    init_db()
    db = SessionLocal()

    try:
        repo = RecommendationRepository(db)
        recommendation = Recommendation(
            analysis_id="analysis-123",
            title="Action for BTC-USDT",
            summary="Test summary",
            rationale="Test rationale",
            expected_outcome="Reduce uncertainty",
            confidence=0.8,
            status=RecommendationStatus.GENERATED,
            outcome_metric_config={"window": "1d"},
        )

        row = repo.create(recommendation)
        loaded = repo.get(row.id)

        assert loaded is not None
        assert loaded.analysis_id == "analysis-123"
        assert loaded.title == "Action for BTC-USDT"
        assert loaded.status == RecommendationStatus.GENERATED.value
    finally:
        db.close()
