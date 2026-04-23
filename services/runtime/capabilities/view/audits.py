from __future__ import annotations

from dataclasses import asdict
from typing import Any

from capabilities.contracts import AuditEventResult
from governance.audit.builders import structured_payload_or_legacy
from governance.audit.service import AuditService


class AuditCapability:
    """View capability for persisted audit event listings."""

    abstraction_type = "view"

    def list_recent(self, service: AuditService, limit: int = 10) -> list[dict[str, Any]]:
        rows = service.list_recent(limit=limit)
        return [asdict(self._row_to_response(row)) for row in rows]

    def _row_to_response(self, row: Any) -> AuditEventResult:
        model_payload = {}
        if hasattr(row, "payload_json"):
            from shared.utils.serialization import from_json_text

            model_payload = from_json_text(row.payload_json, {})
        structured = structured_payload_or_legacy(
            event_type=self._as_string(getattr(row, "event_type", None), default="unknown"),
            entity_type=self._optional_string(getattr(row, "entity_type", None)),
            entity_id=self._optional_string(getattr(row, "entity_id", None)),
            payload_json=getattr(row, "payload_json", ""),
            parsed_payload=model_payload,
        )

        return AuditEventResult(
            event_id=self._as_string(getattr(row, "id", None), default="unknown"),
            workflow_name=structured.workflow_name,
            stage=structured.stage,
            decision=structured.decision,
            subject_id=structured.subject_id,
            status=structured.status,
            context_summary=structured.context_summary,
            details=structured.details,
            report_path=structured.report_path,
            created_at=str(row.created_at),
        )

    def _as_string(self, value: Any, default: str) -> str:
        if isinstance(value, str):
            return value
        if value is None:
            return default
        return str(value)

    def _optional_string(self, value: Any) -> str | None:
        if value is None:
            return None
        if isinstance(value, str):
            return value
        return str(value)
