"""Register Host work tools without owning Host authority."""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import Annotated, Any, Literal, NotRequired, TypedDict

from mcp.server import MCPServer
from pydantic import AfterValidator, ConfigDict, Field, StrictInt, TypeAdapter, with_config

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

# The public MCP Tool schema is an Agent-facing, long-lived ABI. 0.10.12
# exposed open snapshot objects and unconstrained integer fields. Preserve
# that wire shape while checking the *original* strict Host-compatible types
# before any upstream effect. One TypeAdapter per natural validation type,
# rather than a second handwritten schema/validation policy.
_SNAPSHOT = TypeAdapter(WorkSnapshotInput)
_REVISION = TypeAdapter(PositiveWorkRevision)
_ADVANCABLE_REVISION = TypeAdapter(AdvancableWorkRevision)
_LIST_LIMIT = TypeAdapter(PositiveWorkListLimit)


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
        workRef: str, workKind: str, actorRef: str, initialSnapshot: dict[str, Any]
    ) -> dict[str, Any]:
        verified_snapshot = _SNAPSHOT.validate_python(initialSnapshot)
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
    async def work_get(workRef: str, revision: StrictInt | None = None) -> dict[str, Any]:
        verified_revision = _REVISION.validate_python(revision) if revision is not None else None
        return await _host("work.get", {"workRef": workRef, "revision": verified_revision})

    @server.tool(name="work.list")
    async def work_list(
        state: Literal["open", "completed", "abandoned"] | None = None,
        limit: StrictInt = 50,
        beforeUpdatedAt: str | None = None,
        beforeWorkRef: str | None = None,
        maxBytes: HostCollectionBytes = 262_144,
    ) -> dict[str, Any]:
        verified_limit = _LIST_LIMIT.validate_python(limit)
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
        expectedRevision: StrictInt,
        snapshot: dict[str, Any],
        actorRef: str,
        continuityDisposition: Literal["continue", "complete", "abandon"] = "continue",
    ) -> dict[str, Any]:
        verified_revision = _ADVANCABLE_REVISION.validate_python(expectedRevision)
        verified_snapshot = _SNAPSHOT.validate_python(snapshot)
        return await _host(
            "work.snapshot.commit",
            {
                "workRef": workRef,
                "expectedRevision": verified_revision,
                "snapshot": verified_snapshot,
                "actorRef": actorRef,
                "continuityDisposition": continuityDisposition,
            },
        )
