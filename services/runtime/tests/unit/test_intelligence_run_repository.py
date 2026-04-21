from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from domains.intelligence_runs.models import IntelligenceRun
from domains.intelligence_runs.repository import IntelligenceRunRepository
from domains.intelligence_runs.service import IntelligenceRunService
from state.db.base import Base


def test_intelligence_run_repository_create_and_update():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()

    try:
        service = IntelligenceRunService(IntelligenceRunRepository(db))
        row = service.create(
            IntelligenceRun(
                task_type="analysis.generate",
                task_id="task_123",
                trace_id="trace_123",
                idempotency_key="task_123",
                status="pending",
                reason="Analyze BTC",
                actor="pfios.analyze",
                context="analyze.workflow",
                input_summary="Analyze BTC",
            )
        )
        service.mark_completed(
            "task_123",
            provider="gemini",
            model="google/gemini-3.1-pro-preview",
            output_summary="BTC remains constructive.",
        )
        model = service.get_model(row.id)

        assert model is not None
        assert model.status == "completed"
        assert model.provider == "gemini"
        assert model.output_summary == "BTC remains constructive."
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)
