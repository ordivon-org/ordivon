"""Refinement checks: a validated source cut is evaluated once per call."""

import copy
from unittest.mock import patch

import pytest
from test_gate_source_index import admission_profiles, independent_branches
from test_verification_obligation_r1 import _binding_set, _manifest

from ordivon_composition import cognitive_circuit_r1 as compiler
from ordivon_composition.cognitive_circuit_r1 import CircuitContractError, canonical_digest
from ordivon_composition.verification_impact import compare_gate_source_scopes
from ordivon_composition.verification_obligation_r1 import (
    compile_verification_obligations,
    select_manifest_gate_impacts,
)

GOLDEN = {
    "circuit:admission-interactive-r1": (
        "sha256:2fc4f5a51a8cfb058e88e74581850a1309323c5a75281a50ae4dcc7ddc5c6806",
        "sha256:bf936dcc6652ac5844c6c139706d716a998343ec03db90b14fbbbd6d49f50588",
    ),
    "circuit:admission-workload-r1": (
        "sha256:c7ad09916d8773c0ab0858c5b9e6dbbc932fe898d64654d660db15ccc81ac96e",
        "sha256:07db8347327f1356169ec282f6fcfff478913757dbd1b9c63cf5c9985a2cb1a4",
    ),
}


@pytest.mark.parametrize("manifest", admission_profiles(), ids=lambda x: x["circuitId"])
def test_actual_profile_golden_and_two_validations(manifest):
    changed = copy.deepcopy(manifest)
    changed["stages"][0]["responsibility"] += " R5 changed."
    for current, digest in zip((manifest, changed), GOLDEN[manifest["circuitId"]], strict=True):
        with patch.object(
            compiler, "_validate_manifest_and_order", wraps=compiler._validate_manifest_and_order
        ) as validate:
            result = select_manifest_gate_impacts(
                previous_manifest=manifest, current_manifest=current
            )
        assert validate.call_count == 2
        assert validate.call_args_list[0].args[0] is manifest
        assert validate.call_args_list[1].args[0] is current
        assert canonical_digest(result) == digest
        assert result["proofReuseAdmissible"] is False


@pytest.mark.parametrize("side", ["previous", "current", "both"])
@pytest.mark.parametrize("fault", ["port", "duplicate", "unknown_binding"])
def test_each_public_source_cut_still_rejects_invalid_input(side, fault):
    old = independent_branches(2)
    new = copy.deepcopy(old)
    for manifest in [old, new] if side == "both" else [old] if side == "previous" else [new]:
        if fault == "port":
            manifest["edges"][0]["to"]["port"] = "not-a-declared-port"
        elif fault == "duplicate":
            manifest["stages"].append(copy.deepcopy(manifest["stages"][0]))
        else:
            manifest["stages"][0]["capabilityBindings"].append("capability:missing")
    with pytest.raises(CircuitContractError):
        select_manifest_gate_impacts(previous_manifest=old, current_manifest=new)
    with pytest.raises(CircuitContractError):
        compare_gate_source_scopes(old, new)
    with pytest.raises(CircuitContractError):
        compile_verification_obligations(old if side != "current" else new)


def test_validated_result_never_survives_input_mutation():
    old = independent_branches(1)
    new = copy.deepcopy(old)
    select_manifest_gate_impacts(previous_manifest=old, current_manifest=new)
    new["edges"][0]["to"]["port"] = "missing-port"
    with pytest.raises(CircuitContractError, match="target port"):
        select_manifest_gate_impacts(previous_manifest=old, current_manifest=new)


def test_binding_resolution_does_not_recompile_or_accept_stale_binding():
    old = _manifest()
    new = copy.deepcopy(old)
    before = _binding_set(compile_verification_obligations(old), native=True)
    after = copy.deepcopy(before)
    after["bindings"][0]["verifierRef"]["digest"] = "sha256:" + "a" * 64
    with patch.object(
        compiler, "_validate_manifest_and_order", wraps=compiler._validate_manifest_and_order
    ) as validate:
        result = select_manifest_gate_impacts(
            previous_manifest=old,
            current_manifest=new,
            previous_binding_set=before,
            current_binding_set=after,
        )
    assert validate.call_count == 2
    assert result["changedVerifierBindingGateIds"] == ["gate:candidate-contract"]
    assert result["proofReuseAdmissible"] is False
    new["gateRequirements"][0]["guarantee"] += " Changed."
    with pytest.raises(CircuitContractError):
        select_manifest_gate_impacts(
            previous_manifest=old,
            current_manifest=new,
            previous_binding_set=before,
            current_binding_set=after,
        )
