from __future__ import annotations

from dataclasses import asdict
from typing import Any

from capabilities.boundary import ActionContext
from domains.execution_records.models import ExecutionProgressRecord, ExecutionReceipt, ExecutionRequest
from domains.execution_records.repository import ExecutionRecordRepository
from execution.catalog import get_execution_action


class ExecutionRecordService:
    def __init__(self, repository: ExecutionRecordRepository) -> None:
        self.repository = repository

    def start_request(
        self,
        *,
        action_id: str,
        action_context: ActionContext,
        payload: dict[str, Any],
        entity_type: str | None = None,
        entity_id: str | None = None,
        analysis_id: str | None = None,
        recommendation_id: str | None = None,
    ):
        existing = self.repository.get_request_by_idempotency_key(action_context.idempotency_key)
        if existing is not None:
            return existing

        spec = get_execution_action(action_id)
        request = ExecutionRequest(
            action_id=spec.action_id,
            family=spec.family,
            side_effect_level=spec.side_effect_level,
            status="pending",
            actor=action_context.actor,
            context=action_context.context,
            reason=action_context.reason,
            idempotency_key=action_context.idempotency_key,
            entity_type=entity_type,
            entity_id=entity_id,
            analysis_id=analysis_id,
            recommendation_id=recommendation_id,
            payload=payload,
        )
        return self.repository.create_request(request)

    def record_success(
        self,
        request_id: str,
        *,
        result_ref: str | None = None,
        external_reference: str | None = None,
        detail: dict[str, Any] | None = None,
    ):
        request = self.repository.get_request(request_id)
        if request is None:
            raise ValueError(f"Unknown execution request: {request_id}")
        self.repository.update_request_status(request_id, "succeeded")
        latest = self.repository.latest_receipt_for_request(request_id)
        if latest is not None:
            return self.repository.update_receipt(
                latest.id,
                status="succeeded",
                result_ref=result_ref,
                external_reference=external_reference,
                detail=detail or {},
                error=None,
            )
        receipt = ExecutionReceipt(
            request_id=request_id,
            action_id=request.action_id,
            status="succeeded",
            result_ref=result_ref,
            external_reference=external_reference,
            detail=detail or {},
        )
        return self.repository.create_receipt(receipt)

    def record_failure(
        self,
        request_id: str,
        *,
        error: str,
        detail: dict[str, Any] | None = None,
    ):
        request = self.repository.get_request(request_id)
        if request is None:
            raise ValueError(f"Unknown execution request: {request_id}")
        self.repository.update_request_status(request_id, "failed")
        latest = self.repository.latest_receipt_for_request(request_id)
        if latest is not None:
            return self.repository.update_receipt(
                latest.id,
                status="failed",
                detail=detail or {},
                error=error,
            )
        receipt = ExecutionReceipt(
            request_id=request_id,
            action_id=request.action_id,
            status="failed",
            detail=detail or {},
            error=error,
        )
        return self.repository.create_receipt(receipt)

    def attach_request_targets(
        self,
        request_id: str,
        *,
        entity_type: str | None = None,
        entity_id: str | None = None,
        analysis_id: str | None = None,
        recommendation_id: str | None = None,
    ):
        row = self.repository.attach_request_targets(
            request_id,
            entity_type=entity_type,
            entity_id=entity_id,
            analysis_id=analysis_id,
            recommendation_id=recommendation_id,
        )
        if row is None:
            raise ValueError(f"Unknown execution request: {request_id}")
        return row

    def record_progress(
        self,
        request_id: str,
        *,
        progress_state: str,
        progress_message: str = "",
    ):
        request = self.repository.get_request(request_id)
        if request is None:
            raise ValueError(f"Unknown execution request: {request_id}")
        return self.repository.create_progress(
            ExecutionProgressRecord(
                request_id=request_id,
                progress_state=progress_state,
                progress_message=progress_message,
            )
        )

    def record_heartbeat(
        self,
        request_id: str,
        *,
        progress_message: str = "",
    ):
        return self.record_progress(
            request_id,
            progress_state="heartbeat",
            progress_message=progress_message,
        )

    @staticmethod
    def action_context_payload(action_context: ActionContext) -> dict[str, Any]:
        return asdict(action_context)
