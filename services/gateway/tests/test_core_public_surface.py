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
from ordivon_gateway.tool_visibility import (
    COLLABORATION_PUBLIC_TOOLS,
    CORE_PUBLIC_TOOLS,
    project_registered_tools,
)

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


def test_collaboration_specialist_extends_core_without_exposing_administration() -> None:
    full = asyncio.run(_names("full"))
    core = asyncio.run(_names("core"))
    collaboration = asyncio.run(_names("collaboration"))
    assert core == CORE_PUBLIC_TOOLS
    assert collaboration == COLLABORATION_PUBLIC_TOOLS
    assert len(collaboration) == 22
    assert core < collaboration < full
    assert collaboration - core == {
        "actor.declare",
        "space.create",
        "space.get",
        "topic.create",
        "attention.reentry",
    }
    assert (
        set(json.loads((ROOT / "mcp-surface-collaboration.json").read_text())["tools"])
        == collaboration
    )
    assert {"subscription.follow", "topic.cursor.ack", "space.participation.set"} <= (
        full - collaboration
    )


def test_future_registered_tool_is_hidden_in_every_public_profile() -> None:
    """Unknown future Tools must fail closed, even outside the historical 38."""
    owner = HostOwner()
    invoked: list[str] = []

    async def scenario(surface: str):
        server = build_server(GatewayService(owner), surface=surface)

        @server.tool(name="future.experimental.write")
        def future_write() -> dict[str, bool]:
            invoked.append("unexpected-forward")
            return {"effect": True}

        async with Client(server, raise_exceptions=False) as client:
            names = {tool.name for tool in (await client.list_tools()).tools}
            denied = await client.call_tool("future.experimental.write", {})
            return names, denied

    for profile, selected in (
        ("core", CORE_PUBLIC_TOOLS),
        ("collaboration", COLLABORATION_PUBLIC_TOOLS),
    ):
        names, denied = asyncio.run(scenario(profile))
        assert names == selected
        assert denied.is_error
        assert "Unknown tool" in str(denied.content)
    assert invoked == [] and owner.calls == []


def test_public_projection_refuses_missing_required_sdk_registration() -> None:
    from mcp.server import MCPServer

    server = MCPServer("unqualified-projection")
    with pytest.raises(RuntimeError, match="lacks registered tools"):
        asyncio.run(project_registered_tools(server, CORE_PUBLIC_TOOLS))


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
    assert "mcp-surface-collaboration.json" in installer
    assert "mcp-surface-core.json" in verifier
    assert "build_server(surface=SURFACE_PROFILE)" in verifier
    assert "mcp-surface-collaboration.json" in verifier


def test_all_hidden_core_tools_fail_without_reaching_owner() -> None:
    """Exhaustively falsify tool-name guessing against the effective Core SDK."""
    owner = HostOwner()
    full = asyncio.run(_names("full"))
    hidden = sorted(full - CORE_PUBLIC_TOOLS)
    assert len(hidden) == 21

    async def scenario() -> None:
        async with Client(
            build_server(GatewayService(owner), surface="core"), raise_exceptions=False
        ) as client:
            for name in hidden:
                result = await client.call_tool(name, {})
                assert result.is_error, name
                assert "Unknown tool" in str(result.content), name

    asyncio.run(scenario())
    assert owner.calls == []


def test_release_requires_active_profile_qualification(tmp_path: Path) -> None:
    """A two-profile installed release never implies its running public ABI."""
    import os
    import subprocess

    repo = ROOT.parents[1]
    installed = tmp_path / "releases" / "old"
    installed.mkdir(parents=True)
    (installed / "mcp-surface-core.json").write_text("{}")
    (installed / "mcp-surface.json").write_text("{}")
    (tmp_path / "current").symlink_to(installed, target_is_directory=True)
    revision = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=repo, text=True).strip()
    env = os.environ.copy()
    env.pop("ORDIVON_GATEWAY_CURRENT_SURFACE_PROFILE", None)
    env["ORDIVON_GATEWAY_SURFACE_PROFILE"] = "core"
    result = subprocess.run(
        [
            "bash",
            str(ROOT / "packaging/install_release.sh"),
            str(repo),
            revision,
            str(tmp_path),
        ],
        check=False,
        capture_output=True,
        text=True,
        env=env,
    )
    assert result.returncode == 2, (result.stdout, result.stderr)
    assert "require verified ORDIVON_GATEWAY_CURRENT_SURFACE_PROFILE" in result.stderr


def test_collaboration_full_task_lifecycle_uses_only_existing_host_authority() -> None:
    """Ordinary Agent bootstrap / recovery / handoff: one SDK and one Host owner.

    This is an ordered, typed SDK consumer test; it does NOT prove PG Host
    write atomicity, installed Principal grant, or real external client refresh.
    """
    owner = HostOwner()
    actor = "actor:agent:collaboration-source-consumer"
    space = "space:gateway-collaboration-source-consumer"
    topic = "topic:gateway-collaboration-source-consumer"
    work = "work:gateway-collaboration-source-consumer"
    script = [
        ("actor.declare", {"actorRef": actor, "actorKind": "agent"}),
        ("space.create", {"spaceRef": space, "purpose": "Agent review", "actorRef": actor}),
        (
            "topic.create",
            {"topicRef": topic, "spaceRef": space, "title": "Gateway consumer", "actorRef": actor},
        ),
        (
            "work.create",
            {
                "workRef": work,
                "workKind": "audit",
                "actorRef": actor,
                "initialSnapshot": {"phase": "opened"},
            },
        ),
        (
            "message.post",
            {
                "messageRef": "message:gateway-consumer-1",
                "spaceRef": space,
                "topicRef": topic,
                "authorActorRef": actor,
                "body": "Source consumer handoff",
                "recordedAtMs": 1790000000000,
                "messageKind": "handoff",
            },
        ),
        ("space.get", {"spaceRef": space}),
        ("work.get", {"workRef": work}),
        ("attention.reentry", {"actorRef": actor}),
        ("topic.resume", {"topicRef": topic}),
        (
            "work.snapshot.commit",
            {
                "workRef": work,
                "expectedRevision": 1,
                "snapshot": {"phase": "reviewed"},
                "actorRef": actor,
                "continuityDisposition": "continue",
            },
        ),
    ]

    async def scenario():
        async with Client(
            build_server(GatewayService(owner), surface="collaboration"),
            raise_exceptions=False,
        ) as client:
            listed = {t.name for t in (await client.list_tools()).tools}
            assert listed == COLLABORATION_PUBLIC_TOOLS
            results = []
            for name, arguments in script:
                result = await client.call_tool(name, arguments)
                assert not result.is_error, (name, result.content)
                assert result.structured_content["ownerTool"] == name
                results.append(result)
            return results

    assert len(asyncio.run(scenario())) == len(script)
    assert [name for _owner, name, _args in owner.calls] == [name for name, _ in script]
    assert all(route == "host" for route, _name, _args in owner.calls)
    assert owner.calls[1][2]["subjectRefs"] is None
    assert owner.calls[-1][2]["expectedRevision"] == 1
    assert owner.calls[-1][2]["continuityDisposition"] == "continue"
    assert owner.calls[4][2]["authorActorRef"] == actor
