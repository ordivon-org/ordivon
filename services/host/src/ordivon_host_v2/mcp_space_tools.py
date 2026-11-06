from __future__ import annotations

from collections.abc import Callable
from typing import Literal

from mcp.server import MCPServer

from .collaboration_inputs import (
    ParticipationStanding,
    SpaceInput,
)
from .mcp_domain_errors import _project_domain_errors
from .social_contracts import (
    ParticipationListResponse,
    ParticipationResponse,
    SpaceListResponse,
    SpaceResponse,
    SpaceSubjectsResponse,
)
from .social_store import SocialStore


def register_space_tools(
    mcp: MCPServer,
    social: SocialStore,
    request_id: Callable[[str, object], str],
) -> None:
    """Register native Space MCP tools; SocialStore owns semantics."""

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
