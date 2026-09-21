from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from opentelemetry import context as otel_context
from opentelemetry import trace
from opentelemetry.propagate import extract

from harness_otel_event_sink import OpenTelemetryHarnessEventSink
from ordivon_harness.ordivon.loop import OrdivonAgentLoop, RunStopCode
from ordivon_harness.ordivon.model import ScriptedTurnAdapter

from tests.test_p2_tool_program import Bridge
from tests.test_p2_tool_program_provider_loop import _budget, _complete_turn, _program_turn


@dataclass
class RecordedSpan:
    name: str
    parent_trace_id: int
    attributes: dict[str, Any]
    start_time: int | None
    end_time: int | None = None

    def set_attribute(self, name: str, value: Any) -> None:
        self.attributes[name] = value

    def end(self, end_time: int | None = None) -> None:
        self.end_time = end_time


@dataclass
class RecordingTracer:
    spans: list[RecordedSpan] = field(default_factory=list)

    def start_span(
        self,
        name: str,
        *,
        context=None,
        kind=None,
        attributes=None,
        links=None,
        start_time=None,
        record_exception=True,
        set_status_on_exception=True,
    ) -> RecordedSpan:
        del kind, links, record_exception, set_status_on_exception
        parent = trace.get_current_span(context).get_span_context()
        span = RecordedSpan(
            name=name,
            parent_trace_id=parent.trace_id,
            attributes=dict(attributes or {}),
            start_time=start_time,
        )
        self.spans.append(span)
        return span


def _run(*, event_sink=None):
    bridge = Bridge()
    adapter = ScriptedTurnAdapter((_program_turn("t04"), _complete_turn("t04")))
    return OrdivonAgentLoop(
        adapter,
        bridge,
        budget=_budget(),
        clock_ms=lambda: 1_000,
        monotonic_ms=lambda: 1_000,
        tool_program_actions=True,
        event_sink=event_sink,
    ).run(
        harness_run_id="harness-run:t04-loop",
        assignment_id="assignment:t04-loop",
        context_digest="sha256:" + "a" * 64,
        initial_messages=({"role": "user", "content": "derive the dependent value"},),
    )


def test_caller_owned_sink_correlates_tool_lifecycle_with_ambient_w3c_trace() -> None:
    tracer = RecordingTracer()
    sink = OpenTelemetryHarnessEventSink(
        "harness-run:t04-loop",
        tracer=tracer,  # type: ignore[arg-type]
    )
    parent = extract({"traceparent": ("00-aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa-bbbbbbbbbbbbbbbb-01")})
    token = otel_context.attach(parent)
    try:
        result = _run(event_sink=sink)
    finally:
        otel_context.detach(token)

    assert result.stop_code is RunStopCode.CANDIDATE_COMPLETED
    assert [span.attributes["gen_ai.tool.name"] for span in tracer.spans] == [
        "read_value",
        "lookup_value",
    ]
    assert {f"{span.parent_trace_id:032x}" for span in tracer.spans} == {
        "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
    }
    assert {span.attributes["gen_ai.operation.name"] for span in tracer.spans} == {"execute_tool"}
    assert {span.attributes["ordivon.harness.run.id"] for span in tracer.spans} == {
        "harness-run:t04-loop"
    }
    assert {span.attributes["ordivon.harness.tool.status"] for span in tracer.spans} == {"observed"}
    assert all(span.end_time is not None for span in tracer.spans)
    for span in tracer.spans:
        encoded = repr(span.attributes)
        assert "arguments" not in encoded
        assert "structuredContent" not in encoded
        assert "observationDigest" not in encoded


def test_live_projection_does_not_change_canonical_harness_trace() -> None:
    tracer = RecordingTracer()
    with_sink = _run(
        event_sink=OpenTelemetryHarnessEventSink(
            "harness-run:t04-loop",
            tracer=tracer,  # type: ignore[arg-type]
        )
    )
    without_sink = _run()

    assert with_sink.trace.digest == without_sink.trace.digest
    assert with_sink.trace.to_dict() == without_sink.trace.to_dict()
    assert with_sink.observations == without_sink.observations
