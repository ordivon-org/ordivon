from __future__ import annotations

from dataclasses import dataclass

from capabilities.boundary import ActionContext
from domains.execution_records.repository import ExecutionRecordRepository
from domains.execution_records.service import ExecutionRecordService
from domains.journal.issue_service import IssueService
from governance_engine.audit.auditor import RiskAuditor


@dataclass(slots=True)
class ValidationExecutionResult:
    issue_row: object
    execution_request_id: str
    execution_receipt_id: str


class ValidationExecutionFailure(Exception):
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


class ValidationExecutionAdapter:
    """Family execution facade for validation actions."""

    family_name = "validation"

    def __init__(self, db, auditor: RiskAuditor | None = None) -> None:
        self.db = db
        self.execution_service = ExecutionRecordService(ExecutionRecordRepository(db))
        self.auditor = auditor or RiskAuditor()

    def report_issue(
        self,
        *,
        service: IssueService,
        issue,
        action_context: ActionContext,
    ) -> ValidationExecutionResult:
        request_row = self.execution_service.start_request(
            action_id="validation_issue_report",
            action_context=action_context,
            entity_type="issue",
            entity_id=issue.id,
            payload={
                "issue_id": issue.id,
                "severity": issue.severity,
                "category": issue.category,
                "summary": issue.summary,
                "action_context": ExecutionRecordService.action_context_payload(action_context),
            },
        )
        self.execution_service.record_progress(
            request_row.id,
            progress_state="started",
            progress_message="validation issue report started",
        )
        try:
            issue_row = service.create_with_options(
                issue,
                emit_validation_issue_audit=False,
            )
        except Exception as exc:
            receipt_row = self.execution_service.record_failure(
                request_row.id,
                error=str(exc),
                detail={
                    "issue_id": issue.id,
                    "severity": issue.severity,
                    "category": issue.category,
                    "action_context": ExecutionRecordService.action_context_payload(action_context),
                },
            )
            self.execution_service.record_progress(
                request_row.id,
                progress_state="failed",
                progress_message=str(exc),
            )
            self.auditor.record_event(
                "validation_issue_report_failed",
                {
                    "error": str(exc),
                    "execution_request_id": request_row.id,
                    "execution_receipt_id": receipt_row.id,
                    "action_context": ExecutionRecordService.action_context_payload(action_context),
                },
                entity_type="issue",
                entity_id=issue.id,
                db=self.db,
            )
            raise ValidationExecutionFailure(
                message=str(exc),
                execution_request_id=request_row.id,
                execution_receipt_id=receipt_row.id,
                status_code=500,
            ) from exc

        self.execution_service.attach_request_targets(
            request_row.id,
            entity_type="issue",
            entity_id=issue_row.id,
        )
        receipt_row = self.execution_service.record_success(
            request_row.id,
            result_ref=issue_row.id,
            detail={
                "issue_id": issue_row.id,
                "severity": issue_row.severity,
                "category": issue_row.category,
                "action_context": ExecutionRecordService.action_context_payload(action_context),
            },
        )
        self.auditor.record_event(
            "validation_issue_reported",
            {
                "severity": issue.severity,
                "area": issue.category,
                "description": issue.summary,
                "execution_request_id": request_row.id,
                "execution_receipt_id": receipt_row.id,
                "action_context": ExecutionRecordService.action_context_payload(action_context),
            },
            entity_type="issue",
            entity_id=issue_row.id,
            db=self.db,
        )
        self.execution_service.record_progress(
            request_row.id,
            progress_state="completed",
            progress_message="validation issue report completed",
        )
        return ValidationExecutionResult(
            issue_row=issue_row,
            execution_request_id=request_row.id,
            execution_receipt_id=receipt_row.id,
        )
