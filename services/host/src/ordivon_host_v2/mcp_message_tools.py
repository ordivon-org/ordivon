from __future__ import annotations

from collections.abc import Callable
from typing import Literal

from mcp.server import MCPServer

from .collaboration_inputs import (
    MessageInput,
    MessageKind,
    MessageRelationInput,
    MessageRelationKind,
)
from .mcp_domain_errors import _project_domain_errors
from .social_contracts import (
    MessageReadResponse,
    MessageRelationResponse,
    MessageRelationsResponse,
    MessageResponse,
    MessageSearchResponse,
)
from .social_store import SocialStore


def register_message_tools(
    mcp: MCPServer,
    social: SocialStore,
    request_id: Callable[[str, object], str],
) -> None:
    """Register native Message MCP tools; SocialStore owns semantics."""

    @mcp.tool(name="message.post")
    @_project_domain_errors
    def message_post(
        messageRef: str,
        spaceRef: str,
        topicRef: str,
        authorActorRef: str,
        body: str,
        recordedAtMs: int,
        messageKind: Literal[
            "note", "question", "proposal", "warning", "finding", "handoff"
        ] = "note",
    ) -> MessageResponse:
        request = {
            "messageRef": messageRef,
            "spaceRef": spaceRef,
            "topicRef": topicRef,
            "authorActorRef": authorActorRef,
            "body": body,
            "recordedAtMs": recordedAtMs,
            "messageKind": messageKind,
        }
        client_request_id = request_id("message-post", request)
        value = MessageInput(
            message_ref=messageRef,
            client_request_id=client_request_id,
            space_ref=spaceRef,
            topic_ref=topicRef,
            author_actor_ref=authorActorRef,
            body=body,
            recorded_at_ms=recordedAtMs,
            message_kind=MessageKind(messageKind),
        )
        return social.post_message(value)

    @mcp.tool(name="message.get")
    @_project_domain_errors
    def message_get(
        messageRef: str,
        expectedDigest: str | None = None,
    ) -> MessageReadResponse:
        return social.get_message(messageRef, expected_digest=expectedDigest)

    @mcp.tool(name="message.search")
    @_project_domain_errors
    def message_search(
        query: str,
        spaceRef: str | None = None,
        topicRef: str | None = None,
        beforeSequence: int | None = None,
        limit: int = 50,
        maxBytes: int = 524_288,
    ) -> MessageSearchResponse:
        return social.search_messages(
            query,
            space_ref=spaceRef,
            topic_ref=topicRef,
            before_sequence=beforeSequence,
            limit=limit,
            max_bytes=maxBytes,
        )

    @mcp.tool(name="message.relation.add")
    @_project_domain_errors
    def message_relation_add(
        sourceMessageRef: str,
        relation: Literal[
            "reply_to", "mentions", "references", "acknowledges", "supersedes", "about"
        ],
        targetRef: str,
        actorRef: str,
    ) -> MessageRelationResponse:
        value = MessageRelationInput(
            source_message_ref=sourceMessageRef,
            relation=MessageRelationKind(relation),
            target_ref=targetRef,
            actor_ref=actorRef,
        )
        return social.add_message_relation(
            value,
            client_request_id=request_id("message-relation-add", value.model_dump(mode="json")),
        )

    @mcp.tool(name="message.relation.list")
    @_project_domain_errors
    def message_relation_list(
        messageRef: str,
        direction: Literal["outgoing", "incoming", "both"] = "both",
        relation: Literal[
            "reply_to", "mentions", "references", "acknowledges", "supersedes", "about"
        ]
        | None = None,
        afterChangeSequence: int = 0,
        limit: int = 100,
        maxBytes: int = 262_144,
    ) -> MessageRelationsResponse:
        return social.list_message_relations(
            messageRef,
            direction=direction,
            relation=None if relation is None else MessageRelationKind(relation),
            after_change_sequence=afterChangeSequence,
            limit=limit,
            max_bytes=maxBytes,
        )
