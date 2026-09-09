"""Read-only Agent/operator projections over existing Harness truth owners."""

from __future__ import annotations

from anc_canonical import JsonValue, validate_json_value

from .core_contracts import HarnessRunContract
from .ordivon.model import AgentTurnRequest
from .ordivon.sqlite_agent_bridge import (
    NO_TOOL_AGENT_GRANT_DIGEST,
    NO_TOOL_AGENT_SURFACE,
    NO_TOOL_AGENT_SURFACE_DIGEST,
)
from .ordivon.sqlite_runtime_bridge import (
    INDEPENDENT_SEARCH_TOOL_GRANT_DIGEST,
    INDEPENDENT_SEARCH_TOOL_SURFACE,
    INDEPENDENT_SEARCH_TOOL_SURFACE_DIGEST,
)


def _project_run_composition(contract: HarnessRunContract) -> dict[str, JsonValue]:
    """Project only exact Contract-bound execution facts used by explain/workbench."""

    if (
        contract.tool_catalog_digest == NO_TOOL_AGENT_SURFACE_DIGEST
        and contract.tool_grant_digest == NO_TOOL_AGENT_GRANT_DIGEST
    ):
        tool_surface: dict[str, JsonValue] = {
            "resolution": "recognized-built-in",
            "surfaceId": "harness.execution.no-tool.v1",
            "toolCatalogDigest": contract.tool_catalog_digest,
            "toolGrantDigest": contract.tool_grant_digest,
            "tools": list(NO_TOOL_AGENT_SURFACE["tools"]),
            "supportedByHarnessAgentRun": True,
        }
    elif (
        contract.tool_catalog_digest == INDEPENDENT_SEARCH_TOOL_SURFACE_DIGEST
        and contract.tool_grant_digest == INDEPENDENT_SEARCH_TOOL_GRANT_DIGEST
    ):
        tool_surface = {
            "resolution": "recognized-built-in",
            "surfaceId": "harness.execution.runtime-search.v1",
            "toolCatalogDigest": contract.tool_catalog_digest,
            "toolGrantDigest": contract.tool_grant_digest,
            "tools": list(INDEPENDENT_SEARCH_TOOL_SURFACE["tools"]),
            "supportedByHarnessAgentRun": True,
        }
    else:
        tool_surface = {
            "resolution": "custom-or-unrecognized",
            "toolCatalogDigest": contract.tool_catalog_digest,
            "toolGrantDigest": contract.tool_grant_digest,
            "supportedByHarnessAgentRun": False,
        }

    value: dict[str, JsonValue] = {
        "schemaVersion": 1,
        "kind": "ordivon.harness-run-capability-projection",
        "truthRole": "derived-from-harness-run-contract",
        "stage": "run-admitted",
        "harnessRunId": contract.harness_run_id,
        "provider": {
            "providerId": contract.provider_id,
            "adapterId": contract.adapter_id,
            "requestedModelId": contract.requested_model_id,
        },
        "toolSurface": tool_surface,
        "cognitionMechanisms": {
            "status": "process-local-not-bound-by-run-contract",
            "reason": (
                "HarnessCognitionProfile is structural process composition; exact native "
                "actions are bound only on AgentTurnRequest"
            ),
        },
        "privacy": contract.privacy.to_dict(),
        "budget": dict(contract.budget),
    }
    validate_json_value(value)
    return value


def _project_turn_actions(request: AgentTurnRequest) -> dict[str, JsonValue]:
    """Project only the exact actions already bound into one Provider request."""

    native: list[str] = []
    if request.capabilities.conclusion:
        native.append("conclusion")
    if request.capabilities.working_set_transition:
        native.append("working-set-transition")
    if request.capabilities.caller_ingress_promotion:
        native.append("caller-ingress-promotion")
    if request.capabilities.working_set_history:
        native.append("working-set-history")
    if request.capabilities.tool_program:
        native.append("tool-program")
    value: dict[str, JsonValue] = {
        "schemaVersion": 1,
        "kind": "ordivon.harness-turn-capability-projection",
        "truthRole": "derived-from-exact-agent-turn-request",
        "stage": "turn-admitted",
        "harnessRunId": request.harness_run_id,
        "turnId": request.turn_id,
        "sequence": request.sequence,
        "toolCatalogDigest": request.tool_catalog_digest,
        "tools": [tool.to_dict() for tool in request.tools],
        "nativeActions": native,
        "callerIngressAddressable": bool(request.caller_ingress_refs),
        "workingSetSources": [ref.pin.slot for ref in request.working_set_refs],
        "requestDigest": request.digest,
        "dispatchDigest": request.dispatch_digest,
    }
    validate_json_value(value)
    return value


def build_durable_workbench_projection(
    *,
    run: dict[str, JsonValue],
    contract: HarnessRunContract,
    provider_call: dict[str, JsonValue] | None,
    provider_request: AgentTurnRequest | None,
    snapshot: dict[str, JsonValue] | None,
    recovery: dict[str, JsonValue] | None,
    run_receipt: dict[str, JsonValue] | None,
    completion_proposal: dict[str, JsonValue] | None,
) -> dict[str, JsonValue]:
    """Build one compact projection without adding a second durable state model."""

    if provider_request is not None:
        action_surface: dict[str, JsonValue] = {
            "status": "retained-exact-request",
            "projection": _project_turn_actions(provider_request),
        }
    elif provider_call is not None:
        action_surface = {
            "status": "unavailable",
            "reason": (
                "the current Provider Call is durable but its AgentTurnRequest content is "
                "not retained/available under this privacy and continuity state"
            ),
        }
    else:
        action_surface = {
            "status": "not-observed",
            "reason": "no current Provider Call exists",
        }

    value: dict[str, JsonValue] = {
        "schemaVersion": 1,
        "kind": "ordivon.harness-workbench-projection",
        "truthRole": "derived-read-only-projection",
        "run": {
            "harnessRunId": contract.harness_run_id,
            "status": run.get("status", "unknown"),
            "contractDigest": contract.digest,
        },
        "composition": _project_run_composition(contract),
        "currentActionSurface": action_surface,
        "provider": {
            "status": "not-observed" if provider_call is None else provider_call.get("status", "unknown"),
            "record": provider_call,
        },
        "continuity": {
            "snapshot": snapshot,
            "recovery": recovery,
        },
        "completion": {
            "runReceipt": run_receipt,
            "completionProposal": completion_proposal,
            "semanticCompletionAuthority": "caller-or-domain",
        },
        "proofBoundaries": {
            "durable": "Run/Contract/Provider/Snapshot/Recovery objects come from Harness Journal/CAS",
            "processLocal": (
                "Adapter factory, Runtime client and other application objects are not inferred "
                "by a fresh durable-state inspection"
            ),
            "external": "Provider/Runtime/domain liveness and world truth are not claimed",
        },
    }
    validate_json_value(value)
    return value


__all__ = ["build_durable_workbench_projection"]
