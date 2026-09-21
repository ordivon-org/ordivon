from __future__ import annotations

import hashlib
import json
from importlib.metadata import version as package_version
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
from .routes import CapabilityRoute, default_routes
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
            gateway_version=package_version("ordivon-gateway"),
            owners=owners,
            capabilities=sorted(self._routes),
        )

    async def capability_describe(self, capability: str | None = None) -> CapabilityProjection:
        if capability is not None:
            route = self._routes.get(capability)
            if route is None:
                raise GatewayError(f"unknown capability: {capability}")
            selected = [route]
        else:
            selected = [self._routes[key] for key in sorted(self._routes)]

        runtime_cache: dict[str, tuple[dict[str, Any] | None, str | None]] = {}

        async def runtime_description(
            owner_id: str,
        ) -> tuple[dict[str, Any] | None, str | None]:
            cached = runtime_cache.get(owner_id)
            if cached is not None:
                return cached
            if not _configured(self._caller, owner_id):
                value = (None, None)
                runtime_cache[owner_id] = value
                return value
            try:
                result = await self._caller.call_tool(
                    owner_id, "runtime.describe", {"schemaVersion": 1}
                )
                value = (result, None)
            except Exception as exc:
                value = (
                    None,
                    f"{type(exc).__name__}: {str(exc)[:240]}",
                )
            runtime_cache[owner_id] = value
            return value

        async def execution_descriptor(route: CapabilityRoute) -> CapabilityDescriptor:
            configured_at_gateway = _configured(self._caller, route.owner_id)
            if not configured_at_gateway:
                return CapabilityDescriptor(
                    capability=route.capability,
                    owner_id=route.owner_id,
                    category=route.category,
                    configured=False,
                    available=False,
                    context_mode=route.context_mode,  # type: ignore[arg-type]
                    truth_boundary=route.truth_boundary,
                )

            result, error = await runtime_description(route.owner_id)
            if result is None:
                return CapabilityDescriptor(
                    capability=route.capability,
                    owner_id=route.owner_id,
                    category=route.category,
                    configured=True,
                    available=False,
                    context_mode=route.context_mode,  # type: ignore[arg-type]
                    observation_error=error,
                    truth_boundary=route.truth_boundary,
                )

            target = next(
                (
                    item
                    for item in result.get("targets", [])
                    if isinstance(item, dict) and item.get("target") == route.execution_target
                ),
                None,
            )
            if target is None:
                return CapabilityDescriptor(
                    capability=route.capability,
                    owner_id=route.owner_id,
                    category=route.category,
                    configured=False,
                    available=False,
                    context_mode=route.context_mode,  # type: ignore[arg-type]
                    observation_error="owner did not advertise the routed execution target",
                    truth_boundary=route.truth_boundary,
                )

            node = result.get("node")
            node_id = (
                str(node["nodeId"])
                if isinstance(node, dict) and isinstance(node.get("nodeId"), str)
                else None
            )
            context_key = (
                "windowsAuthorities"
                if route.execution_target == "windows_native"
                else "executionProfiles"
            )
            contexts = [
                str(value) for value in target.get(context_key, []) if isinstance(value, str)
            ]
            return CapabilityDescriptor(
                capability=route.capability,
                owner_id=route.owner_id,
                category=route.category,
                configured=bool(target.get("configured", False)),
                available=bool(target.get("available", False)),
                context_mode=route.context_mode,  # type: ignore[arg-type]
                contexts=contexts,
                owner_node_id=node_id,
                truth_boundary=route.truth_boundary,
            )

        values: list[CapabilityDescriptor] = []
        for route in selected:
            if route.category == "execution":
                values.append(await execution_descriptor(route))
                continue

            if route.capability == "continuity.external":
                configured = _configured(self._caller, "host")
                available = False
                error: str | None = None
                if configured:
                    try:
                        await self._caller.call_tool(
                            "host",
                            "task.list",
                            {"limit": 1, "includeTerminal": False},
                        )
                        available = True
                    except Exception as exc:
                        error = f"{type(exc).__name__}: {str(exc)[:240]}"
                values.append(
                    CapabilityDescriptor(
                        capability=route.capability,
                        owner_id=route.owner_id,
                        category=route.category,
                        configured=configured,
                        available=available,
                        context_mode=route.context_mode,  # type: ignore[arg-type]
                        observation_error=error,
                        truth_boundary=route.truth_boundary,
                    )
                )
                continue

            if route.capability == "artifact.runtime":
                nodes: list[str] = []
                available = False
                any_configured = False
                errors: list[str] = []
                for owner_id in ("runtime.linux", "runtime.windows"):
                    if not _configured(self._caller, owner_id):
                        continue
                    any_configured = True
                    result, error = await runtime_description(owner_id)
                    if error is not None:
                        errors.append(f"{owner_id}: {error}")
                        continue
                    if result is None:
                        continue
                    node = result.get("node")
                    node_id = (
                        str(node["nodeId"])
                        if isinstance(node, dict) and isinstance(node.get("nodeId"), str)
                        else None
                    )
                    owner_available = any(
                        isinstance(item, dict)
                        and bool(item.get("configured", False))
                        and bool(item.get("available", False))
                        for item in result.get("targets", [])
                    )
                    if owner_available:
                        available = True
                        if node_id is not None:
                            nodes.append(node_id)
                values.append(
                    CapabilityDescriptor(
                        capability=route.capability,
                        owner_id=route.owner_id,
                        category=route.category,
                        configured=any_configured,
                        available=available,
                        context_mode=route.context_mode,  # type: ignore[arg-type]
                        owner_node_ids=sorted(set(nodes)),
                        observation_error="; ".join(errors) if errors else None,
                        truth_boundary=route.truth_boundary,
                    )
                )
                continue

            values.append(
                CapabilityDescriptor(
                    capability=route.capability,
                    owner_id=route.owner_id,
                    category=route.category,
                    configured=False,
                    available=False,
                    context_mode=route.context_mode,  # type: ignore[arg-type]
                    observation_error="no projection adapter for capability",
                    truth_boundary=route.truth_boundary,
                )
            )

        payload = [value.model_dump(mode="json") for value in values]
        digest = (
            "sha256:"
            + hashlib.sha256(
                json.dumps(
                    payload,
                    sort_keys=True,
                    separators=(",", ":"),
                    ensure_ascii=False,
                ).encode("utf-8")
            ).hexdigest()
        )
        return CapabilityProjection(
            projection_digest=digest,
            capabilities=values,
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
        context: str | None = None,
        env: dict[str, str] | None = None,
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
        if env is not None:
            if not all(
                isinstance(key, str) and key and isinstance(value, str)
                for key, value in env.items()
            ):
                raise GatewayError("env must map non-empty string names to string values")
            execution["env"] = dict(env)
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
        # eventLimit is retained on the northbound surface for connector compatibility.
        # Runtime's execution observation authority is job.observe; Gateway does not
        # project the job.get event timeline, so forwarding eventLimit would add no truth.
        _ = event_limit
        result = await self._caller.call_tool(
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

        if bool(result.get("executionTerminal", False)) or artifacts_available:
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
            artifacts_available=artifacts_available,
            artifact_count=artifact_count,
            artifact_ids=artifacts,
            artifact_projection_complete=artifact_projection_complete,
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
