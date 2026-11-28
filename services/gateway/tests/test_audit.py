from __future__ import annotations

import asyncio
import json
import logging
from types import SimpleNamespace
from typing import Any

import pytest
from opentelemetry.sdk.trace import TracerProvider

from ordivon_gateway.mcp_server import build_server
from ordivon_gateway.security.audit import GatewayAuditMiddleware


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
        "observationSchemaVersion": 2,
        "outcome": "returned",
        "durationNs": event["durationNs"],
        "nativeId": "job-1",
        "operationRef": "ordivon-exec:v1:runtime.linux:job-1",
        "ownerId": "runtime.linux",
        "principal": principal,
        "spanId": event["spanId"],
        "toolName": "execution.submit",
        "traceId": trace_id,
        "truthRole": "observability-correlation-only",
    }
    assert event["durationNs"] >= 0
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


@pytest.mark.parametrize("fault", ["before", "after"])
def test_optional_audit_failure_preserves_exact_owner_result(monkeypatch, fault) -> None:
    import ordivon_gateway.security.audit as audit

    ctx = SimpleNamespace(
        request=SimpleNamespace(
            scope={
                "state": {
                    "ordivon_access_principal": "principal:test",
                    "ordivon_access_issuer": "https://issuer.example",
                }
            }
        ),
        method="tools/call",
        params={"name": "execution.submit"},
    )
    result = {"structuredContent": {"native_id": "job-1"}, "isError": False}
    calls = []

    def fail(*args, **kwargs):
        raise OSError("simulated diagnostic sink failure")

    if fault == "before":
        monkeypatch.setattr(audit.trace, "get_current_span", fail)
    else:
        monkeypatch.setattr(audit.logger, "info", fail)

    async def owner(_ctx):
        calls.append(_ctx)
        return result

    assert asyncio.run(GatewayAuditMiddleware()(ctx, owner)) is result
    assert calls == [ctx]


@pytest.mark.parametrize("failure", [PermissionError("owner denied"), asyncio.CancelledError()])
def test_audit_does_not_swallow_owner_failure_or_cancellation(failure) -> None:
    ctx = SimpleNamespace(request=None, method="tools/call", params={"name": "execution.submit"})

    async def owner(_ctx):
        raise failure

    with pytest.raises(type(failure)) as caught:
        asyncio.run(GatewayAuditMiddleware()(ctx, owner))
    assert caught.value is failure


@pytest.mark.parametrize("denied", [False, True])
def test_native_mcp_result_survives_broken_audit_handler(caplog, denied) -> None:
    from mcp import Client

    from ordivon_gateway.logic.owner_protocol import OwnerCallError
    from ordivon_gateway.service import GatewayService

    calls = []
    owner_error = {"code": "UNAUTHORIZED", "message": "fixture denied"}

    class Owner:
        def is_configured(self, owner_id):
            return owner_id == "host"

        async def call_tool(self, owner_id, tool_name, arguments):
            calls.append((owner_id, tool_name))
            if denied:
                raise OwnerCallError(
                    "fixture denied", owner_id=owner_id, tool_name=tool_name, error=owner_error
                )
            return {"fixtureReceipt": "owner-result"}

    class BrokenSink(logging.Handler):
        emitted = 0

        def emit(self, record):
            self.emitted += 1
            raise OSError("simulated log device unavailable")

    async def run() -> None:
        async with Client(build_server(GatewayService(Owner())), raise_exceptions=False) as client:
            result = await client.call_tool("topic.resume", {"topicRef": "topic:fixture"})
            assert result.is_error is denied
            if denied:
                assert result.structured_content["error"] == owner_error
            else:
                assert result.structured_content == {"fixtureReceipt": "owner-result"}

    logger = logging.getLogger("ordivon_gateway.audit")
    caplog.set_level(logging.INFO, logger=logger.name)
    sink = BrokenSink()
    logger.addHandler(sink)
    try:
        asyncio.run(run())
    finally:
        logger.removeHandler(sink)
    assert calls == [("host", "topic.resume")]
    # Both the correlation event and the bounded diagnostic fallback failed.
    assert sink.emitted == 2


@pytest.mark.parametrize(
    "mode,expected",
    [
        ("ok", "returned"),
        ("tool-error", "tool_error"),
        ("unknown", "unknown"),
        ("exception", "raised"),
        ("cancel", "cancelled"),
    ],
)
def test_audit_terminal_observation_covers_middleware_outcomes(caplog, mode, expected):
    ctx = SimpleNamespace(request=None, method="tools/call", params={"name": "topic.resume"})
    failure = asyncio.CancelledError() if mode == "cancel" else OSError("secret-fixture")
    result = (
        {"isError": False}
        if mode == "ok"
        else (
            {"isError": True, "structuredContent": {"error": {"message": "secret-fixture"}}}
            if mode == "tool-error"
            else {}
        )
    )
    calls = []

    async def owner(_ctx):
        calls.append(_ctx)
        if mode in ("exception", "cancel"):
            raise failure
        return result

    caplog.set_level(logging.INFO, logger="ordivon_gateway.audit")
    if mode in ("exception", "cancel"):
        with pytest.raises(type(failure)) as caught:
            asyncio.run(GatewayAuditMiddleware()(ctx, owner))
        assert caught.value is failure
    else:
        assert asyncio.run(GatewayAuditMiddleware()(ctx, owner)) is result
    assert calls == [ctx]
    events = [
        json.loads(r.message)
        for r in caplog.records
        if r.name == "ordivon_gateway.audit" and r.message.startswith("{")
    ]
    assert len(events) == 1
    assert events[0]["outcome"] == expected
    assert events[0]["observationSchemaVersion"] == 2
    assert events[0]["durationNs"] >= 0
    assert events[0]["truthRole"] == "observability-correlation-only"
    assert "secret-fixture" not in json.dumps(events[0])
    if mode in ("exception", "cancel"):
        assert "nativeId" not in events[0]


@pytest.mark.parametrize(
    "flags",
    [
        {"isError": False, "is_error": True},
        {"isError": 0},
        {"is_error": None},
        {"isError": True, "is_error": "true"},
    ],
)
def test_audit_ambiguous_wire_status_is_unknown(caplog, flags):
    ctx = SimpleNamespace(request=None, method="tools/call", params={"name": "execution.get"})

    async def owner(_ctx):
        return flags

    caplog.set_level(logging.INFO, logger="ordivon_gateway.audit")
    assert asyncio.run(GatewayAuditMiddleware()(ctx, owner)) is flags
    event = json.loads(caplog.records[-1].message)
    assert event["outcome"] == "unknown"


@pytest.mark.parametrize("cancelled", [False, True])
def test_audit_sink_failure_preserves_original_exception(monkeypatch, cancelled):
    import ordivon_gateway.security.audit as audit

    ctx = SimpleNamespace(request=None, method="tools/call", params={"name": "execution.get"})
    error = asyncio.CancelledError() if cancelled else RuntimeError("owner failure")
    calls = []

    def broken(*args, **kwargs):
        raise OSError("unavailable diagnostic sink")

    monkeypatch.setattr(audit.logger, "info", broken)
    monkeypatch.setattr(audit.logger, "warning", broken)

    async def owner(_ctx):
        calls.append(_ctx)
        raise error

    with pytest.raises(type(error)) as caught:
        asyncio.run(GatewayAuditMiddleware()(ctx, owner))
    assert caught.value is error
    assert calls == [ctx]


@pytest.mark.parametrize("denied", [False, True])
def test_native_mcp_audit_reports_protocol_result_not_owner_completion(caplog, denied):
    from mcp import Client

    from ordivon_gateway.logic.owner_protocol import OwnerCallError
    from ordivon_gateway.service import GatewayService

    calls = []

    class Owner:
        def is_configured(self, owner_id):
            return owner_id == "host"

        async def call_tool(self, owner_id, tool_name, arguments):
            calls.append((owner_id, tool_name))
            if denied:
                raise OwnerCallError(
                    "secret-fixture",
                    owner_id=owner_id,
                    tool_name=tool_name,
                    error={"code": "UNAUTHORIZED", "message": "secret-fixture"},
                )
            return {"fixtureReceipt": "not-a-semantic-completion"}

    async def run():
        async with Client(build_server(GatewayService(Owner())), raise_exceptions=False) as client:
            result = await client.call_tool("topic.resume", {"topicRef": "topic:fixture"})
            assert result.is_error is denied

    caplog.set_level(logging.INFO, logger="ordivon_gateway.audit")
    asyncio.run(run())
    assert calls == [("host", "topic.resume")]
    events = [
        json.loads(record.message)
        for record in caplog.records
        if record.name == "ordivon_gateway.audit" and record.message.startswith("{")
    ]
    assert len(events) == 1
    assert events[0]["outcome"] == ("tool_error" if denied else "returned")
    assert events[0]["toolName"] == "topic.resume"
    assert "secret-fixture" not in json.dumps(events[0])
    assert "not-a-semantic-completion" not in json.dumps(events[0])


def test_non_tool_middleware_does_not_create_tool_observation(caplog):
    ctx = SimpleNamespace(request=None, method="tools/list", params={})
    result = {"isError": False}

    async def owner(_ctx):
        return result

    caplog.set_level(logging.INFO, logger="ordivon_gateway.audit")
    assert asyncio.run(GatewayAuditMiddleware()(ctx, owner)) is result
    assert not [r for r in caplog.records if r.name == "ordivon_gateway.audit"]
