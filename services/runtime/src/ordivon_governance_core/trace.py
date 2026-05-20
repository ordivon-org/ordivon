"""Governance trace — trace_id/span_id model for governance operations."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone


def new_trace_id() -> str:
    """Generate a governance trace identifier."""
    return f"trace-{uuid.uuid4().hex[:12]}"


def new_span_id() -> str:
    """Generate a span identifier within a trace."""
    return f"span-{uuid.uuid4().hex[:8]}"


def new_run_id() -> str:
    """Generate a tool execution run identifier."""
    return uuid.uuid4().hex[:8]


def new_evidence_id() -> str:
    """Generate an evidence record identifier."""
    return f"ev-{uuid.uuid4().hex[:8]}"


class GovernanceTrace:
    """A trace of a governance operation, composed of spans."""

    def __init__(self, trace_id: str = "", operation: str = ""):
        self.trace_id = trace_id or new_trace_id()
        self.operation = operation
        self.started_at = datetime.now(timezone.utc).isoformat()
        self.spans: list[dict] = []

    def add_span(
        self,
        tool: str,
        status: str,
        input_refs: list[str] = None,
        output_refs: list[str] = None,
        evidence_refs: list[str] = None,
        parent_span_id: str = "",
        duration_ms: int = 0,
    ) -> str:
        span_id = new_span_id()
        self.spans.append({
            "span_id": span_id,
            "trace_id": self.trace_id,
            "parent_span_id": parent_span_id,
            "tool": tool,
            "status": status,
            "input_refs": input_refs or [],
            "output_refs": output_refs or [],
            "evidence_refs": evidence_refs or [],
            "duration_ms": duration_ms,
            "ended_at": datetime.now(timezone.utc).isoformat(),
        })
        return span_id

    def to_dict(self) -> dict:
        return {
            "trace_id": self.trace_id,
            "operation": self.operation,
            "started_at": self.started_at,
            "span_count": len(self.spans),
            "spans": self.spans,
        }
