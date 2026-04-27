from __future__ import annotations

from typing import Any

from governance.audit.contracts import AUDIT_SCHEMA_VERSION, StructuredAuditPayload
from governance.audit.models import AuditEvent


def normalize_audit_event(event: AuditEvent) -> AuditEvent:
    payload = event.payload if isinstance(event.payload, dict) else {"value": event.payload}
    if payload.get("schema_version") == AUDIT_SCHEMA_VERSION and "details" in payload:
        return event

    structured = StructuredAuditPayload(
        workflow_name=_as_string(payload.get("workflow_name"), default=event.event_type or "unknown"),
        stage=_as_string(payload.get("stage"), default=event.entity_type or "unknown"),
        decision=_as_string(payload.get("decision"), default=_default_decision(event.event_type)),
        status=_as_string(payload.get("status"), default=_default_status(event.event_type, payload)),
        context_summary=_as_string(
            payload.get("context_summary") or payload.get("summary"),
            default=_default_context_summary(event.event_type),
        ),
        subject_id=_optional_string(payload.get("subject_id") or event.entity_id),
        report_path=_optional_string(payload.get("report_path")),
        details=payload,
    )
    event.payload = structured.to_payload()
    return event


def structured_payload_or_legacy(
    event_type: str, entity_type: str | None, entity_id: str | None, payload_json: str, parsed_payload: Any
) -> StructuredAuditPayload:
    if isinstance(parsed_payload, dict) and parsed_payload.get("schema_version") == AUDIT_SCHEMA_VERSION:
        details = parsed_payload.get("details", {})
        if not isinstance(details, dict):
            details = {"value": details}
        return StructuredAuditPayload(
            workflow_name=_as_string(parsed_payload.get("workflow_name"), default=event_type or "unknown"),
            stage=_as_string(parsed_payload.get("stage"), default=entity_type or "unknown"),
            decision=_as_string(parsed_payload.get("decision"), default="legacy_unstructured"),
            status=_as_string(parsed_payload.get("status"), default="persisted"),
            context_summary=_as_string(
                parsed_payload.get("context_summary"),
                default=_default_context_summary(event_type),
            ),
            subject_id=_optional_string(parsed_payload.get("subject_id") or entity_id),
            report_path=_optional_string(parsed_payload.get("report_path")),
            details=details,
        )

    details = parsed_payload if isinstance(parsed_payload, dict) else {"legacy_payload": parsed_payload}
    return StructuredAuditPayload(
        workflow_name=_as_string(event_type, default="unknown"),
        stage=_as_string(entity_type, default="unknown"),
        decision="legacy_unstructured",
        status="legacy_unstructured",
        context_summary="Legacy audit record without structured envelope.",
        subject_id=_optional_string(entity_id),
        report_path=None,
        details=details,
    )


def _default_decision(event_type: str) -> str:
    if event_type.endswith("_failed"):
        return "failed"
    return "logged"


def _default_status(event_type: str, payload: dict[str, Any]) -> str:
    if isinstance(payload.get("error"), str) and payload["error"]:
        return "failed"
    if event_type.endswith("_failed"):
        return "failed"
    return "persisted"


def _default_context_summary(event_type: str) -> str:
    label = (event_type or "audit_event").replace("_", " ").strip()
    if not label:
        return "Audit event recorded."
    return f"{label.capitalize()}."


def _as_string(value: Any, default: str) -> str:
    if isinstance(value, str) and value:
        return value
    if value is None:
        return default
    return str(value)


def _optional_string(value: Any) -> str | None:
    if value is None:
        return None
    if isinstance(value, str):
        return value
    return str(value)
