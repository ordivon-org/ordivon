from __future__ import annotations

from dataclasses import dataclass

from opentelemetry import trace
from opentelemetry.trace import Span, Tracer
from opentelemetry.trace.status import Status, StatusCode

from ordivon_harness.ordivon.events import HarnessRunEvent

_TERMINAL_TOOL_EVENTS = {
    "tool_call_observed": "observed",
    "tool_call_rejected": "rejected",
    "tool_call_unknown": "unknown",
    "tool_call_cancelled": "cancelled",
}


@dataclass(slots=True)
class _PendingToolSpan:
    span: Span
    tool_name: str
    step_id: str | None
    runtime_job_ref: str | None


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
        self._terminal_calls: set[str] = set()
        self._stopped = False

    def __call__(self, event: HarnessRunEvent) -> None:
        if self._stopped:
            return
        if event.kind == "tool_call_dispatched":
            self._start_dispatched(event)
            return
        if event.kind == "tool_call_cancel_requested":
            self._mark_cancel_requested(event)
            return
        if event.kind == "run_stopped":
            self._close_unresolved(event)
            self._stopped = True
            return
        if event.kind == "tool_call_reconciled":
            # A recovered durable Tool result is an observation, not a redispatch.
            status = event.payload.get("status")
            if status in ("observed", "rejected", "unknown", "cancelled"):
                self._finish(event, status, reconciled=True)
            return
        status = _TERMINAL_TOOL_EVENTS.get(event.kind)
        if status is not None:
            self._finish(event, status)

    def _start_dispatched(self, event: HarnessRunEvent) -> None:
        call_id = _text(event.payload.get("toolCallId"))
        tool_name = _text(event.payload.get("toolName"))
        if call_id is None or tool_name is None:
            return
        if call_id in self._pending or call_id in self._terminal_calls:
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
        self._pending[call_id] = _PendingToolSpan(span, tool_name, step_id, runtime_job_ref)

    def _mark_cancel_requested(self, event: HarnessRunEvent) -> None:
        # Cancellation intent does not establish physical Runtime termination.
        call_id = _text(event.payload.get("toolCallId"))
        tool_name = _text(event.payload.get("toolName"))
        pending = self._pending.get(call_id) if call_id is not None else None
        if pending is None or pending.tool_name != tool_name:
            return
        step_id = _text(event.payload.get("stepId"))
        if step_id is not None and pending.step_id != step_id:
            return
        runtime_job_ref = _text(event.payload.get("runtimeJobRef"))
        if (
            runtime_job_ref is not None
            and pending.runtime_job_ref is not None
            and pending.runtime_job_ref != runtime_job_ref
        ):
            return
        pending.span.set_attribute("ordivon.harness.tool.cancel_requested", True)

    def _close_unresolved(self, event: HarnessRunEvent) -> None:
        # The Run has stopped. Do not invent physical Tool completion.
        for call_id, pending in self._pending.items():
            pending.span.set_attribute("ordivon.harness.tool.status", "unknown")
            pending.span.set_attribute("error.type", "tool_unknown")
            pending.span.set_status(Status(StatusCode.ERROR))
            pending.span.end(end_time=event.occurred_at_ms * 1_000_000)
            self._terminal_calls.add(call_id)
        self._pending.clear()

    def _finish(self, event: HarnessRunEvent, status: str, *, reconciled: bool = False) -> None:
        call_id = _text(event.payload.get("toolCallId"))
        tool_name = _text(event.payload.get("toolName"))
        if call_id is None or tool_name is None or call_id in self._terminal_calls:
            return

        # Reconciliation cannot terminate a different dispatched Tool step.
        pending = self._pending.get(call_id)
        if pending is not None and (
            pending.tool_name != tool_name
            or (
                (step_id := _text(event.payload.get("stepId"))) is not None
                and pending.step_id != step_id
            )
            or (
                (job_ref := _text(event.payload.get("runtimeJobRef"))) is not None
                and pending.runtime_job_ref is not None
                and pending.runtime_job_ref != job_ref
            )
        ):
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
        if status in ("rejected", "unknown"):
            # Standard OTel error status is consumed by external trajectory graders.
            span.set_attribute("error.type", f"tool_{status}")
            span.set_status(Status(StatusCode.ERROR))
        if reconciled:
            span.set_attribute("ordivon.harness.tool.reconciled", True)
            span.set_attribute("ordivon.harness.tool.dispatch_observed", pending is not None)
        runtime_job_ref = _text(event.payload.get("runtimeJobRef"))
        if runtime_job_ref is not None:
            span.set_attribute("ordivon.runtime.job.ref", runtime_job_ref)
        span.end(end_time=event.occurred_at_ms * 1_000_000)
        self._terminal_calls.add(call_id)


def _text(value: object) -> str | None:
    return value if isinstance(value, str) and value else None


__all__ = ["OpenTelemetryHarnessEventSink"]
