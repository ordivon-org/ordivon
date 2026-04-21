from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from capabilities.boundary import ActionContext
from domains.execution_records.repository import ExecutionRecordRepository
from domains.execution_records.service import ExecutionRecordService
from state.db.base import Base
from state.db.bootstrap import init_db  # noqa: F401


def _make_db():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)
    return engine, TestingSessionLocal


def test_execution_record_service_creates_request_and_success_receipt():
    engine, TestingSessionLocal = _make_db()
    db = TestingSessionLocal()
    try:
        service = ExecutionRecordService(ExecutionRecordRepository(db))
        request = service.start_request(
            action_id="analysis_report_write",
            action_context=ActionContext(
                actor="workflow.analyze",
                context="write_wiki_step",
                reason="write analysis report",
                idempotency_key="report-request-1",
            ),
            entity_type="analysis",
            entity_id="analysis_123",
            analysis_id="analysis_123",
            payload={"analysis_id": "analysis_123", "document_id": "doc_123"},
        )
        receipt = service.record_success(
            request.id,
            result_ref="wiki/reports/doc_123.md",
            detail={"document_path": "wiki/reports/doc_123.md"},
        )

        assert request.action_id == "analysis_report_write"
        assert receipt.request_id == request.id
        assert receipt.status == "succeeded"
        assert receipt.result_ref == "wiki/reports/doc_123.md"

        refreshed = service.repository.get_request(request.id)
        assert refreshed is not None
        assert refreshed.status == "succeeded"
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


def test_execution_record_service_updates_receipt_to_failed():
    engine, TestingSessionLocal = _make_db()
    db = TestingSessionLocal()
    try:
        service = ExecutionRecordService(ExecutionRecordRepository(db))
        request = service.start_request(
            action_id="analysis_report_write",
            action_context=ActionContext(
                actor="workflow.analyze",
                context="write_wiki_step",
                reason="write analysis report",
                idempotency_key="report-request-2",
            ),
            entity_type="analysis",
            entity_id="analysis_456",
            analysis_id="analysis_456",
            payload={"analysis_id": "analysis_456", "document_id": "doc_456"},
        )
        service.record_success(
            request.id,
            result_ref="wiki/reports/doc_456.md",
            detail={"document_path": "wiki/reports/doc_456.md"},
        )
        receipt = service.record_failure(
            request.id,
            error="metadata update failed",
            detail={"compensation_applied": True},
        )

        receipts = service.repository.list_receipts_for_request(request.id)
        assert len(receipts) == 1
        assert receipt.status == "failed"
        assert receipt.error == "metadata update failed"
        assert receipt.detail_json == '{"compensation_applied": true}'

        refreshed = service.repository.get_request(request.id)
        assert refreshed is not None
        assert refreshed.status == "failed"
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)
