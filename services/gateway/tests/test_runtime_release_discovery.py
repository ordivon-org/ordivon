"""Agent discovery of Linux release without claiming a production release grant."""

from __future__ import annotations

import asyncio
from copy import deepcopy
from typing import Any

import pytest
from mcp import Client

from ordivon_gateway.mcp_server import build_server
from ordivon_gateway.service import GatewayService


class ReleaseOwner:
    def __init__(self, *, configured: bool = True) -> None:
        self.configured = configured
        self.calls: list[tuple[str, str, dict[str, Any]]] = []
        self.description: dict[str, Any] = {
            "schemaVersion": 1,
            "node": {"nodeId": "linux-pg", "native": True, "platform": "linux"},
            "structuredReleaseConfigured": True,
            "targets": [
                {"target": "local_linux", "configured": True, "available": True},
            ],
        }

    def is_configured(self, owner: str) -> bool:
        return self.configured and owner == "runtime.linux"

    def configuration_error(self, owner: str) -> str | None:
        return None if self.is_configured(owner) else "owner endpoint missing"

    async def call_tool(self, owner: str, tool: str, args: dict[str, Any]) -> dict[str, Any]:
        self.calls.append((owner, tool, args))
        assert (owner, tool) == ("runtime.linux", "runtime.describe")
        return deepcopy(self.description)


async def _probe(owner: ReleaseOwner):
    service = GatewayService(owner)
    discovery = await service.capability_search(
        query="release",
        category="release",
        owner_id="runtime.linux",
        limit=5,
    )
    described = await service.capability_describe("runtime.release.linux")
    return discovery, described, service.system_describe()


def test_release_discovery_is_read_only_and_source_status_is_not_a_grant() -> None:
    owner = ReleaseOwner()
    searched, described, system = asyncio.run(_probe(owner))
    assert searched.total_matches == 1
    entry = searched.matches[0]
    assert entry.capability.capability == "runtime.release.linux"
    assert entry.capability.category == "release"
    assert entry.match_kind in {"token", "substring", "prefix"}
    assert "runtime.release.linux" in system.capabilities
    found = described.capabilities[0]
    assert found.configured is True
    assert found.available is False
    assert found.readiness_state == "unknown"
    assert found.owner_node_id == "linux-pg"
    assert "Security" in found.observation_error
    assert found.context_mode == "none"
    assert [tool for _, tool, _ in owner.calls] == ["runtime.describe", "runtime.describe"]
    assert all(args == {"schemaVersion": 1} for _, _, args in owner.calls)


def test_unconfigured_runtime_release_is_listed_without_owner_rpc() -> None:
    owner = ReleaseOwner(configured=False)
    searched, described, _ = asyncio.run(_probe(owner))
    assert searched.total_matches == 1
    found = described.capabilities[0]
    assert found.configured is False
    assert found.available is False
    assert found.observation_error == "owner endpoint missing"
    assert owner.calls == []


@pytest.mark.parametrize(
    "change",
    [
        {"node": {"nodeId": "other-linux", "platform": "linux", "native": True}},
        {"node": {"nodeId": "linux-pg", "platform": "windows", "native": True}},
        {"node": {"nodeId": "linux-pg", "platform": "linux", "native": "true"}},
        {"structuredReleaseConfigured": "true"},
        {"structuredReleaseConfigured": 1},
        {"schemaVersion": "1"},
        {
            "targets": [
                {"target": "local_linux", "configured": True, "available": True},
                {"target": "local_linux", "configured": False, "available": False},
            ]
        },
        {"targets": [{"target": "local_linux", "configured": "true", "available": True}]},
        {"targets": [{"target": "local_linux", "configured": False, "available": True}]},
        {"targets": [{"target": "other", "configured": True, "available": True}]},
    ],
)
def test_malformed_release_observation_is_unknown_not_false_or_ready(change: dict) -> None:
    owner = ReleaseOwner()
    owner.description.update(change)
    result = asyncio.run(
        GatewayService(owner).capability_describe("runtime.release.linux")
    ).capabilities[0]
    assert result.available is False
    assert result.configured is False
    assert result.readiness_state == "unknown"
    assert result.observation_error


def test_runtime_explicitly_disabled_release_is_not_ready_not_unknown() -> None:
    owner = ReleaseOwner()
    owner.description["structuredReleaseConfigured"] = False
    result = asyncio.run(
        GatewayService(owner).capability_describe("runtime.release.linux")
    ).capabilities[0]
    assert result.configured is False
    assert result.available is False
    assert result.readiness_state == "not_ready"
    assert result.observation_error is None


def test_mcp_native_public_discovery_works_without_deployment_commands() -> None:
    owner = ReleaseOwner()

    async def verify():
        async with Client(
            build_server(service=GatewayService(owner)), raise_exceptions=True
        ) as client:
            listed = await client.list_tools()
            assert "capability.search" in {t.name for t in listed.tools}
            assert "runtime.release.apply" in {t.name for t in listed.tools}
            found = await client.call_tool(
                "capability.search",
                {"query": "runtime.release.linux", "category": "release"},
            )
            assert found.is_error is False
            content = found.structured_content
            assert content["matches"][0]["capability"]["capability"] == "runtime.release.linux"
            assert content["matches"][0]["capability"]["available"] is False
            assert "ReleaseEffect" in content["matches"][0]["capability"]["truth_boundary"]

    asyncio.run(verify())
    assert [tool for _, tool, _ in owner.calls] == ["runtime.describe"]


def test_runtime_release_requires_real_configured_linux_target() -> None:
    owner = ReleaseOwner()
    owner.description["targets"] = [
        {"target": "local_linux", "configured": False, "available": False}
    ]
    result = asyncio.run(
        GatewayService(owner).capability_describe("runtime.release.linux")
    ).capabilities[0]
    assert result.configured is False
    assert result.available is False
    assert result.readiness_state == "not_ready"
    assert result.observation_error is None


def test_runtime_release_target_true_configured_false_availability_is_not_an_allow() -> None:
    owner = ReleaseOwner()
    owner.description["targets"] = [
        {"target": "local_linux", "configured": True, "available": False}
    ]
    result = asyncio.run(
        GatewayService(owner).capability_describe("runtime.release.linux")
    ).capabilities[0]
    assert result.configured is True
    assert result.available is False
    assert result.readiness_state == "unknown"
