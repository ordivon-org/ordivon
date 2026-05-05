from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


AUDIT_SCHEMA_VERSION = "audit.v1"


@dataclass(frozen=True, slots=True)
class StructuredAuditPayload:
    workflow_name: str
    stage: str
    decision: str
    status: str
    context_summary: str
    subject_id: str | None
    report_path: str | None
    details: dict[str, Any] = field(default_factory=dict)

    def to_payload(self) -> dict[str, Any]:
        payload = {
            "schema_version": AUDIT_SCHEMA_VERSION,
            "workflow_name": self.workflow_name,
            "stage": self.stage,
            "decision": self.decision,
            "status": self.status,
            "context_summary": self.context_summary,
            "subject_id": self.subject_id,
            "report_path": self.report_path,
            "details": self.details,
        }
        # Transitional compatibility: keep detail keys top-level until every
        # downstream reader has switched to `details`.
        payload.update(self.details)
        return payload
