from pfios.core.db.bootstrap import init_db
from pfios.core.db.session import SessionLocal
from pfios.domain.analysis.models import AnalysisResult
from pfios.domain.analysis.repository import AnalysisRepository


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
