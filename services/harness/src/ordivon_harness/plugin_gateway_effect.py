from __future__ import annotations

from dataclasses import dataclass

from anc_canonical import JsonValue, canonical_digest, validate_json_value

from .agent_plugin import AgentPluginMcpComponent
from .agent_tool_observation import HarnessToolObservation
from .core_contracts import HarnessRunContract
from .execution_binding import HarnessExecutionBinding
from .ordivon.model import AgentToolCall, AgentToolDefinition
from .ordivon.run_store_port import HarnessRunContinuityStore
from .ordivon.sqlite_runtime_bridge import SQLiteHarnessRuntimeBridge
from .ordivon.tool_errors import ToolBridgeError, ToolBridgeErrorKind
from .plugin_mcp import HarnessMcpClient
from .protocol import HarnessRecoveryConsequence
from .runtime_port import HarnessRuntimeClientError


@dataclass(frozen=True, slots=True)
class PluginGatewayExecutionGrant:
    capability: str
    workspace_id: str
    executable_allowlist: tuple[str, ...]
    context: str | None = None
    env_allowlist: tuple[str, ...] = ()
    max_timeout_ms: int = 300_000

    def __post_init__(self) -> None:
        if (
            not self.capability.startswith("execution.")
            or self.capability != self.capability.strip()
        ):
            raise ValueError("Gateway execution capability must be one trimmed execution.* name")
        if not self.workspace_id or self.workspace_id != self.workspace_id.strip():
            raise ValueError("Gateway execution workspace must be non-empty and trimmed")
        if (
            not self.executable_allowlist
            or len(self.executable_allowlist) != len(set(self.executable_allowlist))
            or tuple(sorted(self.executable_allowlist)) != self.executable_allowlist
            or any(not item or item != item.strip() for item in self.executable_allowlist)
        ):
            raise ValueError(
                "Gateway executable allowlist must be non-empty, unique, sorted, and trimmed"
            )
        if (
            len(self.env_allowlist) != len(set(self.env_allowlist))
            or tuple(sorted(self.env_allowlist)) != self.env_allowlist
            or any(not item or item != item.strip() for item in self.env_allowlist)
        ):
            raise ValueError("Gateway environment allowlist must be unique, sorted, and trimmed")
        if self.context is not None and (not self.context or self.context != self.context.strip()):
            raise ValueError("Gateway execution context must be trimmed")
        if type(self.max_timeout_ms) is not int or not 1 <= self.max_timeout_ms <= 900_000:
            raise ValueError("Gateway execution timeout bound must be between 1 and 900000 ms")

    def to_dict(self) -> dict[str, JsonValue]:
        return {
            "schemaVersion": 1,
            "kind": "ordivon.plugin-gateway-execution-grant",
            "capability": self.capability,
            "workspaceId": self.workspace_id,
            "executableAllowlist": list(self.executable_allowlist),
            "context": self.context,
            "envAllowlist": list(self.env_allowlist),
            "maxTimeoutMs": self.max_timeout_ms,
            "authorityBoundary": (
                "caller-selected fixed target and allow-by-exception process authority; "
                "the model cannot choose capability, workspace, context, credentials, or request identity"
            ),
        }


def _model_execution_definition(grant: PluginGatewayExecutionGrant) -> AgentToolDefinition:
    return AgentToolDefinition(
        name="execution.submit",
        description=(
            "Run one caller-authorized process through the Ordivon Gateway. "
            "Capability, workspace, context, request identity, and authority references are fixed by the Host."
        ),
        input_schema={
            "type": "object",
            "properties": {
                "executable": {"type": "string", "enum": list(grant.executable_allowlist)},
                "args": {"type": "array", "items": {"type": "string"}},
                "cwdRelative": {"type": "string"},
                "env": {
                    "type": "object",
                    "propertyNames": {"enum": list(grant.env_allowlist)},
                    "additionalProperties": {"type": "string"},
                },
                "timeoutMs": {
                    "type": "integer",
                    "minimum": 1,
                    "maximum": grant.max_timeout_ms,
                },
            },
            "required": ["executable", "args"],
            "additionalProperties": False,
        },
    )


def _tool_digest(raw: dict[str, JsonValue]) -> str:
    value = {
        "name": raw.get("name"),
        "description": raw.get("description"),
        "inputSchema": raw.get("inputSchema"),
        "outputSchema": raw.get("outputSchema"),
    }
    validate_json_value(value)
    return canonical_digest(value)


def _required_text(value: object, label: str) -> str:
    if not isinstance(value, str) or not value:
        raise HarnessRuntimeClientError(f"Gateway {label} is missing")
    return value


def _gateway_field(payload: dict[str, JsonValue], snake: str, camel: str) -> JsonValue | None:
    if snake in payload:
        return payload[snake]
    return payload.get(camel)


class GatewayMcpRuntimeAdapter:
    """Translate the Gateway public execution projection into the existing Runtime port.

    This adapter deliberately preserves Runtime as the physical execution owner. Gateway
    adds routing and a recovery lookup, while Harness retains durable intent/fence/receipt
    authority.
    """

    def __init__(
        self,
        component: AgentPluginMcpComponent,
        client: HarnessMcpClient,
        grant: PluginGatewayExecutionGrant,
    ) -> None:
        self.component = component
        self.client = client
        self.grant = grant
        self._operation_refs: dict[str, str] = {}

    def _call(self, name: str, arguments: dict[str, JsonValue]) -> dict[str, JsonValue]:
        try:
            is_error, payload = self.client.call_tool(name, arguments)
        except Exception as exc:
            raise HarnessRuntimeClientError(
                f"Gateway MCP {name} transport/protocol failure: {type(exc).__name__}: {exc}"
            ) from exc
        if is_error:
            raise HarnessRuntimeClientError(f"Gateway MCP {name} returned an error result")
        validate_json_value(payload)
        return payload

    def call_tool(self, name: str, arguments: dict[str, JsonValue]) -> dict[str, JsonValue]:
        if name == "workspace.exec":
            return self._submit(arguments)
        if name == "job.list":
            return self._resolve(arguments)
        if name == "job.observe":
            return self._observe(arguments)
        raise HarnessRuntimeClientError(f"Gateway adapter does not expose Runtime operation {name}")

    def _submit(self, arguments: dict[str, JsonValue]) -> dict[str, JsonValue]:
        request_id = _required_text(arguments.get("clientRequestId"), "clientRequestId")
        execution = arguments.get("execution")
        if not isinstance(execution, dict):
            raise HarnessRuntimeClientError("Gateway execution lowering omitted execution")
        if execution.get("workspaceId") != self.grant.workspace_id:
            raise HarnessRuntimeClientError(
                "Gateway execution lowering changed workspace authority"
            )
        foreign = execution.get("foreignReferences")
        if not isinstance(foreign, list) or any(not isinstance(item, dict) for item in foreign):
            raise HarnessRuntimeClientError(
                "Gateway execution lowering omitted authority references"
            )
        gateway_args: dict[str, JsonValue] = {
            "capability": self.grant.capability,
            "requestId": request_id,
            "workspaceId": self.grant.workspace_id,
            "executable": _required_text(execution.get("executable"), "executable"),
            "args": execution.get("args", []),
            "cwdRelative": execution.get("cwdRelative", "."),
            "authorityReferences": foreign,
        }
        if self.grant.context is not None:
            gateway_args["context"] = self.grant.context
        if "env" in execution:
            gateway_args["env"] = execution["env"]
        if "timeoutMs" in execution:
            gateway_args["timeoutMs"] = execution["timeoutMs"]

        receipt = self._call("execution.submit", gateway_args)
        operation_ref = _required_text(
            _gateway_field(receipt, "operation_ref", "operationRef"), "operationRef"
        )
        native_id = _required_text(_gateway_field(receipt, "native_id", "nativeId"), "nativeId")
        self._operation_refs[native_id] = operation_ref
        terminal = _gateway_field(receipt, "terminal", "terminal")
        if terminal is True:
            return self._observe_operation(operation_ref, native_id, wait_ms=0)
        if terminal is not False:
            raise HarnessRuntimeClientError("Gateway execution receipt omitted terminal")
        return {
            "jobId": native_id,
            "status": _required_text(receipt.get("state"), "state"),
            "executionTerminal": False,
            "executionDisposition": None,
            "deliveryDisposition": (
                _gateway_field(receipt, "delivery_disposition", "deliveryDisposition")
                or "in_progress"
            ),
            "recoveryRequired": False,
            "resultAvailable": False,
            "semanticCompletionEvaluated": False,
            "artifactsAvailable": False,
            "artifacts": [],
        }

    def _resolve(self, arguments: dict[str, JsonValue]) -> dict[str, JsonValue]:
        request_id = _required_text(arguments.get("clientRequestId"), "clientRequestId")
        resolution = self._call(
            "execution.resolve",
            {"capability": self.grant.capability, "requestId": request_id},
        )
        state = _required_text(resolution.get("resolution"), "resolution")
        if state == "absent":
            return {"jobs": [], "nextCursor": None}
        if state != "found":
            raise HarnessRuntimeClientError(f"Gateway execution resolution is {state}")
        native_id = _required_text(_gateway_field(resolution, "native_id", "nativeId"), "nativeId")
        operation_ref = _required_text(
            _gateway_field(resolution, "operation_ref", "operationRef"), "operationRef"
        )
        self._operation_refs[native_id] = operation_ref
        return {
            "jobs": [{"jobId": native_id, "clientRequestId": request_id}],
            "nextCursor": None,
        }

    def cancel_job(self, native_id: str) -> tuple[str, dict[str, JsonValue]]:
        operation_ref = self._operation_refs.get(native_id)
        if operation_ref is None:
            raise HarnessRuntimeClientError(
                "Gateway operationRef is unknown; reconcile before cancellation"
            )
        receipt = self._call("execution.cancel", {"operationRef": operation_ref})
        if (
            _required_text(_gateway_field(receipt, "native_id", "nativeId"), "nativeId")
            != native_id
        ):
            raise HarnessRuntimeClientError(
                "Gateway cancellation changed native execution identity"
            )
        terminal = _gateway_field(receipt, "terminal", "terminal")
        if not isinstance(terminal, bool):
            raise HarnessRuntimeClientError("Gateway cancellation receipt omitted terminal")
        state = _required_text(receipt.get("state"), "state")
        if terminal and state != "cancelled":
            return "terminal", self._observe_operation(operation_ref, native_id, wait_ms=0)
        return ("cancelled" if terminal else "cancel-requested"), {
            "operationRef": operation_ref,
            "jobId": native_id,
            "state": state,
            "terminal": terminal,
            "cancellationAcknowledged": True,
        }

    def _observe(self, arguments: dict[str, JsonValue]) -> dict[str, JsonValue]:
        native_id = _required_text(arguments.get("jobId"), "jobId")
        operation_ref = self._operation_refs.get(native_id)
        if operation_ref is None:
            raise HarnessRuntimeClientError(
                "Gateway operationRef is unknown; reconcile by clientRequestId first"
            )
        wait_ms = arguments.get("waitMs", 0)
        if type(wait_ms) is not int:
            raise HarnessRuntimeClientError("Gateway waitMs must be integer")
        return self._observe_operation(
            operation_ref, native_id, wait_ms=max(0, min(wait_ms, 30_000))
        )

    def _observe_operation(
        self, operation_ref: str, native_id: str, *, wait_ms: int
    ) -> dict[str, JsonValue]:
        observed = self._call(
            "execution.get",
            {"operationRef": operation_ref, "eventLimit": 10, "waitMs": wait_ms},
        )
        if (
            _required_text(_gateway_field(observed, "native_id", "nativeId"), "nativeId")
            != native_id
        ):
            raise HarnessRuntimeClientError("Gateway observation changed native execution identity")
        terminal = _gateway_field(observed, "terminal", "terminal")
        if not isinstance(terminal, bool):
            raise HarnessRuntimeClientError("Gateway observation omitted terminal")
        delivery = _gateway_field(observed, "delivery_disposition", "deliveryDisposition")
        if not isinstance(delivery, str):
            delivery = "committed" if terminal else "in_progress"
        disposition = _gateway_field(observed, "execution_disposition", "executionDisposition")
        if disposition is not None and not isinstance(disposition, str):
            raise HarnessRuntimeClientError("Gateway executionDisposition is invalid")
        recovery = _gateway_field(observed, "recovery_required", "recoveryRequired")
        if recovery is None:
            recovery = False
        if not isinstance(recovery, bool):
            raise HarnessRuntimeClientError("Gateway recoveryRequired is invalid")
        artifact_ids = _gateway_field(observed, "artifact_ids", "artifactIds")
        if artifact_ids is None:
            artifact_ids = []
        if not isinstance(artifact_ids, list) or any(
            not isinstance(item, str) for item in artifact_ids
        ):
            raise HarnessRuntimeClientError("Gateway artifactIds are invalid")
        return {
            "jobId": native_id,
            "status": _required_text(observed.get("state"), "state"),
            "executionTerminal": terminal,
            "executionDisposition": disposition,
            "deliveryDisposition": delivery,
            "recoveryRequired": recovery,
            "resultAvailable": terminal,
            "semanticCompletionEvaluated": False,
            "exitCode": _gateway_field(observed, "exit_code", "exitCode"),
            "artifactsAvailable": bool(artifact_ids),
            "artifacts": [{"artifactId": item} for item in artifact_ids],
        }


class PluginGatewayExecutionBridge(SQLiteHarnessRuntimeBridge):
    recovery_consequence = HarnessRecoveryConsequence.PROCESS_OR_EXTERNAL_EFFECT_POSSIBLE

    def __init__(
        self,
        contract: HarnessRunContract,
        run_store: HarnessRunContinuityStore,
        execution_binding: HarnessExecutionBinding,
        runtime: GatewayMcpRuntimeAdapter,
        *,
        grant: PluginGatewayExecutionGrant,
        definition: AgentToolDefinition,
        catalog_digest: str,
        grant_digest: str,
        remote_tool_digests: dict[str, str],
        provider_source=None,
    ) -> None:
        self.gateway_grant = grant
        self.gateway_client = runtime.client
        self.gateway_remote_tool_digests = dict(remote_tool_digests)
        super().__init__(
            contract,
            run_store,
            execution_binding,
            runtime,
            provider_source=provider_source,
            tool_definitions=(definition,),
            tool_surface_digest=catalog_digest,
            tool_grant_digest=grant_digest,
        )

    @property
    def grant_digest(self) -> str:
        return self._tool_grant_digest

    def validate_runtime_catalog(self) -> None:
        current: dict[str, str] = {}
        for raw in self.gateway_client.list_tools():
            name = raw.get("name")
            if name in self.gateway_remote_tool_digests:
                current[str(name)] = _tool_digest(raw)
        if current != self.gateway_remote_tool_digests:
            raise ToolBridgeError(
                "Gateway MCP execution/recovery catalog drifted after Run admission",
                kind=ToolBridgeErrorKind.PROTOCOL_INVALID,
            )

    def _control_stop_observation(
        self,
        *,
        tool_call_id: str,
        tool_name: str,
        runtime_job_ref: str,
        query: str | None,
        relative_path: str | None,
        reconciled: bool,
    ) -> HarnessToolObservation | None:
        _ = (query, relative_path)
        try:
            status, payload = self.runtime.cancel_job(runtime_job_ref)
        except HarnessRuntimeClientError as exc:
            return self._unknown_observation(
                tool_call_id,
                tool_name,
                reason=f"Gateway cooperative cancellation could not be acknowledged: {exc}",
                client_request_id=None,
                query=None,
                relative_path=None,
                runtime_job_ref=runtime_job_ref,
                reconciled=True,
            )
        if status == "terminal":
            return self._observation_from_payload(
                tool_call_id,
                tool_name,
                payload,
                query=None,
                relative_path=None,
                reconciled=True,
            )
        return HarnessToolObservation(
            tool_call_id=tool_call_id,
            tool_name=tool_name,
            status=status,
            structured_content=payload,
            runtime_job_ref=runtime_job_ref,
            artifact_refs=(),
            reconciled=reconciled,
        )

    def _lower_runtime_tool_call(
        self, call: AgentToolCall, *, step_id: str
    ) -> tuple[str, dict[str, JsonValue], str | None]:
        if call.name != "execution.submit":
            raise ToolBridgeError(
                f"Gateway execution bridge does not expose {call.name}",
                kind=ToolBridgeErrorKind.MODEL_CORRECTABLE,
            )
        if call.argument_error is not None:
            raise ToolBridgeError(
                f"Gateway execution arguments are invalid: {call.argument_error}",
                kind=ToolBridgeErrorKind.MODEL_CORRECTABLE,
            )
        allowed = {"executable", "args", "cwdRelative", "env", "timeoutMs"}
        unknown = set(call.arguments) - allowed
        if unknown:
            raise ToolBridgeError(
                f"Gateway execution arguments contain unsupported fields: {sorted(unknown)}",
                kind=ToolBridgeErrorKind.MODEL_CORRECTABLE,
            )
        executable = call.arguments.get("executable")
        args = call.arguments.get("args")
        cwd = call.arguments.get("cwdRelative", ".")
        env = call.arguments.get("env")
        timeout = call.arguments.get("timeoutMs")
        if executable not in self.gateway_grant.executable_allowlist:
            raise ToolBridgeError(
                "Gateway executable is outside the caller grant",
                kind=ToolBridgeErrorKind.AUTHORITY_DENIED,
            )
        if not isinstance(args, list) or any(not isinstance(item, str) for item in args):
            raise ToolBridgeError(
                "Gateway args must be strings", kind=ToolBridgeErrorKind.MODEL_CORRECTABLE
            )
        if not isinstance(cwd, str) or not cwd or cwd.startswith("/") or ".." in cwd.split("/"):
            raise ToolBridgeError(
                "Gateway cwdRelative must stay inside the bound workspace",
                kind=ToolBridgeErrorKind.AUTHORITY_DENIED,
            )
        if env is not None:
            if not isinstance(env, dict) or any(
                not isinstance(key, str) or not isinstance(value, str) for key, value in env.items()
            ):
                raise ToolBridgeError(
                    "Gateway env must be a string map",
                    kind=ToolBridgeErrorKind.MODEL_CORRECTABLE,
                )
            if set(env) - set(self.gateway_grant.env_allowlist):
                raise ToolBridgeError(
                    "Gateway environment variable is outside the caller grant",
                    kind=ToolBridgeErrorKind.AUTHORITY_DENIED,
                )
        if timeout is not None and (
            type(timeout) is not int or timeout < 1 or timeout > self.gateway_grant.max_timeout_ms
        ):
            raise ToolBridgeError(
                "Gateway timeout exceeds the caller grant",
                kind=ToolBridgeErrorKind.AUTHORITY_DENIED,
            )

        request_id = (
            "request:harness-gateway:"
            + canonical_digest(
                {
                    "harnessRunId": self.contract.harness_run_id,
                    "stepId": step_id,
                    "toolCallDigest": call.digest,
                    "toolGrantDigest": self.contract.tool_grant_digest,
                }
            )[7:39]
        )
        execution: dict[str, JsonValue] = {
            "workspaceId": self.gateway_grant.workspace_id,
            "executable": executable,
            "args": list(args),
            "cwdRelative": cwd,
            "foreignReferences": [dict(item) for item in self.execution_binding.runtime_references],
        }
        if env is not None:
            execution["env"] = dict(env)
        if timeout is not None:
            execution["timeoutMs"] = timeout
        return (
            "workspace.exec",
            {
                "schemaVersion": 1,
                "clientRequestId": request_id,
                "execution": execution,
            },
            request_id,
        )


class PluginGatewayExecutionBridgeFactory:
    _REQUIRED_REMOTE_TOOLS = (
        "execution.cancel",
        "execution.get",
        "execution.resolve",
        "execution.submit",
    )

    def __init__(
        self,
        component: AgentPluginMcpComponent,
        client: HarnessMcpClient,
        grant: PluginGatewayExecutionGrant,
    ) -> None:
        self.component = component
        self.client = client
        self.execution_grant = grant
        remote: dict[str, dict[str, JsonValue]] = {}
        for raw in client.list_tools():
            name = raw.get("name")
            if isinstance(name, str) and name in self._REQUIRED_REMOTE_TOOLS:
                remote[name] = raw
        missing = sorted(set(self._REQUIRED_REMOTE_TOOLS) - set(remote))
        if missing:
            raise ToolBridgeError(
                f"Gateway MCP omitted execution recovery Tools: {missing}",
                kind=ToolBridgeErrorKind.PROTOCOL_INVALID,
            )
        self._remote_tool_digests = {
            name: _tool_digest(remote[name]) for name in self._REQUIRED_REMOTE_TOOLS
        }
        self._definition = _model_execution_definition(grant)
        surface: dict[str, JsonValue] = {
            "schemaVersion": 1,
            "kind": "ordivon.plugin-gateway-execution-tool-surface",
            "component": component.to_dict(),
            "modelTools": [self._definition.to_dict()],
            "remoteRecoveryToolDigests": dict(self._remote_tool_digests),
        }
        self.catalog_digest = canonical_digest(surface)
        grant_value: dict[str, JsonValue] = {
            "schemaVersion": 1,
            "kind": "ordivon.plugin-gateway-execution-tool-grant",
            "component": component.to_dict(),
            "grant": grant.to_dict(),
            "modelTools": ["execution.submit"],
            "recoveryTools": ["execution.resolve", "execution.get"],
            "controlTools": ["execution.cancel"],
        }
        self.grant_digest = canonical_digest(grant_value)

    def build(
        self,
        contract: HarnessRunContract,
        continuity: HarnessRunContinuityStore,
        *,
        provider_source=None,
    ) -> PluginGatewayExecutionBridge:
        references: tuple[dict[str, JsonValue], ...] = (
            {
                "namespace": "ordivon.harness",
                "type": "harness_run",
                "id": contract.harness_run_id,
            },
            {
                "namespace": "ordivon.harness",
                "type": "run_contract",
                "id": contract.harness_run_id,
                "digest": contract.digest,
            },
            {
                "namespace": "ordivon.harness",
                "type": "tool_grant",
                "id": "plugin-gateway-execution",
                "digest": self.grant_digest,
            },
        )
        binding = HarnessExecutionBinding(
            harness_run_id=contract.harness_run_id,
            workspace_ref=self.execution_grant.workspace_id,
            runtime_references=references,
        )
        runtime = GatewayMcpRuntimeAdapter(self.component, self.client, self.execution_grant)
        return PluginGatewayExecutionBridge(
            contract,
            continuity,
            binding,
            runtime,
            grant=self.execution_grant,
            definition=self._definition,
            catalog_digest=self.catalog_digest,
            grant_digest=self.grant_digest,
            remote_tool_digests=self._remote_tool_digests,
            provider_source=provider_source,
        )


__all__ = [
    "GatewayMcpRuntimeAdapter",
    "PluginGatewayExecutionBridge",
    "PluginGatewayExecutionBridgeFactory",
    "PluginGatewayExecutionGrant",
]
