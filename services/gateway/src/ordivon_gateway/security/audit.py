from __future__ import annotations

import asyncio
import json
import logging
import time
from contextlib import suppress
from typing import Any

from mcp.server.context import CallNext, HandlerResult, ServerRequestContext
from opentelemetry import trace

from .ingress_identity import identity_from_state, request_state

logger = logging.getLogger("ordivon_gateway.audit")


def _trace_identity() -> tuple[str | None, str | None]:
    span_context = trace.get_current_span().get_span_context()
    if not span_context.is_valid:
        return None, None
    return f"{span_context.trace_id:032x}", f"{span_context.span_id:016x}"


def _structured_identity(structured: Any) -> dict[str, str] | None:
    if not isinstance(structured, dict):
        return None
    identity: dict[str, str] = {}
    for snake, camel in (
        ("operation_ref", "operationRef"),
        ("owner_id", "ownerId"),
        ("native_id", "nativeId"),
        ("task_id", "taskId"),
    ):
        values = [structured[key] for key in (snake, camel) if key in structured]
        if len(values) == 2 and (
            any(not isinstance(value, str) or not value for value in values)
            or values[0] != values[1]
        ):
            # A contradictory identity tuple is not a qualified correlation.
            return None
        if values and isinstance(values[0], str) and values[0]:
            identity[camel] = values[0]
    return identity


def _result_identity(result: HandlerResult) -> dict[str, str]:
    if isinstance(result, dict):
        projections = [
            _structured_identity(result[key])
            for key in ("structuredContent", "structured_content")
            if key in result
        ]
    else:
        projections = [_structured_identity(getattr(result, "structured_content", None))]
    if not projections or projections[0] is None:
        return {}
    if any(projection != projections[0] for projection in projections):
        return {}
    return projections[0]


def _report_projection_failure(phase: str) -> None:
    # A diagnostic fallback must not become a second failure path. Do not
    # serialize the exception, request, credentials, or Owner response.
    with suppress(Exception):
        logger.warning("gateway audit projection unavailable: %s", phase)


def _annotate_ingress(principal: str | None, issuer: str | None) -> None:
    span = trace.get_current_span()
    if principal:
        span.set_attribute("enduser.id", principal)
        span.set_attribute("ordivon.gateway.auth.principal", principal)
    if issuer:
        span.set_attribute("ordivon.auth.issuer", issuer)
        span.set_attribute("ordivon.gateway.auth.issuer", issuer)


def _result_outcome(result: HandlerResult) -> str:
    """Classify only the observed protocol result, not the Owner's effect."""
    if isinstance(result, dict):
        flags = [result[key] for key in ("isError", "is_error") if key in result]
    else:
        flags = [getattr(result, "is_error", None)]
    if not flags or any(type(flag) is not bool for flag in flags):
        return "unknown"
    if any(flag != flags[0] for flag in flags):
        return "unknown"
    return "tool_error" if flags[0] else "returned"


def _record_result_projection(
    ctx: ServerRequestContext[Any, Any],
    result: HandlerResult | None,
    principal: str | None,
    outcome: str,
    duration_ns: int,
) -> None:
    tool_name = None
    if isinstance(ctx.params, dict):
        candidate = ctx.params.get("name")
        if isinstance(candidate, str):
            tool_name = candidate

    span = trace.get_current_span()
    result_identity = _result_identity(result) if result is not None else {}
    for source, attribute in (
        ("operationRef", "ordivon.operation_ref"),
        ("ownerId", "ordivon.owner_id"),
        ("nativeId", "ordivon.native_id"),
        ("taskId", "ordivon.task_id"),
    ):
        value = result_identity.get(source)
        if value:
            span.set_attribute(attribute, value)

    trace_id, span_id = _trace_identity()
    event: dict[str, Any] = {
        "event": "ordivon.gateway.audit",
        "truthRole": "observability-correlation-only",
        "observationSchemaVersion": 2,
        "outcome": outcome,
        "durationNs": duration_ns,
        "mcpMethod": ctx.method,
        "toolName": tool_name,
        "principal": principal if isinstance(principal, str) else None,
        "traceId": trace_id,
        "spanId": span_id,
    }
    event.update(result_identity)
    logger.info(json.dumps(event, sort_keys=True, separators=(",", ":")))


class GatewayAuditMiddleware:
    """Best-effort correlation, never authentication or authorization.

    Only verified request state supplies the principal. Diagnostic failures
    cannot prevent the Owner call or replace its result. The Owner invocation
    is never retried; cancellation, denial and all other Owner errors
    retain their original semantics.
    """

    async def __call__(
        self,
        ctx: ServerRequestContext[Any, Any],
        call_next: CallNext,
    ) -> HandlerResult:
        principal = None
        try:
            identity = identity_from_state(request_state(ctx))
            principal = identity.principal if identity is not None else None
            issuer = identity.issuer if identity is not None else None
            _annotate_ingress(principal, issuer)
        except Exception:
            _report_projection_failure("ingress")

        started_ns: int | None = None
        try:
            if ctx.method == "tools/call":
                started_ns = time.monotonic_ns()
        except Exception:
            _report_projection_failure("clock")

        def observe(result: HandlerResult | None, outcome: str | None = None) -> None:
            try:
                if ctx.method == "tools/call" and started_ns is not None:
                    _record_result_projection(
                        ctx,
                        result,
                        principal,
                        outcome if outcome is not None else _result_outcome(result),
                        time.monotonic_ns() - started_ns,
                    )
            except Exception:
                _report_projection_failure("result")

        try:
            result = await call_next(ctx)
        except asyncio.CancelledError:
            observe(None, "cancelled")
            raise
        except Exception:
            observe(None, "raised")
            raise
        observe(result)
        return result
