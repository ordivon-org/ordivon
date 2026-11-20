"""Contract-bound Run composition and lifecycle admission, without Gateway execution policy.

Native Workspace Claims and durable Run state retain their respective Runtime and
Harness owners. Gateway effect authorization lives in gateway_execution_policy.
"""
from __future__ import annotations

from typing import Protocol

from .core_contracts import HarnessRunContract
# Existing import paths remain valid for callers while Gateway policy is isolated.
from .gateway_execution_policy import (
    PluginGatewayExecutionGrant as PluginGatewayExecutionGrant,
    _forward_granted_timeout as _forward_granted_timeout,
    authorize_gateway_tool_call as authorize_gateway_tool_call,
    is_original_effect_authority as is_original_effect_authority,
    require_gateway_workspace_effect as require_gateway_workspace_effect,
)
from .execution_binding import HarnessExecutionBinding
from .ordivon.agent_bridge import NO_TOOL_AGENT_SURFACE_DIGEST, NO_TOOL_AGENT_GRANT_DIGEST
from .ordivon.runtime_bridge import (
    INDEPENDENT_SEARCH_TOOL_SURFACE_DIGEST,
    INDEPENDENT_SEARCH_TOOL_GRANT_DIGEST,
)
from .ordivon.loop import RunBudget
from .ordivon.tool_bridge import ToolBridge
from .runtime_port import (
    HarnessRuntimeClient, HarnessWorkspaceAdmissionUnavailable,
)
from .standalone import HarnessCognitionProfile
from .workspace_claim import NativeWorkspaceClaimClient, WorkspaceRunClaim


from .ordivon.run_store_port import HarnessRunContinuityStore


class HarnessToolBridgeFactory(Protocol):
    catalog_digest: str
    grant_digest: str

    def build(
        self,
        contract: HarnessRunContract,
        continuity: HarnessRunContinuityStore,
        *,
        provider_source=None,
    ) -> ToolBridge: ...


class HarnessAgentRunCompositionError(ValueError):
    """The exact Run Contract cannot be composed by this supported surface."""


class RunCompositionPolicy:
    @staticmethod
    def validate(
        contract: HarnessRunContract,
        *,
        cognition_profile: HarnessCognitionProfile | None,
        execution_binding: HarnessExecutionBinding | None,
        runtime: HarnessRuntimeClient | None,
        tool_bridge: ToolBridge | None,
        tool_bridge_factory: HarnessToolBridgeFactory | None,
    ) -> None:
        """Admit every supported composition fact provable before state creation.

        This does not probe Provider or Runtime availability. It only rejects exact
        caller inputs that cannot lawfully compose the persisted Contract.
        """

        RunBudget.from_contract_dict(contract.budget)
        if cognition_profile is not None:
            if not contract.privacy.allow_model_content:
                raise HarnessAgentRunCompositionError(
                    "Harness cognition requires Contract permission to retain model content"
                )
            if cognition_profile.working_set_history and not contract.privacy.allow_tool_content:
                raise HarnessAgentRunCompositionError(
                    "Harness cognition history requires Tool-content authority"
                )

        if tool_bridge is not None and tool_bridge_factory is not None:
            raise HarnessAgentRunCompositionError(
                "Harness Agent Run accepts either a Tool bridge or a Tool bridge factory, not both"
            )
        custom_bridge = tool_bridge if tool_bridge is not None else tool_bridge_factory

        no_tool = (
            contract.tool_catalog_digest == NO_TOOL_AGENT_SURFACE_DIGEST
            and contract.tool_grant_digest == NO_TOOL_AGENT_GRANT_DIGEST
        )
        runtime_search = (
            contract.tool_catalog_digest == INDEPENDENT_SEARCH_TOOL_SURFACE_DIGEST
            and contract.tool_grant_digest == INDEPENDENT_SEARCH_TOOL_GRANT_DIGEST
        )
        if no_tool:
            if execution_binding is not None or runtime is not None or custom_bridge is not None:
                raise HarnessAgentRunCompositionError(
                    "no-Tool Harness Agent Run must not receive Tool or Runtime authority"
                )
            return
        if runtime_search:
            if custom_bridge is not None:
                raise HarnessAgentRunCompositionError(
                    "built-in Runtime Tool surface must not be replaced by a custom Tool bridge"
                )
            if execution_binding is None or runtime is None:
                raise HarnessAgentRunCompositionError(
                    "Runtime Tool Harness Agent Run requires exact execution binding and Runtime client"
                )
            RunCompositionPolicy._validate_execution_binding(contract, execution_binding)
            return
        if execution_binding is not None or runtime is not None:
            raise HarnessAgentRunCompositionError(
                "custom Tool bridge surface must not receive Runtime execution binding"
            )
        if custom_bridge is None:
            raise HarnessAgentRunCompositionError(
                "Harness Agent Run does not implement this exact Tool surface without an explicit custom Tool bridge"
            )
        if custom_bridge.catalog_digest != contract.tool_catalog_digest:
            raise HarnessAgentRunCompositionError(
                "custom Tool bridge catalog differs from the Run Contract"
            )
        bridge_grant_digest = getattr(custom_bridge, "grant_digest", None)
        if bridge_grant_digest != contract.tool_grant_digest:
            raise HarnessAgentRunCompositionError(
                "custom Tool bridge grant differs from the Run Contract"
            )
        return

    @staticmethod
    def _validate_execution_binding(
        contract: HarnessRunContract,
        execution_binding: HarnessExecutionBinding,
    ) -> None:
        if execution_binding.harness_run_id != contract.harness_run_id:
            raise HarnessAgentRunCompositionError(
                "Harness Execution Binding differs from the independent Run binding"
            )
        references = execution_binding.runtime_references
        if not references:
            raise HarnessAgentRunCompositionError(
                "independent Runtime execution requires foreign references"
            )
        if any(reference["namespace"] != "ordivon.harness" for reference in references):
            raise HarnessAgentRunCompositionError(
                "independent Runtime execution may reference only ordivon.harness authority"
            )
        run_refs = [reference for reference in references if reference["type"] == "harness_run"]
        if len(run_refs) != 1 or run_refs[0]["id"] != contract.harness_run_id:
            raise HarnessAgentRunCompositionError("Harness Execution Binding Run reference differs")
        contract_refs = [
            reference for reference in references if reference["type"] == "run_contract"
        ]
        if len(contract_refs) != 1 or contract_refs[0].get("digest") != contract.digest:
            raise HarnessAgentRunCompositionError(
                "Harness Execution Binding Contract reference differs"
            )
        grant_refs = [reference for reference in references if reference["type"] == "tool_grant"]
        if (
            len(grant_refs) != 1
            or grant_refs[0].get("digest") != INDEPENDENT_SEARCH_TOOL_GRANT_DIGEST
            or contract.tool_grant_digest != INDEPENDENT_SEARCH_TOOL_GRANT_DIGEST
        ):
            raise HarnessAgentRunCompositionError(
                "Harness Execution Binding Tool Grant reference differs"
            )


    @staticmethod
    def select_workspace_claim(
        contract: HarnessRunContract,
        *,
        execution_binding: HarnessExecutionBinding | None,
        tool_bridge: ToolBridge | None,
        tool_bridge_factory: HarnessToolBridgeFactory | None,
        workspace_claim_workspace_id: str | None,
        workspace_claim_client: NativeWorkspaceClaimClient | None,
    ) -> WorkspaceRunClaim | None:
        """Select the exact Workspace from the supported Run's frozen Tool source.

        Native Claims require an authenticated Runtime MCP client distinct from
        Gateway's execution-only client. Pure model and workspace-free custom
        tools remain unchanged; custom Workspace tools declare their ID.
        """
        candidates: list[str] = []
        if execution_binding is not None:
            candidates.append(execution_binding.workspace_ref)
        for source, field in ((tool_bridge_factory, "execution_grant"),
                              (tool_bridge, "gateway_grant")):
            grant = getattr(source, field, None)
            workspace_id = getattr(grant, "workspace_id", None)
            if workspace_id is not None:
                candidates.append(workspace_id)
        if workspace_claim_workspace_id is not None:
            candidates.append(workspace_claim_workspace_id)
        if not candidates:
            return None
        if any(not isinstance(item, str) or not item for item in candidates):
            raise HarnessAgentRunCompositionError("Run Workspace identity is invalid")
        if len(set(candidates)) != 1:
            raise HarnessAgentRunCompositionError("Run Workspace references conflict")
        if workspace_claim_client is None:
            raise HarnessWorkspaceAdmissionUnavailable(
                "Workspace-bearing Run requires authenticated native Runtime Claim client"
            )
        return WorkspaceRunClaim(contract, candidates[0], workspace_claim_client)
