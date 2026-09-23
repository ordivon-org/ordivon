"""HUX-30 no-Tool Cognitive Circuit -> Harness consumer lowering.

This module is a product-side consumer adapter. It binds already-selected exact identities
and calls public owner contracts. It does not select providers, discover/grant Tools, infer
Runtime authority, own workflow/session state, or establish domain completion.
"""

from __future__ import annotations

from collections.abc import Callable
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
    "create_no_tool_harness_run",
    "validate_no_tool_harness_binding",
]
