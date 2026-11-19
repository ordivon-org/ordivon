"""Gateway execution grant validation and effect-admission decisions.

Only checks caller-supplied grant shape and the exact execution request. These
pure decisions are not Harness Journal commits, Runtime Claim reservations,
native spawn authorization, or evidence of Domain completion.
"""
from __future__ import annotations

from dataclasses import dataclass

from anc_canonical import JsonValue

from .ordivon.model import AgentToolCall
from .ordivon.tool_errors import ToolBridgeError, ToolBridgeErrorKind
from .runtime_port import (
    HarnessRuntimeClientError,
    HarnessWorkspaceAdmissionUnavailable,
    WorkspaceBoundEffectAdmission,
)


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
