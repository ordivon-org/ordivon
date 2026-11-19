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


# Canonical Host query selectors describe *wire semantics*, not grants.
# Security consumes these same fields for its independently enforced PDP.
# A new Host tool is treated as a write until explicitly registered here.
HOST_READ_SELECTORS: dict[str, tuple[str, ...]] = {
    "host.status": (),
    "work.get": ("workRef",),
    "work.list": (),
    "space.get": ("spaceRef",),
    "space.list": ("actorRef", "subjectRef"),
    "space.participation.list": ("spaceRef",),
    "space.subject.list": ("spaceRef",),
    "topic.cursor.get": ("actorRef", "topicRef"),
    "topic.list": ("spaceRef",),
    "topic.resume": ("topicRef",),
    "message.get": ("messageRef",),
    "message.search": ("spaceRef", "topicRef"),
    "message.relation.list": ("messageRef",),
    "subscription.list": ("actorRef",),
    "attention.get": ("actorRef",),
    "attention.delta": ("actorRef",),
    "attention.reentry": ("actorRef",),
}


HOST_READ_TOOLS = frozenset(HOST_READ_SELECTORS)
assert HOST_READ_TOOLS <= SOCIAL_WORK_HOST_TOOLS


def host_read_transport_route(caller: object) -> str:
    """Optional same-Host read endpoint, never a new semantic Owner.

    Only the real transport declares routes; fake/test callers without this
    optional method continue using the original Host endpoint.
    """
    declared = getattr(caller, "has_route", None)
    return "host.read" if callable(declared) and declared("host.read") else "host"
