from __future__ import annotations

from typing import TYPE_CHECKING, Any

from capabilities.boundary import ActionContext, require_action_context
from capabilities.contracts import UsageSyncResult, ValidationSummaryResult
from domains.journal.issue_models import Issue
from execution.adapters import build_default_execution_adapter_registry
from state.usage.models import UsageSnapshot

if TYPE_CHECKING:
    from domains.journal.issue_repository import IssueRepository
    from domains.journal.issue_service import IssueService
    from state.usage.service import UsageService


class ValidationCapability:
    """Diagnostic capability for validation summaries plus bounded issue intake."""

    abstraction_type = "diagnostic"

    def get_summary(self, usage_service: UsageService, issue_repo: IssueRepository) -> ValidationSummaryResult:
        metrics = usage_service.get_aggregate_metrics(issue_repo)
        period_id = self._build_period_id(usage_service)

        return ValidationSummaryResult(
            period_id=period_id,
            days_active=metrics.get("days_used", 0),
            total_analyses=metrics.get("analysis_count", 0),
            total_recommendations=metrics.get("recommendations_count", 0),
            open_critical_issues=metrics.get("open_p0_count", 0) + metrics.get("open_p1_count", 0),
            system_go_no_go=metrics.get("go_no_go"),
            metrics=metrics,
            metadata={"key_lessons": metrics.get("key_lessons", []), "contract_type": "diagnostic"},
        )

    def sync_usage(self, usage_service: UsageService, action_context: ActionContext | None) -> UsageSyncResult:
        context = require_action_context("usage sync", action_context)
        snapshot = UsageSnapshot(
            metadata={
                "note": "manual_sync",
                "actor": context.actor,
                "context": context.context,
                "reason": context.reason,
                "idempotency_key": context.idempotency_key,
            }
        )
        row = usage_service.create(snapshot)
        return UsageSyncResult(
            snapshot_id=row.id,
            created_at=str(row.created_at),
        )

    def report_issue(
        self,
        issue_service: IssueService,
        severity: str,
        area: str,
        description: str,
        action_context: ActionContext | None,
    ) -> dict[str, str]:
        context = require_action_context("validation issue report", action_context)
        issue = Issue(
            title=f"{severity.upper()} {area}",
            summary=description,
            severity=severity.lower(),
            category=area,
            detail={
                "description": description,
                "actor": context.actor,
                "context": context.context,
                "reason": context.reason,
                "idempotency_key": context.idempotency_key,
            },
        )
        result = (
            build_default_execution_adapter_registry()
            .resolve("validation", issue_service.repository.db)
            .report_issue(
                service=issue_service,
                issue=issue,
                action_context=context,
            )
        )

        return {
            "issue_id": result.issue_row.id,
            "execution_request_id": result.execution_request_id,
            "execution_receipt_id": result.execution_receipt_id,
        }

    def _decode_metadata(self, metadata_json: str) -> dict[str, Any]:
        from shared.utils.serialization import from_json_text

        return from_json_text(metadata_json, {})

    def _build_period_id(self, usage_service: UsageService, limit: int = 7) -> str | None:
        usage_rows = usage_service.list_recent(limit=limit)
        if not usage_rows:
            return None

        snapshot_dates = [
            row.snapshot_date.date().isoformat() for row in usage_rows if getattr(row, "snapshot_date", None)
        ]
        if not snapshot_dates:
            return None

        newest = max(snapshot_dates)
        oldest = min(snapshot_dates)
        return newest if newest == oldest else f"{oldest}..{newest}"
