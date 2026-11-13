"""Register Host work tools without owning Host authority."""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import Any, Literal

from mcp.server import MCPServer

from .host_tool_contracts import HostCollectionBytes


def register_host_work_tools(
    server: MCPServer,
    _host: Callable[[str, dict[str, Any]], Awaitable[Any]],
) -> None:
    @server.tool(name="host.status")
    async def host_status(
        detail: Literal["summary", "integrity", "history"] = "summary",
    ) -> dict[str, Any]:
        return await _host("host.status", {"detail": detail})

    @server.tool(name="actor.declare")
    async def actor_declare(
        actorRef: str,
        actorKind: Literal["unknown", "human", "agent", "service", "organization"],
    ) -> dict[str, Any]:
        return await _host("actor.declare", {"actorRef": actorRef, "actorKind": actorKind})

    @server.tool(name="work.create")
    async def work_create(
        workRef: str, workKind: str, actorRef: str, initialSnapshot: dict[str, Any]
    ) -> dict[str, Any]:
        return await _host(
            "work.create",
            {
                "workRef": workRef,
                "workKind": workKind,
                "actorRef": actorRef,
                "initialSnapshot": initialSnapshot,
            },
        )

    @server.tool(name="work.get")
    async def work_get(workRef: str, revision: int | None = None) -> dict[str, Any]:
        return await _host("work.get", {"workRef": workRef, "revision": revision})

    @server.tool(name="work.list")
    async def work_list(
        state: Literal["open", "completed", "abandoned"] | None = None,
        limit: int = 50,
        beforeUpdatedAt: str | None = None,
        beforeWorkRef: str | None = None,
        maxBytes: HostCollectionBytes = 262_144,
    ) -> dict[str, Any]:
        return await _host(
            "work.list",
            {
                "state": state,
                "limit": limit,
                "beforeUpdatedAt": beforeUpdatedAt,
                "beforeWorkRef": beforeWorkRef,
                "maxBytes": maxBytes,
            },
        )

    @server.tool(name="work.snapshot.commit")
    async def work_snapshot_commit(
        workRef: str,
        expectedRevision: int,
        snapshot: dict[str, Any],
        actorRef: str,
        continuityDisposition: Literal["continue", "complete", "abandon"] = "continue",
    ) -> dict[str, Any]:
        return await _host(
            "work.snapshot.commit",
            {
                "workRef": workRef,
                "expectedRevision": expectedRevision,
                "snapshot": snapshot,
                "actorRef": actorRef,
                "continuityDisposition": continuityDisposition,
            },
        )
