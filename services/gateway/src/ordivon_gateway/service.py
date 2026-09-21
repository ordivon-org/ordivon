from __future__ import annotations

from typing import Any

from .contracts import (
    ArtifactChunk,
    CapabilityDescriptor,
    CapabilityProjection,
    ContinuityItem,
    ContinuityObservation,
    ContinuityPage,
    ExecutionObservation,
    ExecutionReceipt,
    OwnerDescriptor,
    SystemDescription,
)
from .registry import CapabilityRoute, default_routes
from .upstream import OwnerToolCaller


class GatewayError(RuntimeError):
    pass


_OWNER_ROLES = {
    "runtime.linux": "physical execution owner",
    "runtime.windows": "physical execution owner",
    "host": "external semantic continuity owner",
}


def _configured(caller: OwnerToolCaller, owner_id: str) -> bool:
    probe = getattr(caller, "is_configured", None)
    if callable(probe):
        return bool(probe(owner_id))
    return True


def _execution_ref(owner_id: str, native_id: str) -> str:
    return f"ordivon-exec:v1:{owner_id}:{native_id}"


def _parse_execution_ref(value: str) -> tuple[str, str]:
    prefix = "ordivon-exec:v1:"
    if not value.startswith(prefix):
        raise GatewayError("invalid execution operationRef")
    rest = value[len(prefix) :]
    try:
        owner_id, native_id = rest.rsplit(":", 1)
    except ValueError as exc:
        raise GatewayError("invalid execution operationRef") from exc
    if owner_id not in {"runtime.linux", "runtime.windows"} or not native_id:
        raise GatewayError("unsupported execution operationRef owner")
    return owner_id, native_id


def _required_str(payload: dict[str, Any], key: str) -> str:
    value = payload.get(key)
    if not isinstance(value, str) or not value:
        raise GatewayError(f"owner response omitted {key}")
    return value


class GatewayService:
    def __init__(
        self,
        caller: OwnerToolCaller,
        routes: dict[str, CapabilityRoute] | None = None,
    ) -> None:
        self._caller = caller
        self._routes = routes or default_routes()

    def system_describe(self) -> SystemDescription:
        owners = [
            OwnerDescriptor(
                owner_id=owner_id,
                role=role,
                configured=_configured(self._caller, owner_id),
            )
            for owner_id, role in _OWNER_ROLES.items()
        ]
        return SystemDescription(
            owners=owners,
            capabilities=sorted(self._routes),
        )

    def capability_describe(self, capability: str | None = None) -> CapabilityProjection:
        if capability is not None:
            route = self._routes.get(capability)
            if route is None:
                raise GatewayError(f"unknown capability: {capability}")
            selected = [route]
        else:
            selected = [self._routes[key] for key in sorted(self._routes)]

        values = [
            CapabilityDescriptor(
                capability=route.capability,
                owner_id=route.owner_id,
                category=route.category,
                configured=(
                    True
                    if route.owner_id == "runtime.dynamic"
                    else _configured(self._caller, route.owner_id)
                ),
                context_mode=route.context_mode,  # type: ignore[arg-type]
                truth_boundary=route.truth_boundary,
            )
            for route in selected
        ]
        return CapabilityProjection(capabilities=values)

    async def execution_submit(
        self,
        *,
        capability: str,
        request_id: str,
        workspace_id: str,
        executable: str,
        args: list[str],
        cwd_relative: str = ".",
        context: str | None = None,
        timeout_ms: int | None = None,
    ) -> ExecutionReceipt:
        route = self._routes.get(capability)
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
            execution["executionProfile"] = context or route.default_context
        elif route.owner_id == "runtime.windows":
            execution["executionProfile"] = "trusted_local"
            execution["windowsAuthority"] = context or route.default_context
        else:
            raise GatewayError(f"unsupported execution owner: {route.owner_id}")
        if timeout_ms is not None:
            execution["timeoutMs"] = timeout_ms

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
            terminal=bool(result.get("executionTerminal", False)),
            delivery_disposition=(
                str(result["deliveryDisposition"])
                if result.get("deliveryDisposition") is not None
                else None
            ),
        )

    async def execution_get(
        self, operation_ref: str, *, event_limit: int = 10
    ) -> ExecutionObservation:
        owner_id, native_id = _parse_execution_ref(operation_ref)
        result = await self._caller.call_tool(
            owner_id,
            "job.get",
            {"schemaVersion": 1, "jobId": native_id, "eventLimit": event_limit},
        )
        job = result.get("job")
        if isinstance(job, dict):
            observed_native_id = _required_str(job, "jobId")
            if observed_native_id != native_id:
                raise GatewayError("Runtime job.get returned mismatched job identity")

            attempts = [item for item in result.get("attempts", []) if isinstance(item, dict)]
            latest_attempt = max(
                attempts,
                key=lambda item: (
                    item.get("attemptNumber") if isinstance(item.get("attemptNumber"), int) else -1
                ),
                default=None,
            )
            resolution = job.get("resolution")
            state = (
                str(resolution)
                if isinstance(resolution, str) and resolution
                else (
                    str(latest_attempt.get("state", "unknown"))
                    if latest_attempt is not None
                    else str(job.get("desiredState", "unknown"))
                )
            )
            terminal = (
                isinstance(resolution, str)
                and bool(resolution)
                and job.get("mechanicallyConverged") is True
            )
            exit_code = (
                int(latest_attempt["exitCode"])
                if latest_attempt is not None and isinstance(latest_attempt.get("exitCode"), int)
                else None
            )
            recovery_required: bool | None = None
            if latest_attempt is not None:
                for condition in latest_attempt.get("conditions", []):
                    if not isinstance(condition, dict):
                        continue
                    if condition.get("conditionType") != "recovery_required":
                        continue
                    status = condition.get("status")
                    if status == "true":
                        recovery_required = True
                    elif status == "false":
                        recovery_required = False
                    break
            artifact_summary = result.get("artifacts")
            artifact_count = (
                int(artifact_summary["count"])
                if isinstance(artifact_summary, dict)
                and isinstance(artifact_summary.get("count"), int)
                else None
            )
            return ExecutionObservation(
                operation_ref=operation_ref,
                capability=(
                    "execution.windows" if owner_id == "runtime.windows" else "execution.linux"
                ),
                owner_id=owner_id,
                native_id=observed_native_id,
                state=state,
                terminal=terminal,
                execution_disposition=(
                    str(resolution) if isinstance(resolution, str) and resolution else None
                ),
                exit_code=exit_code,
                recovery_required=recovery_required,
                artifact_count=artifact_count,
            )

        artifacts: list[str] = []
        for item in result.get("artifacts", []):
            if isinstance(item, dict) and isinstance(item.get("artifactId"), str):
                artifacts.append(item["artifactId"])
        return ExecutionObservation(
            operation_ref=operation_ref,
            capability=(
                "execution.windows" if owner_id == "runtime.windows" else "execution.linux"
            ),
            owner_id=owner_id,
            native_id=_required_str(result, "jobId"),
            state=str(result.get("status", result.get("attemptState", "unknown"))),
            terminal=bool(result.get("executionTerminal", False)),
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
            artifact_count=len(artifacts) if artifacts else None,
            artifact_ids=artifacts,
        )

    async def execution_cancel(self, operation_ref: str) -> ExecutionReceipt:
        owner_id, native_id = _parse_execution_ref(operation_ref)
        result = await self._caller.call_tool(
            owner_id,
            "job.cancel",
            {"schemaVersion": 1, "jobId": native_id},
        )
        return ExecutionReceipt(
            operation_ref=operation_ref,
            capability=(
                "execution.windows" if owner_id == "runtime.windows" else "execution.linux"
            ),
            owner_id=owner_id,
            native_id=_required_str(result, "jobId"),
            state=str(result.get("status", "unknown")),
            terminal=bool(result.get("executionTerminal", False)),
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
        owner_id, native_id = _parse_execution_ref(operation_ref)
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

    async def continuity_get(self, task_id: str) -> ContinuityObservation:
        result = await self._caller.call_tool("host", "task.resume", {"taskId": task_id})
        task = result.get("task")
        checkpoint = result.get("checkpoint")
        if not isinstance(task, dict) or not isinstance(checkpoint, dict):
            raise GatewayError("Host task.resume omitted task/checkpoint")
        return ContinuityObservation(
            task_id=_required_str(task, "task_id"),
            goal_id=(str(task["goal_id"]) if task.get("goal_id") is not None else None),
            revision=int(task["revision"]),
            state=_required_str(task, "state"),
            checkpoint_digest=(
                str(task["checkpoint_digest"])
                if task.get("checkpoint_digest") is not None
                else None
            ),
            checkpoint=checkpoint,
            truth_boundary=(
                str(result["truthBoundary"]) if result.get("truthBoundary") is not None else None
            ),
        )

    async def continuity_list(
        self,
        *,
        goal_id: str | None = None,
        limit: int = 50,
        cursor: str | None = None,
        include_terminal: bool = False,
    ) -> ContinuityPage:
        arguments: dict[str, Any] = {
            "limit": limit,
            "includeTerminal": include_terminal,
        }
        if goal_id is not None:
            arguments["goalId"] = goal_id
        if cursor is not None:
            arguments["cursor"] = cursor
        result = await self._caller.call_tool("host", "task.list", arguments)
        items: list[ContinuityItem] = []
        for task in result.get("tasks", []):
            if not isinstance(task, dict):
                continue
            items.append(
                ContinuityItem(
                    task_id=_required_str(task, "task_id"),
                    goal_id=(str(task["goal_id"]) if task.get("goal_id") is not None else None),
                    revision=int(task["revision"]),
                    state=_required_str(task, "state"),
                    checkpoint_digest=(
                        str(task["checkpoint_digest"])
                        if task.get("checkpoint_digest") is not None
                        else None
                    ),
                )
            )
        return ContinuityPage(
            items=items,
            has_more=bool(result.get("hasMore", False)),
            next_cursor=(
                str(result["nextCursor"]) if result.get("nextCursor") is not None else None
            ),
        )
