from __future__ import annotations

from typing import Any

from .contracts import (
    ExecutionReceipt,
)
from .execution_refs import GatewayError, parse_execution_ref
from .execution_refs import format_execution_ref as _execution_ref
from .owner_protocol import _required_bool, _required_str
from .routing import CapabilityRoute
from .upstream import OwnerToolCaller


class ExecutionCommandMethods:
    """Gateway owner delegation; authoritative Job and Artifact data stay upstream."""

    _caller: OwnerToolCaller
    _routes: dict[str, CapabilityRoute]

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

    async def execution_cancel(self, operation_ref: str) -> ExecutionReceipt:
        owner_id, native_id = parse_execution_ref(operation_ref)
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
