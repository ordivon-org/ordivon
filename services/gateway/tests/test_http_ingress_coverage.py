"""Consumer verification: actual MCP surface ↔ ingress guard ↔ Security evidence."""

from __future__ import annotations

import asyncio
import json
from pathlib import Path
from types import SimpleNamespace
from typing import Any

from mcp import Client

from ordivon_gateway.http_ingress_guard import (
    PUBLIC_METADATA_TOOLS,
    GatewayHTTPIngressGuard,
    needs_verified_ingress,
)
from ordivon_gateway.mcp_server import build_server

ROOT = Path(__file__).resolve().parents[1]
SURFACE = ROOT / "enforcement-surface.json"


async def _call_next(_ctx: Any) -> dict[str, Any]:
    return {"content": [], "structuredContent": {"ownerReached": True}}


def _ctx(name: str, *, state: dict | None = None, arguments: dict | None = None):
    return SimpleNamespace(
        method="tools/call",
        params={"name": name, "arguments": arguments or {}},
        request=SimpleNamespace(scope={"state": state or {}}),
    )


def test_undocumented_or_forged_host_tool_never_reaches_owner() -> None:
    guard = GatewayHTTPIngressGuard()

    async def attempt(name: str, state: dict, arguments: dict):
        reached = False

        async def owner(_ctx):
            nonlocal reached
            reached = True
            return await _call_next(_ctx)

        result = await guard(_ctx(name, state=state, arguments=arguments), owner)
        return result, reached

    # Tool-controlled identity is never a trusted HTTP ingress state.
    for name in ("work.create", "message.post", "subscription.follow", "unknown.tool"):
        result, reached = asyncio.run(
            attempt(name, {}, {"ordivon_access_principal": "forged", "_meta": {"issuer": "x"}})
        )
        assert result.is_error is True
        assert result.structured_content["error"]["code"] == "HTTP_INGRESS_IDENTITY_MISSING"
        assert not reached

    trusted_state = {
        "ordivon_access_principal": "principal:cf-access:verified",
        "ordivon_access_issuer": "https://trusted.example",
    }
    result, reached = asyncio.run(attempt("work.create", trusted_state, {}))
    assert result["structuredContent"]["ownerReached"] is True
    assert reached  # This is *identity*, not a claim that Owner granted the effect.

    result, reached = asyncio.run(attempt("system.describe", {}, {}))
    assert result["structuredContent"]["ownerReached"] is True
    assert reached


def test_http_server_composes_ingress_guard_and_object_pep() -> None:
    server = build_server(
        service=object(),  # type: ignore[arg-type]
        require_http_execution_identity=True,
        protect_artifact_reads=True,
    )
    chain = [type(m).__name__ for m in server.middleware]
    assert "GatewayHTTPIngressGuard" in chain
    assert "GatewayCapabilityAuthorizationMiddleware" in chain
    assert chain.index("GatewayHTTPIngressGuard") < chain.index(
        "GatewayCapabilityAuthorizationMiddleware"
    )
    plain = build_server(service=object())  # type: ignore[arg-type]
    assert not any(isinstance(m, GatewayHTTPIngressGuard) for m in plain.middleware)


def test_live_mcp_sdk_surface_has_complete_reviewed_security_projection() -> None:
    contract = json.loads(SURFACE.read_text(encoding="utf-8"))
    assert contract["schemaVersion"] == 1
    assert contract["truthBoundary"] == "SOURCE_CONSUMER_ONLY"
    entries = contract["tools"]
    assert len(entries) == len({entry["name"] for entry in entries})
    assert all(entry["downstreamAuthorization"] == "UNKNOWN" for entry in entries)

    async def scenario() -> list[str]:
        async with Client(build_server(), raise_exceptions=True) as client:
            listed = await client.list_tools()
            return sorted(tool.name for tool in listed.tools)

    actual = asyncio.run(scenario())
    assert sorted(entry["name"] for entry in entries) == actual
    assert actual == json.loads((ROOT / "mcp-surface.json").read_text())["tools"]

    for entry in entries:
        name = entry["name"]
        assert entry["httpIngress"] == (
            "public-metadata" if name in PUBLIC_METADATA_TOOLS else "verified-principal"
        )
        assert needs_verified_ingress(name) == (name not in PUBLIC_METADATA_TOOLS)
        assert entry["gatewayObjectPep"] == (
            "runtime-artifact-authzen" if name == "artifact.read" else "none"
        )
        assert entry["routeOwner"] in {"gateway", "host", "runtime", "skills"}
        assert entry["operation"] in {"metadata", "read", "write", "execute"}
        if entry["operation"] in {"write", "execute"}:
            assert entry["httpIngress"] == "verified-principal"

    assert {e["name"] for e in entries if e["httpIngress"] == "public-metadata"} == (
        PUBLIC_METADATA_TOOLS
    )


def test_real_mcp_tool_call_rejects_host_without_http_identity() -> None:
    async def scenario():
        # Exercise actual registered MCP Tool/Middleware, not a mocked decorator.
        async with Client(
            build_server(
                service=object(),  # type: ignore[arg-type]
                require_http_execution_identity=True,
                protect_artifact_reads=True,
            ),
            raise_exceptions=False,
        ) as client:
            return await client.call_tool(
                "work.create",
                {
                    "workRef": "test",
                    "workKind": "test",
                    "actorRef": "a",
                    "initialSnapshot": {},
                },
            )

    result = asyncio.run(scenario())
    assert result.is_error is True
    assert result.structured_content["error"]["code"] == "HTTP_INGRESS_IDENTITY_MISSING"


def test_exhaustive_tool_surface_denies_all_unverified_protected_calls() -> None:
    """Finite, exact released tool-set property; no implied Owner/PDP proof."""
    entries = json.loads(SURFACE.read_text(encoding="utf-8"))["tools"]
    guard = GatewayHTTPIngressGuard()

    async def scenario(name: str, state: dict[str, Any]):
        touched = False

        async def owner(_ctx):
            nonlocal touched
            touched = True
            return await _call_next(_ctx)

        result = await guard(
            _ctx(
                name,
                state=state,
                arguments={
                    "ordivon_access_principal": "forged-by-tool",
                    "_meta": {"ordivon_access_issuer": "forged-by-tool"},
                },
            ),
            owner,
        )
        return result, touched

    malformed_states = (
        {},
        {"ordivon_access_principal": "forged"},
        {"ordivon_access_principal": 123, "ordivon_access_issuer": "issuer"},
        {"ordivon_access_principal": "principal", "ordivon_access_issuer": ""},
    )
    for entry in entries:
        if entry["httpIngress"] == "public-metadata":
            continue
        for state in malformed_states:
            result, reached = asyncio.run(scenario(entry["name"], state))
            assert result.is_error is True, entry["name"]
            assert result.structured_content["error"]["code"] == "HTTP_INGRESS_IDENTITY_MISSING"
            assert not reached, entry["name"]


def test_guard_forwards_non_tool_methods_without_interference() -> None:
    guard = GatewayHTTPIngressGuard()
    ctx = _ctx("work.create")
    ctx.method = "tools/list"
    forwarded = asyncio.run(guard(ctx, _call_next))
    assert forwarded["structuredContent"]["ownerReached"] is True
