from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from domains.workflow_runs.models import WorkflowRun
from domains.workflow_runs.repository import WorkflowRunRepository
from domains.workflow_runs.service import WorkflowRunService
from state.db.base import Base


def test_workflow_run_repository_create_and_update():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()

    try:
        service = WorkflowRunService(WorkflowRunRepository(db))
        row = service.create(
            WorkflowRun(
                workflow_name="analyze",
                request_summary="Analyze BTC [BTC/USDT]",
                status="pending",
                lineage_refs={"symbol": "BTC/USDT"},
            )
        )
        run = WorkflowRun(
            id=row.id,
            workflow_name="analyze",
            request_summary="Analyze BTC [BTC/USDT]",
            status="completed",
            analysis_id="analysis_123",
            recommendation_id="reco_123",
            intelligence_run_id="irun_123",
            step_statuses=[
                {"step": "BuildContextStep", "status": "completed"},
                {"step": "ReasonStep", "status": "completed"},
            ],
            lineage_refs={"symbol": "BTC/USDT"},
            started_at=row.started_at.isoformat(),
            completed_at=row.started_at.isoformat(),
        )
        service.save(run)
        model = service.get_model(row.id)

        assert model is not None
        assert model.status == "completed"
        assert model.analysis_id == "analysis_123"
        assert model.step_statuses[-1]["step"] == "ReasonStep"
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)
