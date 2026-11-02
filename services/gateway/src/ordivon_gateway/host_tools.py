"""Host MCP registration only: owner-derived Work, Space and Attention tools.

Registration is distinct from Gateway's own execution/discovery tools.
This module owns no Host persistence, scheduling, or authorization truth.
"""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import Annotated, Any, Literal

from mcp.server import MCPServer
from pydantic import Field

from .service import GatewayService

HostCollectionBytes = Annotated[int, Field(ge=16_384, le=4_194_304)]
HostMessageBytes = Annotated[int, Field(ge=131_072, le=4_194_304)]


def register_host_tools(
    server: MCPServer,
    gateway: GatewayService,
    owner_boundary: Callable[[Awaitable[Any]], Awaitable[Any]],
) -> None:
    async def _host(tool_name: str, arguments: dict[str, Any]) -> Any:
        return await owner_boundary(gateway.social_work_call(tool_name, arguments))

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

    @server.tool(name="space.create")
    async def space_create(
        spaceRef: str, purpose: str, actorRef: str, subjectRefs: list[str] | None = None
    ) -> dict[str, Any]:
        return await _host(
            "space.create",
            {
                "spaceRef": spaceRef,
                "purpose": purpose,
                "actorRef": actorRef,
                "subjectRefs": subjectRefs,
            },
        )

    @server.tool(name="space.get")
    async def space_get(
        spaceRef: str,
        participantLimit: int = 200,
        topicLimit: int = 200,
        maxBytes: Annotated[int, Field(ge=1_048_576, le=4_194_304)] = 2_097_152,
    ) -> dict[str, Any]:
        return await _host(
            "space.get",
            {
                "spaceRef": spaceRef,
                "participantLimit": participantLimit,
                "topicLimit": topicLimit,
                "maxBytes": maxBytes,
            },
        )

    @server.tool(name="space.list")
    async def space_list(
        actorRef: str | None = None,
        subjectRef: str | None = None,
        limit: int = 50,
        beforeCreatedAt: str | None = None,
        beforeSpaceRef: str | None = None,
        maxBytes: HostCollectionBytes = 262_144,
    ) -> dict[str, Any]:
        return await _host(
            "space.list",
            {
                "actorRef": actorRef,
                "subjectRef": subjectRef,
                "limit": limit,
                "beforeCreatedAt": beforeCreatedAt,
                "beforeSpaceRef": beforeSpaceRef,
                "maxBytes": maxBytes,
            },
        )

    @server.tool(name="space.subject.list")
    async def space_subject_list(
        spaceRef: str,
        afterSubjectRef: str | None = None,
        limit: int = 100,
        maxBytes: HostCollectionBytes = 262_144,
    ) -> dict[str, Any]:
        return await _host(
            "space.subject.list",
            {
                "spaceRef": spaceRef,
                "afterSubjectRef": afterSubjectRef,
                "limit": limit,
                "maxBytes": maxBytes,
            },
        )

    @server.tool(name="space.participation.list")
    async def space_participation_list(
        spaceRef: str,
        afterActorRef: str | None = None,
        limit: int = 100,
        maxBytes: HostCollectionBytes = 262_144,
    ) -> dict[str, Any]:
        return await _host(
            "space.participation.list",
            {
                "spaceRef": spaceRef,
                "afterActorRef": afterActorRef,
                "limit": limit,
                "maxBytes": maxBytes,
            },
        )

    @server.tool(name="space.participation.set")
    async def space_participation_set(
        spaceRef: str, actorRef: str, standing: Literal["joined", "left", "observer"]
    ) -> dict[str, Any]:
        return await _host(
            "space.participation.set",
            {
                "spaceRef": spaceRef,
                "actorRef": actorRef,
                "standing": standing,
            },
        )

    @server.tool(name="topic.create")
    async def topic_create(
        topicRef: str, spaceRef: str, title: str, actorRef: str
    ) -> dict[str, Any]:
        return await _host(
            "topic.create",
            {
                "topicRef": topicRef,
                "spaceRef": spaceRef,
                "title": title,
                "actorRef": actorRef,
            },
        )

    @server.tool(name="topic.list")
    async def topic_list(
        spaceRef: str,
        afterTopicRef: str | None = None,
        limit: int = 100,
        maxBytes: HostCollectionBytes = 262_144,
    ) -> dict[str, Any]:
        return await _host(
            "topic.list",
            {
                "spaceRef": spaceRef,
                "afterTopicRef": afterTopicRef,
                "limit": limit,
                "maxBytes": maxBytes,
            },
        )

    @server.tool(name="topic.cursor.get")
    async def topic_cursor_get(actorRef: str, topicRef: str) -> dict[str, Any]:
        return await _host("topic.cursor.get", {"actorRef": actorRef, "topicRef": topicRef})

    @server.tool(name="topic.cursor.ack")
    async def topic_cursor_ack(actorRef: str, topicRef: str, cursor: int) -> dict[str, Any]:
        return await _host(
            "topic.cursor.ack", {"actorRef": actorRef, "topicRef": topicRef, "cursor": cursor}
        )

    @server.tool(name="topic.resume")
    async def topic_resume(
        topicRef: str,
        afterSequence: int = 0,
        limit: int = 50,
        maxBytes: Annotated[int, Field(ge=131_072, le=4_194_304)] = 524_288,
    ) -> dict[str, Any]:
        return await _host(
            "topic.resume",
            {
                "topicRef": topicRef,
                "afterSequence": afterSequence,
                "limit": limit,
                "maxBytes": maxBytes,
            },
        )

    @server.tool(name="message.post")
    async def message_post(
        messageRef: str,
        spaceRef: str,
        topicRef: str,
        authorActorRef: str,
        body: str,
        recordedAtMs: int,
        messageKind: Literal[
            "note", "question", "proposal", "warning", "finding", "handoff"
        ] = "note",
    ) -> dict[str, Any]:
        return await _host(
            "message.post",
            {
                "messageRef": messageRef,
                "spaceRef": spaceRef,
                "topicRef": topicRef,
                "authorActorRef": authorActorRef,
                "body": body,
                "recordedAtMs": recordedAtMs,
                "messageKind": messageKind,
            },
        )

    @server.tool(name="message.search")
    async def message_search(
        query: str,
        spaceRef: str | None = None,
        topicRef: str | None = None,
        beforeSequence: int | None = None,
        limit: int = 50,
        maxBytes: HostMessageBytes = 524_288,
    ) -> dict[str, Any]:
        return await _host(
            "message.search",
            {
                "query": query,
                "spaceRef": spaceRef,
                "topicRef": topicRef,
                "beforeSequence": beforeSequence,
                "limit": limit,
                "maxBytes": maxBytes,
            },
        )

    @server.tool(name="message.relation.add")
    async def message_relation_add(
        sourceMessageRef: str,
        relation: Literal[
            "reply_to", "mentions", "references", "acknowledges", "supersedes", "about"
        ],
        targetRef: str,
        actorRef: str,
    ) -> dict[str, Any]:
        return await _host(
            "message.relation.add",
            {
                "sourceMessageRef": sourceMessageRef,
                "relation": relation,
                "targetRef": targetRef,
                "actorRef": actorRef,
            },
        )

    @server.tool(name="message.relation.list")
    async def message_relation_list(
        messageRef: str,
        direction: Literal["outgoing", "incoming", "both"] = "both",
        relation: Literal[
            "reply_to", "mentions", "references", "acknowledges", "supersedes", "about"
        ]
        | None = None,
        afterChangeSequence: int = 0,
        limit: int = 100,
        maxBytes: HostCollectionBytes = 262_144,
    ) -> dict[str, Any]:
        return await _host(
            "message.relation.list",
            {
                "messageRef": messageRef,
                "direction": direction,
                "relation": relation,
                "afterChangeSequence": afterChangeSequence,
                "limit": limit,
                "maxBytes": maxBytes,
            },
        )

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
