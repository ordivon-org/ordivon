from __future__ import annotations

import hashlib
import json
from importlib.metadata import version as package_version
from typing import Any

from .contracts import (
    ArtifactChunk,
    CapabilityDescriptor,
    CapabilityProjection,
    CollaborationMessage,
    CollaborationPage,
    CollaborationPostReceipt,
    CollaborationSearch,
    CollaborationSearchHit,
    ContinuityAttention,
    ContinuityChanges,
    ContinuityEvent,
    ContinuityItem,
    ContinuityMutationReceipt,
    ContinuityObservation,
    ContinuityObserved,
    ContinuityPage,
    ExecutionObservation,
    ExecutionReceipt,
    ExecutionResolution,
    OwnerDescriptor,
    SystemDescription,
)
from .external_worker import ExternalPullWorkerTransport, WorkerConflict
from .routes import CapabilityRoute, default_routes
from .upstream import OwnerToolCaller


class GatewayError(RuntimeError):
    pass


_OWNER_ROLES = {
    "runtime.linux": "physical execution owner",
    "runtime.windows": "physical execution owner",
    "host": "external semantic continuity owner",
    "external.pull": "provider-neutral outbound pull execution transport",
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
    if owner_id not in {"runtime.linux", "runtime.windows", "external.pull"} or not native_id:
        raise GatewayError("unsupported execution operationRef owner")
    return owner_id, native_id


def _required_str(payload: dict[str, Any], key: str) -> str:
    value = payload.get(key)
    if not isinstance(value, str) or not value:
        raise GatewayError(f"owner response omitted {key}")
    return value


def _optional_str(payload: dict[str, Any], key: str) -> str | None:
    value = payload.get(key)
    if value is None:
        return None
    if not isinstance(value, str):
        raise GatewayError(f"owner response has invalid {key}")
    return value


def _collaboration_message(payload: dict[str, Any]) -> CollaborationMessage:
    return CollaborationMessage(
        sequence=int(payload["sequence"]),
        client_message_id=_required_str(payload, "clientMessageId"),
        author_label=_required_str(payload, "authorLabel"),
        author_identity_role=_required_str(payload, "authorIdentityRole"),
        message_kind=_required_str(payload, "messageKind"),
        topic=_optional_str(payload, "topic"),
        message=_required_str(payload, "message"),
        reply_to_client_message_id=_optional_str(payload, "replyToClientMessageId"),
        task_id=_optional_str(payload, "taskId"),
        recorded_at_ms=int(payload["recordedAtMs"]),
        message_digest=_required_str(payload, "messageDigest"),
        truth_role=_required_str(payload, "truthRole"),
    )


class GatewayService:
    def __init__(
        self,
        caller: OwnerToolCaller,
        routes: dict[str, CapabilityRoute] | None = None,
        *,
        external_workers: ExternalPullWorkerTransport | None = None,
    ) -> None:
        self._caller = caller
        self._routes = routes or default_routes()
        self._external_workers = external_workers

    def system_describe(self) -> SystemDescription:
        owners = [
            OwnerDescriptor(
                owner_id=owner_id,
                role=role,
                configured=(
                    self._external_workers is not None
                    if owner_id == "external.pull"
                    else _configured(self._caller, owner_id)
                ),
            )
            for owner_id, role in _OWNER_ROLES.items()
            if owner_id != "external.pull" or self._external_workers is not None
        ]
        capabilities = set(self._routes)
        if self._external_workers is not None:
            capabilities.update(self._external_workers.capability_projection())
        return SystemDescription(
            gateway_version=package_version("ordivon-gateway"),
            owners=owners,
            capabilities=sorted(capabilities),
        )

    async def capability_describe(self, capability: str | None = None) -> CapabilityProjection:
        external_projection = (
            self._external_workers.capability_projection()
            if self._external_workers is not None
            else {}
        )
        if capability is not None:
            route = self._routes.get(capability)
            if route is None and capability not in external_projection:
                raise GatewayError(f"unknown capability: {capability}")
            selected = [route] if route is not None else []
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
            context_mode = route.context_mode
            if route.execution_target == "windows_native":
                structured_contexts = target.get("windowsContexts")
                if isinstance(structured_contexts, list) and any(
                    isinstance(value, dict) for value in structured_contexts
                ):
                    contexts = [
                        dict(value) for value in structured_contexts if isinstance(value, dict)
                    ]
                    context_mode = "provider-defined-json"
                else:
                    contexts = [
                        str(value)
                        for value in target.get("windowsAuthorities", [])
                        if isinstance(value, str)
                    ]
                    context_mode = "provider-defined-string"
            else:
                contexts = [
                    str(value)
                    for value in target.get("executionProfiles", [])
                    if isinstance(value, str)
                ]
            return CapabilityDescriptor(
                capability=route.capability,
                owner_id=route.owner_id,
                category=route.category,
                configured=bool(target.get("configured", False)),
                available=bool(target.get("available", False)),
                context_mode=context_mode,  # type: ignore[arg-type]
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

        external_keys = (
            [capability]
            if capability is not None and capability in external_projection
            else sorted(external_projection)
            if capability is None
            else []
        )
        for external_capability in external_keys:
            nodes = external_projection[external_capability]
            values.append(
                CapabilityDescriptor(
                    capability=external_capability,
                    owner_id="external.pull",
                    category="execution",
                    configured=True,
                    available=bool(nodes),
                    context_mode="none",
                    owner_node_ids=nodes,
                    truth_boundary=(
                        "External worker transport owns queue/lease/attempt delivery mechanics only; "
                        "workers do not acquire Task ownership or domain authority."
                    ),
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
            terminal=bool(result.get("executionTerminal", False)),
            delivery_disposition=(
                str(result["deliveryDisposition"])
                if result.get("deliveryDisposition") is not None
                else None
            ),
        )

    async def execution_resolve(self, *, capability: str, request_id: str) -> ExecutionResolution:
        route = self._routes.get(capability)
        if route is None and self._external_workers is not None:
            operation = self._external_workers.resolve(capability, request_id)
            if operation is None:
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
            )
        if route is None:
            raise GatewayError(f"unknown capability: {capability}")
        if route.category != "execution" or route.owner_tool != "workspace.exec":
            raise GatewayError(f"capability is not executable: {capability}")
        if not request_id:
            raise GatewayError("requestId is required")

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
        return ExecutionResolution(
            request_id=request_id,
            capability=capability,
            owner_id=route.owner_id,
            resolution="found",
            operation_ref=_execution_ref(route.owner_id, native_id),
            native_id=native_id,
        )

    async def execution_get(
        self, operation_ref: str, *, event_limit: int = 10, wait_ms: int = 0
    ) -> ExecutionObservation:
        owner_id, native_id = _parse_execution_ref(operation_ref)
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
                delivery_disposition="committed" if operation.terminal else "in_progress",
                execution_disposition=(
                    "succeeded"
                    if operation.terminal and operation.exit_code == 0
                    else "failed"
                    if operation.terminal and operation.exit_code is not None
                    else None
                ),
                exit_code=operation.exit_code,
                recovery_required=False,
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
            created_at=_optional_str(task, "created_at"),
            updated_at=_optional_str(task, "updated_at"),
            checkpoint=checkpoint,
            truth_boundary=(
                str(result["truthBoundary"]) if result.get("truthBoundary") is not None else None
            ),
        )

    async def continuity_list(
        self,
        *,
        goal_id: str | None = None,
        runtime_workspace_id: str | None = None,
        limit: int = 50,
        cursor: str | None = None,
        include_terminal: bool = False,
        sort_key: str = "created",
    ) -> ContinuityPage:
        if sort_key not in {"created", "updated"}:
            raise GatewayError("continuity sort_key must be created or updated")
        arguments: dict[str, Any] = {
            "limit": limit,
            "includeTerminal": include_terminal,
        }
        if goal_id is not None:
            arguments["goalId"] = goal_id
        if runtime_workspace_id is not None:
            arguments["runtimeWorkspaceId"] = runtime_workspace_id
        if cursor is not None:
            arguments["cursor"] = cursor
        if sort_key != "created":
            arguments["sortKey"] = sort_key
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
                    created_at=_optional_str(task, "created_at"),
                    updated_at=_optional_str(task, "updated_at"),
                )
            )
        return ContinuityPage(
            items=items,
            has_more=bool(result.get("hasMore", False)),
            next_cursor=(
                str(result["nextCursor"]) if result.get("nextCursor") is not None else None
            ),
            sort_key=sort_key,
        )

    async def continuity_observe(
        self, task_id: str, *, expected_revision: int | None = None, event_limit: int = 5
    ) -> ContinuityObserved:
        arguments: dict[str, Any] = {"taskId": task_id, "eventLimit": event_limit}
        if expected_revision is not None:
            arguments["expectedRevision"] = expected_revision
        result = await self._caller.call_tool("host", "task.observe", arguments)
        task = result.get("task")
        if not isinstance(task, dict):
            raise GatewayError("Host task.observe omitted task")
        checkpoint = task.get("checkpoint")
        if not isinstance(checkpoint, dict):
            raise GatewayError("Host task.observe omitted checkpoint")
        events: list[ContinuityEvent] = []
        for event in result.get("recentEvents", []):
            if isinstance(event, dict):
                events.append(
                    ContinuityEvent(
                        revision=int(event["revision"]),
                        event_type=_required_str(event, "eventType"),
                        state=_required_str(event, "state"),
                        created_at=_required_str(event, "createdAt"),
                    )
                )
        return ContinuityObserved(
            task_id=_required_str(task, "task_id"),
            goal_id=_optional_str(task, "goal_id"),
            revision=int(task["revision"]),
            state=_required_str(task, "state"),
            checkpoint_digest=_optional_str(task, "checkpoint_digest"),
            created_at=_optional_str(task, "created_at"),
            updated_at=_optional_str(task, "updated_at"),
            checkpoint=checkpoint,
            recent_events=events,
            truth_boundary=_optional_str(result, "truthBoundary"),
        )

    async def continuity_adopt(
        self,
        *,
        task_id: str,
        goal_id: str,
        checkpoint: dict[str, Any],
        writer_label: str | None = None,
    ) -> ContinuityMutationReceipt:
        arguments: dict[str, Any] = {
            "taskId": task_id,
            "goalId": goal_id,
            "initialCheckpoint": checkpoint,
        }
        if writer_label is not None:
            arguments["writerLabel"] = writer_label
        return self._continuity_mutation(
            await self._caller.call_tool("host", "task.adopt", arguments)
        )

    async def continuity_checkpoint(
        self,
        *,
        task_id: str,
        expected_revision: int,
        checkpoint: dict[str, Any],
        disposition: str = "continue",
        writer_label: str | None = None,
    ) -> ContinuityMutationReceipt:
        if disposition not in {"continue", "complete", "abandon"}:
            raise GatewayError("invalid continuity disposition")
        arguments: dict[str, Any] = {
            "taskId": task_id,
            "expectedRevision": expected_revision,
            "checkpoint": checkpoint,
            "continuityDisposition": disposition,
        }
        if writer_label is not None:
            arguments["writerLabel"] = writer_label
        return self._continuity_mutation(
            await self._caller.call_tool("host", "task.checkpoint", arguments)
        )

    @staticmethod
    def _continuity_mutation(result: dict[str, Any]) -> ContinuityMutationReceipt:
        task = result.get("task")
        checkpoint = result.get("checkpoint")
        if not isinstance(task, dict) or not isinstance(checkpoint, dict):
            raise GatewayError("Host continuity mutation omitted task/checkpoint")
        return ContinuityMutationReceipt(
            task_id=_required_str(task, "task_id"),
            goal_id=_optional_str(task, "goal_id"),
            revision=int(task["revision"]),
            state=_required_str(task, "state"),
            checkpoint_digest=_optional_str(task, "checkpoint_digest"),
            created_at=_optional_str(task, "created_at"),
            updated_at=_optional_str(task, "updated_at"),
            checkpoint=checkpoint,
            admission=_required_str(result, "admission"),
            writer_label=_optional_str(result, "writerLabel"),
            truth_boundary=_optional_str(result, "truthBoundary")
            or "Host owns semantic continuity state; Gateway is a non-authoritative projection.",
        )

    async def continuity_attention(
        self, *, after_sequence: int, limit: int = 100
    ) -> ContinuityAttention:
        result = await self._caller.call_tool(
            "host", "attention.delta", {"afterSequence": after_sequence, "limit": limit}
        )
        board_fence, summary = result.get("boardFence"), result.get("summary")
        routed, unrouted = result.get("routedTasks"), result.get("unroutedMessages")
        if (
            not isinstance(board_fence, dict)
            or not isinstance(summary, dict)
            or not isinstance(routed, list)
            or not isinstance(unrouted, list)
        ):
            raise GatewayError("Host attention.delta omitted projection fields")
        return ContinuityAttention(
            board_fence=board_fence,
            summary=summary,
            routed_tasks=[x for x in routed if isinstance(x, dict)],
            unrouted_messages=[x for x in unrouted if isinstance(x, dict)],
            truth_boundary=_optional_str(result, "truthBoundary"),
        )

    async def continuity_changes(
        self, *, after_sequence: int, limit: int = 100
    ) -> ContinuityChanges:
        legacy = await self.continuity_attention(after_sequence=after_sequence, limit=limit)
        return ContinuityChanges(
            board_fence=legacy.board_fence,
            summary=legacy.summary,
            routed_tasks=legacy.routed_tasks,
            unrouted_messages=legacy.unrouted_messages,
            truth_boundary=legacy.truth_boundary,
        )

    async def collaboration_post(
        self,
        *,
        client_message_id: str,
        author_label: str,
        message: str,
        message_kind: str = "note",
        topic: str | None = None,
        reply_to_client_message_id: str | None = None,
        task_id: str | None = None,
    ) -> CollaborationPostReceipt:
        arguments: dict[str, Any] = {
            "clientMessageId": client_message_id,
            "authorLabel": author_label,
            "message": message,
            "messageKind": message_kind,
        }
        if topic is not None:
            arguments["topic"] = topic
        if reply_to_client_message_id is not None:
            arguments["replyToClientMessageId"] = reply_to_client_message_id
        if task_id is not None:
            arguments["taskId"] = task_id
        result = await self._caller.call_tool("host", "board.post", arguments)
        payload = result.get("message")
        if not isinstance(payload, dict):
            raise GatewayError("Host board.post omitted message")
        return CollaborationPostReceipt(
            admission=_required_str(result, "admission"),
            message=_collaboration_message(payload),
            truth_boundary=_optional_str(result, "truthBoundary"),
        )

    async def collaboration_publish(
        self,
        *,
        client_message_id: str,
        author_label: str,
        message: str,
        scope: str,
        continuity_id: str | None = None,
        message_kind: str = "note",
        topic: str | None = None,
        reply_to_client_message_id: str | None = None,
    ) -> CollaborationPostReceipt:
        """Publish collaboration with an explicit global or continuity scope."""
        if scope == "global":
            if continuity_id is not None:
                raise GatewayError("global collaboration scope must not include continuity_id")
            if reply_to_client_message_id is not None:
                raise GatewayError(
                    "global collaboration.publish cannot reply to an existing message because "
                    "Host reply routing may inherit continuity scope"
                )
            task_id = None
        elif scope == "continuity":
            if not continuity_id:
                raise GatewayError("continuity collaboration scope requires continuity_id")
            task_id = continuity_id
        else:
            raise GatewayError("collaboration scope must be global or continuity")
        return await self.collaboration_post(
            client_message_id=client_message_id,
            author_label=author_label,
            message=message,
            message_kind=message_kind,
            topic=topic,
            reply_to_client_message_id=reply_to_client_message_id,
            task_id=task_id,
        )

    async def collaboration_list(
        self,
        *,
        after_sequence: int | None = None,
        limit: int = 50,
        topic: str | None = None,
        client_message_id: str | None = None,
        reply_to_client_message_id: str | None = None,
        reply_to_author_label: str | None = None,
    ) -> CollaborationPage:
        arguments: dict[str, Any] = {"limit": limit}
        optional = {
            "afterSequence": after_sequence,
            "topic": topic,
            "clientMessageId": client_message_id,
            "replyToClientMessageId": reply_to_client_message_id,
            "replyToAuthorLabel": reply_to_author_label,
        }
        arguments.update({k: v for k, v in optional.items() if v is not None})
        result = await self._caller.call_tool("host", "board.list", arguments)
        rows = result.get("messages")
        if not isinstance(rows, list):
            raise GatewayError("Host board.list omitted messages")
        return CollaborationPage(
            messages=[_collaboration_message(x) for x in rows if isinstance(x, dict)],
            last_sequence=int(result["lastSequence"]),
            next_after_sequence=int(result["nextAfterSequence"]),
            has_more=bool(result.get("hasMore", False)),
            truth_boundary=_optional_str(result, "truthBoundary"),
        )

    async def collaboration_search(self, query: str, *, limit: int = 20) -> CollaborationSearch:
        result = await self._caller.call_tool(
            "host", "board.search", {"query": query, "limit": limit}
        )
        hits = [
            CollaborationSearchHit(
                sequence=int(x["sequence"]), client_message_id=_required_str(x, "clientMessageId")
            )
            for x in result.get("results", [])
            if isinstance(x, dict)
        ]
        return CollaborationSearch(
            source_snapshot_high_water=int(result["sourceSnapshotHighWater"]),
            live_high_water=int(result["liveHighWater"]),
            negative_result_authoritative=bool(result.get("negativeResultAuthoritative", False)),
            requires_exact_source_reentry=bool(result.get("requiresExactSourceReentry", True)),
            results=hits,
        )
