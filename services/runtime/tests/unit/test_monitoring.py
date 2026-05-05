from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from domains.execution_records.models import ExecutionReceipt, ExecutionRequest
from domains.execution_records.repository import ExecutionRecordRepository
from domains.workflow_runs.models import WorkflowRun
from domains.workflow_runs.repository import WorkflowRunRepository
from infra.scheduler import ScheduledTrigger, SchedulerService
from governance_engine.audit.models import AuditEvent
from governance_engine.audit.repository import AuditEventRepository
from infra.monitoring import MonitoringService
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


def test_monitoring_snapshot_counts_recent_failures_and_activity():
    engine, TestingSessionLocal = _make_db()
    db = TestingSessionLocal()
    try:
        WorkflowRunRepository(db).create(
            WorkflowRun(
                id="wfrun_monitor_1",
                workflow_name="analyze",
                status="failed",
                request_summary="Analyze BTC",
            )
        )
        execution_repo = ExecutionRecordRepository(db)
        execution_repo.create_request(
            ExecutionRequest(
                id="exreq_monitor_1",
                action_id="review_complete",
                family="review",
                side_effect_level="state_mutation",
                status="failed",
                actor="test",
                context="monitoring_test",
                reason="test",
                idempotency_key="monitoring-test-1",
            )
        )
        execution_repo.create_receipt(
            ExecutionReceipt(
                id="exrcpt_monitor_1",
                request_id="exreq_monitor_1",
                action_id="review_complete",
                status="failed",
                error="failed",
            )
        )
        AuditEventRepository(db).create(
            AuditEvent(
                id="audit_monitor_1",
                event_type="review_completed_failed",
                entity_type="review",
                entity_id="review_monitor_1",
                payload={"detail": "failed"},
            )
        )
        scheduler = SchedulerService()
        scheduler.register_target("dashboard_summary_refresh", lambda payload: {"refreshed": payload.get("scope")})
        scheduler.register_trigger(
            ScheduledTrigger(
                id="sched_monitor_1",
                target_capability="dashboard_summary_refresh",
                payload={"scope": "dashboard"},
            )
        )
        scheduler.dispatch("sched_monitor_1")
        scheduler.save_to_repository(db)
        db.commit()

        snapshot = MonitoringService(db).get_snapshot()

        assert snapshot.monitoring_status == "attention"
        assert snapshot.recent_failed_workflow_count == 1
        assert snapshot.recent_failed_execution_count == 1
        assert snapshot.last_workflow_at is not None
        assert snapshot.last_audit_at is not None
        assert snapshot.monitoring_window_hours == 24
        assert snapshot.history is not None
        assert snapshot.history.workflow_failures_by_type["workflow_failed"] == 1
        assert snapshot.history.execution_failures_by_family["review"] == 1
        assert snapshot.history.top_workflow_failure_type == "workflow_failed"
        assert snapshot.history.top_execution_failure_family == "review"
        assert snapshot.history.scheduler is not None
        assert snapshot.history.scheduler.total_trigger_count == 1
        assert snapshot.history.scheduler.dispatched_trigger_count == 1
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


def test_monitoring_snapshot_returns_honest_zeroes_for_empty_db():
    engine, TestingSessionLocal = _make_db()
    db = TestingSessionLocal()
    try:
        snapshot = MonitoringService(db).get_snapshot()
        assert snapshot.monitoring_status == "nominal"
        assert snapshot.recent_failed_workflow_count == 0
        assert snapshot.recent_failed_execution_count == 0
        assert snapshot.last_workflow_at is None
        assert snapshot.last_audit_at is None
        assert snapshot.history is not None
        assert snapshot.history.approval_blocked_count == 0
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)
