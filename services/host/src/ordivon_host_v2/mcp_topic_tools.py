from __future__ import annotations

from collections.abc import Callable
from typing import Literal

from mcp.server import MCPServer

from .collaboration_inputs import (
    TopicInput,
)
from .mcp_domain_errors import _project_domain_errors
from .social_contracts import (
    TopicCursorResponse,
    TopicListResponse,
    TopicResponse,
    TopicResumeResponse,
)
from .social_store import SocialStore


def register_topic_tools(
    mcp: MCPServer,
    social: SocialStore,
    request_id: Callable[[str, object], str],
) -> None:
    """Register native Topic MCP tools; SocialStore owns semantics."""

    @mcp.tool(name="topic.create")
    @_project_domain_errors
    def topic_create(topicRef: str, spaceRef: str, title: str, actorRef: str) -> TopicResponse:
        value = TopicInput(
            topic_ref=topicRef,
            space_ref=spaceRef,
            title=title,
            actor_ref=actorRef,
        )
        return social.create_topic(
            value,
            client_request_id=request_id("topic-create", value.model_dump(mode="json")),
        )

    @mcp.tool(name="topic.state.set")
    @_project_domain_errors
    def topic_state_set(
        topicRef: str,
        actorRef: str,
        state: Literal["open", "closed"],
        expectedState: Literal["open", "closed"],
        expectedHighSequence: int,
    ) -> TopicResponse:
        request = {
            "topicRef": topicRef,
            "actorRef": actorRef,
            "state": state,
            "expectedState": expectedState,
            "expectedHighSequence": expectedHighSequence,
        }
        return social.set_topic_state(
            topic_ref=topicRef,
            actor_ref=actorRef,
            state=state,
            expected_state=expectedState,
            expected_high_sequence=expectedHighSequence,
            client_request_id=request_id("topic-state-set", request),
        )

    @mcp.tool(name="topic.list")
    @_project_domain_errors
    def topic_list(
        spaceRef: str,
        afterTopicRef: str | None = None,
        limit: int = 100,
        maxBytes: int = 262_144,
    ) -> TopicListResponse:
        return social.list_topics(
            spaceRef, after_topic_ref=afterTopicRef, limit=limit, max_bytes=maxBytes
        )

    @mcp.tool(name="topic.cursor.get")
    @_project_domain_errors
    def topic_cursor_get(actorRef: str, topicRef: str) -> TopicCursorResponse:
        return social.get_topic_cursor(actor_ref=actorRef, topic_ref=topicRef)

    @mcp.tool(name="topic.cursor.ack")
    @_project_domain_errors
    def topic_cursor_ack(actorRef: str, topicRef: str, cursor: int) -> TopicCursorResponse:
        request = {"actorRef": actorRef, "topicRef": topicRef, "cursor": cursor}
        return social.ack_topic_cursor(
            actor_ref=actorRef,
            topic_ref=topicRef,
            cursor=cursor,
            client_request_id=request_id("topic-cursor-ack", request),
        )

    @mcp.tool(name="topic.resume")
    @_project_domain_errors
    def topic_resume(
        topicRef: str,
        afterSequence: int = 0,
        limit: int = 50,
        maxBytes: int = 524_288,
    ) -> TopicResumeResponse:
        return social.resume_topic(
            topicRef, after_sequence=afterSequence, limit=limit, max_bytes=maxBytes
        )
