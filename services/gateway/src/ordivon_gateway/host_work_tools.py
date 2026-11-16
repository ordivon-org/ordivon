"""Register Host work tools without owning Host authority."""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import Annotated, Any, Literal, NotRequired, TypedDict

from mcp.server import MCPServer
from pydantic import AfterValidator, ConfigDict, Field, with_config

from .host_tool_contracts import HostCollectionBytes


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


PositiveWorkRevision = Annotated[int, Field(strict=True, ge=1, le=2**63 - 1)]
AdvancableWorkRevision = Annotated[int, Field(strict=True, ge=1, le=2**63 - 2)]
PositiveWorkListLimit = Annotated[int, Field(strict=True, ge=1, le=200)]


def register_host_work_tools(
    server: MCPServer,
    _host: Callable[[str, dict[str, Any]], Awaitable[Any]],
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
        workRef: str, workKind: str, actorRef: str, initialSnapshot: WorkSnapshotInput
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
    async def work_get(
        workRef: str, revision: PositiveWorkRevision | None = None
    ) -> dict[str, Any]:
        return await _host("work.get", {"workRef": workRef, "revision": revision})

    @server.tool(name="work.list")
    async def work_list(
        state: Literal["open", "completed", "abandoned"] | None = None,
        limit: PositiveWorkListLimit = 50,
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
        expectedRevision: AdvancableWorkRevision,
        snapshot: WorkSnapshotInput,
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
