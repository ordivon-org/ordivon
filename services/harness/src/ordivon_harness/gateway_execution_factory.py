"""Factory for one immutable original Gateway catalog/grant and Run binding.

The factory protects the admission snapshot; the bridge and Runtime MCP
adapter own their separate execution responsibilities.
"""

from __future__ import annotations

from copy import deepcopy

from anc_canonical import JsonValue, canonical_digest

from .agent_plugin import AgentPluginMcpComponent
from .core_contracts import HarnessRunContract
from .execution_binding import HarnessExecutionBinding
from .gateway_execution_bridge import PluginGatewayExecutionBridge
from .gateway_execution_policy import PluginGatewayExecutionGrant, is_original_effect_authority
from .gateway_mcp_runtime import GatewayMcpRuntimeAdapter
from .gateway_mcp_wire import _tool_digest
from .ordivon.model import AgentToolDefinition
from .ordivon.run_store_port import HarnessRunContinuityStore
from .ordivon.tool_errors import ToolBridgeError, ToolBridgeErrorKind
from .plugin_mcp import HarnessMcpClient
from .runtime_port import WorkspaceBoundEffectAdmission


def _model_execution_definition(grant: PluginGatewayExecutionGrant) -> AgentToolDefinition:
    return AgentToolDefinition(
        # DeepSeek/OpenAI function names cannot contain ".". This is the
        # single model-facing alias; the remote MCP operation remains
        # exactly "execution.submit" in GatewayMcpRuntimeAdapter.
        name="execution_submit",
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
                    # The upstream AgentToolCall canonical JSON port deliberately
                    # rejects floating-point spellings, even values such as 1.0
                    # that JSON Schema considers integers. Disclose this narrower
                    # representation contract without claiming Schema equivalence.
                    "description": (
                        "Use a canonical JSON integer token (for example 1000, not 1000.0). "
                        "Omit the property to use the caller-granted limit; null is invalid."
                    ),
                },
            },
            "required": ["executable", "args"],
            "additionalProperties": False,
        },
    )


class PluginGatewayExecutionBridgeFactory:
    _REQUIRED_REMOTE_TOOLS = (
        "execution.cancel",
        "execution.get",
        "execution.resolve",
        "execution.submit",
    )
    _OPTIONAL_REMOTE_TOOLS = ("artifact.read",)

    def __init__(
        self,
        component: AgentPluginMcpComponent,
        client: HarnessMcpClient,
        grant: PluginGatewayExecutionGrant,
        *,
        workspace_admission: WorkspaceBoundEffectAdmission | None = None,
        require_workspace_admission: bool = False,
    ) -> None:
        self.component = component
        self.client = client
        self.execution_grant = grant
        self._workspace_admission = workspace_admission
        self._workspace_admission_required = require_workspace_admission
        # Grant/Catalog digests describe model authority, not the MCP caller
        # identity or native effect-qualification Port selected for this Run.
        # Save constructor provenance: this local identity is no NativeIssuer.
        self._original_client = client
        self._original_workspace_admission = workspace_admission
        self._original_workspace_admission_required = require_workspace_admission
        remote: dict[str, dict[str, JsonValue]] = {}
        for raw in client.list_tools():
            name = raw.get("name")
            if isinstance(name, str) and name in (
                *self._REQUIRED_REMOTE_TOOLS,
                *self._OPTIONAL_REMOTE_TOOLS,
            ):
                if name in remote:
                    raise ToolBridgeError(
                        f"Gateway MCP returned duplicate required Tool: {name}",
                        kind=ToolBridgeErrorKind.PROTOCOL_INVALID,
                    )
                remote[name] = raw
        missing = sorted(set(self._REQUIRED_REMOTE_TOOLS) - set(remote))
        if missing:
            raise ToolBridgeError(
                f"Gateway MCP omitted execution recovery Tools: {missing}",
                kind=ToolBridgeErrorKind.PROTOCOL_INVALID,
            )
        self._remote_tool_digests = {
            name: _tool_digest(raw) for name, raw in sorted(remote.items())
        }
        self._definition = _model_execution_definition(grant)
        self.catalog_digest = self._current_catalog_digest()
        self.grant_digest = self._current_grant_digest()

    def _current_catalog_digest(
        self,
        *,
        component: AgentPluginMcpComponent | None = None,
        definition: AgentToolDefinition | None = None,
        remote_tool_digests: dict[str, str] | None = None,
    ) -> str:
        """Reconstruct the existing ToolSurface from one captured source view."""
        current_component = self.component if component is None else component
        current_definition = self._definition if definition is None else definition
        remote = self._remote_tool_digests if remote_tool_digests is None else remote_tool_digests
        surface: dict[str, JsonValue] = {
            "schemaVersion": 1,
            "kind": "ordivon.plugin-gateway-execution-tool-surface",
            "component": current_component.to_dict(),
            "modelTools": [current_definition.to_dict()],
            "remoteRecoveryToolDigests": dict(remote),
        }
        return canonical_digest(surface)

    def _current_grant_digest(
        self,
        *,
        component: AgentPluginMcpComponent | None = None,
        grant: PluginGatewayExecutionGrant | None = None,
        remote_tool_digests: dict[str, str] | None = None,
    ) -> str:
        """Reconstruct existing ToolGrant without inventing a second RunRoot."""
        current_component = self.component if component is None else component
        current_grant = self.execution_grant if grant is None else grant
        remote = self._remote_tool_digests if remote_tool_digests is None else remote_tool_digests
        if not isinstance(current_grant, PluginGatewayExecutionGrant):
            raise ToolBridgeError(
                "Gateway factory frozen Tool Grant type drifted",
                kind=ToolBridgeErrorKind.AUTHORITY_DENIED,
            )
        grant_value: dict[str, JsonValue] = {
            "schemaVersion": 1,
            "kind": "ordivon.plugin-gateway-execution-tool-grant",
            "component": current_component.to_dict(),
            "grant": current_grant.to_dict(),
            "modelTools": ["execution.submit"],
            "recoveryTools": ["execution.resolve", "execution.get"],
            "controlTools": ["execution.cancel"],
        }
        if "artifact.read" in remote:
            grant_value["outputTools"] = ["artifact.read"]
        return canonical_digest(grant_value)

    def build(
        self,
        contract: HarnessRunContract,
        continuity: HarnessRunContinuityStore,
        *,
        provider_source=None,
    ) -> PluginGatewayExecutionBridge:
        # One SOURCE snapshot before admission; all descendants consume
        # these captured values, never mutable Factory attributes again.
        # Grant and Component are frozen dataclasses, but the Tool definition
        # contains a mutable nested schema and remote digests are a dict.
        component = self.component
        client = self.client
        grant = self.execution_grant
        definition = deepcopy(self._definition)
        remote_tool_digests = dict(self._remote_tool_digests)
        workspace_admission = self._workspace_admission
        require_workspace_admission = self._workspace_admission_required
        frozen_grant_digest = self.grant_digest
        frozen_catalog_digest = self.catalog_digest
        if not is_original_effect_authority(
            effect_client=client,
            original_effect_client=self._original_client,
            admission_port=workspace_admission,
            original_admission_port=self._original_workspace_admission,
            admission_required=require_workspace_admission,
            original_admission_required=self._original_workspace_admission_required,
        ):
            raise ToolBridgeError(
                "Gateway Factory effect client or Native admission policy drifted from original source",
                kind=ToolBridgeErrorKind.AUTHORITY_DENIED,
            )
        if (
            self._current_grant_digest(
                component=component, grant=grant, remote_tool_digests=remote_tool_digests
            ) != frozen_grant_digest
            or self._current_catalog_digest(
                component=component, definition=definition,
                remote_tool_digests=remote_tool_digests,
            ) != frozen_catalog_digest
            or contract.tool_grant_digest != frozen_grant_digest
            or contract.tool_catalog_digest != frozen_catalog_digest
        ):
            raise ToolBridgeError(
                "Gateway factory frozen Tool Grant or catalog drifted from Original Run",
                kind=ToolBridgeErrorKind.AUTHORITY_DENIED,
            )
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
                "digest": frozen_grant_digest,
            },
        )
        binding = HarnessExecutionBinding(
            harness_run_id=contract.harness_run_id,
            workspace_ref=grant.workspace_id,
            runtime_references=references,
        )
        runtime = GatewayMcpRuntimeAdapter(
            component,
            client,
            grant,
            artifact_read_enabled=(
                "artifact.read" in remote_tool_digests
                and contract.privacy.allow_tool_content
            ),
            workspace_admission=workspace_admission,
            require_workspace_admission=require_workspace_admission,
            run_ref=contract.harness_run_id,
            grant_digest=frozen_grant_digest,
        )
        return PluginGatewayExecutionBridge(
            contract,
            continuity,
            binding,
            runtime,
            grant=grant,
            definition=definition,
            catalog_digest=frozen_catalog_digest,
            grant_digest=frozen_grant_digest,
            remote_tool_digests=remote_tool_digests,
            provider_source=provider_source,
            workspace_admission=workspace_admission,
            require_workspace_admission=require_workspace_admission,
        )
