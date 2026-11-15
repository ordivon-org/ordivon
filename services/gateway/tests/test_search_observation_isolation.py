"""Capability search observes only matching Owners; routes are not readiness truth."""

from __future__ import annotations

import asyncio
from dataclasses import replace
from typing import Any

from ordivon_gateway.capability_projection import project_capability_search
from ordivon_gateway.routing import default_routes
from ordivon_gateway.service import GatewayService


class ProbingCaller:
    def __init__(self) -> None:
        self.calls: list[tuple[str, str]] = []
        self.linux_available = True
        self.fail_windows = False

    def is_configured(self, owner: str) -> bool:
        return owner in {"runtime.linux", "runtime.windows", "host"}

    async def call_tool(self, owner: str, tool: str, args: dict[str, Any]) -> dict[str, Any]:
        self.calls.append((owner, tool))
        if owner == "runtime.windows" and self.fail_windows:
            await asyncio.Event().wait()
        if owner == "host":
            return {"schemaVersion": 3, "kind": "ordivon.host-status"}
        return {
            "node": {"nodeId": owner},
            "targets": [
                {
                    "target": "local_linux" if owner == "runtime.linux" else "windows_native",
                    "configured": True,
                    "available": self.linux_available if owner == "runtime.linux" else True,
                    "executionProfiles": ["trusted_local"],
                }
            ],
        }


def test_research_and_no_match_discovery_never_probe_unrelated_owners() -> None:
    async def verify() -> None:
        caller = ProbingCaller()
        caller.fail_windows = True
        svc = GatewayService(caller, projection_timeout_seconds=0.02)
        research = await asyncio.wait_for(
            svc.capability_search(query="research", include_unavailable=False),
            timeout=0.15,
        )
        assert research.total_matches > 0
        assert all(item.capability.readiness_state == "unknown" for item in research.matches)
        assert caller.calls == []
        missing = await asyncio.wait_for(
            svc.capability_search(query="unfindable-capability-xyz"),
            timeout=0.15,
        )
        assert missing.total_matches == 0
        assert missing.matches == []
        assert missing.route_digest == research.route_digest
        assert caller.calls == []

    asyncio.run(verify())


def test_exact_search_observes_only_selected_natural_owner() -> None:
    async def verify() -> None:
        caller = ProbingCaller()
        caller.fail_windows = True
        svc = GatewayService(caller, projection_timeout_seconds=0.02)
        linux = await asyncio.wait_for(
            svc.capability_search(query="execution.linux"),
            timeout=0.15,
        )
        assert [m.capability.capability for m in linux.matches] == ["execution.linux"]
        assert caller.calls == [("runtime.linux", "runtime.describe")]
        caller.calls.clear()
        host = await asyncio.wait_for(
            svc.capability_search(query="continuity.external"),
            timeout=0.15,
        )
        assert [m.capability.capability for m in host.matches] == ["continuity.external"]
        assert caller.calls == [("host", "host.status")]

    asyncio.run(verify())


def test_route_digest_is_stable_across_owner_changes_but_tracks_route_changes() -> None:
    async def verify() -> None:
        caller = ProbingCaller()
        svc = GatewayService(caller)
        first = await svc.capability_describe("execution.linux")
        caller.linux_available = False
        second = await svc.capability_describe("execution.linux")
        assert first.projection_digest != second.projection_digest
        assert first.route_digest == second.route_digest == svc.system_describe().route_digest
        search = await svc.capability_search(
            query="execution.linux",
            include_unavailable=True,
        )
        assert search.route_digest == first.route_digest
        assert search.matches[0].capability.readiness_state == "not_ready"
        hidden = await svc.capability_search(
            query="execution.linux",
            include_unavailable=False,
        )
        assert hidden.total_matches == 0
        routes = default_routes()
        routes["execution.linux"] = replace(
            routes["execution.linux"],
            description="Changed authoritative route metadata",
        )
        other = GatewayService(caller, routes=routes)
        assert other.system_describe().route_digest != svc.system_describe().route_digest

    asyncio.run(verify())


def test_search_matches_original_full_projection_for_query_and_filter_semantics() -> None:
    async def verify() -> None:
        caller = ProbingCaller()
        svc = GatewayService(caller)
        full = await svc.capability_describe()
        for query, category, owner_id, include_unavailable in [
            ("execution.linux", None, None, True),
            ("runtime", None, None, True),
            ("research", "research", None, False),
            ("host", None, "host", False),
            ("nonexistent", None, None, True),
            ("read", None, None, True),
        ]:
            expected = project_capability_search(
                full,
                query=query,
                category=category,
                owner_id=owner_id,
                limit=50,
                include_unavailable=include_unavailable,
            )
            actual = await svc.capability_search(
                query=query,
                category=category,
                owner_id=owner_id,
                limit=50,
                include_unavailable=include_unavailable,
            )
            assert [(m.match_kind, m.capability) for m in actual.matches] == [
                (m.match_kind, m.capability) for m in expected.matches
            ]
            assert actual.total_matches == expected.total_matches

    asyncio.run(verify())


def test_real_mcp_sdk_discovery_surface_does_not_trigger_unmatched_owner_rpc() -> None:
    from mcp import Client

    from ordivon_gateway.mcp_server import build_server

    async def verify() -> None:
        caller = ProbingCaller()
        caller.fail_windows = True
        svc = GatewayService(caller, projection_timeout_seconds=0.02)
        async with Client(build_server(service=svc), raise_exceptions=True) as client:
            listing = await client.list_tools()
            assert "capability.search" in {tool.name for tool in listing.tools}
            route = await asyncio.wait_for(
                client.call_tool("system.describe", {}),
                timeout=0.5,
            )
            assert route.structured_content is not None
            stable = route.structured_content["route_digest"]
            result = await asyncio.wait_for(
                client.call_tool("capability.search", {"query": "research"}),
                timeout=0.5,
            )
            assert not result.is_error
            assert result.structured_content is not None
            assert result.structured_content["route_digest"] == stable
            assert result.structured_content["total_matches"] > 0
            assert caller.calls == []

    asyncio.run(verify())
