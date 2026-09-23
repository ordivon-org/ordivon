"""HUX-30 no-Tool Cognitive Circuit -> Harness consumer lowering.

This module is a product-side consumer adapter. It binds already-selected exact identities
and calls public owner contracts. It does not select providers, discover/grant Tools, infer
Runtime authority, own workflow/session state, or establish domain completion.
"""

from __future__ import annotations

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
    HarnessPrivacyPolicy,
    HarnessRunContract,
)

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
    if binding["cognitionBindingRefs"]:
        raise AgentRunLoweringError(
            "COGNITION_LOWERING_REQUIRED",
            "HUX-30 does not admit cognition bindings",
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
    return HarnessAgentRun.create(state_root, contract, adapter_factory)


__all__ = [
    "AgentRunLoweringError",
    "compile_no_tool_harness_binding",
    "compile_no_tool_harness_run_contract",
    "create_no_tool_harness_run",
    "validate_no_tool_harness_binding",
    "validate_no_tool_harness_run_contract",
]
