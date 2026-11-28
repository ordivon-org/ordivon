"""Register Host work tools without owning Host authority."""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import Annotated, Any, Literal, NotRequired, TypedDict

from mcp.server import MCPServer
from mcp_types import CallToolResult
from pydantic import (
    AfterValidator,
    ConfigDict,
    Field,
    StrictInt,
    TypeAdapter,
    ValidationError,
    with_config,
)

from ...logic.host_tool_contracts import HostCollectionBytes
from ...logic.owner_protocol import OwnerCallError
from .numeric_wire import HostAdvancableRevision, HostPositiveRevision


# Match the natural Host's published WorkSnapshotInput wire shape without
# importing its PostgreSQL-backed service into the Gateway process.
# The Owner remains authoritative for semantic validation and persistence.
# The native Host/Gateway MCP SDK tool-schema differential is the source oracle.
def _validate_host_snapshot_strings(values: list[str]) -> list[str]:
    # This wire-level check matches the existing Host WorkSnapshotInput validator.
    # The Host still owns all domain acceptance.
    if any(not value or value != value.strip() for value in values):
        raise ValueError("snapshot list entries must be non-empty trimmed text")
    return values


@with_config(ConfigDict(extra="forbid"))
class WorkSnapshotInput(TypedDict):
    objective: Annotated[str, Field(min_length=1, max_length=4096)]
    frontier: Annotated[str, Field(min_length=1, max_length=4096)]
    established: NotRequired[
        Annotated[list[str], Field(max_length=128), AfterValidator(_validate_host_snapshot_strings)]
    ]
    unresolved: NotRequired[
        Annotated[list[str], Field(max_length=128), AfterValidator(_validate_host_snapshot_strings)]
    ]
    rejected: NotRequired[
        Annotated[list[str], Field(max_length=128), AfterValidator(_validate_host_snapshot_strings)]
    ]
    constraints: NotRequired[
        Annotated[list[str], Field(max_length=128), AfterValidator(_validate_host_snapshot_strings)]
    ]
    nextActions: NotRequired[
        Annotated[list[str], Field(max_length=128), AfterValidator(_validate_host_snapshot_strings)]
    ]
    referenceRefs: NotRequired[
        Annotated[list[str], Field(max_length=256), AfterValidator(_validate_host_snapshot_strings)]
    ]


PositiveWorkListLimit = Annotated[int, Field(strict=True, ge=1, le=200)]

# Preserve the historical open snapshot object and Work list ABI. Revision
# bounds are now explicit on the native SDK wire, matching Host V1. The
# remaining adapters check the original payload before an upstream effect.
_SNAPSHOT = TypeAdapter(WorkSnapshotInput)
_LIST_LIMIT = TypeAdapter(PositiveWorkListLimit)


def _legacy_work_validation_error(
    tool: str, project_error: Callable[[OwnerCallError], CallToolResult]
) -> CallToolResult:
    """Same public error as an original Host rejection, without an Owner RPC."""
    return project_error(
        OwnerCallError(
            f"owner tool returned error: host/{tool}",
            owner_id="host",
            tool_name=tool,
        )
    )


def register_host_work_tools(
    server: MCPServer,
    _host: Callable[[str, dict[str, Any]], Awaitable[Any]],
    project_error: Callable[[OwnerCallError], CallToolResult],
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
        try:
            verified_snapshot = _SNAPSHOT.validate_python(initialSnapshot)
        except ValidationError:
            return _legacy_work_validation_error("work.create", project_error)
        return await _host(
            "work.create",
            {
                "workRef": workRef,
                "workKind": workKind,
                "actorRef": actorRef,
                "initialSnapshot": verified_snapshot,
            },
        )

    @server.tool(name="work.get")
    async def work_get(
        workRef: str, revision: HostPositiveRevision | None = None
    ) -> dict[str, Any]:
        return await _host("work.get", {"workRef": workRef, "revision": revision})

    @server.tool(name="work.list")
    async def work_list(
        state: Literal["open", "completed", "abandoned"] | None = None,
        limit: StrictInt = 50,
        beforeUpdatedAt: str | None = None,
        beforeWorkRef: str | None = None,
        maxBytes: HostCollectionBytes = 262_144,
    ) -> dict[str, Any]:
        try:
            verified_limit = _LIST_LIMIT.validate_python(limit)
        except ValidationError:
            return _legacy_work_validation_error("work.list", project_error)
        return await _host(
            "work.list",
            {
                "state": state,
                "limit": verified_limit,
                "beforeUpdatedAt": beforeUpdatedAt,
                "beforeWorkRef": beforeWorkRef,
                "maxBytes": maxBytes,
            },
        )

    @server.tool(name="work.snapshot.commit")
    async def work_snapshot_commit(
        workRef: str,
        expectedRevision: HostAdvancableRevision,
        snapshot: dict[str, Any],
        actorRef: str,
        continuityDisposition: Literal["continue", "complete", "abandon"] = "continue",
    ) -> dict[str, Any]:
        try:
            verified_snapshot = _SNAPSHOT.validate_python(snapshot)
        except ValidationError:
            return _legacy_work_validation_error("work.snapshot.commit", project_error)
        return await _host(
            "work.snapshot.commit",
            {
                "workRef": workRef,
                "expectedRevision": expectedRevision,
                "snapshot": verified_snapshot,
                "actorRef": actorRef,
                "continuityDisposition": continuityDisposition,
            },
        )
