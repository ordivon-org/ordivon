from __future__ import annotations

from dataclasses import asdict
from typing import Any

from capabilities.contracts import AuditEventResult
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
        if not isinstance(model_payload, dict):
            model_payload = {"value": model_payload}

        return AuditEventResult(
            event_id=row.id,
            workflow_name=row.event_type,
            stage=row.entity_type or "unknown",
            decision=model_payload.get("decision", "logged"),
            subject_id=row.entity_id,
            status="persisted",
            context_summary=model_payload.get("summary", row.event_type),
            details=model_payload,
            report_path=model_payload.get("report_path"),
            created_at=str(row.created_at),
        )
