from __future__ import annotations

import json
import logging
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


def _result_identity(result: HandlerResult) -> dict[str, str]:
    if isinstance(result, dict):
        structured = result.get("structuredContent", result.get("structured_content"))
    else:
        structured = getattr(result, "structured_content", None)
    if not isinstance(structured, dict):
        return {}
    identity: dict[str, str] = {}
    for source, target in (
        ("operation_ref", "operationRef"),
        ("operationRef", "operationRef"),
        ("owner_id", "ownerId"),
        ("ownerId", "ownerId"),
        ("native_id", "nativeId"),
        ("nativeId", "nativeId"),
        ("task_id", "taskId"),
        ("taskId", "taskId"),
    ):
        value = structured.get(source)
        if isinstance(value, str) and value and target not in identity:
            identity[target] = value
    return identity


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


def _record_result_projection(
    ctx: ServerRequestContext[Any, Any], result: HandlerResult, principal: str | None
) -> None:
    tool_name = None
    if isinstance(ctx.params, dict):
        candidate = ctx.params.get("name")
        if isinstance(candidate, str):
            tool_name = candidate

    span = trace.get_current_span()
    result_identity = _result_identity(result)
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
    is deliberately outside both Exception handlers; cancellation, denial
    and all other Owner errors retain their original semantics.
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

        result = await call_next(ctx)

        try:
            if ctx.method == "tools/call":
                _record_result_projection(ctx, result, principal)
        except Exception:
            _report_projection_failure("result")

        return result
