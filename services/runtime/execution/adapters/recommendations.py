from __future__ import annotations

from dataclasses import dataclass

from capabilities.boundary import ActionContext
from domains.execution_records.repository import ExecutionRecordRepository
from domains.execution_records.service import ExecutionRecordService
from domains.strategy.models import Recommendation
from domains.strategy.service import RecommendationService
from governance_engine.audit.auditor import RiskAuditor
from shared.enums.domain import RecommendationStatus
from shared.errors.domain import DomainNotFound, InvalidStateTransition


@dataclass(slots=True)
class RecommendationExecutionResult:
    recommendation: Recommendation
    execution_request_id: str
    execution_receipt_id: str


class RecommendationExecutionFailure(Exception):
    def __init__(
        self,
        *,
        message: str,
        execution_request_id: str,
        execution_receipt_id: str,
        status_code: int,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.execution_request_id = execution_request_id
        self.execution_receipt_id = execution_receipt_id
        self.status_code = status_code


class RecommendationExecutionAdapter:
    """Family execution facade for recommendation actions.

    Responsibilities:
    - request / receipt lifecycle
    - family-level execution semantics
    - audit refs attachment

    Non-responsibilities:
    - recommendation domain transition rules
    - recommendation state-machine semantics
    """

    family_name = "recommendation"

    def __init__(self, db, auditor: RiskAuditor | None = None) -> None:
        self.db = db
        self.execution_service = ExecutionRecordService(ExecutionRecordRepository(db))
        self.auditor = auditor or RiskAuditor()

    def generate(
        self,
        *,
        service: RecommendationService,
        action_context: ActionContext,
        recommendation: Recommendation,
        analysis_id: str | None,
        symbol: str | None,
        governance_decision: str | None,
        governance_source: str | None,
    ) -> RecommendationExecutionResult:
        request_row = self.execution_service.start_request(
            action_id="recommendation_generate",
            action_context=action_context,
            entity_type="analysis",
            entity_id=analysis_id,
            analysis_id=analysis_id,
            payload={
                "analysis_id": analysis_id,
                "symbol": symbol,
                "governance_decision": governance_decision,
                "governance_source": governance_source,
            },
        )
        self.execution_service.record_progress(
            request_row.id,
            progress_state="started",
            progress_message="recommendation generation started",
        )
        try:
            row = service.create(recommendation)
            self.execution_service.attach_request_targets(
                request_row.id,
                entity_type="recommendation",
                entity_id=row.id,
                analysis_id=analysis_id,
                recommendation_id=row.id,
            )
            receipt_row = self.execution_service.record_success(
                request_row.id,
                result_ref=row.id,
                detail={
                    "analysis_id": analysis_id,
                    "recommendation_id": row.id,
                    "governance_decision": governance_decision,
                    "governance_source": governance_source,
                    "action_context": ExecutionRecordService.action_context_payload(action_context),
                },
            )
            self.execution_service.record_progress(
                request_row.id,
                progress_state="completed",
                progress_message="recommendation generation completed",
            )
            return RecommendationExecutionResult(
                recommendation=service.repository.to_model(row),
                execution_request_id=request_row.id,
                execution_receipt_id=receipt_row.id,
            )
        except Exception as exc:
            receipt_row = self.execution_service.record_failure(
                request_row.id,
                error=str(exc),
                detail={
                    "analysis_id": analysis_id,
                    "governance_decision": governance_decision,
                    "governance_source": governance_source,
                    "action_context": ExecutionRecordService.action_context_payload(action_context),
                },
            )
            self.execution_service.record_progress(
                request_row.id,
                progress_state="failed",
                progress_message=str(exc),
            )
            raise RecommendationExecutionFailure(
                message=str(exc),
                execution_request_id=request_row.id,
                execution_receipt_id=receipt_row.id,
                status_code=500,
            ) from exc

    def update_status(
        self,
        *,
        service: RecommendationService,
        recommendation_id: str,
        target_status: RecommendationStatus,
        action_context: ActionContext,
    ) -> RecommendationExecutionResult:
        request_row = self.execution_service.start_request(
            action_id="recommendation_status_update",
            action_context=action_context,
            entity_type="recommendation",
            entity_id=recommendation_id,
            recommendation_id=recommendation_id,
            payload={
                "recommendation_id": recommendation_id,
                "target_status": target_status.value,
                "action_context": ExecutionRecordService.action_context_payload(action_context),
            },
        )
        self.execution_service.record_progress(
            request_row.id,
            progress_state="started",
            progress_message="recommendation status update started",
        )
        try:
            recommendation = service.transition(
                recommendation_id=recommendation_id,
                target_status=target_status,
                emit_recommendation_status_audit=False,
            )
            receipt_row = self.execution_service.record_success(
                request_row.id,
                result_ref=recommendation.id,
                detail={
                    "recommendation_id": recommendation.id,
                    "target_status": target_status.value,
                    "action_context": ExecutionRecordService.action_context_payload(action_context),
                },
            )
            self.auditor.record_event(
                "recommendation_status_update",
                {
                    "new_status": target_status.value,
                    "execution_request_id": request_row.id,
                    "execution_receipt_id": receipt_row.id,
                    "action_context": ExecutionRecordService.action_context_payload(action_context),
                },
                entity_type="recommendation",
                entity_id=recommendation_id,
                recommendation_id=recommendation_id,
                db=self.db,
            )
            self.execution_service.record_progress(
                request_row.id,
                progress_state="completed",
                progress_message="recommendation status update completed",
            )
            return RecommendationExecutionResult(
                recommendation=recommendation,
                execution_request_id=request_row.id,
                execution_receipt_id=receipt_row.id,
            )
        except Exception as exc:
            receipt_row = self.execution_service.record_failure(
                request_row.id,
                error=str(exc),
                detail={
                    "recommendation_id": recommendation_id,
                    "target_status": target_status.value,
                    "action_context": ExecutionRecordService.action_context_payload(action_context),
                },
            )
            self.auditor.record_event(
                "recommendation_status_update_failed",
                {
                    "attempted_status": target_status.value,
                    "error": str(exc),
                    "execution_request_id": request_row.id,
                    "execution_receipt_id": receipt_row.id,
                    "action_context": ExecutionRecordService.action_context_payload(action_context),
                },
                entity_type="recommendation",
                entity_id=recommendation_id,
                recommendation_id=recommendation_id,
                db=self.db,
            )
            self.execution_service.record_progress(
                request_row.id,
                progress_state="failed",
                progress_message=str(exc),
            )
            status_code = 500
            if isinstance(exc, InvalidStateTransition):
                status_code = 409
            elif isinstance(exc, DomainNotFound):
                status_code = 404
            raise RecommendationExecutionFailure(
                message=str(exc),
                execution_request_id=request_row.id,
                execution_receipt_id=receipt_row.id,
                status_code=status_code,
            ) from exc
