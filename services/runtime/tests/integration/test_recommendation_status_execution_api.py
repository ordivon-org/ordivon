from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from apps.api.app.deps import get_db
from apps.api.app.main import app
from domains.execution_records.orm import ExecutionReceiptORM, ExecutionRequestORM
from domains.strategy.models import Recommendation
from domains.strategy.orm import RecommendationORM
from domains.strategy.repository import RecommendationRepository
from governance.audit.orm import AuditEventORM
from shared.enums.domain import RecommendationStatus
from shared.utils.serialization import from_json_text
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


def test_recommendation_status_update_api_keeps_response_audit_execution_and_state_consistent():
    engine, TestingSessionLocal = _make_db()

    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    db = TestingSessionLocal()
    try:
        RecommendationRepository(db).create(
            Recommendation(
                id="reco_status_api",
                analysis_id="ana_status_api",
                title="Track BTC",
                summary="Track BTC setup",
                status=RecommendationStatus.GENERATED,
            )
        )
        db.commit()
    finally:
        db.close()

    client = TestClient(app)
    response = client.patch(
        "/api/v1/recommendations/reco_status_api/status",
        json={
            "lifecycle_status": "adopted",
            "action_context": {
                "actor": "api-test",
                "context": "recommendation-status-update",
                "reason": "mark recommendation adopted",
                "idempotency_key": "reco_status_api:adopted",
            },
        },
    )

    assert response.status_code == 200
    body = response.json()

    db = TestingSessionLocal()
    try:
        request_row = db.query(ExecutionRequestORM).one()
        receipt_row = db.query(ExecutionReceiptORM).one()
        recommendation_row = db.query(RecommendationORM).one()
        audit_row = (
            db.query(AuditEventORM)
            .filter(AuditEventORM.event_type == "recommendation_status_update")
            .order_by(AuditEventORM.created_at.desc())
            .first()
        )

        assert audit_row is not None
        payload = from_json_text(audit_row.payload_json, {})
        success_audit_count = (
            db.query(AuditEventORM).filter(AuditEventORM.event_type == "recommendation_status_update").count()
        )

        assert body["status"] == "success"
        assert body["recommendation_id"] == "reco_status_api"
        assert body["lifecycle_status"] == "adopted"
        assert body["execution_request_id"] == request_row.id
        assert body["execution_receipt_id"] == receipt_row.id

        assert request_row.action_id == "recommendation_status_update"
        assert request_row.status == "succeeded"
        assert request_row.recommendation_id == "reco_status_api"
        assert receipt_row.request_id == request_row.id
        assert receipt_row.status == "succeeded"
        assert receipt_row.result_ref == "reco_status_api"

        assert recommendation_row.id == "reco_status_api"
        assert recommendation_row.status == RecommendationStatus.ADOPTED.value

        assert success_audit_count == 1
        assert payload["new_status"] == "adopted"
        assert payload["execution_request_id"] == request_row.id
        assert payload["execution_receipt_id"] == receipt_row.id
    finally:
        db.close()
        app.dependency_overrides.clear()
        Base.metadata.drop_all(bind=engine)


def test_recommendation_status_update_api_failure_persists_failed_refs_without_success_state():
    engine, TestingSessionLocal = _make_db()

    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    db = TestingSessionLocal()
    try:
        RecommendationRepository(db).create(
            Recommendation(
                id="reco_status_fail_api",
                analysis_id="ana_status_fail_api",
                title="Track BTC",
                summary="Track BTC setup",
                status=RecommendationStatus.GENERATED,
            )
        )
        db.commit()
    finally:
        db.close()

    client = TestClient(app)
    response = client.patch(
        "/api/v1/recommendations/reco_status_fail_api/status",
        json={
            "lifecycle_status": "reviewed",
            "action_context": {
                "actor": "api-test",
                "context": "recommendation-status-update",
                "reason": "force invalid transition",
                "idempotency_key": "reco_status_fail_api:reviewed",
            },
        },
    )

    assert response.status_code == 409
    detail = response.json()["detail"]

    db = TestingSessionLocal()
    try:
        request_row = db.query(ExecutionRequestORM).one()
        receipt_row = db.query(ExecutionReceiptORM).one()
        recommendation_row = db.query(RecommendationORM).one()
        audit_row = (
            db.query(AuditEventORM)
            .filter(AuditEventORM.event_type == "recommendation_status_update_failed")
            .order_by(AuditEventORM.created_at.desc())
            .first()
        )

        assert audit_row is not None
        payload = from_json_text(audit_row.payload_json, {})

        assert detail["execution_request_id"] == request_row.id
        assert detail["execution_receipt_id"] == receipt_row.id
        assert request_row.status == "failed"
        assert receipt_row.status == "failed"
        assert recommendation_row.status == RecommendationStatus.GENERATED.value
        assert payload["execution_request_id"] == request_row.id
        assert payload["execution_receipt_id"] == receipt_row.id
        assert payload["attempted_status"] == "reviewed"
    finally:
        db.close()
        app.dependency_overrides.clear()
        Base.metadata.drop_all(bind=engine)
