from state.db.bootstrap import init_db
from state.db.session import SessionLocal
from domains.research.models import AnalysisResult
from domains.research.repository import AnalysisRepository


def test_analysis_repository_create_and_get():
    init_db()
    db = SessionLocal()

    try:
        repo = AnalysisRepository(db)
        analysis = AnalysisResult(
            query="Test query",
            symbol="ETH-USDT",
            timeframe="1h",
            summary="Test summary",
            thesis="Test thesis",
            risks=["risk_a"],
            suggested_actions=["action_a"],
            metadata={"provider": "mock"},
        )

        row = repo.create(analysis)
        loaded = repo.get(row.id)

        assert loaded is not None
        assert loaded.symbol == "ETH-USDT"
        assert loaded.summary == "Test summary"
    finally:
        db.close()
