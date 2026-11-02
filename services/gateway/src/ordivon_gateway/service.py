from __future__ import annotations

import math
from typing import Any

from .capability_catalog import CapabilityCatalog
from .contracts import (
    ArtifactChunk,
    CapabilityProjection,
    CapabilityResolution,
    CapabilitySearchProjection,
    ExecutionObservation,
    ExecutionReceipt,
    ExecutionResolution,
    SystemDescription,
)
from .execution_coordinator import ExecutionCoordinator
from .execution_refs import GatewayError
from .execution_refs import parse_execution_ref as parse_execution_ref
from .external_worker import ExternalPullWorkerTransport
from .routing import CapabilityRoute, default_routes
from .upstream import OwnerToolCaller

_SOCIAL_WORK_HOST_TOOLS = frozenset(
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
        "topic.resume",
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


class GatewayService:
    def __init__(
        self,
        caller: OwnerToolCaller,
        routes: dict[str, CapabilityRoute] | None = None,
        *,
        external_workers: ExternalPullWorkerTransport | None = None,
        projection_timeout_seconds: float = 5.0,
    ) -> None:
        if (
            isinstance(projection_timeout_seconds, bool)
            or not math.isfinite(projection_timeout_seconds)
            or projection_timeout_seconds <= 0
        ):
            raise ValueError("projection_timeout_seconds must be positive finite")
        self._caller = caller
        self._routes = default_routes() if routes is None else dict(routes)
        if any(
            not isinstance(route, CapabilityRoute) or name != route.capability
            for name, route in self._routes.items()
        ):
            raise GatewayError("route identity must match its capability")
        self._external_workers = external_workers
        self._catalog = CapabilityCatalog(
            caller, self._routes, external_workers, projection_timeout_seconds
        )
        self._execution = ExecutionCoordinator(caller, self._routes, external_workers)

    def system_describe(self) -> SystemDescription:
        return self._catalog.system_describe()

    async def capability_describe(self, capability: str | None = None) -> CapabilityProjection:
        return await self._catalog.capability_describe(capability)

    async def capability_search(
        self,
        *,
        query: str,
        category: str | None = None,
        owner_id: str | None = None,
        limit: int = 10,
        include_unavailable: bool = True,
    ) -> CapabilitySearchProjection:
        return await self._catalog.capability_search(
            query=query,
            category=category,
            owner_id=owner_id,
            limit=limit,
            include_unavailable=include_unavailable,
        )

    async def capability_resolve(
        self,
        *,
        capability: str,
        workspace_id: str | None = None,
        agent_id: str | None = None,
    ) -> CapabilityResolution:
        return await self._catalog.capability_resolve(
            capability=capability,
            workspace_id=workspace_id,
            agent_id=agent_id,
        )

    async def execution_submit(
        self,
        *,
        capability: str,
        request_id: str,
        workspace_id: str,
        executable: str,
        args: list[str],
        cwd_relative: str = ".",
        context: str | dict[str, Any] | None = None,
        env: dict[str, str] | None = None,
        timeout_ms: int | None = None,
        authority_references: list[dict[str, Any]] | None = None,
    ) -> ExecutionReceipt:
        return await self._execution.execution_submit(
            capability=capability,
            request_id=request_id,
            workspace_id=workspace_id,
            executable=executable,
            args=args,
            cwd_relative=cwd_relative,
            context=context,
            env=env,
            timeout_ms=timeout_ms,
            authority_references=authority_references,
        )

    async def execution_resolve(self, *, capability: str, request_id: str) -> ExecutionResolution:
        return await self._execution.execution_resolve(capability=capability, request_id=request_id)

    async def execution_get(
        self, operation_ref: str, *, event_limit: int = 10, wait_ms: int = 0
    ) -> ExecutionObservation:
        return await self._execution.execution_get(
            operation_ref, event_limit=event_limit, wait_ms=wait_ms
        )

    async def execution_cancel(self, operation_ref: str) -> ExecutionReceipt:
        return await self._execution.execution_cancel(operation_ref)

    async def artifact_read(
        self,
        operation_ref: str,
        artifact_id: str,
        *,
        offset: int = 0,
        max_bytes: int = 1_048_576,
    ) -> ArtifactChunk:
        return await self._execution.artifact_read(
            operation_ref, artifact_id, offset=offset, max_bytes=max_bytes
        )

    async def social_work_call(self, tool_name: str, arguments: dict[str, Any]) -> dict[str, Any]:
        """Route one promoted Social Work Fabric operation to Host without re-owning semantics."""
        if tool_name not in _SOCIAL_WORK_HOST_TOOLS:
            raise GatewayError(f"unsupported Host Social Work tool: {tool_name}")
        result = await self._caller.call_tool("host", tool_name, arguments)
        if not isinstance(result, dict):
            raise GatewayError("Host Social Work owner returned non-object response")
        return result
