from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from apps.api.app.deps import get_db
from apps.api.app.main import app
from domains.execution_records.orm import ExecutionReceiptORM, ExecutionRequestORM
from domains.journal.issue_orm import IssueORM
from governance_engine.audit.orm import AuditEventORM
from state.db.base import Base


engine = create_engine(
    "sqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def _make_client() -> tuple[TestClient, Session]:
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()

    def override_get_db():
        try:
            yield db
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    return TestClient(app), db


def _close_client(client: TestClient, db: Session) -> None:
    client.close()
    db.close()
    Base.metadata.drop_all(bind=engine)
    app.dependency_overrides.clear()


def test_validation_issue_report_response_audit_request_receipt_and_row_are_consistent():
    client, db = _make_client()
    try:
        response = client.post(
            "/api/v1/validation/issue",
            json={
                "severity": "P1",
                "area": "review",
                "description": "Review outcome signal drifted",
            },
        )

        assert response.status_code == 200
        body = response.json()
        request_id = body["execution_request_id"]
        receipt_id = body["execution_receipt_id"]
        issue_id = body["issue_id"]

        request_row = db.get(ExecutionRequestORM, request_id)
        receipt_row = db.get(ExecutionReceiptORM, receipt_id)
        issue_row = db.get(IssueORM, issue_id)
        audit_row = (
            db
            .query(AuditEventORM)
            .filter(AuditEventORM.event_type == "validation_issue_reported", AuditEventORM.entity_id == issue_id)
            .one()
        )

        assert request_row is not None
        assert request_row.action_id == "validation_issue_report"
        assert request_row.status == "succeeded"
        assert request_row.entity_type == "issue"
        assert request_row.entity_id == issue_id
        assert receipt_row is not None
        assert receipt_row.status == "succeeded"
        assert receipt_row.result_ref == issue_id
        assert issue_row is not None
        assert issue_row.id == issue_id
        assert request_id in audit_row.payload_json
        assert receipt_id in audit_row.payload_json
    finally:
        _close_client(client, db)


def test_validation_issue_report_failure_returns_failed_refs_and_no_issue_row(monkeypatch):
    client, db = _make_client()
    try:
        from domains.journal.issue_service import IssueService

        def _boom(*args, **kwargs):
            raise RuntimeError("validation issue exploded")

        monkeypatch.setattr(IssueService, "create_with_options", _boom)

        response = client.post(
            "/api/v1/validation/issue",
            json={
                "severity": "P1",
                "area": "review",
                "description": "Review outcome signal drifted",
            },
        )

        assert response.status_code == 500
        detail = response.json()["detail"]
        request_id = detail["execution_request_id"]
        receipt_id = detail["execution_receipt_id"]
        request_row = db.get(ExecutionRequestORM, request_id)
        receipt_row = db.get(ExecutionReceiptORM, receipt_id)
        failed_audit = (
            db.query(AuditEventORM).filter(AuditEventORM.event_type == "validation_issue_report_failed").one()
        )

        assert request_row is not None
        assert request_row.status == "failed"
        assert receipt_row is not None
        assert receipt_row.status == "failed"
        assert request_id in failed_audit.payload_json
        assert receipt_id in failed_audit.payload_json
        assert db.get(IssueORM, request_row.entity_id) is None
    finally:
        _close_client(client, db)
