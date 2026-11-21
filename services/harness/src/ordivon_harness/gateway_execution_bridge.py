"""Compose one admitted Gateway Tool into the original Harness Runtime bridge.

Only this module translates model calls into the approved execution request.
It never creates a separate grant/registry, OS runner or Finalizer.
"""

from __future__ import annotations

from anc_canonical import JsonValue, canonical_digest

from .agent_tool_observation import HarnessToolObservation
from .core_contracts import HarnessRunContract
from .execution_binding import HarnessExecutionBinding
from .gateway_execution_policy import (
    PluginGatewayExecutionGrant,
    _forward_granted_timeout,
    authorize_gateway_tool_call,
)
from .gateway_mcp_runtime import GatewayMcpRuntimeAdapter
from .gateway_mcp_wire import _tool_digest
from .ordivon.model import AgentToolCall, AgentToolDefinition
from .ordivon.run_store_port import HarnessRunContinuityStore
from .ordivon.runtime_bridge import HarnessRuntimeBridge
from .ordivon.runtime_lowering import DEFAULT_RUNTIME_EXEC_OUTPUT_LIMIT_BYTES
from .ordivon.tool_errors import ToolBridgeError, ToolBridgeErrorKind
from .protocol import HarnessRecoveryConsequence
from .runtime_port import HarnessRuntimeClientError, WorkspaceBoundEffectAdmission


class PluginGatewayExecutionBridge(HarnessRuntimeBridge):
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
        workspace_admission: WorkspaceBoundEffectAdmission | None = None,
        require_workspace_admission: bool = False,
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
            workspace_admission=workspace_admission,
            require_workspace_admission=require_workspace_admission,
        )

    @property
    def grant_digest(self) -> str:
        return self._tool_grant_digest

    def validate_runtime_catalog(self) -> None:
        current: dict[str, str] = {}
        for raw in self.gateway_client.list_tools():
            name = raw.get("name")
            if name in self.gateway_remote_tool_digests:
                if name in current:
                    raise ToolBridgeError(
                        f"Gateway MCP returned duplicate required Tool: {name}",
                        kind=ToolBridgeErrorKind.PROTOCOL_INVALID,
                    )
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
        executable, args, cwd, env, timeout = authorize_gateway_tool_call(
            self.gateway_grant, call
        )

        # The Run-level MCP catalog preflight only validates a snapshot.
        # Reject a changed Gateway execution/recovery ToolSpec here, before
        # Harness persists any effect intent or dispatches the Runtime call.
        # Recovery of a previously committed ToolStep bypasses lowering and
        # uses the original durable intent and owner reconciliation instead.
        try:
            self.validate_runtime_catalog()
        except ToolBridgeError:
            raise
        except Exception as exc:
            # This failed BEFORE writing a ToolStep intent or invoking the
            # owner. Preserve a typed non-model-correctable protocol failure,
            # not an unstructured Harness crash or a post-dispatch retry.
            raise ToolBridgeError(
                f"Gateway MCP Tool catalog could not be verified: {type(exc).__name__}: {exc}",
                kind=ToolBridgeErrorKind.PROTOCOL_INVALID,
            ) from exc

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
            "stdoutLimitBytes": DEFAULT_RUNTIME_EXEC_OUTPUT_LIMIT_BYTES,
            "stderrLimitBytes": DEFAULT_RUNTIME_EXEC_OUTPUT_LIMIT_BYTES,
            "foreignReferences": [dict(item) for item in self.execution_binding.runtime_references],
        }
        if env is not None:
            execution["env"] = dict(env)
        # Runtime's omitted-timeout default is owned by Runtime and may be
        # wider than this Harness caller's grant. Preserve the explicit
        # capability bound even when the model leaves timeoutMs unspecified.
        execution["timeoutMs"] = _forward_granted_timeout(
            self.gateway_grant.max_timeout_ms, timeout
        )
        return (
            "workspace.exec",
            {
                "schemaVersion": 1,
                "clientRequestId": request_id,
                "execution": execution,
            },
            request_id,
        )
