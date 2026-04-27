from __future__ import annotations

from dataclasses import dataclass

from capabilities.boundary import ActionContext
from domains.execution_records.repository import ExecutionRecordRepository
from domains.execution_records.service import ExecutionRecordService
from domains.journal.service import ReviewService
from governance.approval import ApprovalRequiredError, HumanApprovalGate
from governance.approval_repository import ApprovalRepository
from governance.audit.auditor import RiskAuditor
from shared.errors.domain import DomainNotFound, InvalidStateTransition


@dataclass(slots=True)
class ReviewExecutionResult:
    review_row: object
    lesson_rows: list[object]
    knowledge_feedback: object | None
    execution_request_id: str
    execution_receipt_id: str


class ReviewExecutionFailure(Exception):
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


class ReviewExecutionAdapter:
    """Family execution facade for review actions.

    Responsibilities:
    - request / receipt lifecycle
    - family-level execution semantics
    - audit refs attachment

    Non-responsibilities:
    - review domain transition rules
    - review state-machine semantics
    """

    family_name = "review"

    def __init__(self, db, auditor: RiskAuditor | None = None) -> None:
        self.db = db
        self.execution_service = ExecutionRecordService(ExecutionRecordRepository(db))
        self.auditor = auditor or RiskAuditor()
        self.approval_gate = HumanApprovalGate(ApprovalRepository(db))

    def submit(
        self,
        *,
        service: ReviewService,
        review,
        action_context: ActionContext,
    ) -> ReviewExecutionResult:
        request_row = self.execution_service.start_request(
            action_id="review_submit",
            action_context=action_context,
            entity_type="review",
            entity_id=review.id,
            payload={
                "review_id": review.id,
                "recommendation_id": review.recommendation_id,
                "review_type": review.review_type,
                "expected_outcome": review.expected_outcome,
                "action_context": ExecutionRecordService.action_context_payload(action_context),
            },
        )
        self.execution_service.record_progress(
            request_row.id,
            progress_state="started",
            progress_message="review submission started",
        )
        try:
            review_row = service.create_with_options(
                review,
                emit_review_submitted_audit=False,
            )
        except Exception as exc:
            receipt_row = self.execution_service.record_failure(
                request_row.id,
                error=str(exc),
                detail={
                    "review_id": review.id,
                    "recommendation_id": review.recommendation_id,
                    "action_context": ExecutionRecordService.action_context_payload(action_context),
                },
            )
            self.execution_service.record_progress(
                request_row.id,
                progress_state="failed",
                progress_message=str(exc),
            )
            self.auditor.record_event(
                "review_submitted_failed",
                {
                    "error": str(exc),
                    "execution_request_id": request_row.id,
                    "execution_receipt_id": receipt_row.id,
                    "action_context": ExecutionRecordService.action_context_payload(action_context),
                },
                entity_type="review",
                entity_id=review.id,
                review_id=review.id,
                recommendation_id=review.recommendation_id,
                db=self.db,
            )
            status_code = 500
            if isinstance(exc, DomainNotFound):
                status_code = 404
            raise ReviewExecutionFailure(
                message=str(exc),
                execution_request_id=request_row.id,
                execution_receipt_id=receipt_row.id,
                status_code=status_code,
            ) from exc

        self.execution_service.attach_request_targets(
            request_row.id,
            entity_type="review",
            entity_id=review_row.id,
            recommendation_id=review_row.recommendation_id,
        )
        receipt_row = self.execution_service.record_success(
            request_row.id,
            result_ref=review_row.id,
            detail={
                "review_id": review_row.id,
                "recommendation_id": review_row.recommendation_id,
                "review_type": review_row.review_type,
                "action_context": ExecutionRecordService.action_context_payload(action_context),
            },
        )
        service.review_repository.attach_submit_execution_refs(
            review_row.id,
            request_id=request_row.id,
            receipt_id=receipt_row.id,
        )
        self.auditor.record_event(
            "review_submitted",
            {
                "expected_outcome": review.expected_outcome,
                "actual_outcome": review.observed_outcome,
                "lessons_count": len(review.lessons) if hasattr(review, "lessons") else 0,
                "execution_request_id": request_row.id,
                "execution_receipt_id": receipt_row.id,
                "action_context": ExecutionRecordService.action_context_payload(action_context),
            },
            entity_type="review",
            entity_id=review_row.id,
            review_id=review_row.id,
            recommendation_id=review_row.recommendation_id,
            db=self.db,
        )
        self.execution_service.record_progress(
            request_row.id,
            progress_state="completed",
            progress_message="review submission completed",
        )
        return ReviewExecutionResult(
            review_row=review_row,
            lesson_rows=[],
            knowledge_feedback=None,
            execution_request_id=request_row.id,
            execution_receipt_id=receipt_row.id,
        )

    def complete(
        self,
        *,
        service: ReviewService,
        review_id: str,
        observed_outcome: str,
        verdict,
        variance_summary: str | None,
        cause_tags: list[str],
        lessons: list[str],
        followup_actions: list[str],
        action_context: ActionContext,
        approval_id: str | None = None,
        require_approval: bool = False,
        lesson_types: list[str] | None = None,
    ) -> ReviewExecutionResult:
        self.approval_gate.ensure_approved(
            action_key="review.complete",
            entity_type="review",
            entity_id=review_id,
            approval_id=approval_id,
            require_approval=require_approval,
        )
        request_row = self.execution_service.start_request(
            action_id="review_complete",
            action_context=action_context,
            entity_type="review",
            entity_id=review_id,
            payload={
                "review_id": review_id,
                "observed_outcome": observed_outcome,
                "verdict": verdict.value if hasattr(verdict, "value") else str(verdict),
                "variance_summary": variance_summary,
                "cause_tags": list(cause_tags),
                "lessons": list(lessons),
                "followup_actions": list(followup_actions),
                "approval_id": approval_id,
                "require_approval": require_approval,
                "action_context": ExecutionRecordService.action_context_payload(action_context),
            },
        )
        self.execution_service.record_progress(
            request_row.id,
            progress_state="started",
            progress_message="review completion started",
        )
        try:
            review_row, lesson_rows, knowledge_feedback = service.complete_review(
                review_id=review_id,
                observed_outcome=observed_outcome,
                verdict=verdict,
                variance_summary=variance_summary,
                cause_tags=cause_tags,
                lessons=lessons,
                followup_actions=followup_actions,
                emit_review_completed_audit=False,
                lesson_types=lesson_types,
            )
        except ApprovalRequiredError:
            raise
        except Exception as exc:
            receipt_row = self.execution_service.record_failure(
                request_row.id,
                error=str(exc),
                detail={
                    "review_id": review_id,
                    "verdict": verdict.value if hasattr(verdict, "value") else str(verdict),
                    "action_context": ExecutionRecordService.action_context_payload(action_context),
                },
            )
            self.execution_service.record_progress(
                request_row.id,
                progress_state="failed",
                progress_message=str(exc),
            )
            self.auditor.record_event(
                "review_completed_failed",
                {
                    "error": str(exc),
                    "attempted_verdict": verdict.value if hasattr(verdict, "value") else str(verdict),
                    "execution_request_id": request_row.id,
                    "execution_receipt_id": receipt_row.id,
                    "action_context": ExecutionRecordService.action_context_payload(action_context),
                },
                entity_type="review",
                entity_id=review_id,
                review_id=review_id,
                db=self.db,
            )
            status_code = 500
            if isinstance(exc, InvalidStateTransition):
                status_code = 409
            elif isinstance(exc, DomainNotFound):
                status_code = 404
            raise ReviewExecutionFailure(
                message=str(exc),
                execution_request_id=request_row.id,
                execution_receipt_id=receipt_row.id,
                status_code=status_code,
            ) from exc

        self.execution_service.attach_request_targets(
            request_row.id,
            entity_type="review",
            entity_id=review_row.id,
            recommendation_id=review_row.recommendation_id,
        )
        receipt_row = self.execution_service.record_success(
            request_row.id,
            result_ref=review_row.id,
            detail={
                "review_id": review_row.id,
                "recommendation_id": review_row.recommendation_id,
                "verdict": verdict.value if hasattr(verdict, "value") else str(verdict),
                "lessons_created": len(lesson_rows),
                "knowledge_feedback_prepared": knowledge_feedback is not None,
                "action_context": ExecutionRecordService.action_context_payload(action_context),
            },
        )
        service.review_repository.attach_complete_execution_refs(
            review_row.id,
            request_id=request_row.id,
            receipt_id=receipt_row.id,
        )
        self.auditor.record_event(
            "review_completed",
            {
                "verdict": verdict.value if hasattr(verdict, "value") else str(verdict),
                "observed_outcome": observed_outcome,
                "lessons_count": len(lessons),
                "followup_actions_count": len(followup_actions),
                "execution_request_id": request_row.id,
                "execution_receipt_id": receipt_row.id,
                "action_context": ExecutionRecordService.action_context_payload(action_context),
            },
            entity_type="review",
            entity_id=review_row.id,
            review_id=review_row.id,
            recommendation_id=review_row.recommendation_id,
            db=self.db,
        )
        self.execution_service.record_progress(
            request_row.id,
            progress_state="completed",
            progress_message="review completion completed",
        )
        return ReviewExecutionResult(
            review_row=review_row,
            lesson_rows=lesson_rows,
            knowledge_feedback=knowledge_feedback,
            execution_request_id=request_row.id,
            execution_receipt_id=receipt_row.id,
        )
