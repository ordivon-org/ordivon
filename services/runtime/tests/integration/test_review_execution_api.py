import json

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from apps.api.app.deps import get_db
from apps.api.app.main import app
from domains.execution_records.orm import ExecutionReceiptORM, ExecutionRequestORM
from domains.journal.models import Review
from domains.journal.orm import ReviewORM
from domains.journal.repository import ReviewRepository
from domains.strategy.models import Recommendation
from domains.strategy.repository import RecommendationRepository
from governance.audit.orm import AuditEventORM
from shared.enums.domain import ReviewStatus
from state.db.base import Base


engine = create_engine(
    "sqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def _payload(row: AuditEventORM) -> dict:
    return json.loads(row.payload_json)


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


def test_review_complete_response_audit_request_receipt_and_row_are_consistent():
    client, db = _make_client()
    try:
        RecommendationRepository(db).create(
            Recommendation(
                id="reco_review_consistency",
                analysis_id="analysis_review_consistency",
                title="Trend setup",
                summary="summary",
            )
        )
        db.commit()

        submit_response = client.post(
            "/api/v1/reviews/submit",
            json={
                "linked_recommendation_id": "reco_review_consistency",
                "expected_outcome": "Trend holds",
                "actual_outcome": "Trend failed",
                "deviation": "Late entry",
                "mistake_tags": "timing",
                "lessons": [{"lesson_text": "Use confirmation"}],
                "new_rule_candidate": "Wait for pullback",
            },
        )
        review_id = submit_response.json()["id"]

        complete_response = client.post(
            f"/api/v1/reviews/{review_id}/complete",
            json={
                "observed_outcome": "Loss contained",
                "verdict": "invalidated",
                "variance_summary": "Setup failed quickly",
                "cause_tags": ["timing"],
                "lessons": ["Use confirmation candle"],
                "followup_actions": ["Update checklist"],
            },
        )

        assert complete_response.status_code == 200
        body = complete_response.json()
        request_id = body["metadata"]["execution_request_id"]
        receipt_id = body["metadata"]["execution_receipt_id"]

        request_row = db.get(ExecutionRequestORM, request_id)
        receipt_row = db.get(ExecutionReceiptORM, receipt_id)
        review_row = db.get(ReviewORM, review_id)
        audit_row = (
            db
            .query(AuditEventORM)
            .filter(AuditEventORM.event_type == "review_completed", AuditEventORM.review_id == review_id)
            .one()
        )
        audit_payload = _payload(audit_row)

        assert request_row is not None
        assert request_row.id == request_id
        assert request_row.action_id == "review_complete"
        assert request_row.status == "succeeded"
        assert request_row.entity_type == "review"
        assert request_row.entity_id == review_id
        assert receipt_row is not None
        assert receipt_row.id == receipt_id
        assert receipt_row.status == "succeeded"
        assert receipt_row.result_ref == review_id
        assert review_row is not None
        assert review_row.status == ReviewStatus.COMPLETED.value
        assert audit_payload["execution_request_id"] == request_id
        assert audit_payload["execution_receipt_id"] == receipt_id
        assert body["id"] == review_id
        assert body["status"] == ReviewStatus.COMPLETED.value
    finally:
        _close_client(client, db)


def test_review_complete_failure_returns_failed_refs_and_preserves_review_state():
    client, db = _make_client()
    try:
        RecommendationRepository(db).create(
            Recommendation(
                id="reco_review_fail",
                analysis_id="analysis_review_fail",
                title="Trend setup",
                summary="summary",
            )
        )
        ReviewRepository(db).create(
            Review(
                id="review_already_completed",
                recommendation_id="reco_review_fail",
                status=ReviewStatus.COMPLETED,
                expected_outcome="Trend holds",
            )
        )
        db.commit()

        response = client.post(
            "/api/v1/reviews/review_already_completed/complete",
            json={
                "observed_outcome": "Still bad",
                "verdict": "invalidated",
                "variance_summary": "Should fail",
                "cause_tags": ["timing"],
                "lessons": ["Do not reopen implicitly"],
                "followup_actions": ["Keep immutable"],
            },
        )

        assert response.status_code == 409
        detail = response.json()["detail"]
        request_id = detail["execution_request_id"]
        receipt_id = detail["execution_receipt_id"]

        request_row = db.get(ExecutionRequestORM, request_id)
        receipt_row = db.get(ExecutionReceiptORM, receipt_id)
        review_row = db.get(ReviewORM, "review_already_completed")
        failed_audit = (
            db
            .query(AuditEventORM)
            .filter(
                AuditEventORM.event_type == "review_completed_failed",
                AuditEventORM.review_id == "review_already_completed",
            )
            .one()
        )
        failed_payload = _payload(failed_audit)

        assert request_row is not None
        assert request_row.status == "failed"
        assert request_row.entity_id == "review_already_completed"
        assert receipt_row is not None
        assert receipt_row.status == "failed"
        assert review_row is not None
        assert review_row.status == ReviewStatus.COMPLETED.value
        assert failed_payload["execution_request_id"] == request_id
        assert failed_payload["execution_receipt_id"] == receipt_id
        assert (
            db
            .query(AuditEventORM)
            .filter(
                AuditEventORM.event_type == "review_completed",
                AuditEventORM.review_id == "review_already_completed",
            )
            .count()
            == 0
        )
    finally:
        _close_client(client, db)
