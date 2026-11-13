"""Real SDK proof for the lean public projection and existing Host PEP."""

from __future__ import annotations

import asyncio
import json
from pathlib import Path
from typing import Any

import pytest
from mcp import Client

from ordivon_gateway.http_ingress_guard import GatewayHTTPIngressGuard
from ordivon_gateway.mcp_server import build_server
from ordivon_gateway.service import GatewayService
from ordivon_gateway.tool_visibility import CORE_PUBLIC_TOOLS

ROOT = Path(__file__).resolve().parents[1]


class HostOwner:
    def __init__(self) -> None:
        self.calls: list[tuple[str, str, dict[str, Any]]] = []

    async def call_tool(self, owner_id: str, tool_name: str, arguments: dict[str, Any]):
        self.calls.append((owner_id, tool_name, arguments))
        return {"ownerTool": tool_name, "arguments": arguments}


async def _names(surface: str) -> set[str]:
    async with Client(build_server(surface=surface), raise_exceptions=True) as client:
        return {tool.name for tool in (await client.list_tools()).tools}


def test_core_is_exact_subset_of_live_sdk_full_surface() -> None:
    full = asyncio.run(_names("full"))
    core = asyncio.run(_names("core"))
    assert len(full) == 38
    assert core == CORE_PUBLIC_TOOLS
    assert len(core) == 17
    assert core < full
    assert full == set(json.loads((ROOT / "mcp-surface.json").read_text())["tools"])
    assert core == set(json.loads((ROOT / "mcp-surface-core.json").read_text())["tools"])
    assert {
        "actor.declare",
        "host.status",
        "space.participation.set",
        "topic.cursor.ack",
        "subscription.follow",
        "capability.resolve",
    } <= full - core


def test_core_retains_exact_host_owner_calls_and_hides_internal_tools() -> None:
    owner = HostOwner()

    async def scenario():
        async with Client(
            build_server(GatewayService(owner), surface="core"), raise_exceptions=False
        ) as client:
            get = await client.call_tool("work.get", {"workRef": "work:sample", "revision": 2})
            search = await client.call_tool("message.search", {"query": "Gateway"})
            hidden = await client.call_tool(
                "space.participation.set",
                {"spaceRef": "space:sample", "actorRef": "actor:sample", "standing": "joined"},
            )
            return get, search, hidden

    get, search, hidden = asyncio.run(scenario())
    assert not get.is_error
    assert get.structured_content["ownerTool"] == "work.get"
    assert not search.is_error
    assert search.structured_content["ownerTool"] == "message.search"
    assert hidden.is_error
    assert owner.calls == [
        ("host", "work.get", {"workRef": "work:sample", "revision": 2}),
        (
            "host",
            "message.search",
            {
                "query": "Gateway",
                "spaceRef": None,
                "topicRef": None,
                "beforeSequence": None,
                "limit": 50,
                "maxBytes": 524288,
            },
        ),
    ]


def test_core_http_host_access_requires_verified_ingress_and_object_pep() -> None:
    owner = HostOwner()
    server = build_server(
        GatewayService(owner),
        surface="core",
        require_http_execution_identity=True,
        protect_artifact_reads=True,
    )
    assert any(isinstance(m, GatewayHTTPIngressGuard) for m in server.middleware)

    async def scenario():
        async with Client(server, raise_exceptions=False) as client:
            host = await client.call_tool("work.get", {"workRef": "work:sample"})
            missing = await client.call_tool(
                "topic.cursor.ack",
                {"actorRef": "actor:sample", "topicRef": "topic:sample", "cursor": 1},
            )
            return host, missing

    host, missing = asyncio.run(scenario())
    assert host.is_error
    assert host.structured_content["error"]["code"] == "HTTP_INGRESS_IDENTITY_MISSING"
    assert missing.is_error
    assert not owner.calls


@pytest.mark.parametrize("invalid", ["other", "auto", ""])
def test_unknown_surface_profile_is_rejected(invalid: str) -> None:
    with pytest.raises(ValueError, match="Gateway surface"):
        build_server(surface=invalid)  # type: ignore[arg-type]


def test_core_sdk_schema_digest_matches_release_manifest() -> None:
    from importlib.util import module_from_spec, spec_from_file_location

    spec = spec_from_file_location(
        "gateway_core_sdk_verifier", ROOT / "packaging/windows/verify_release.py"
    )
    assert spec is not None and spec.loader is not None
    module = module_from_spec(spec)
    spec.loader.exec_module(module)
    manifest = json.loads((ROOT / "mcp-surface-core.json").read_text())

    async def verify():
        async with Client(build_server(surface="core"), raise_exceptions=True) as client:
            return module.native_tool_contract_digest((await client.list_tools()).tools)

    assert manifest["contractDigest"] == asyncio.run(verify())
    assert (
        manifest["surfaceEpoch"]
        > json.loads((ROOT / "mcp-surface.json").read_text())["surfaceEpoch"]
    )


def test_release_preflight_checks_explicit_core_profile() -> None:
    installer = (ROOT / "packaging/install_release.sh").read_text()
    verifier = (ROOT / "packaging/windows/verify_release.py").read_text()
    assert "ORDIVON_GATEWAY_SURFACE_PROFILE" in installer
    assert "mcp-surface-core.json" in installer
    assert "mcp-surface-core.json" in verifier
    assert "build_server(surface=SURFACE_PROFILE)" in verifier
