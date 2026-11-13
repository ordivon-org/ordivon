"""Register Host work tools without owning Host authority."""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import Any, Literal

from mcp.server import MCPServer

from .host_tool_contracts import HostCollectionBytes
from .tool_visibility import expose_tool


def register_host_work_tools(
    server: MCPServer,
    _host: Callable[[str, dict[str, Any]], Awaitable[Any]],
    visible_tools: frozenset[str] | None = None,
) -> None:
    @expose_tool(server, "host.status", visible_tools)
    async def host_status(
        detail: Literal["summary", "integrity", "history"] = "summary",
    ) -> dict[str, Any]:
        return await _host("host.status", {"detail": detail})

    @expose_tool(server, "actor.declare", visible_tools)
    async def actor_declare(
        actorRef: str,
        actorKind: Literal["unknown", "human", "agent", "service", "organization"],
    ) -> dict[str, Any]:
        return await _host("actor.declare", {"actorRef": actorRef, "actorKind": actorKind})

    @expose_tool(server, "work.create", visible_tools)
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

    @expose_tool(server, "work.get", visible_tools)
    async def work_get(workRef: str, revision: int | None = None) -> dict[str, Any]:
        return await _host("work.get", {"workRef": workRef, "revision": revision})

    @expose_tool(server, "work.list", visible_tools)
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

    @expose_tool(server, "work.snapshot.commit", visible_tools)
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
