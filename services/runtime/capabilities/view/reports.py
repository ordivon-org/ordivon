from __future__ import annotations

from capabilities.contracts import ReportResult
from domains.research.service import AnalysisService
from shared.utils.serialization import from_json_text


class ReportCapability:
    """View capability for report artifact listings."""

    abstraction_type = "view"

    def list_latest(self, analysis_service: AnalysisService, limit: int = 10) -> list[ReportResult]:
        rows = analysis_service.list_recent(limit=limit)
        return [self._row_to_result(row) for row in rows]

    def _row_to_result(self, row) -> ReportResult:
        sym = row.symbol if hasattr(row, "symbol") else None
        metadata = {}
        metadata_json = getattr(row, "metadata_json", None)
        if isinstance(metadata_json, str):
            metadata = from_json_text(row.metadata_json, {})
        elif isinstance(getattr(row, "metadata", None), dict):
            metadata = row.metadata

        title = getattr(row, "title", None) or getattr(row, "query", None) or f"Analysis report for {sym or 'UNKNOWN'}"
        document_path = metadata.get("document_path")
        status = metadata.get("status")
        resolved_status = status or "generated" if document_path else "not_generated"
        return ReportResult(
            report_id=row.id,
            symbol=sym,
            title=title,
            status=resolved_status,
            report_path=document_path,
            created_at=row.created_at.isoformat() if hasattr(row.created_at, "isoformat") else str(row.created_at),
            metadata={
                "query": getattr(row, "query", None),
                "agent_action_id": metadata.get("agent_action_id"),
            },
        )
