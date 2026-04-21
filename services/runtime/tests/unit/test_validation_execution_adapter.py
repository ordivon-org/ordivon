from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from capabilities.boundary import ActionContext
from domains.execution_records.orm import ExecutionReceiptORM, ExecutionRequestORM
from domains.journal.issue_models import Issue
from domains.journal.issue_orm import IssueORM
from domains.journal.issue_repository import IssueRepository
from domains.journal.issue_service import IssueService
from execution.adapters import ValidationExecutionAdapter, ValidationExecutionFailure
from state.db.base import Base


def _make_db():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    testing_session_local = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)
    return engine, testing_session_local


def test_validation_adapter_writes_success_request_and_receipt():
    engine, testing_session_local = _make_db()
    db = testing_session_local()
    try:
        service = IssueService(IssueRepository(db))
        adapter = ValidationExecutionAdapter(db)

        result = adapter.report_issue(
            service=service,
            issue=Issue(
                id="issue_exec_ok",
                title="P1 review",
                summary="Validation drift detected",
                severity="p1",
                category="review",
            ),
            action_context=ActionContext(
                actor="test-suite",
                context="validation_issue_test",
                reason="report validation issue",
                idempotency_key="issue_exec_ok:report",
            ),
        )

        request_row = db.query(ExecutionRequestORM).one()
        receipt_row = db.query(ExecutionReceiptORM).one()
        persisted_issue = db.get(IssueORM, "issue_exec_ok")

        assert result.execution_request_id == request_row.id
        assert result.execution_receipt_id == receipt_row.id
        assert request_row.action_id == "validation_issue_report"
        assert request_row.status == "succeeded"
        assert request_row.entity_type == "issue"
        assert request_row.entity_id == "issue_exec_ok"
        assert receipt_row.status == "succeeded"
        assert receipt_row.result_ref == "issue_exec_ok"
        assert persisted_issue is not None
        assert persisted_issue.id == "issue_exec_ok"
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


def test_validation_adapter_writes_failed_receipt_without_success_issue_row():
    engine, testing_session_local = _make_db()
    db = testing_session_local()
    try:
        service = IssueService(IssueRepository(db))
        adapter = ValidationExecutionAdapter(db)
        original_create = service.create_with_options

        def _boom(*args, **kwargs):
            raise RuntimeError("validation issue exploded")

        service.create_with_options = _boom  # type: ignore[assignment]
        try:
            adapter.report_issue(
                service=service,
                issue=Issue(
                    id="issue_exec_fail",
                    title="P1 review",
                    summary="Validation drift detected",
                    severity="p1",
                    category="review",
                ),
                action_context=ActionContext(
                    actor="test-suite",
                    context="validation_issue_test",
                    reason="force validation issue failure",
                    idempotency_key="issue_exec_fail:report",
                ),
            )
        except ValidationExecutionFailure as exc:
            assert exc.status_code == 500
        else:
            raise AssertionError("Expected ValidationExecutionFailure")
        finally:
            service.create_with_options = original_create  # type: ignore[assignment]

        request_row = db.query(ExecutionRequestORM).one()
        receipt_row = db.query(ExecutionReceiptORM).one()
        persisted_issue = db.get(IssueORM, "issue_exec_fail")

        assert request_row.status == "failed"
        assert receipt_row.status == "failed"
        assert persisted_issue is None
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


def test_validation_adapter_avoids_begin_nested_for_duckdb_compatibility(monkeypatch):
    engine, testing_session_local = _make_db()
    db = testing_session_local()
    try:
        service = IssueService(IssueRepository(db))
        adapter = ValidationExecutionAdapter(db)

        def _no_nested_transactions():
            raise AssertionError("begin_nested should not be called in validation adapter")

        monkeypatch.setattr(db, "begin_nested", _no_nested_transactions)

        result = adapter.report_issue(
            service=service,
            issue=Issue(
                id="issue_no_nested",
                title="P1 review",
                summary="Validation drift detected",
                severity="p1",
                category="review",
            ),
            action_context=ActionContext(
                actor="test-suite",
                context="validation_issue_test",
                reason="assert duckdb compatibility without savepoints",
                idempotency_key="issue_no_nested:report",
            ),
        )

        persisted_issue = db.get(IssueORM, "issue_no_nested")
        assert result.execution_request_id
        assert result.execution_receipt_id
        assert persisted_issue is not None
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)
