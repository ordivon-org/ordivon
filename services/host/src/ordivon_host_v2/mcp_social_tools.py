from __future__ import annotations

from collections.abc import Callable
from typing import Literal

from mcp.server import MCPServer

from .collaboration_inputs import (
    MessageInput,
    MessageKind,
    MessageRelationInput,
    MessageRelationKind,
    ParticipationStanding,
    SpaceInput,
    TopicInput,
)
from .mcp_domain_errors import _project_domain_errors
from .social_contracts import (
    MessageReadResponse,
    MessageRelationResponse,
    MessageRelationsResponse,
    MessageResponse,
    MessageSearchResponse,
    ParticipationListResponse,
    ParticipationResponse,
    SpaceListResponse,
    SpaceResponse,
    SpaceSubjectsResponse,
    TopicCursorResponse,
    TopicListResponse,
    TopicResponse,
    TopicResumeResponse,
)
from .social_store import SocialStore


def register_social_tools(
    mcp: MCPServer,
    social: SocialStore,
    request_id: Callable[[str, object], str],
) -> None:
    """Expose Space, Topic and Message tools through the native SocialStore."""

    @mcp.tool(name="space.create")
    @_project_domain_errors
    def space_create(
        spaceRef: str,
        purpose: str,
        actorRef: str,
        subjectRefs: list[str] | None = None,
    ) -> SpaceResponse:
        value = SpaceInput(
            space_ref=spaceRef,
            purpose=purpose,
            actor_ref=actorRef,
            subject_refs=[] if subjectRefs is None else subjectRefs,
        )
        return social.create_space(
            value,
            client_request_id=request_id("space-create", value.model_dump(mode="json")),
        )

    @mcp.tool(name="space.get")
    @_project_domain_errors
    def space_get(
        spaceRef: str,
        participantLimit: int = 200,
        topicLimit: int = 200,
        maxBytes: int = 2_097_152,
    ) -> SpaceResponse:
        return social.get_space(
            spaceRef,
            participant_limit=participantLimit,
            topic_limit=topicLimit,
            max_bytes=maxBytes,
        )

    @mcp.tool(name="space.list")
    @_project_domain_errors
    def space_list(
        actorRef: str | None = None,
        subjectRef: str | None = None,
        limit: int = 50,
        beforeCreatedAt: str | None = None,
        beforeSpaceRef: str | None = None,
        maxBytes: int = 262_144,
    ) -> SpaceListResponse:
        return social.list_spaces(
            actor_ref=actorRef,
            subject_ref=subjectRef,
            limit=limit,
            before_created_at=beforeCreatedAt,
            before_space_ref=beforeSpaceRef,
            max_bytes=maxBytes,
        )

    @mcp.tool(name="space.subject.list")
    @_project_domain_errors
    def space_subject_list(
        spaceRef: str,
        afterSubjectRef: str | None = None,
        limit: int = 100,
        maxBytes: int = 262_144,
    ) -> SpaceSubjectsResponse:
        return social.list_space_subjects(
            spaceRef, after_subject_ref=afterSubjectRef, limit=limit, max_bytes=maxBytes
        )

    @mcp.tool(name="space.participation.list")
    @_project_domain_errors
    def space_participation_list(
        spaceRef: str,
        afterActorRef: str | None = None,
        limit: int = 100,
        maxBytes: int = 262_144,
    ) -> ParticipationListResponse:
        return social.list_participations(
            spaceRef, after_actor_ref=afterActorRef, limit=limit, max_bytes=maxBytes
        )

    @mcp.tool(name="space.participation.set")
    @_project_domain_errors
    def space_participation_set(
        spaceRef: str,
        actorRef: str,
        standing: Literal["joined", "left", "observer"],
    ) -> ParticipationResponse:
        request = {"spaceRef": spaceRef, "actorRef": actorRef, "standing": standing}
        return social.set_participation(
            space_ref=spaceRef,
            actor_ref=actorRef,
            standing=ParticipationStanding(standing),
            client_request_id=request_id("space-participation-set", request),
        )

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
