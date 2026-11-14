from __future__ import annotations

import json
import logging
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


class GatewayAuditMiddleware:
    """Correlate authenticated ingress with MCP trace and owner references.

    This is an observability projection only. The principal comes exclusively
    from Cloudflare Access-verified HTTP request state; tool arguments are never
    consulted for identity, and no JWT or downstream credential is recorded.
    """

    async def __call__(
        self,
        ctx: ServerRequestContext[Any, Any],
        call_next: CallNext,
    ) -> HandlerResult:
        identity = identity_from_state(request_state(ctx))
        principal = identity.principal if identity is not None else None
        issuer = identity.issuer if identity is not None else None

        span = trace.get_current_span()
        if isinstance(principal, str) and principal:
            span.set_attribute("enduser.id", principal)
            span.set_attribute("ordivon.gateway.auth.principal", principal)
        if isinstance(issuer, str) and issuer:
            span.set_attribute("ordivon.auth.issuer", issuer)
            span.set_attribute("ordivon.gateway.auth.issuer", issuer)

        result = await call_next(ctx)

        if ctx.method != "tools/call":
            return result

        tool_name = None
        if isinstance(ctx.params, dict):
            candidate = ctx.params.get("name")
            if isinstance(candidate, str):
                tool_name = candidate

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
        return result
