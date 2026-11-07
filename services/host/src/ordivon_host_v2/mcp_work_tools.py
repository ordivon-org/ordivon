from __future__ import annotations

from collections.abc import Callable
from typing import Annotated, Literal

from mcp.server import MCPServer
from pydantic import Field

from .mcp_domain_errors import _project_domain_errors
from .postgres_bounds import POSTGRES_BIGINT_MAX
from .social_contracts import ActorRefResponse, WorkListResponse, WorkResponse
from .work_inputs import ActorKind, ActorRefInput, WorkCreateInput, WorkSnapshotInput, WorkState
from .work_store import WorkStore

# Exact Host CAS identities and inventory limits use bounded strict integers.
PositiveWorkRevision = Annotated[int, Field(strict=True, ge=1, le=POSTGRES_BIGINT_MAX)]
AdvancableWorkRevision = Annotated[int, Field(strict=True, ge=1, le=POSTGRES_BIGINT_MAX - 1)]
PositiveWorkListLimit = Annotated[int, Field(strict=True, ge=1, le=200)]


def register_work_tools(
    mcp: MCPServer,
    work: WorkStore,
    request_id: Callable[[str, object], str],
) -> None:
    """Expose WorkStore contracts, without introducing another state authority."""

    @mcp.tool(name="actor.declare")
    @_project_domain_errors
    def actor_declare(
        actorRef: str,
        actorKind: Literal["unknown", "human", "agent", "service", "organization"],
    ) -> ActorRefResponse:
        value = ActorRefInput(actor_ref=actorRef, actor_kind=ActorKind(actorKind))
        request = value.model_dump(mode="json")
        return work.declare_actor(
            value,
            client_request_id=request_id("actor-declare", request),
        )

    @mcp.tool(name="work.create")
    @_project_domain_errors
    def work_create(
        workRef: str,
        workKind: str,
        actorRef: str,
        initialSnapshot: WorkSnapshotInput,
    ) -> WorkResponse:
        value = WorkCreateInput(
            work_ref=workRef,
            kind=workKind,
            actor_ref=actorRef,
            initial_snapshot=initialSnapshot,
        )
        request = value.model_dump(mode="json")
        return work.create_work(value, client_request_id=request_id("work-create", request))

    @mcp.tool(name="work.get")
    @_project_domain_errors
    def work_get(workRef: str, revision: PositiveWorkRevision | None = None) -> WorkResponse:
        return work.get_work(workRef, revision)

    @mcp.tool(name="work.list")
    @_project_domain_errors
    def work_list(
        state: Literal["open", "completed", "abandoned"] | None = None,
        limit: PositiveWorkListLimit = 50,
        beforeUpdatedAt: str | None = None,
        beforeWorkRef: str | None = None,
        maxBytes: int = 262_144,
    ) -> WorkListResponse:
        return work.list_works(
            state=state,
            limit=limit,
            before_updated_at=beforeUpdatedAt,
            before_work_ref=beforeWorkRef,
            max_bytes=maxBytes,
        )

    @mcp.tool(name="work.snapshot.commit")
    @_project_domain_errors
    def work_snapshot_commit(
        workRef: str,
        expectedRevision: AdvancableWorkRevision,
        snapshot: WorkSnapshotInput,
        actorRef: str,
        continuityDisposition: Literal["continue", "complete", "abandon"] = "continue",
    ) -> WorkResponse:
        state = {
            "continue": WorkState.OPEN,
            "complete": WorkState.COMPLETED,
            "abandon": WorkState.ABANDONED,
        }[continuityDisposition]
        request = {
            "workRef": workRef,
            "expectedRevision": expectedRevision,
            "snapshot": snapshot.canonical_payload(),
            "actorRef": actorRef,
            "continuityDisposition": continuityDisposition,
        }
        return work.commit_snapshot(
            workRef,
            expected_revision=expectedRevision,
            snapshot=snapshot,
            actor_ref=actorRef,
            state=state,
            client_request_id=request_id("work-snapshot-commit", request),
        )
