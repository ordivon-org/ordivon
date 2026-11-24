"""Source-contract regressions for the one verified-ingress identity projection.

The HTTP ingress producer is the only trust root. These consumers may read
that request state, never Tool arguments, _meta, or a guessed bearer identity.
"""

from __future__ import annotations

import asyncio
from types import SimpleNamespace

import pytest
from mcp.server.mcpserver import Context

from ordivon_gateway.security import verified_execution_scope
from ordivon_gateway.security.authorization_targets import (
    _HOST_READ_ONLY_TOOLS,
    _HOST_READ_SELECTORS,
)
from ordivon_gateway.security.capability_authz import GatewayCapabilityAuthorizationMiddleware
from ordivon_gateway.security.http_ingress_guard import GatewayHTTPIngressGuard
from ordivon_gateway.security.ingress_identity import (
    identity_from_state,
    request_state,
    tool_context_state,
)

PRINCIPAL = "principal:cf-access:" + "a" * 64
ISSUER = "https://auth.example.test"
STATE = {"ordivon_access_principal": PRINCIPAL, "ordivon_access_issuer": ISSUER}


def _ctx(state, *, params=None):
    return SimpleNamespace(
        method="tools/call",
        params=params or {"name": "work.get", "arguments": {"workRef": "work:test:1"}},
        request=SimpleNamespace(scope={"state": state}),
    )


def test_request_and_sdk_tool_context_produce_one_canonical_identity() -> None:
    ctx = _ctx(dict(STATE))
    tool = Context(request_context=SimpleNamespace(request=ctx.request), mcp_server=object())
    observed = identity_from_state(request_state(ctx))
    assert observed is not None
    assert observed.principal == PRINCIPAL
    assert observed.issuer == ISSUER
    assert identity_from_state(tool_context_state(tool)) == observed
    assert verified_execution_scope(tool) == (ISSUER, PRINCIPAL)


@pytest.mark.parametrize(
    "state",
    [
        None,
        42,
        {},
        {"ordivon_access_principal": PRINCIPAL},
        {"ordivon_access_principal": PRINCIPAL, "ordivon_access_issuer": ""},
        {"ordivon_access_principal": "  ", "ordivon_access_issuer": ISSUER},
        {"ordivon_access_principal": PRINCIPAL, "ordivon_access_issuer": " \t "},
        {"ordivon_access_principal": 2, "ordivon_access_issuer": ISSUER},
        {"ordivon_access_principal": PRINCIPAL, "ordivon_access_issuer": ["spoof"]},
    ],
)
def test_malformed_trusted_state_cannot_become_request_identity(state) -> None:
    ctx = _ctx(state)
    assert identity_from_state(request_state(ctx)) is None
    tool = Context(request_context=SimpleNamespace(request=ctx.request), mcp_server=object())
    assert identity_from_state(tool_context_state(tool)) is None
    assert verified_execution_scope(tool) is None


def test_both_security_layers_reject_blank_claims_before_owner_call() -> None:
    entered: list[str] = []
    context = _ctx(
        {"ordivon_access_principal": "  ", "ordivon_access_issuer": ISSUER},
        params={
            "name": "work.get",
            "arguments": {
                "workRef": "work:correct:one",
                "ordivon_access_principal": PRINCIPAL,
                "_meta": {"ordivon_access_issuer": ISSUER},
            },
        },
    )

    async def owner(_ctx):
        entered.append("owner")
        return {"structuredContent": {"ownerReached": True}}

    ingress = asyncio.run(GatewayHTTPIngressGuard()(context, owner))
    pep = asyncio.run(GatewayCapabilityAuthorizationMiddleware(None)(context, owner))
    assert ingress.is_error
    assert ingress.structured_content["error"]["code"] == "HTTP_INGRESS_IDENTITY_MISSING"
    assert pep.is_error
    assert pep.structured_content["error"]["code"] == "CAPABILITY_AUTHZ_INGRESS_IDENTITY_MISSING"
    assert entered == []


def test_invalid_sdk_context_does_not_invent_an_identity() -> None:
    class InvalidRequest:
        @property
        def request(self):
            raise ValueError("unavailable SDK request")

    tool = Context(request_context=InvalidRequest(), mcp_server=object())
    assert tool_context_state(tool) == {}
    assert verified_execution_scope(tool) is None


def test_host_read_selector_map_is_the_only_local_read_name_source() -> None:
    assert _HOST_READ_ONLY_TOOLS == frozenset(_HOST_READ_SELECTORS)
    assert len(_HOST_READ_ONLY_TOOLS) == 17
    assert _HOST_READ_SELECTORS["message.get"] == ("messageRef",)


def test_host_read_and_write_security_partition_matches_actual_mcp_manifest() -> None:
    """One cross-layer consumer obligation, not a second copy of the Tool catalog."""
    import json
    from pathlib import Path

    from ordivon_gateway.logic.host_tool_contracts import (
        SOCIAL_WORK_HOST_TOOLS as _SOCIAL_WORK_HOST_TOOLS,
    )

    surface = Path(__file__).resolve().parents[1] / "enforcement-surface.json"
    manifest = json.loads(surface.read_text(encoding="utf-8"))["tools"]
    reads = {
        item["name"]
        for item in manifest
        if item["routeOwner"] == "host" and item["operation"] == "read"
    }
    writes = {
        item["name"]
        for item in manifest
        if item["routeOwner"] == "host" and item["operation"] == "write"
    }
    assert reads == _HOST_READ_ONLY_TOOLS
    assert writes == _SOCIAL_WORK_HOST_TOOLS - _HOST_READ_ONLY_TOOLS
    assert not reads & writes
    assert {
        item["name"] for item in manifest if item["routeOwner"] == "host"
    } == _SOCIAL_WORK_HOST_TOOLS


def test_audit_does_not_claim_a_partially_observed_principal(caplog) -> None:
    import json
    import logging

    from ordivon_gateway.security.audit import GatewayAuditMiddleware

    ctx = _ctx(
        {"ordivon_access_principal": PRINCIPAL},
        params={"name": "work.get", "arguments": {"ordivon_access_issuer": ISSUER}},
    )

    async def owner(_ctx):
        return {"content": [], "structuredContent": {"ok": True}}

    caplog.set_level(logging.INFO, logger="ordivon_gateway.audit")
    asyncio.run(GatewayAuditMiddleware()(ctx, owner))
    event = json.loads(caplog.records[-1].message)
    assert event["principal"] is None
    assert PRINCIPAL not in caplog.records[-1].message
    assert ISSUER not in caplog.records[-1].message
