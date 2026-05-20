"""OpenTelemetry trace integration — replaces hand-rolled GovernanceTrace with OTel SDK.

Usage:
    from ordivon_governance_core.otel_trace import get_tracer, start_span

    tracer = get_tracer("aos-submit")
    with tracer.start_as_current_span("identity_validation") as span:
        span.set_attribute("status", "PASS")
"""

from __future__ import annotations


try:
    from opentelemetry import trace
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import ConsoleSpanExporter, SimpleSpanProcessor

    _provider = TracerProvider()
    _provider.add_span_processor(SimpleSpanProcessor(ConsoleSpanExporter()))
    trace.set_tracer_provider(_provider)

    _OTEL_AVAILABLE = True
except ImportError:
    _OTEL_AVAILABLE = False


def get_tracer(name: str = "ordivon-governance"):
    """Get an OTel tracer. Falls back to a no-op if OTel not installed."""
    if _OTEL_AVAILABLE:
        return trace.get_tracer(name)
    return _NoopTracer()


def start_span(name: str, attributes: dict | None = None):
    """Start a span manually. Use context manager when possible."""
    tracer = get_tracer()
    return tracer.start_span(name, attributes=attributes or {})


class _NoopTracer:
    def start_span(self, name, attributes=None):
        return _NoopSpan()

    def start_as_current_span(self, name, attributes=None):
        from contextlib import nullcontext

        return nullcontext(_NoopSpan())


class _NoopSpan:
    def set_attribute(self, key, value):
        pass

    def set_status(self, status):
        pass

    def add_event(self, name, attributes=None):
        pass

    def __enter__(self):
        return self

    def __exit__(self, *args):
        pass


def otel_available() -> bool:
    return _OTEL_AVAILABLE
