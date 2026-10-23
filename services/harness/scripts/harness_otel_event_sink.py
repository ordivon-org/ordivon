from __future__ import annotations

from dataclasses import dataclass

from opentelemetry import trace
from opentelemetry.trace import Span, Tracer

from ordivon_harness.ordivon.events import HarnessRunEvent

_TERMINAL_TOOL_EVENTS = {
    "tool_call_observed": "observed",
    "tool_call_rejected": "rejected",
    "tool_call_unknown": "unknown",
    "tool_call_cancel_requested": "cancel-requested",
    "tool_call_cancelled": "cancelled",
}


@dataclass(slots=True)
class _PendingToolSpan:
    span: Span
    tool_name: str
    step_id: str | None


class OpenTelemetryHarnessEventSink:
    """Project canonical Harness Tool lifecycle events into OpenTelemetry.

    This adapter is intentionally outside the ordivon_harness package. Harness
    owns its canonical event stream; OpenTelemetry owns only a best-effort live
    projection. Tool arguments, observations, and credentials are never copied
    into span attributes.
    """

    def __init__(self, harness_run_id: str, *, tracer: Tracer | None = None) -> None:
        if not harness_run_id or harness_run_id != harness_run_id.strip():
            raise ValueError("Harness Run identity must be non-empty and trimmed")
        self.harness_run_id = harness_run_id
        self.tracer = tracer or trace.get_tracer("ordivon-harness-caller")
        self._pending: dict[str, _PendingToolSpan] = {}

    def __call__(self, event: HarnessRunEvent) -> None:
        if event.kind == "tool_call_dispatched":
            self._start_dispatched(event)
            return
        status = _TERMINAL_TOOL_EVENTS.get(event.kind)
        if status is not None:
            self._finish(event, status)

    def _start_dispatched(self, event: HarnessRunEvent) -> None:
        call_id = _text(event.payload.get("toolCallId"))
        tool_name = _text(event.payload.get("toolName"))
        if call_id is None or tool_name is None:
            return
        if call_id in self._pending:
            return
        step_id = _text(event.payload.get("stepId"))
        attributes: dict[str, str] = {
            "gen_ai.operation.name": "execute_tool",
            "gen_ai.tool.name": tool_name,
            "gen_ai.tool.call.id": call_id,
            "ordivon.harness.run.id": self.harness_run_id,
        }
        if step_id is not None:
            attributes["ordivon.harness.tool.step.id"] = step_id
        runtime_job_ref = _text(event.payload.get("runtimeJobRef"))
        if runtime_job_ref is not None:
            attributes["ordivon.runtime.job.ref"] = runtime_job_ref
        span = self.tracer.start_span(
            f"execute_tool {tool_name}",
            attributes=attributes,
            start_time=event.occurred_at_ms * 1_000_000,
        )
        self._pending[call_id] = _PendingToolSpan(span, tool_name, step_id)

    def _finish(self, event: HarnessRunEvent, status: str) -> None:
        call_id = _text(event.payload.get("toolCallId"))
        tool_name = _text(event.payload.get("toolName"))
        if call_id is None or tool_name is None:
            return

        pending = self._pending.pop(call_id, None)
        if pending is None:
            attributes: dict[str, str] = {
                "gen_ai.operation.name": "execute_tool",
                "gen_ai.tool.name": tool_name,
                "gen_ai.tool.call.id": call_id,
                "ordivon.harness.run.id": self.harness_run_id,
            }
            span = self.tracer.start_span(
                f"execute_tool {tool_name}",
                attributes=attributes,
                start_time=event.occurred_at_ms * 1_000_000,
            )
        else:
            span = pending.span

        span.set_attribute("ordivon.harness.tool.status", status)
        runtime_job_ref = _text(event.payload.get("runtimeJobRef"))
        if runtime_job_ref is not None:
            span.set_attribute("ordivon.runtime.job.ref", runtime_job_ref)
        span.end(end_time=event.occurred_at_ms * 1_000_000)


def _text(value: object) -> str | None:
    return value if isinstance(value, str) and value else None


__all__ = ["OpenTelemetryHarnessEventSink"]
