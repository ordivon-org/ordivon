"""Register Host work tools without owning Host authority."""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import Any, Literal

from mcp.server import MCPServer

from .host_tool_contracts import HostCollectionBytes


def register_host_work_tools(
    server: MCPServer,
    _host: Callable[[str, dict[str, Any]], Awaitable[Any]],
    *,
    register_engagement: bool = False,
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

    # Versioned accountability tools are only registered by Gateway when
    # verified HTTP ingress AND an installed Security authorizer are present.
    # Legacy stdio/default Gateway must not expose an unauthenticated direct
    # route for callers to claim the consumer ActorRef themselves.
    if register_engagement:

        @server.tool(name="work.engagement.advance")
        async def work_engagement_advance(
            workRef: str,
            expectedRevision: int,
            actorRef: str,
            action: dict[str, Any],
            clientRequestId: str,
        ) -> dict[str, Any]:
            # Never copy Work state transitions or accept policy in Gateway.
            # The Rust owner validates the typed EngagementAction; Gateway's
            # existing AuthZEN PEP verifies the Principal/Actor/Work/action.
            return await _host(
                "work.engagement.advance",
                {
                    "workRef": workRef,
                    "expectedRevision": expectedRevision,
                    "actorRef": actorRef,
                    "action": action,
                    "clientRequestId": clientRequestId,
                },
            )

        @server.tool(name="work.engagement.list")
        async def work_engagement_list(
            phase: Literal["offered", "claimed", "submitted", "returned", "accepted", "cancelled"]
            | None = None,
            assigneeActorRef: str | None = None,
            consumerActorRef: str | None = None,
            limit: int = 50,
            maxBytes: HostCollectionBytes = 262_144,
            beforeUpdatedAt: str | None = None,
            beforeWorkRef: str | None = None,
        ) -> dict[str, Any]:
            return await _host(
                "work.engagement.list",
                {
                    "phase": phase,
                    "assigneeActorRef": assigneeActorRef,
                    "consumerActorRef": consumerActorRef,
                    "limit": limit,
                    "maxBytes": maxBytes,
                    "beforeUpdatedAt": beforeUpdatedAt,
                    "beforeWorkRef": beforeWorkRef,
                },
            )
