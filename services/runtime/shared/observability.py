from __future__ import annotations

from contextlib import contextmanager
from time import perf_counter
from typing import Any

import sentry_sdk
from opentelemetry import metrics, trace
from opentelemetry.exporter.otlp.proto.http.metric_exporter import OTLPMetricExporter
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
from opentelemetry.sdk.resources import SERVICE_NAME, Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from sentry_sdk.integrations.fastapi import FastApiIntegration

from shared.config.settings import settings

_INITIALIZED = False
_COUNTERS: dict[str, Any] = {}


def init_observability() -> None:
    global _INITIALIZED
    if _INITIALIZED:
        return

    resource = Resource.create({SERVICE_NAME: settings.otel_service_name})

    if settings.otel_exporter_otlp_endpoint:
        tracer_provider = TracerProvider(resource=resource)
        tracer_provider.add_span_processor(
            BatchSpanProcessor(
                OTLPSpanExporter(
                    endpoint=f"{settings.otel_exporter_otlp_endpoint.rstrip('/')}/v1/traces",
                )
            )
        )
        trace.set_tracer_provider(tracer_provider)

        metric_reader = PeriodicExportingMetricReader(
            OTLPMetricExporter(
                endpoint=f"{settings.otel_exporter_otlp_endpoint.rstrip('/')}/v1/metrics",
            )
        )
        metrics.set_meter_provider(MeterProvider(resource=resource, metric_readers=[metric_reader]))

    if settings.sentry_dsn:
        sentry_sdk.init(
            dsn=settings.sentry_dsn,
            integrations=[FastApiIntegration()],
            traces_sample_rate=1.0 if settings.debug else 0.1,
            environment=settings.env,
            release="aegisos@0.1.0",
        )

    _INITIALIZED = True


def _meter():
    return metrics.get_meter(settings.otel_service_name)


def increment_counter(name: str, value: int = 1, *, attributes: dict[str, Any] | None = None) -> None:
    counter = _COUNTERS.get(name)
    if counter is None:
        counter = _meter().create_counter(name)
        _COUNTERS[name] = counter
    counter.add(value, attributes or {})


def record_exception(exc: Exception, *, attributes: dict[str, Any] | None = None) -> None:
    span = trace.get_current_span()
    if span is not None:
        span.record_exception(exc)
        span.set_attribute("error", True)
    if attributes:
        for key, value in attributes.items():
            if span is not None:
                span.set_attribute(key, value)
    if settings.sentry_dsn:
        sentry_sdk.capture_exception(exc)


@contextmanager
def span(name: str, *, attributes: dict[str, Any] | None = None):
    tracer = trace.get_tracer(settings.otel_service_name)
    with tracer.start_as_current_span(name) as current_span:
        for key, value in (attributes or {}).items():
            current_span.set_attribute(key, value)
        started_at = perf_counter()
        try:
            yield current_span
        except Exception as exc:
            record_exception(exc, attributes=attributes)
            raise
        finally:
            current_span.set_attribute("duration_ms", (perf_counter() - started_at) * 1000)
