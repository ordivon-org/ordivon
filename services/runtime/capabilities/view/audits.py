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

        workflow_name = self._as_string(getattr(row, "event_type", None), default="unknown")
        stage = self._as_string(getattr(row, "entity_type", None), default="unknown")
        decision = self._as_string(model_payload.get("decision"), default="logged")
        context_summary = self._as_string(model_payload.get("summary"), default=workflow_name)
        report_path = model_payload.get("report_path")
        if report_path is not None and not isinstance(report_path, str):
            report_path = str(report_path)

        return AuditEventResult(
            event_id=self._as_string(getattr(row, "id", None), default="unknown"),
            workflow_name=workflow_name,
            stage=stage,
            decision=decision,
            subject_id=self._optional_string(getattr(row, "entity_id", None)),
            status="persisted",
            context_summary=context_summary,
            details=model_payload,
            report_path=report_path,
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
