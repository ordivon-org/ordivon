"""HUX-30 no-Tool Cognitive Circuit -> Harness consumer lowering.

This module is a product-side consumer adapter. It binds already-selected exact identities
and calls public owner contracts. It does not select providers, discover/grant Tools, infer
Runtime authority, own workflow/session state, or establish domain completion.
"""

from __future__ import annotations

import json
from collections.abc import Callable, Mapping
from pathlib import Path
from typing import Any

from ordivon_composition import (
    compile_agent_run_binding,
    compile_manifest,
    require_ready_agent_run_binding,
)
from ordivon_harness.api import (
    NO_TOOL_AGENT_GRANT_DIGEST,
    NO_TOOL_AGENT_SURFACE_DIGEST,
    AgentTurnAdapter,
    HarnessAgentRun,
    HarnessBoundReference,
    HarnessCognitionProfile,
    HarnessCognitionRefresh,
    HarnessCognitionRefreshSource,
    HarnessCognitionSeed,
    HarnessCognitionSeedSource,
    HarnessPrivacyPolicy,
    HarnessRunContract,
    HarnessWorkingViewSource,
)

from .cognitive_delta_r1 import project_agent_cognitive_delta
from .cognitive_orientation_r1 import project_agent_orientation_view

AdapterFactory = Callable[[HarnessRunContract], AgentTurnAdapter]


class AgentRunLoweringError(ValueError):
    """Machine-classified product-side lowering error."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code


def _assert_no_tool_contract(contract: HarnessRunContract) -> None:
    if (
        contract.tool_catalog_digest != NO_TOOL_AGENT_SURFACE_DIGEST
        or contract.tool_grant_digest != NO_TOOL_AGENT_GRANT_DIGEST
    ):
        raise AgentRunLoweringError(
            "TOOL_LOWERING_REQUIRED",
            "HUX-30 admits only the canonical no-Tool Harness surface",
        )


def _compiled_circuit_reference(compiled: dict[str, Any]) -> HarnessBoundReference:
    return HarnessBoundReference(
        compiled["circuitId"],
        "cognitive-circuit",
        compiled["compiledDigest"],
    )


def _compiled_objective_reference(compiled: dict[str, Any]) -> HarnessBoundReference:
    objective = compiled["objectiveRef"]
    return HarnessBoundReference(objective["id"], "objective", objective["digest"])


def validate_no_tool_harness_run_contract(
    manifest: dict[str, Any], contract: HarnessRunContract
) -> None:
    """Fail closed when a caller-authored Harness contract is stale or cross-bound."""

    compiled = compile_manifest(manifest)
    if compiled["unresolvedAssumptions"]:
        raise AgentRunLoweringError(
            "CIRCUIT_UNRESOLVED",
            "Harness Run Contract lowering requires a Circuit with no unresolved assumptions",
        )
    _assert_no_tool_contract(contract)

    if contract.objective_ref != _compiled_objective_reference(compiled):
        raise AgentRunLoweringError(
            "OBJECTIVE_BINDING_MISMATCH",
            "Harness Run Contract objective differs from the compiled Cognitive Circuit",
        )

    circuit_ref = _compiled_circuit_reference(compiled)
    if circuit_ref not in contract.source_refs:
        raise AgentRunLoweringError(
            "CIRCUIT_SOURCE_BINDING_MISMATCH",
            "Harness Run Contract does not bind the exact compiled Cognitive Circuit source",
        )


def compile_no_tool_harness_run_contract(
    manifest: dict[str, Any],
    *,
    harness_run_id: str,
    harness_implementation_id: str,
    caller_id: str,
    caller_run_ref: str,
    context_refs: tuple[HarnessBoundReference, ...],
    provider_id: str,
    adapter_id: str,
    requested_model_id: str,
    budget: Mapping[str, Any],
    completion_contract: Mapping[str, Any],
    system_manifest_ref: HarnessBoundReference,
    created_at_ms: int,
    source_refs: tuple[HarnessBoundReference, ...] = (),
    prior_artifact_refs: tuple[HarnessBoundReference, ...] = (),
    privacy: HarnessPrivacyPolicy | None = None,
    deadline_ms: int | None = None,
) -> HarnessRunContract:
    """Lower one resolved Circuit plus exact caller selections into the public Harness waist.

    This function selects nothing and grants nothing. The only derived fields are the exact
    Circuit/objective references and the canonical no-Tool surface digests. Everything else
    is caller-selected and independently validated by HarnessRunContract.
    """

    compiled = compile_manifest(manifest)
    if compiled["unresolvedAssumptions"]:
        raise AgentRunLoweringError(
            "CIRCUIT_UNRESOLVED",
            "Harness Run Contract lowering requires a Circuit with no unresolved assumptions",
        )

    circuit_ref = _compiled_circuit_reference(compiled)
    if any(reference.ref == circuit_ref.ref for reference in source_refs):
        raise AgentRunLoweringError(
            "CIRCUIT_SOURCE_DUPLICATED",
            "caller source_refs must not duplicate the derived Cognitive Circuit reference",
        )

    contract = HarnessRunContract(
        harness_run_id=harness_run_id,
        harness_implementation_id=harness_implementation_id,
        caller_id=caller_id,
        caller_run_ref=caller_run_ref,
        objective_ref=_compiled_objective_reference(compiled),
        context_refs=context_refs,
        provider_id=provider_id,
        adapter_id=adapter_id,
        requested_model_id=requested_model_id,
        tool_catalog_digest=NO_TOOL_AGENT_SURFACE_DIGEST,
        tool_grant_digest=NO_TOOL_AGENT_GRANT_DIGEST,
        budget=budget,
        completion_contract=completion_contract,
        system_manifest_ref=system_manifest_ref,
        created_at_ms=created_at_ms,
        source_refs=(circuit_ref, *source_refs),
        prior_artifact_refs=prior_artifact_refs,
        privacy=privacy if privacy is not None else HarnessPrivacyPolicy(),
        deadline_ms=deadline_ms,
    )
    validate_no_tool_harness_run_contract(manifest, contract)
    return contract


def compile_no_tool_harness_binding(
    manifest: dict[str, Any],
    contract: HarnessRunContract,
    *,
    adapter_binding_ref: dict[str, str],
    cognition_binding_refs: tuple[dict[str, str], ...] = (),
) -> dict[str, Any]:
    """Compile the first bounded no-Tool consumer seam without inventing authority."""

    _assert_no_tool_contract(contract)
    compiled = compile_manifest(manifest)
    unresolved_inputs: tuple[str, ...] = ()
    if compiled["unresolvedAssumptions"]:
        unresolved_inputs = ("circuit-unresolved-assumptions",)

    return compile_agent_run_binding(
        source_circuit_ref={
            "id": compiled["circuitId"],
            "digest": compiled["compiledDigest"],
        },
        run_contract_ref={
            "id": contract.harness_run_id,
            "digest": contract.digest,
        },
        adapter_binding_ref=adapter_binding_ref,
        cognition_binding_refs=cognition_binding_refs,
        unresolved_inputs=unresolved_inputs,
    )


def validate_no_tool_harness_binding(
    manifest: dict[str, Any],
    binding: dict[str, Any],
    contract: HarnessRunContract,
    *,
    adapter_binding_ref: dict[str, str],
) -> None:
    """Revalidate the product projection against exact public owner contracts."""

    require_ready_agent_run_binding(binding)
    _assert_no_tool_contract(contract)
    compiled = compile_manifest(manifest)

    expected_source = {
        "id": compiled["circuitId"],
        "digest": compiled["compiledDigest"],
    }
    if binding["sourceCircuitRef"] != expected_source:
        raise AgentRunLoweringError(
            "CIRCUIT_BINDING_MISMATCH",
            "AgentRunBinding source circuit differs from the supplied compiled circuit",
        )

    expected_contract = {
        "id": contract.harness_run_id,
        "digest": contract.digest,
    }
    if binding["runContractRef"] != expected_contract:
        raise AgentRunLoweringError(
            "RUN_CONTRACT_BINDING_MISMATCH",
            "AgentRunBinding Run Contract differs from the supplied HarnessRunContract",
        )

    if binding["adapterBindingRef"] != adapter_binding_ref:
        raise AgentRunLoweringError(
            "ADAPTER_BINDING_MISMATCH",
            "AgentRunBinding adapter reference differs from the caller-selected adapter binding",
        )

    if binding["toolBindingRef"] is not None:
        raise AgentRunLoweringError(
            "TOOL_LOWERING_REQUIRED",
            "HUX-30 does not admit a Tool binding",
        )
    if binding["executionBindingRef"] is not None:
        raise AgentRunLoweringError(
            "EXECUTION_LOWERING_REQUIRED",
            "HUX-30 does not admit an execution binding",
        )
    if len(binding["cognitionBindingRefs"]) > 1:
        raise AgentRunLoweringError(
            "COGNITION_BINDING_CARDINALITY_UNSUPPORTED",
            "HUX-30 environment lowering admits at most one exact cognition binding",
        )


def create_no_tool_harness_run(
    state_root: str | Path,
    manifest: dict[str, Any],
    binding: dict[str, Any],
    contract: HarnessRunContract,
    adapter_factory: AdapterFactory,
    *,
    adapter_binding_ref: dict[str, str],
) -> HarnessAgentRun:
    """Create a Run only after app-side reference checks; Harness still revalidates independently."""

    validate_no_tool_harness_binding(
        manifest,
        binding,
        contract,
        adapter_binding_ref=adapter_binding_ref,
    )
    cognition_profile = HarnessCognitionProfile() if binding["cognitionBindingRefs"] else None
    return HarnessAgentRun.create(
        state_root,
        contract,
        adapter_factory,
        cognition_profile=cognition_profile,
    )


def _single_cognition_binding(binding: Mapping[str, Any]) -> dict[str, str]:
    require_ready_agent_run_binding(dict(binding))
    refs = binding["cognitionBindingRefs"]
    if len(refs) != 1:
        raise AgentRunLoweringError(
            "COGNITION_BINDING_REQUIRED",
            "dynamic environment lowering requires exactly one cognition binding",
        )
    ref = refs[0]
    return {"id": ref["id"], "digest": ref["digest"]}


def _environment_orientation_source(
    binding_ref: Mapping[str, str],
    projection: Mapping[str, Any],
) -> tuple[dict[str, object], HarnessWorkingViewSource]:
    if projection.get("agentRun") is not None or projection.get("reentry") is not None:
        raise AgentRunLoweringError(
            "COGNITION_ENVIRONMENT_SELF_STATE_UNSUPPORTED",
            "external environment cognition must not embed Harness Run or re-entry self-state",
        )
    orientation = project_agent_orientation_view(projection)
    generation = orientation.get("viewDigest")
    if not isinstance(generation, str) or not generation.startswith("sha256:"):
        raise AgentRunLoweringError(
            "COGNITION_ORIENTATION_DIGEST_INVALID",
            "Agent Orientation View must expose one exact sha256 viewDigest",
        )
    content = json.dumps(
        orientation,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )
    source = HarnessWorkingViewSource(
        logical_ref=binding_ref["id"],
        logical_generation=generation,
        messages=({"role": "system", "content": content},),
    )
    return orientation, source


def compile_no_tool_agent_environment_seed(
    binding: dict[str, Any],
    projection: Mapping[str, Any],
    *,
    attempt_id: str,
    basis: str,
    slot: str = "environment",
) -> HarnessCognitionSeed:
    """Lower one exact R1 environment projection into the initial Harness WorkingSet seed.

    The AgentRunBinding supplies the stable caller-selected logical reference and binds
    the initial exact Orientation digest. Harness remains responsible only for source
    materialization and WorkingSet state.
    """

    binding_ref = _single_cognition_binding(binding)
    orientation, source = _environment_orientation_source(binding_ref, projection)
    if binding_ref["digest"] != orientation["viewDigest"]:
        raise AgentRunLoweringError(
            "COGNITION_BINDING_MISMATCH",
            "cognition binding digest differs from the exact initial Agent Orientation View",
        )
    return HarnessCognitionSeed(
        attempt_id=attempt_id,
        sources=(HarnessCognitionSeedSource(slot=slot, source=source),),
        basis=basis,
    )


def compile_no_tool_agent_environment_refresh(
    binding: dict[str, Any],
    previous_projection: Mapping[str, Any],
    current_projection: Mapping[str, Any],
    *,
    next_attempt_id: str,
    basis: str,
    slot: str = "environment",
) -> HarnessCognitionRefresh | None:
    """Compile a selected-environment R1 delta into one exact caller cognition refresh.

    This function does no discovery, watch, relevance ranking, or effect authorization.
    The two projections are already-selected environment inputs. No owner-qualified change
    means no Harness successor; any selected component change replaces only the environment
    slot through Harness slot-level CAS.
    """

    binding_ref = _single_cognition_binding(binding)
    delta = project_agent_cognitive_delta(previous_projection, current_projection)
    if not delta["hasChanges"]:
        return None

    _previous_orientation, expected = _environment_orientation_source(
        binding_ref, previous_projection
    )
    _current_orientation, replacement = _environment_orientation_source(
        binding_ref, current_projection
    )
    return HarnessCognitionRefresh(
        next_attempt_id=next_attempt_id,
        sources=(
            HarnessCognitionRefreshSource(
                slot=slot,
                expected_source=expected,
                replacement_source=replacement,
            ),
        ),
        basis=basis,
    )


__all__ = [
    "AgentRunLoweringError",
    "compile_no_tool_agent_environment_refresh",
    "compile_no_tool_agent_environment_seed",
    "compile_no_tool_harness_binding",
    "compile_no_tool_harness_run_contract",
    "create_no_tool_harness_run",
    "validate_no_tool_harness_binding",
    "validate_no_tool_harness_run_contract",
]
