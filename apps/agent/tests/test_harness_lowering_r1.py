from __future__ import annotations

import copy

import pytest
from ordivon_composition import canonical_digest, compile_manifest
from ordivon_harness.api import (
    NO_TOOL_AGENT_GRANT_DIGEST,
    NO_TOOL_AGENT_SURFACE_DIGEST,
    AgentTurnResult,
    HarnessAgentRunCompositionError,
    HarnessBoundReference,
    HarnessPrivacyPolicy,
    HarnessRunContract,
)
from ordivon_harness.ordivon.model import AgentRunConclusion, ScriptedTurnAdapter

from ordivon_agent import (
    AgentRunLoweringError,
    compile_no_tool_harness_binding,
    create_no_tool_harness_run,
    validate_no_tool_harness_binding,
)


def _digest(label: str) -> str:
    return canonical_digest({"hux30": label})


def _manifest(*, unresolved: bool = False) -> dict:
    return {
        "schemaVersion": 1,
        "kind": "ordivon.cognitive-circuit-manifest",
        "circuitId": "circuit:hux30-no-tool-r1",
        "objectiveRef": {"id": "objective:hux30", "digest": _digest("objective")},
        "methodBindings": [],
        "capabilityBindings": [],
        "stages": [
            {
                "id": "stage:agent-run",
                "ownerId": "agent-app",
                "responsibility": "Run one already-bound no-Tool Agent task.",
                "dependsOn": [],
                "methodBindings": [],
                "capabilityBindings": [],
                "inputs": ["objective"],
                "outputs": ["candidate"],
            }
        ],
        "edges": [],
        "gateRequirements": [],
        "unresolvedAssumptions": (
            ["Caller still needs to resolve one exact external prerequisite."] if unresolved else []
        ),
        "nonClaims": [
            "Circuit compilation does not grant provider, Tool, execution, or completion authority."
        ],
    }


def _contract(
    *, tools: bool = False, model_id: str = ScriptedTurnAdapter.model_id
) -> HarnessRunContract:
    tool_catalog = NO_TOOL_AGENT_SURFACE_DIGEST
    tool_grant = NO_TOOL_AGENT_GRANT_DIGEST
    if tools:
        tool_catalog = _digest("non-no-tool-catalog")
        tool_grant = _digest("non-no-tool-grant")
    return HarnessRunContract(
        harness_run_id="harness-run:hux30-r1",
        harness_implementation_id="ordivon-harness@hux30",
        caller_id="caller:hux30",
        caller_run_ref="agent-request:hux30-r1",
        objective_ref=HarnessBoundReference("objective:hux30", "objective", _digest("objective")),
        context_refs=(HarnessBoundReference("context:hux30", "context", _digest("context")),),
        provider_id="provider:scripted",
        adapter_id=ScriptedTurnAdapter.adapter_id,
        requested_model_id=model_id,
        tool_catalog_digest=tool_catalog,
        tool_grant_digest=tool_grant,
        budget={
            "maxModelCalls": 2,
            "maxToolCalls": 0,
            "maxObservationBytes": 65536,
            "maxWallTimeMs": 10000,
            "maxTotalTokens": 10000,
            "maxModelRetries": 1,
            "maxToolCorrections": 2,
            "maxConclusionCorrections": 3,
            "maxObservationOnlyTurns": 4,
            "maxNoProgressTurns": 3,
        },
        completion_contract={"mode": "record"},
        system_manifest_ref=HarnessBoundReference(
            "manifest:hux30", "system-manifest", _digest("system-manifest")
        ),
        created_at_ms=1000,
        privacy=HarnessPrivacyPolicy(),
    )


def _adapter_ref() -> dict[str, str]:
    return {
        "id": "adapter-binding:scripted-hux30",
        "digest": _digest("adapter-binding"),
    }


def _completed() -> AgentTurnResult:
    return AgentTurnResult(
        model_call_id="model-call:hux30",
        model_id=ScriptedTurnAdapter.model_id,
        content="candidate",
        tool_calls=(),
        conclusion=AgentRunConclusion(
            status="candidate_completed",
            summary="HUX-30 deterministic candidate.",
            unresolved_unknowns=(),
        ),
        usage={"inputTokens": 1, "outputTokens": 1},
        finish_reason="stop",
        raw_response_digest=_digest("model-call"),
    )


def test_no_tool_lowering_binds_exact_public_owner_refs() -> None:
    manifest = _manifest()
    contract = _contract()
    binding = compile_no_tool_harness_binding(
        manifest, contract, adapter_binding_ref=_adapter_ref()
    )
    compiled = compile_manifest(manifest)

    assert binding["sourceCircuitRef"] == {
        "id": compiled["circuitId"],
        "digest": compiled["compiledDigest"],
    }
    assert binding["runContractRef"] == {
        "id": contract.harness_run_id,
        "digest": contract.digest,
    }
    assert binding["adapterBindingRef"] == _adapter_ref()
    assert binding["readyForHarness"] is True
    assert binding["authorityGranted"] is False


def test_unresolved_circuit_remains_not_ready() -> None:
    binding = compile_no_tool_harness_binding(
        _manifest(unresolved=True),
        _contract(),
        adapter_binding_ref=_adapter_ref(),
    )
    assert binding["readyForHarness"] is False
    assert binding["unresolvedInputs"] == ["circuit-unresolved-assumptions"]


def test_tool_contract_fails_closed_into_later_lowerer() -> None:
    with pytest.raises(AgentRunLoweringError) as error:
        compile_no_tool_harness_binding(
            _manifest(),
            _contract(tools=True),
            adapter_binding_ref=_adapter_ref(),
        )
    assert error.value.code == "TOOL_LOWERING_REQUIRED"


def test_tampered_run_contract_binding_fails_before_harness(tmp_path) -> None:
    manifest = _manifest()
    contract = _contract()
    binding = compile_no_tool_harness_binding(
        manifest, contract, adapter_binding_ref=_adapter_ref()
    )
    binding = copy.deepcopy(binding)
    binding["runContractRef"]["digest"] = _digest("other-contract")
    base = dict(binding)
    del base["bindingDigest"]
    binding["bindingDigest"] = canonical_digest(base)

    with pytest.raises(AgentRunLoweringError) as error:
        validate_no_tool_harness_binding(
            manifest,
            binding,
            contract,
            adapter_binding_ref=_adapter_ref(),
        )
    assert error.value.code == "RUN_CONTRACT_BINDING_MISMATCH"


def test_harness_still_independently_revalidates_adapter(tmp_path) -> None:
    manifest = _manifest()
    contract = _contract(model_id="model:wrong-for-scripted")
    binding = compile_no_tool_harness_binding(
        manifest, contract, adapter_binding_ref=_adapter_ref()
    )

    with pytest.raises(HarnessAgentRunCompositionError):
        create_no_tool_harness_run(
            tmp_path,
            manifest,
            binding,
            contract,
            lambda _exact: ScriptedTurnAdapter((_completed(),)),
            adapter_binding_ref=_adapter_ref(),
        )


def test_no_tool_vertical_executes_through_existing_harness(tmp_path) -> None:
    manifest = _manifest()
    contract = _contract()
    binding = compile_no_tool_harness_binding(
        manifest, contract, adapter_binding_ref=_adapter_ref()
    )
    run = create_no_tool_harness_run(
        tmp_path,
        manifest,
        binding,
        contract,
        lambda _exact: ScriptedTurnAdapter((_completed(),)),
        adapter_binding_ref=_adapter_ref(),
    )
    execution = run.run(({"role": "user", "content": "Execute the bounded HUX-30 canary."},))

    assert execution.loop_result.stop_code.value == "candidate_completed"
    assert execution.loop_result.conclusion is not None
    assert execution.loop_result.conclusion.summary == "HUX-30 deterministic candidate."


def test_product_lowerer_imports_only_public_harness_surface() -> None:
    from pathlib import Path

    source = (
        Path(__file__).resolve().parents[1] / "src" / "ordivon_agent" / "harness_lowering_r1.py"
    ).read_text(encoding="utf-8")

    assert "from ordivon_harness.api import" in source
    for forbidden in (
        "ordivon_harness.agent_run",
        "ordivon_harness.core_contracts",
        "ordivon_harness.ordivon",
        "ordivon_harness.sqlite_store",
    ):
        assert forbidden not in source
