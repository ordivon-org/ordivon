import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from apps.api.app.deps import get_db
from apps.api.app.main import app
from domains.execution_records.orm import ExecutionReceiptORM, ExecutionRequestORM
from domains.knowledge_feedback.orm import KnowledgeFeedbackPacketORM
from governance.approval import HumanApprovalGate
from governance.approval_repository import ApprovalRepository
from domains.strategy.models import Recommendation
from domains.research.models import AnalysisResult
from domains.research.repository import AnalysisRepository
from domains.strategy.outcome_orm import OutcomeSnapshotORM
from domains.strategy.outcome_repository import OutcomeRepository
from domains.strategy.outcome_service import OutcomeService
from domains.strategy.repository import RecommendationRepository
from domains.strategy.orm import RecommendationORM
from domains.strategy.service import RecommendationService
from governance.audit.orm import AuditEventORM
from domains.journal.models import Review
from domains.journal.orm import ReviewORM
from domains.journal.repository import ReviewRepository
from domains.journal.lesson_repository import LessonRepository
from domains.journal.lesson_service import LessonService
from domains.journal.service import ReviewService
from shared.enums.domain import ReviewVerdict
from state.db.base import Base


engine = create_engine(
    "sqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture
def db() -> Session:
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture
def client(db: Session):
    def override_get_db():
        try:
            yield db
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


def test_api_v1_review_submit_returns_success_and_writes_audit(client: TestClient, db: Session):
    response = client.post(
        "/api/v1/reviews/submit",
        json={
            "linked_recommendation_id": "reco_1",
            "expected_outcome": "Breakout continues",
            "actual_outcome": "Breakout failed",
            "deviation": "Momentum faded",
            "mistake_tags": "timing,risk",
            "lessons": [{"lesson_text": "Wait for confirmation"}],
            "new_rule_candidate": "Require higher timeframe confirmation",
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["id"].startswith("review_")
    assert body["recommendation_id"] == "reco_1"
    assert body["metadata"]["execution_request_id"].startswith("exreq_")
    assert body["metadata"]["execution_receipt_id"].startswith("exrcpt_")

    audit_events = db.query(AuditEventORM).filter(AuditEventORM.event_type == "review_submitted").all()
    assert len(audit_events) == 1
    assert audit_events[0].review_id == body["id"]
    assert body["metadata"]["execution_request_id"] in audit_events[0].payload_json
    assert body["metadata"]["execution_receipt_id"] in audit_events[0].payload_json
    request_row = db.get(ExecutionRequestORM, body["metadata"]["execution_request_id"])
    receipt_row = db.get(ExecutionReceiptORM, body["metadata"]["execution_receipt_id"])
    review_row = db.get(ReviewORM, body["id"])
    assert request_row is not None
    assert request_row.action_id == "review_submit"
    assert request_row.status == "succeeded"
    assert request_row.entity_id == body["id"]
    assert receipt_row is not None
    assert receipt_row.status == "succeeded"
    assert receipt_row.result_ref == body["id"]
    assert review_row.id == body["id"]


def test_api_v1_review_submit_failure_returns_failed_refs_and_no_review_row(
    client: TestClient, db: Session, monkeypatch
):
    def _boom(*args, **kwargs):
        raise RuntimeError("submit exploded")

    monkeypatch.setattr(ReviewService, "create_with_options", _boom)

    response = client.post(
        "/api/v1/reviews/submit",
        json={
            "linked_recommendation_id": "reco_fail_submit",
            "expected_outcome": "Breakout continues",
            "actual_outcome": "Breakout failed",
            "deviation": "Momentum faded",
            "mistake_tags": "timing,risk",
            "lessons": [{"lesson_text": "Wait for confirmation"}],
            "new_rule_candidate": "Require higher timeframe confirmation",
        },
    )

    assert response.status_code == 500
    detail = response.json()["detail"]
    request_row = db.get(ExecutionRequestORM, detail["execution_request_id"])
    receipt_row = db.get(ExecutionReceiptORM, detail["execution_receipt_id"])
    failed_audits = db.query(AuditEventORM).filter(AuditEventORM.event_type == "review_submitted_failed").all()
    assert request_row is not None
    assert request_row.status == "failed"
    assert receipt_row is not None
    assert receipt_row.status == "failed"
    assert len(failed_audits) == 1
    assert detail["execution_request_id"] in failed_audits[0].payload_json
    assert detail["execution_receipt_id"] in failed_audits[0].payload_json
    assert db.get(ReviewORM, request_row.entity_id) is None


def test_api_v1_reviews_pending_returns_capability_backed_results(client: TestClient, db: Session):
    ReviewRepository(db).create(
        Review(
            id="review_pending_1",
            recommendation_id="reco_pending_1",
            review_type="recommendation_postmortem",
            expected_outcome="Trend holds",
        )
    )
    db.commit()

    response = client.get("/api/v1/reviews/pending?limit=5")

    assert response.status_code == 200
    body = response.json()
    assert len(body["reviews"]) == 1
    assert body["reviews"][0]["id"] == "review_pending_1"
    assert body["reviews"][0]["recommendation_id"] == "reco_pending_1"
    assert body["reviews"][0]["status"] == "pending"
    assert body["reviews"][0]["workflow_run_id"] is None
    assert body["reviews"][0]["intelligence_run_id"] is None
    assert body["reviews"][0]["recommendation_generate_receipt_id"] is None
    assert body["reviews"][0]["latest_outcome_status"] is None
    assert body["reviews"][0]["latest_outcome_reason"] is None
    assert body["reviews"][0]["knowledge_hint_count"] == 0


def test_api_v1_reviews_pending_exposes_review_trace_outcome_and_hint_signals(client: TestClient, db: Session):
    AnalysisRepository(db).create(
        AnalysisResult(
            id="analysis_pending_surface",
            query="Analyze BTC trend",
            symbol="BTC-USDT",
            metadata={
                "workflow_run_id": "wfrun_pending_surface",
                "intelligence_run_id": "irun_pending_surface",
                "recommendation_generate_receipt_id": "exrcpt_pending_surface",
            },
        )
    )
    RecommendationRepository(db).create(
        Recommendation(
            id="reco_pending_surface",
            analysis_id="analysis_pending_surface",
            title="Track BTC breakout",
            summary="Track BTC breakout setup",
        )
    )
    review_service = ReviewService(
        ReviewRepository(db),
        LessonService(LessonRepository(db)),
        outcome_service=OutcomeService(OutcomeRepository(db)),
        recommendation_service=RecommendationService(RecommendationRepository(db)),
    )
    review_row = review_service.create(
        Review(
            id="review_pending_surface",
            recommendation_id="reco_pending_surface",
            review_type="recommendation_postmortem",
            expected_outcome="BTC breakout confirmation",
        )
    )
    review_service.complete_review(
        review_id=review_row.id,
        observed_outcome="BTC breakout failed",
        verdict=ReviewVerdict.INVALIDATED,
        variance_summary="Breakout rejected",
        cause_tags=["momentum"],
        lessons=["Wait for stronger confirmation"],
        followup_actions=["Tighten invalidation"],
    )
    ReviewRepository(db).create(
        Review(
            id="review_pending_surface_2",
            recommendation_id="reco_pending_surface",
            review_type="recommendation_postmortem",
            expected_outcome="Retry confirmation",
        )
    )
    db.commit()

    response = client.get("/api/v1/reviews/pending?limit=5")

    assert response.status_code == 200
    body = response.json()
    review = next(item for item in body["reviews"] if item["id"] == "review_pending_surface_2")
    assert review["workflow_run_id"] == "wfrun_pending_surface"
    assert review["intelligence_run_id"] == "irun_pending_surface"
    assert review["recommendation_generate_receipt_id"] == "exrcpt_pending_surface"
    assert review["latest_outcome_status"] == "failed"
    assert review["latest_outcome_reason"] == "review_completion_backfill"
    assert review["knowledge_hint_count"] == 1


def test_api_v1_review_complete_returns_success_and_writes_audits(client: TestClient, db: Session):
    RecommendationRepository(db).create(
        Recommendation(
            id="reco_2",
            analysis_id="analysis_2",
            title="Trend setup",
            summary="Trend setup summary",
        )
    )
    db.commit()

    submit_response = client.post(
        "/api/v1/reviews/submit",
        json={
            "linked_recommendation_id": "reco_2",
            "expected_outcome": "Trend holds",
            "actual_outcome": "Trend reversed",
            "deviation": "Entry was late",
            "mistake_tags": "timing",
            "lessons": [{"lesson_text": "Cut earlier"}],
            "new_rule_candidate": "Tighter invalidation",
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
    assert body["id"] == review_id
    assert body["status"] == "completed"
    assert body["lessons_created"] == 1
    assert body["metadata"]["execution_request_id"].startswith("exreq_")
    assert body["metadata"]["execution_receipt_id"].startswith("exrcpt_")
    assert body["metadata"]["knowledge_feedback"]["id"].startswith("kfpkt_")
    assert body["metadata"]["knowledge_feedback"]["recommendation_id"] == "reco_2"
    assert body["metadata"]["knowledge_feedback"]["review_id"] == review_id
    assert len(body["metadata"]["knowledge_feedback"]["governance_hints"]) == 1
    assert len(body["metadata"]["knowledge_feedback"]["intelligence_hints"]) == 1

    completed_audits = db.query(AuditEventORM).filter(AuditEventORM.event_type == "review_completed").all()
    lesson_audits = db.query(AuditEventORM).filter(AuditEventORM.event_type == "lesson_persisted").all()
    outcome_audits = db.query(AuditEventORM).filter(AuditEventORM.event_type == "outcome_backfilled").all()
    feedback_audits = db.query(AuditEventORM).filter(AuditEventORM.event_type == "knowledge_feedback_prepared").all()
    feedback_packet = db.get(KnowledgeFeedbackPacketORM, body["metadata"]["knowledge_feedback"]["id"])
    request_row = db.get(ExecutionRequestORM, body["metadata"]["execution_request_id"])
    receipt_row = db.get(ExecutionReceiptORM, body["metadata"]["execution_receipt_id"])
    recommendation = db.get(RecommendationORM, "reco_2")
    outcomes = db.query(OutcomeSnapshotORM).filter(OutcomeSnapshotORM.recommendation_id == "reco_2").all()
    assert len(completed_audits) == 1
    assert completed_audits[0].review_id == review_id
    assert body["metadata"]["execution_request_id"] in completed_audits[0].payload_json
    assert body["metadata"]["execution_receipt_id"] in completed_audits[0].payload_json
    assert len(lesson_audits) == 1
    assert lesson_audits[0].review_id == review_id
    assert len(outcome_audits) == 1
    assert outcome_audits[0].review_id == review_id
    assert len(feedback_audits) == 1
    assert feedback_audits[0].review_id == review_id
    assert body["metadata"]["knowledge_feedback"]["id"] in feedback_audits[0].payload_json
    assert feedback_packet is not None
    assert feedback_packet.review_id == review_id
    assert feedback_packet.recommendation_id == "reco_2"
    assert request_row is not None
    assert request_row.status == "succeeded"
    assert request_row.entity_id == review_id
    assert receipt_row is not None
    assert receipt_row.status == "succeeded"
    assert receipt_row.result_ref == review_id
    assert recommendation is not None
    assert recommendation.latest_outcome_snapshot_id is not None
    assert len(outcomes) == 1
    assert outcomes[0].id == recommendation.latest_outcome_snapshot_id


def test_api_v1_review_complete_requires_approval_when_requested(client: TestClient, db: Session):
    RecommendationRepository(db).create(
        Recommendation(
            id="reco_approval_required",
            analysis_id="analysis_approval_required",
            title="Trend setup",
            summary="Trend setup summary",
        )
    )
    db.commit()

    submit_response = client.post(
        "/api/v1/reviews/submit",
        json={
            "linked_recommendation_id": "reco_approval_required",
            "expected_outcome": "Trend holds",
            "actual_outcome": "Trend reversed",
            "deviation": "Entry was late",
            "mistake_tags": "timing",
            "lessons": [{"lesson_text": "Cut earlier"}],
            "new_rule_candidate": "Tighter invalidation",
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
            "require_approval": True,
        },
    )

    assert complete_response.status_code == 409
    detail = complete_response.json()["detail"]
    assert detail["status"] == "approval_required"
    assert detail["approval_id"] is None
    assert db.query(ExecutionRequestORM).filter(ExecutionRequestORM.action_id == "review_complete").count() == 0
    assert db.query(ExecutionReceiptORM).filter(ExecutionReceiptORM.action_id == "review_complete").count() == 0


def test_api_v1_review_complete_succeeds_with_approved_record_when_required(client: TestClient, db: Session):
    RecommendationRepository(db).create(
        Recommendation(
            id="reco_approval_ok",
            analysis_id="analysis_approval_ok",
            title="Trend setup",
            summary="Trend setup summary",
        )
    )
    db.commit()

    submit_response = client.post(
        "/api/v1/reviews/submit",
        json={
            "linked_recommendation_id": "reco_approval_ok",
            "expected_outcome": "Trend holds",
            "actual_outcome": "Trend reversed",
            "deviation": "Entry was late",
            "mistake_tags": "timing",
            "lessons": [{"lesson_text": "Cut earlier"}],
            "new_rule_candidate": "Tighter invalidation",
        },
    )
    review_id = submit_response.json()["id"]

    gate = HumanApprovalGate(ApprovalRepository(db))
    pending = gate.request_approval(
        action_key="review.complete",
        entity_type="review",
        entity_id=review_id,
        requested_by="supervisor.queue",
        reason="High consequence review completion",
    )
    approved = gate.approve(pending.id, actor="supervisor.user")
    db.commit()

    complete_response = client.post(
        f"/api/v1/reviews/{review_id}/complete",
        json={
            "observed_outcome": "Loss contained",
            "verdict": "invalidated",
            "variance_summary": "Setup failed quickly",
            "cause_tags": ["timing"],
            "lessons": ["Use confirmation candle"],
            "followup_actions": ["Update checklist"],
            "approval_id": approved.id,
            "require_approval": True,
        },
    )

    assert complete_response.status_code == 200
    body = complete_response.json()
    assert body["status"] == "completed"
    request_row = db.get(ExecutionRequestORM, body["metadata"]["execution_request_id"])
    receipt_row = db.get(ExecutionReceiptORM, body["metadata"]["execution_receipt_id"])
    assert request_row is not None
    assert request_row.action_id == "review_complete"
    assert receipt_row is not None
    assert receipt_row.status == "succeeded"


def test_api_v1_review_detail_returns_real_review_execution_outcome_and_packet_signals(client: TestClient, db: Session):
    RecommendationRepository(db).create(
        Recommendation(
            id="reco_detail_1",
            analysis_id="analysis_detail_1",
            title="Trend setup",
            summary="Trend setup summary",
        )
    )
    db.commit()

    submit_response = client.post(
        "/api/v1/reviews/submit",
        json={
            "linked_recommendation_id": "reco_detail_1",
            "expected_outcome": "Trend holds",
            "actual_outcome": "Trend reversed",
            "deviation": "Entry was late",
            "mistake_tags": "timing",
            "lessons": [{"lesson_text": "Cut earlier"}],
            "new_rule_candidate": "Tighter invalidation",
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
    feedback_id = complete_response.json()["metadata"]["knowledge_feedback"]["id"]

    response = client.get(f"/api/v1/reviews/{review_id}")

    assert response.status_code == 200
    body = response.json()
    assert body["id"] == review_id
    assert body["recommendation_id"] == "reco_detail_1"
    assert body["submit_execution_request_id"].startswith("exreq_")
    assert body["submit_execution_receipt_id"].startswith("exrcpt_")
    assert body["complete_execution_request_id"].startswith("exreq_")
    assert body["complete_execution_receipt_id"].startswith("exrcpt_")
    assert body["latest_outcome_status"] == "failed"
    assert body["latest_outcome_reason"] == "review_completion_backfill"
    assert body["knowledge_feedback_packet_id"] == feedback_id
    assert body["governance_hint_count"] == 1
    assert body["intelligence_hint_count"] == 1
    assert body["metadata"]["trace_path"] == f"/api/v1/traces/reviews/{review_id}"
    assert body["metadata"]["knowledge_feedback_status"] == "prepared"


def test_api_v1_review_detail_honestly_returns_missing_execution_outcome_and_packet_signals(
    client: TestClient, db: Session
):
    ReviewRepository(db).create(
        Review(
            id="review_detail_missing",
            recommendation_id="reco_missing_detail",
            review_type="recommendation_postmortem",
            expected_outcome="Trend holds",
        )
    )
    db.commit()

    response = client.get("/api/v1/reviews/review_detail_missing")

    assert response.status_code == 200
    body = response.json()
    assert body["submit_execution_request_id"] is None
    assert body["submit_execution_receipt_id"] is None
    assert body["complete_execution_request_id"] is None
    assert body["complete_execution_receipt_id"] is None
    assert body["latest_outcome_status"] is None
    assert body["latest_outcome_reason"] is None
    assert body["knowledge_feedback_packet_id"] is None
    assert body["governance_hint_count"] == 0
    assert body["intelligence_hint_count"] == 0
    assert body["metadata"]["knowledge_feedback_status"] == "not_prepared_yet"
