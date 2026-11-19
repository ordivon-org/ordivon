"""Shared Host MCP wire byte-budget boundaries."""

from __future__ import annotations

from typing import Annotated

from pydantic import Field

HostCollectionBytes = Annotated[int, Field(ge=16_384, le=4_194_304)]
HostMessageBytes = Annotated[int, Field(ge=131_072, le=4_194_304)]


# Single static allowlist for Host semantic tools. Security authorization remains separate.
SOCIAL_WORK_HOST_TOOLS = frozenset(
    {
        "host.status",
        "actor.declare",
        "work.create",
        "work.get",
        "work.list",
        "work.snapshot.commit",
        "space.create",
        "space.get",
        "space.list",
        "space.participation.set",
        "space.participation.list",
        "space.subject.list",
        "topic.create",
        "topic.cursor.ack",
        "topic.cursor.get",
        "topic.list",
        "topic.state.set",
        "topic.resume",
        "message.get",
        "message.post",
        "message.search",
        "message.relation.add",
        "message.relation.list",
        "subscription.follow",
        "subscription.list",
        "subscription.unfollow",
        "attention.get",
        "attention.delta",
        "attention.ack",
        "attention.reentry",
    }
)
