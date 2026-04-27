from __future__ import annotations

from datetime import datetime

from sqlalchemy.orm import Session

from domains.execution_records.models import ExecutionProgressRecord, ExecutionReceipt, ExecutionRequest
from domains.execution_records.orm import ExecutionProgressRecordORM, ExecutionReceiptORM, ExecutionRequestORM
from shared.utils.serialization import from_json_text, to_json_text


def _parse_dt(value: str | None) -> datetime | None:
    if not value:
        return None
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


class ExecutionRecordRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def create_request(self, request: ExecutionRequest) -> ExecutionRequestORM:
        row = ExecutionRequestORM(
            id=request.id,
            action_id=request.action_id,
            family=request.family,
            side_effect_level=request.side_effect_level,
            status=request.status,
            actor=request.actor,
            context=request.context,
            reason=request.reason,
            idempotency_key=request.idempotency_key,
            entity_type=request.entity_type,
            entity_id=request.entity_id,
            analysis_id=request.analysis_id,
            recommendation_id=request.recommendation_id,
            payload_json=to_json_text(request.payload),
            created_at=_parse_dt(request.created_at),
        )
        self.db.add(row)
        self.db.flush()
        return row

    def get_request(self, request_id: str) -> ExecutionRequestORM | None:
        return self.db.get(ExecutionRequestORM, request_id)

    def get_request_by_idempotency_key(self, idempotency_key: str) -> ExecutionRequestORM | None:
        return self.db.query(ExecutionRequestORM).filter(ExecutionRequestORM.idempotency_key == idempotency_key).first()

    def update_request_status(self, request_id: str, status: str) -> ExecutionRequestORM | None:
        row = self.get_request(request_id)
        if row is None:
            return None
        row.status = status
        self.db.flush()
        return row

    def attach_request_targets(
        self,
        request_id: str,
        *,
        entity_type: str | None = None,
        entity_id: str | None = None,
        analysis_id: str | None = None,
        recommendation_id: str | None = None,
    ) -> ExecutionRequestORM | None:
        row = self.get_request(request_id)
        if row is None:
            return None
        if entity_type is not None:
            row.entity_type = entity_type
        if entity_id is not None:
            row.entity_id = entity_id
        if analysis_id is not None:
            row.analysis_id = analysis_id
        if recommendation_id is not None:
            row.recommendation_id = recommendation_id
        self.db.flush()
        return row

    def get_receipt(self, receipt_id: str) -> ExecutionReceiptORM | None:
        return self.db.get(ExecutionReceiptORM, receipt_id)

    def create_receipt(self, receipt: ExecutionReceipt) -> ExecutionReceiptORM:
        row = ExecutionReceiptORM(
            id=receipt.id,
            request_id=receipt.request_id,
            action_id=receipt.action_id,
            status=receipt.status,
            result_ref=receipt.result_ref,
            external_reference=receipt.external_reference,
            detail_json=to_json_text(receipt.detail),
            error=receipt.error,
            created_at=_parse_dt(receipt.created_at),
        )
        self.db.add(row)
        self.db.flush()
        return row

    def update_receipt(
        self,
        receipt_id: str,
        *,
        status: str,
        result_ref: str | None = None,
        external_reference: str | None = None,
        detail: dict | None = None,
        error: str | None = None,
    ) -> ExecutionReceiptORM | None:
        row = self.db.get(ExecutionReceiptORM, receipt_id)
        if row is None:
            return None
        row.status = status
        row.result_ref = result_ref
        row.external_reference = external_reference
        row.detail_json = to_json_text(detail or {})
        row.error = error
        self.db.flush()
        return row

    def list_receipts_for_request(self, request_id: str) -> list[ExecutionReceiptORM]:
        return (
            self.db.query(ExecutionReceiptORM)
            .filter(ExecutionReceiptORM.request_id == request_id)
            .order_by(ExecutionReceiptORM.created_at.asc())
            .all()
        )

    def latest_receipt_for_request(self, request_id: str) -> ExecutionReceiptORM | None:
        return (
            self.db.query(ExecutionReceiptORM)
            .filter(ExecutionReceiptORM.request_id == request_id)
            .order_by(ExecutionReceiptORM.created_at.desc())
            .first()
        )

    def create_progress(self, progress: ExecutionProgressRecord) -> ExecutionProgressRecordORM:
        row = ExecutionProgressRecordORM(
            id=progress.id,
            request_id=progress.request_id,
            progress_state=progress.progress_state,
            progress_message=progress.progress_message,
            heartbeat_at=_parse_dt(progress.heartbeat_at),
            created_at=_parse_dt(progress.created_at),
        )
        self.db.add(row)
        self.db.flush()
        return row

    def latest_progress_for_request(self, request_id: str) -> ExecutionProgressRecordORM | None:
        return (
            self.db.query(ExecutionProgressRecordORM)
            .filter(ExecutionProgressRecordORM.request_id == request_id)
            .order_by(ExecutionProgressRecordORM.created_at.desc())
            .first()
        )

    def list_progress_for_request(self, request_id: str) -> list[ExecutionProgressRecordORM]:
        return (
            self.db.query(ExecutionProgressRecordORM)
            .filter(ExecutionProgressRecordORM.request_id == request_id)
            .order_by(ExecutionProgressRecordORM.created_at.asc())
            .all()
        )

    def to_request_model(self, row: ExecutionRequestORM) -> ExecutionRequest:
        return ExecutionRequest(
            id=row.id,
            action_id=row.action_id,
            family=row.family,
            side_effect_level=row.side_effect_level,
            status=row.status,
            actor=row.actor,
            context=row.context,
            reason=row.reason,
            idempotency_key=row.idempotency_key,
            entity_type=row.entity_type,
            entity_id=row.entity_id,
            analysis_id=row.analysis_id,
            recommendation_id=row.recommendation_id,
            payload=from_json_text(row.payload_json, {}),
            created_at=row.created_at.isoformat(),
        )

    def to_receipt_model(self, row: ExecutionReceiptORM) -> ExecutionReceipt:
        return ExecutionReceipt(
            id=row.id,
            request_id=row.request_id,
            action_id=row.action_id,
            status=row.status,
            result_ref=row.result_ref,
            external_reference=row.external_reference,
            detail=from_json_text(row.detail_json, {}),
            error=row.error,
            created_at=row.created_at.isoformat(),
        )

    def to_progress_model(self, row: ExecutionProgressRecordORM) -> ExecutionProgressRecord:
        return ExecutionProgressRecord(
            id=row.id,
            request_id=row.request_id,
            progress_state=row.progress_state,
            progress_message=row.progress_message,
            heartbeat_at=row.heartbeat_at.isoformat(),
            created_at=row.created_at.isoformat(),
        )
