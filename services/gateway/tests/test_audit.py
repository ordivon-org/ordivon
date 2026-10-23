from __future__ import annotations

import asyncio
import json
import logging
from types import SimpleNamespace
from typing import Any

from opentelemetry.sdk.trace import TracerProvider

from ordivon_gateway.audit import GatewayAuditMiddleware
from ordivon_gateway.mcp_server import build_server


def test_gateway_audit_middleware_runs_inside_sdk_opentelemetry() -> None:
    server = build_server(service=object())  # type: ignore[arg-type]
    names = [type(middleware).__name__ for middleware in server.middleware]
    assert names[0] == "OpenTelemetryMiddleware"
    assert "GatewayAuditMiddleware" in names
    assert names.index("GatewayAuditMiddleware") > names.index("OpenTelemetryMiddleware")


def test_gateway_audit_uses_verified_request_state_not_tool_arguments(caplog) -> None:
    middleware = GatewayAuditMiddleware()
    principal = "principal:cf-access:" + "a" * 64
    request = SimpleNamespace(
        scope={
            "state": {
                "ordivon_access_principal": principal,
                "ordivon_access_issuer": "https://team.cloudflareaccess.com",
            }
        }
    )
    ctx = SimpleNamespace(
        request=request,
        method="tools/call",
        params={
            "name": "execution.submit",
            "arguments": {
                "ordivon_access_principal": "principal:cf-access:forged",
                "cf-access-jwt-assertion": "must-not-be-read",
            },
        },
    )

    async def call_next(_ctx: Any) -> dict[str, Any]:
        return {
            "content": [],
            "structuredContent": {
                "operation_ref": "ordivon-exec:v1:runtime.linux:job-1",
                "owner_id": "runtime.linux",
                "native_id": "job-1",
            },
            "isError": False,
        }

    tracer = TracerProvider().get_tracer("ordivon-gateway-audit-test")
    caplog.set_level(logging.INFO, logger="ordivon_gateway.audit")
    with tracer.start_as_current_span("gateway-test") as span:
        trace_id = f"{span.get_span_context().trace_id:032x}"
        result = asyncio.run(middleware(ctx, call_next))

    assert result["structuredContent"]["native_id"] == "job-1"
    event = json.loads(caplog.records[-1].message)
    assert event == {
        "event": "ordivon.gateway.audit",
        "mcpMethod": "tools/call",
        "nativeId": "job-1",
        "operationRef": "ordivon-exec:v1:runtime.linux:job-1",
        "ownerId": "runtime.linux",
        "principal": principal,
        "spanId": event["spanId"],
        "toolName": "execution.submit",
        "traceId": trace_id,
        "truthRole": "observability-correlation-only",
    }
    assert event["spanId"] is not None
    assert "forged" not in caplog.records[-1].message
    assert "must-not-be-read" not in caplog.records[-1].message
    assert span.attributes["enduser.id"] == principal
    assert span.attributes["ordivon.auth.issuer"] == "https://team.cloudflareaccess.com"
    assert span.attributes["ordivon.gateway.auth.principal"] == principal
    assert span.attributes["ordivon.gateway.auth.issuer"] == "https://team.cloudflareaccess.com"
    assert span.attributes["ordivon.operation_ref"] == "ordivon-exec:v1:runtime.linux:job-1"
    assert span.attributes["ordivon.owner_id"] == "runtime.linux"
    assert span.attributes["ordivon.native_id"] == "job-1"
