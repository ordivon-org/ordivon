import pytest

from domains.intelligence_runs.models import IntelligenceRun
from domains.intelligence_runs.repository import IntelligenceRunRepository
from domains.intelligence_runs.service import IntelligenceRunService
from shared.errors.domain import DomainNotFound, InvalidStateTransition
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from state.db.base import Base


def _make_db():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)
    return engine, TestingSessionLocal


def test_intelligence_run_service_rejects_completed_to_failed():
    engine, TestingSessionLocal = _make_db()
    db = TestingSessionLocal()
    try:
        service = IntelligenceRunService(IntelligenceRunRepository(db))
        service.create(
            IntelligenceRun(
                task_type="analysis.generate",
                task_id="task_transition_1",
                idempotency_key="task_transition_1",
                status="pending",
                reason="Analyze BTC",
                actor="pfios.analyze",
                context="analyze.workflow",
                input_summary="Analyze BTC",
            )
        )
        service.mark_completed("task_transition_1")
        with pytest.raises(InvalidStateTransition, match="Invalid intelligence run transition"):
            service.mark_failed("task_transition_1", error="late failure")
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


def test_intelligence_run_service_raises_for_unknown_task():
    engine, TestingSessionLocal = _make_db()
    db = TestingSessionLocal()
    try:
        service = IntelligenceRunService(IntelligenceRunRepository(db))
        with pytest.raises(DomainNotFound, match="Intelligence run not found"):
            service.mark_completed("missing-task")
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)
