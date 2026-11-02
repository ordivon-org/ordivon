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
from .execution_refs import GatewayError
from .execution_refs import format_execution_ref as _execution_ref
from .execution_refs import parse_execution_ref as parse_execution_ref
from .external_worker import ExternalPullWorkerTransport, WorkerConflict
from .owner_protocol import _required_bool, _required_str
from .routes import CapabilityRoute, default_routes
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
        route = self._routes.get(capability)
        if route is None and self._external_workers is not None:
            external_projection = self._external_workers.capability_projection()
            if capability in external_projection:
                if not request_id or not workspace_id or not executable:
                    raise GatewayError("requestId, workspaceId, and executable are required")
                parcel: dict[str, Any] = {
                    "workspace_id": workspace_id,
                    "executable": executable,
                    "args": list(args),
                    "cwd_relative": cwd_relative,
                }
                if context is not None:
                    parcel["context"] = context
                if env is not None:
                    parcel["env"] = dict(env)
                if timeout_ms is not None:
                    parcel["timeout_ms"] = timeout_ms
                if authority_references is not None:
                    parcel["authority_references"] = [dict(item) for item in authority_references]
                try:
                    operation = self._external_workers.submit(
                        capability=capability,
                        request_id=request_id,
                        parcel=parcel,
                    )
                except WorkerConflict as exc:
                    raise GatewayError(str(exc)) from exc
                return ExecutionReceipt(
                    operation_ref=_execution_ref("external.pull", operation.operation_id),
                    capability=capability,
                    owner_id="external.pull",
                    native_id=operation.operation_id,
                    state=operation.state,
                    terminal=operation.terminal,
                    delivery_disposition="queued" if not operation.terminal else "committed",
                )
        if route is None:
            raise GatewayError(f"unknown capability: {capability}")
        if route.category != "execution" or route.owner_tool != "workspace.exec":
            raise GatewayError(f"capability is not executable: {capability}")
        if not request_id or not workspace_id or not executable:
            raise GatewayError("requestId, workspaceId, and executable are required")

        execution: dict[str, Any] = {
            "workspaceId": workspace_id,
            "executable": executable,
            "args": list(args),
            "cwdRelative": cwd_relative,
            "executionTarget": route.execution_target,
        }
        if route.owner_id == "runtime.linux":
            if isinstance(context, dict):
                raise GatewayError("execution.linux context must be a provider-defined string")
            execution["executionProfile"] = context or route.default_context
        elif route.owner_id == "runtime.windows":
            execution["executionProfile"] = "trusted_local"
            if context is None:
                execution["windowsAuthority"] = route.default_context
            elif isinstance(context, str):
                # Compatibility only: Gateway does not interpret legacy authority values.
                execution["windowsAuthority"] = context
            else:
                # Structured Windows authority is opaque provider-owned data. Gateway only
                # lowers the generic northbound envelope into Runtime's owner field.
                execution["windowsContext"] = dict(context)
        else:
            raise GatewayError(f"unsupported execution owner: {route.owner_id}")
        if env is not None:
            if not all(
                isinstance(key, str) and key and isinstance(value, str)
                for key, value in env.items()
            ):
                raise GatewayError("env must map non-empty string names to string values")
            execution["env"] = dict(env)
        if timeout_ms is not None:
            execution["timeoutMs"] = timeout_ms
        if authority_references is not None:
            if any(not isinstance(item, dict) for item in authority_references):
                raise GatewayError("authorityReferences must contain objects")
            execution["foreignReferences"] = [dict(item) for item in authority_references]

        payload = {
            "schemaVersion": 1,
            "clientRequestId": request_id,
            "execution": execution,
            "waitMs": 0,
            "stdoutTailBytes": 4096,
            "stderrTailBytes": 4096,
        }
        result = await self._caller.call_tool(route.owner_id, route.owner_tool, payload)
        native_id = _required_str(result, "jobId")
        return ExecutionReceipt(
            operation_ref=_execution_ref(route.owner_id, native_id),
            capability=capability,
            owner_id=route.owner_id,
            native_id=native_id,
            state=str(result.get("status", result.get("attemptState", "unknown"))),
            terminal=_required_bool(result, "executionTerminal"),
            delivery_disposition=(
                str(result["deliveryDisposition"])
                if result.get("deliveryDisposition") is not None
                else None
            ),
        )

    async def execution_resolve(self, *, capability: str, request_id: str) -> ExecutionResolution:
        if not request_id:
            raise GatewayError("requestId is required")
        route = self._routes.get(capability)
        if route is None and self._external_workers is not None:
            operation = self._external_workers.resolve(capability, request_id)
            if operation is None:
                # A historical operation stays resolvable after its worker
                # expires. Only a genuinely absent and *unadvertised* identity
                # is unknown rather than a known capability's missing request.
                if capability not in self._external_workers.capability_projection():
                    raise GatewayError(f"unknown capability: {capability}")
                return ExecutionResolution(
                    request_id=request_id,
                    capability=capability,
                    owner_id="external.pull",
                    resolution="absent",
                )
            return ExecutionResolution(
                request_id=request_id,
                capability=capability,
                owner_id="external.pull",
                resolution="found",
                operation_ref=_execution_ref("external.pull", operation.operation_id),
                native_id=operation.operation_id,
                workspace_id=operation.workspace_id,
            )
        if route is None:
            raise GatewayError(f"unknown capability: {capability}")
        if route.category != "execution" or route.owner_tool != "workspace.exec":
            raise GatewayError(f"capability is not executable: {capability}")

        page = await self._caller.call_tool(
            route.owner_id,
            "job.list",
            {
                "limit": 2,
                "clientRequestId": request_id,
            },
        )
        jobs = page.get("jobs")
        if not isinstance(jobs, list) or any(not isinstance(item, dict) for item in jobs):
            raise GatewayError("Runtime job.list omitted jobs")
        for job in jobs:
            if job.get("clientRequestId") != request_id:
                raise GatewayError("Runtime job.list returned another clientRequestId")
        next_cursor = page.get("nextCursor")
        ambiguous = len(jobs) > 1 or next_cursor is not None
        if ambiguous:
            return ExecutionResolution(
                request_id=request_id,
                capability=capability,
                owner_id=route.owner_id,
                resolution="ambiguous",
            )
        if not jobs:
            return ExecutionResolution(
                request_id=request_id,
                capability=capability,
                owner_id=route.owner_id,
                resolution="absent",
            )
        native_id = _required_str(jobs[0], "jobId")
        # Do not invent a workspace from the caller's route/grant. The
        # Runtime list row is the physical identity witness for this lookup.
        workspace_id = _required_str(jobs[0], "workspaceId")
        return ExecutionResolution(
            request_id=request_id,
            capability=capability,
            owner_id=route.owner_id,
            resolution="found",
            operation_ref=_execution_ref(route.owner_id, native_id),
            native_id=native_id,
            workspace_id=workspace_id,
        )

    async def execution_get(
        self, operation_ref: str, *, event_limit: int = 10, wait_ms: int = 0
    ) -> ExecutionObservation:
        owner_id, native_id = parse_execution_ref(operation_ref)
        if owner_id == "external.pull":
            if self._external_workers is None:
                raise GatewayError("external pull worker transport is not configured")
            try:
                operation = self._external_workers.get(native_id)
            except WorkerConflict as exc:
                raise GatewayError(str(exc)) from exc
            return ExecutionObservation(
                operation_ref=operation_ref,
                capability=operation.capability,
                owner_id=owner_id,
                native_id=native_id,
                state=operation.state,
                terminal=operation.terminal,
                delivery_disposition=(
                    "committed"
                    if operation.terminal
                    else "unknown"
                    if operation.state == "reconcile_required"
                    else "in_progress"
                ),
                execution_disposition=(
                    "succeeded"
                    if operation.terminal and operation.exit_code == 0
                    else "failed"
                    if operation.terminal and operation.exit_code is not None
                    else None
                ),
                exit_code=operation.exit_code,
                recovery_required=operation.state == "reconcile_required",
                artifacts_available=bool(operation.artifact_ids),
                artifact_count=len(operation.artifact_ids),
                artifact_ids=operation.artifact_ids,
                artifact_projection_complete=True,
            )
        # eventLimit is retained on the northbound surface for connector compatibility.
        # Runtime's execution observation authority is job.observe; Gateway does not
        # project the job.get event timeline, so forwarding eventLimit would add no truth.
        _ = event_limit
        if type(wait_ms) is not int or not 0 <= wait_ms <= 30_000:
            raise GatewayError("waitMs must be an integer between 0 and 30000")
        result = await self._caller.call_tool(
            owner_id,
            "job.observe",
            {
                "schemaVersion": 1,
                "jobId": native_id,
                "waitMs": wait_ms,
                "waitUntil": "change_or_terminal",
                "stdoutTailBytes": 0,
                "stderrTailBytes": 0,
            },
        )
        observed_native_id = _required_str(result, "jobId")
        if observed_native_id != native_id:
            raise GatewayError("Runtime job.observe returned mismatched job identity")

        def artifact_ids(payload: dict[str, Any]) -> list[str]:
            values: list[str] = []
            for item in payload.get("artifacts", []):
                if isinstance(item, dict) and isinstance(item.get("artifactId"), str):
                    values.append(item["artifactId"])
            return values

        artifacts = artifact_ids(result)
        artifacts_available = (
            bool(result["artifactsAvailable"])
            if isinstance(result.get("artifactsAvailable"), bool)
            else None
        )
        artifact_count = len(artifacts)
        artifact_projection_complete: bool | None = None

        if _required_bool(result, "executionTerminal") or artifacts_available:
            inspection = await self._caller.call_tool(
                owner_id,
                "job.get",
                {
                    "schemaVersion": 1,
                    "jobId": native_id,
                    "eventLimit": 1,
                },
            )
            job = inspection.get("job")
            if not isinstance(job, dict) or job.get("jobId") != native_id:
                raise GatewayError("Runtime job.get returned mismatched job identity")
            summary = inspection.get("artifacts")
            summary_count = (
                int(summary["count"])
                if isinstance(summary, dict) and isinstance(summary.get("count"), int)
                else None
            )
            if summary_count is not None:
                artifact_count = summary_count
                if len(artifacts) != summary_count:
                    refreshed = await self._caller.call_tool(
                        owner_id,
                        "job.observe",
                        {
                            "schemaVersion": 1,
                            "jobId": native_id,
                            "waitMs": 0,
                            "waitUntil": "change_or_terminal",
                            "stdoutTailBytes": 0,
                            "stderrTailBytes": 0,
                        },
                    )
                    if _required_str(refreshed, "jobId") != native_id:
                        raise GatewayError(
                            "Runtime job.observe refresh returned mismatched job identity"
                        )
                    artifacts = artifact_ids(refreshed)
                    artifacts_available = (
                        bool(refreshed["artifactsAvailable"])
                        if isinstance(refreshed.get("artifactsAvailable"), bool)
                        else artifacts_available
                    )
                artifact_projection_complete = len(artifacts) == summary_count
            else:
                artifact_projection_complete = not artifacts_available or bool(artifacts)

        return ExecutionObservation(
            operation_ref=operation_ref,
            capability=(
                "execution.windows" if owner_id == "runtime.windows" else "execution.linux"
            ),
            owner_id=owner_id,
            native_id=observed_native_id,
            state=str(result.get("status", result.get("attemptState", "unknown"))),
            terminal=_required_bool(result, "executionTerminal"),
            delivery_disposition=(
                str(result["deliveryDisposition"])
                if result.get("deliveryDisposition") is not None
                else None
            ),
            execution_disposition=(
                str(result["executionDisposition"])
                if result.get("executionDisposition") is not None
                else None
            ),
            exit_code=(
                int(result["exitCode"]) if isinstance(result.get("exitCode"), int) else None
            ),
            recovery_required=(
                bool(result["recoveryRequired"])
                if isinstance(result.get("recoveryRequired"), bool)
                else None
            ),
            artifacts_available=artifacts_available,
            artifact_count=artifact_count,
            artifact_ids=artifacts,
            artifact_projection_complete=artifact_projection_complete,
        )

    async def execution_cancel(self, operation_ref: str) -> ExecutionReceipt:
        owner_id, native_id = parse_execution_ref(operation_ref)
        if owner_id == "external.pull":
            if self._external_workers is None:
                raise GatewayError("external pull worker transport is not configured")
            try:
                operation = self._external_workers.cancel(native_id)
            except WorkerConflict as exc:
                raise GatewayError(str(exc)) from exc
            return ExecutionReceipt(
                operation_ref=operation_ref,
                capability=operation.capability,
                owner_id=owner_id,
                native_id=native_id,
                state=operation.state,
                terminal=operation.terminal,
                delivery_disposition="committed" if operation.terminal else "in_progress",
            )
        result = await self._caller.call_tool(
            owner_id,
            "job.cancel",
            {"schemaVersion": 1, "jobId": native_id},
        )
        observed_native_id = _required_str(result, "jobId")
        if observed_native_id != native_id:
            raise GatewayError("Runtime job.cancel returned mismatched job identity")
        return ExecutionReceipt(
            operation_ref=operation_ref,
            capability=(
                "execution.windows" if owner_id == "runtime.windows" else "execution.linux"
            ),
            owner_id=owner_id,
            native_id=observed_native_id,
            state=str(result.get("status", "unknown")),
            terminal=_required_bool(result, "executionTerminal"),
            delivery_disposition=(
                str(result["deliveryDisposition"])
                if result.get("deliveryDisposition") is not None
                else None
            ),
        )

    async def artifact_read(
        self,
        operation_ref: str,
        artifact_id: str,
        *,
        offset: int = 0,
        max_bytes: int = 1_048_576,
    ) -> ArtifactChunk:
        owner_id, native_id = parse_execution_ref(operation_ref)
        if owner_id == "external.pull":
            if self._external_workers is None:
                raise GatewayError("external pull worker transport is not configured")
            try:
                result = self._external_workers.read_artifact(
                    native_id, artifact_id, offset=offset, max_bytes=max_bytes
                )
            except WorkerConflict as exc:
                raise GatewayError(str(exc)) from exc
            return ArtifactChunk(
                operation_ref=operation_ref,
                owner_id=owner_id,
                native_id=native_id,
                artifact_id=artifact_id,
                offset=int(result["offset"]),
                next_offset=int(result["next_offset"]),
                eof=bool(result["eof"]),
                digest=str(result["digest"]),
                content=str(result["content"]),
            )
        result = await self._caller.call_tool(
            owner_id,
            "artifact.read",
            {
                "schemaVersion": 1,
                "jobId": native_id,
                "artifactId": artifact_id,
                "offset": offset,
                "maxBytes": max_bytes,
            },
        )
        if result.get("jobId") != native_id or result.get("artifactId") != artifact_id:
            raise GatewayError("artifact owner returned mismatched identity")
        return ArtifactChunk(
            operation_ref=operation_ref,
            owner_id=owner_id,
            native_id=native_id,
            artifact_id=artifact_id,
            offset=int(result.get("offset", offset)),
            next_offset=int(result.get("nextOffset", offset)),
            eof=bool(result.get("eof", False)),
            digest=_required_str(result, "digest"),
            content=str(result.get("content", "")),
        )

    async def social_work_call(self, tool_name: str, arguments: dict[str, Any]) -> dict[str, Any]:
        """Route one promoted Social Work Fabric operation to Host without re-owning semantics."""
        if tool_name not in _SOCIAL_WORK_HOST_TOOLS:
            raise GatewayError(f"unsupported Host Social Work tool: {tool_name}")
        result = await self._caller.call_tool("host", tool_name, arguments)
        if not isinstance(result, dict):
            raise GatewayError("Host Social Work owner returned non-object response")
        return result
