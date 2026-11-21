"""Harness application authority policy: one location for composition and permissions.

This module makes decisions, not physical effects or durable claims. The Harness
Journal owns Run state, Runtime owns native Workspace HELD/close; the MCP client
owns credential materialization. Never interpret a grant as an OS spawn receipt.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Protocol

from anc_canonical import JsonValue

from .core_contracts import HarnessRunContract
from .execution_binding import HarnessExecutionBinding
from .ordivon.agent_bridge import NO_TOOL_AGENT_SURFACE_DIGEST, NO_TOOL_AGENT_GRANT_DIGEST
from .ordivon.runtime_bridge import (
    INDEPENDENT_SEARCH_TOOL_SURFACE_DIGEST,
    INDEPENDENT_SEARCH_TOOL_GRANT_DIGEST,
)
from .ordivon.loop import RunBudget
from .ordivon.model import AgentToolCall
from .ordivon.tool_bridge import ToolBridge
from .ordivon.tool_errors import ToolBridgeError, ToolBridgeErrorKind
from .runtime_port import (
    HarnessRuntimeClient, HarnessRuntimeClientError,
    HarnessWorkspaceAdmissionUnavailable, WorkspaceBoundEffectAdmission,
)
from .standalone import HarnessCognitionProfile
from .store import HarnessRunStatus
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


def _forward_granted_timeout(grant: int, requested: int | None) -> int:
    """Native R2.1 StrictLego21 timeout projection, admitted under caller grant.

    pre: 1 <= grant <= 900000
    pre: requested is None or (1 <= requested <= grant)
    post: __return__ == (grant if requested is None else requested)
    post: 1 <= __return__ <= grant

    Source symbolic checking covers this pure projection. Authority admission,
    Gateway forwarding, Runtime effects and installed currentness are separate.
    """
    return grant if requested is None else requested


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

    @staticmethod
    def require_release_ready(
        *,
        harness_run_id: str,
        run_status: HarnessRunStatus,
        finalization: dict[str, JsonValue],
        recipient_ack: dict[str, JsonValue],
        verify_delivered_and_drained: Callable[[dict[str, JsonValue], dict[str, JsonValue]], bool],
    ) -> None:
        if run_status is not HarnessRunStatus.COMPLETED:
            raise HarnessWorkspaceAdmissionUnavailable(
                "Workspace Claim cannot release before original Run completes"
            )
        if finalization.get("sourceStanding") != "source-settled":
            raise HarnessWorkspaceAdmissionUnavailable(
                "Workspace Claim cannot release with unsettled original Run effects"
            )
        if (
            recipient_ack.get("harnessRunId") != harness_run_id
            or recipient_ack.get("runReceiptDigest") != finalization.get("runReceiptDigest")
            or recipient_ack.get("accepted") is not True
        ):
            raise HarnessWorkspaceAdmissionUnavailable(
                "Workspace Claim release lacks bound recipient acknowledgment"
            )
        try:
            accepted = verify_delivered_and_drained(finalization, recipient_ack)
        except Exception as exc:
            raise HarnessWorkspaceAdmissionUnavailable(
                "recipient/Runtime drain verification failed; Claim remains HELD"
            ) from exc
        if accepted is not True:
            raise HarnessWorkspaceAdmissionUnavailable(
                "recipient/Runtime drain not independently accepted; Claim remains HELD"
            )


def authorize_gateway_tool_call(
    grant: PluginGatewayExecutionGrant,
    call: AgentToolCall,
) -> tuple[str, list[str], str, dict[str, str] | None, int | None]:
    """Caller-granted execution parameters, evaluated before Journal Tool Intent."""
    if call.name != "execution_submit":
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
    if executable not in grant.executable_allowlist:
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
        if set(env) - set(grant.env_allowlist):
            raise ToolBridgeError(
                "Gateway environment variable is outside the caller grant",
                kind=ToolBridgeErrorKind.AUTHORITY_DENIED,
            )
    if "timeoutMs" in call.arguments and (
        type(timeout) is not int or timeout < 1 or timeout > grant.max_timeout_ms
    ):
        raise ToolBridgeError(
            "Gateway timeout exceeds the caller grant",
            kind=ToolBridgeErrorKind.AUTHORITY_DENIED,
        )

    assert isinstance(executable, str)
    assert isinstance(args, list)
    return executable, args, cwd, env, timeout


def is_original_effect_authority(
    *,
    effect_client: object,
    original_effect_client: object,
    admission_port: object,
    original_admission_port: object,
    admission_required: bool,
    original_admission_required: bool,
) -> bool:
    """One identity invariant for Gateway Factory and Adapter reconnect paths."""
    return (
        effect_client is original_effect_client
        and admission_port is original_admission_port
        and admission_required is original_admission_required
    )


def require_gateway_workspace_effect(
    *,
    workspace_admission: WorkspaceBoundEffectAdmission | None,
    admission_required: bool,
    run_ref: str | None,
    workspace_id: str,
    grant_digest: str | None,
    request_id: str,
    replay: bool,
) -> None:
    """Enforce the same native issuer Port at first physical send AND replay.

    This is not a Workspace Claim reserve implementation or a second issuer.
    A HELD pin alone never proves that an OS effect is launch-authorized.
    """
    if workspace_admission is None:
        if admission_required:
            raise HarnessWorkspaceAdmissionUnavailable(
                "Gateway bound replay requires a certified Runtime Workspace Claim"
                if replay else "Gateway execution requires a certified Runtime Workspace Claim"
            )
        return
    if not isinstance(run_ref, str) or not run_ref:
        raise HarnessRuntimeClientError("Gateway bound Harness Run is missing")
    if not isinstance(grant_digest, str) or not grant_digest:
        raise HarnessRuntimeClientError("Gateway bound Tool Grant is missing")
    try:
        evidence = workspace_admission.require_effect_ready(
            run_ref=run_ref,
            workspace_id=workspace_id,
            tool_grant_digest=grant_digest,
            runtime_operation="workspace.exec",
            client_request_id=request_id,
        )
    except HarnessWorkspaceAdmissionUnavailable:
        raise
    except Exception as exc:
        context = "Gateway replay Workspace qualification" if replay else "Gateway Workspace qualification"
        raise HarnessWorkspaceAdmissionUnavailable(
            f"{context} unavailable: {type(exc).__name__}"
        ) from exc
    if evidence is not None:
        raise HarnessWorkspaceAdmissionUnavailable(
            "Gateway replay Port returned an unauthenticated caller token"
            if replay else "Gateway Workspace Port returned an unauthenticated caller token"
        )
