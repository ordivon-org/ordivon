"""Register Host attention tools without owning Host authority."""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import Any, Literal

from mcp.server import MCPServer

from .host_tool_contracts import HostCollectionBytes


def register_host_attention_tools(
    server: MCPServer,
    _host: Callable[[str, dict[str, Any]], Awaitable[Any]],
) -> None:
    @server.tool(name="subscription.follow")
    async def subscription_follow(
        actorRef: str, targetKind: Literal["work", "space", "topic"], targetRef: str
    ) -> dict[str, Any]:
        return await _host(
            "subscription.follow",
            {
                "actorRef": actorRef,
                "targetKind": targetKind,
                "targetRef": targetRef,
            },
        )

    @server.tool(name="subscription.list")
    async def subscription_list(
        actorRef: str,
        targetKind: Literal["work", "space", "topic"] | None = None,
        afterTargetKind: str | None = None,
        afterTargetRef: str | None = None,
        limit: int = 200,
        maxBytes: HostCollectionBytes = 262_144,
    ) -> dict[str, Any]:
        return await _host(
            "subscription.list",
            {
                "actorRef": actorRef,
                "targetKind": targetKind,
                "afterTargetKind": afterTargetKind,
                "afterTargetRef": afterTargetRef,
                "limit": limit,
                "maxBytes": maxBytes,
            },
        )

    @server.tool(name="subscription.unfollow")
    async def subscription_unfollow(
        actorRef: str, targetKind: Literal["work", "space", "topic"], targetRef: str
    ) -> dict[str, Any]:
        return await _host(
            "subscription.unfollow",
            {
                "actorRef": actorRef,
                "targetKind": targetKind,
                "targetRef": targetRef,
            },
        )

    @server.tool(name="attention.get")
    async def attention_get(
        actorRef: str, limit: int = 100, maxBytes: HostCollectionBytes = 262_144
    ) -> dict[str, Any]:
        return await _host(
            "attention.get", {"actorRef": actorRef, "limit": limit, "maxBytes": maxBytes}
        )

    @server.tool(name="attention.delta")
    async def attention_delta(
        actorRef: str, afterSequence: int, limit: int = 100, maxBytes: HostCollectionBytes = 262_144
    ) -> dict[str, Any]:
        return await _host(
            "attention.delta",
            {
                "actorRef": actorRef,
                "afterSequence": afterSequence,
                "limit": limit,
                "maxBytes": maxBytes,
            },
        )

    @server.tool(name="attention.reentry")
    async def attention_reentry(
        actorRef: str,
        afterSequence: int | None = None,
        limit: int = 100,
        maxBytes: HostCollectionBytes = 262_144,
    ) -> dict[str, Any]:
        return await _host(
            "attention.reentry",
            {
                "actorRef": actorRef,
                "afterSequence": afterSequence,
                "limit": limit,
                "maxBytes": maxBytes,
            },
        )

    @server.tool(name="attention.ack")
    async def attention_ack(actorRef: str, cursor: int) -> dict[str, Any]:
        return await _host("attention.ack", {"actorRef": actorRef, "cursor": cursor})
