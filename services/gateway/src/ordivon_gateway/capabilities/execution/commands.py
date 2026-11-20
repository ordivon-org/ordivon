from __future__ import annotations

from typing import Any

from ...contracts import (
    CapabilityRoute,
    ExecutionReceipt,
)
from ...logic.capability_projection import project_execution_capability
from ...logic.execution_refs import GatewayError, parse_execution_ref
from ...logic.execution_refs import format_execution_ref as _execution_ref
from ...logic.owner_protocol import (
    OwnerCallError,
    OwnerToolCaller,
    _owner_optional_disposition,
    _owner_receipt_state,
    _required_bool,
    _required_str,
)


def _qualified_profile_switch_failure(
    error: OwnerCallError,
    *,
    owner_id: str,
) -> bool:
    """Only Runtime-native precommit policy denial or exact-key conflict qualifies.

    When the old trusted_local request is already committed, it succeeds
    unchanged. A newly committed contained_local request instead causes an
    exact key/immutable-payload conflict on the trusted default when replayed:
    the one contained_local alternative is safe only because the Runtime
    already reported that original key was occupied. No other error may
    justify a different physical proposal or unbounded retry.
    """
    e = error.error
    return (
        error.owner_id == owner_id
        and error.tool_name == "workspace.exec"
        and isinstance(e, dict)
        and e.get("origin") == "runtime_core"
        and (
            (
                e.get("code") == "AUTHORIZATION_DENIED"
                and e.get("field") == "execution.executionProfile"
            )
            or (e.get("code") == "IDEMPOTENCY_CONFLICT" and "field" not in e)
        )
        and e.get("commitState") == "not_committed"
        and e.get("retryClass") == "never"
        and e.get("retryable") is False
    )


class ExecutionCommandMethods:
    """Gateway owner delegation; authoritative Job and Artifact data stay upstream."""

    _caller: OwnerToolCaller
    _routes: dict[str, CapabilityRoute]

    def __init__(self, caller: OwnerToolCaller, routes: dict[str, CapabilityRoute]) -> None:
        self._caller = caller
        self._routes = routes

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
        stdout_limit_bytes: int | None = None,
        stderr_limit_bytes: int | None = None,
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
        if route.owner_id in {"runtime.linux", "runtime.harness"}:
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
        # Native Runtime already owns the actual allowed output-size bound.
        # Gateway must not silently change the caller's frozen physical
        # request to Runtime's wider defaults when the issuer specified caps.
        for field, value in (
            ("stdoutLimitBytes", stdout_limit_bytes),
            ("stderrLimitBytes", stderr_limit_bytes),
        ):
            if value is not None:
                if type(value) is not int or not 1 <= value <= 2**64 - 1:
                    raise GatewayError(f"{field} must be a positive JSON integer within u64")
                execution[field] = value
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
        try:
            result = await self._caller.call_tool(route.owner_id, route.owner_tool, payload)
        except OwnerCallError as denied:
            # Legacy absent-context requests originally meant trusted_local.
            # They must be replayed with their ORIGINAL immutable payload first:
            # a committed Job cannot be moved to a different executionProfile.
            # Once Runtime proves the NEW trusted default was not admitted
            # (or the key has already committed a different immutable profile),
            # reuse the read-only capability projector to select its only
            # currently admissible contained_local profile. No global cache,
            # second RouteAuthority, or automatic privilege escalation.
            if (
                capability != "execution.linux"
                or context is not None
                or route.default_context != "trusted_local"
                or not _qualified_profile_switch_failure(denied, owner_id=route.owner_id)
            ):
                raise
            description = await self._caller.call_tool(
                route.owner_id, "runtime.describe", {"schemaVersion": 1}
            )
            observed = project_execution_capability(
                route, configured_at_gateway=True, owner_response=description
            )
            # Do not let the projection's filtering of ill-typed context
            # elements silently turn a mixed/unknown inventory into a single
            # qualified profile. This fallback needs exact Owner wire data.
            targets = description.get("targets")
            exact_profiles = (
                [
                    target["executionProfiles"]
                    for target in targets
                    if isinstance(target, dict) and target.get("target") == route.execution_target
                ]
                if isinstance(targets, list)
                else []
            )
            if not (
                observed.configured is True
                and observed.available is True
                and observed.observation_error is None
                and observed.contexts == ["contained_local"]
                and exact_profiles == [["contained_local"]]
            ):
                raise denied
            # A profile denial creates no effect. An idempotency conflict
            # certifies the exact key already exists in Runtime PG: the second
            # call can only recover the existing contained profile, or conflict
            # again. Keep all business fields and identity unchanged.
            next_payload = {
                **payload,
                "execution": {**execution, "executionProfile": "contained_local"},
            }
            result = await self._caller.call_tool(route.owner_id, route.owner_tool, next_payload)
        native_id = _required_str(result, "jobId")
        return ExecutionReceipt(
            operation_ref=_execution_ref(route.owner_id, native_id),
            capability=capability,
            owner_id=route.owner_id,
            native_id=native_id,
            state=_owner_receipt_state(result),
            terminal=_required_bool(result, "executionTerminal"),
            delivery_disposition=_owner_optional_disposition(result, "deliveryDisposition"),
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
                {
                    "runtime.windows": "execution.windows",
                    "runtime.harness": "execution.harness",
                }.get(owner_id, "execution.linux")
            ),
            owner_id=owner_id,
            native_id=observed_native_id,
            state=_owner_receipt_state(result),
            terminal=_required_bool(result, "executionTerminal"),
            delivery_disposition=_owner_optional_disposition(result, "deliveryDisposition"),
        )
