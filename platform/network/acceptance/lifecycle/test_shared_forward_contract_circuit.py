"""Network consumer of existing Composition obligation semantics.

No production effects, new truth owner, or generic Agent-completion evaluator.
This is a Network-owned consumer contract regression using the Composition
public API. It runs under the existing Composition project environment.
"""

from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path

import pytest
from ordivon_composition.cognitive_circuit_r1 import (
    CircuitContractError,
    compile_manifest,
    evaluate_gate_results,
)
from ordivon_composition.verification_obligation_r1 import (
    compile_verification_obligations,
)

MANIFEST_PATH = (
    Path(__file__).resolve().parent / "shared-forward-reload-circuit-r1.json"
)

FROZEN_REQUIRED_NETWORK_GATES = frozenset(
    {"gate:forward-source-installed", "gate:loaded-unit-native-effect"}
)
SPEC_PATH = (
    Path(__file__).resolve().parents[2] / "docs/AGENT_OUTCOME_NETWORK_PILOT_SPEC_R1.md"
)


@pytest.fixture()
def manifest() -> dict:
    return json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))


def _owner_result(manifest: dict, gate: dict, standing: str = "SATISFIED") -> dict:
    compiled = compile_manifest(manifest)
    return {
        "schemaVersion": 1,
        "kind": "ordivon.composition-gate-result",
        "circuitId": manifest["circuitId"],
        "manifestDigest": compiled["manifestDigest"],
        "gateId": gate["id"],
        "verifierOwnerId": gate["verifierOwnerId"],
        "standing": standing,
        "evidenceRefs": []
        if standing == "UNKNOWN"
        else ["owner-native:source-and-effect-readback"],
        "supportScope": gate["supportScope"],
        "nonClaims": ["This is scoped gate evidence, never domain acceptance."],
    }


def test_real_network_circuit_compiles_with_nonvacuous_cross_owner_obligations(
    manifest,
):
    compiled = compile_manifest(manifest)
    obligations = compile_verification_obligations(manifest)
    required = {row["id"] for row in manifest["gateRequirements"] if row["required"]}
    # Natural consumer contract, not merely whatever the candidate declares.
    assert required == FROZEN_REQUIRED_NETWORK_GATES
    assert manifest["objectiveRef"]["digest"] == (
        "sha256:" + hashlib.sha256(SPEC_PATH.read_bytes()).hexdigest()
    )
    assert set(compiled["requiredGateIds"]) == required
    assert {item["gateId"] for item in obligations["obligations"]} == required
    assert (
        compiled["truthRole"] == "task-local-non-authoritative-composition-projection"
    )


def test_network_missing_or_unknown_evidence_stays_open(manifest):
    required = [row for row in manifest["gateRequirements"] if row["required"]]
    missing = evaluate_gate_results(manifest, [])
    assert missing["standing"] == "COMPOSITION_GATES_OPEN"
    assert missing["missingGateIds"]
    assert missing["domainAcceptanceEstablished"] is False

    unknown = evaluate_gate_results(
        manifest, [_owner_result(manifest, row, "UNKNOWN") for row in required]
    )
    assert unknown["standing"] == "COMPOSITION_GATES_OPEN"
    assert unknown["unknownGateIds"] == sorted(row["id"] for row in required)
    assert unknown["unsatisfiedGateIds"] == []
    assert unknown["mechanicalClosure"] is False


def test_even_complete_gate_evidence_does_not_claim_network_domain_outcome(manifest):
    results = [_owner_result(manifest, row) for row in manifest["gateRequirements"]]
    out = evaluate_gate_results(manifest, results)
    assert out["standing"] == "COMPOSITION_GATES_SATISFIED"
    assert out["mechanicalClosure"] is True
    assert out["domainAcceptanceEstablished"] is False
    assert "not-domain-verdict" in out["truthRole"]


@pytest.mark.parametrize("mutation", ["owner", "manifest", "scope", "gate"])
def test_network_forged_or_widened_evidence_is_rejected(manifest, mutation):
    gate = manifest["gateRequirements"][0]
    result = _owner_result(manifest, gate)
    if mutation == "owner":
        result["verifierOwnerId"] = "harness"
    elif mutation == "manifest":
        result["manifestDigest"] = "sha256:" + "a" * 64
    elif mutation == "scope":
        result["supportScope"] = "all-of-ordivon-network"
    elif mutation == "gate":
        result["gateId"] = "gate:not-in-manifest"

    with pytest.raises(CircuitContractError):
        evaluate_gate_results(manifest, [result])


def test_network_manifest_change_invalidates_previously_satisfied_witness(manifest):
    old = _owner_result(manifest, manifest["gateRequirements"][0])
    changed = copy.deepcopy(manifest)
    changed["stages"][0]["responsibility"] += " changed source contract"
    with pytest.raises(CircuitContractError):
        evaluate_gate_results(changed, [old])


def test_removing_required_gate_does_not_lower_network_consumer_requirements(manifest):
    changed = copy.deepcopy(manifest)
    changed["gateRequirements"] = changed["gateRequirements"][:-1]
    # Generic Composition intentionally permits partial Gate coverage; its
    # mechanical result cannot certify a caller-owned required-obligation set.
    compiled = compile_manifest(changed)
    assert set(compiled["requiredGateIds"]) != FROZEN_REQUIRED_NETWORK_GATES
    remaining = [_owner_result(changed, gate) for gate in changed["gateRequirements"]]
    projection = evaluate_gate_results(changed, remaining)
    assert projection["mechanicalClosure"] is True
    assert projection["domainAcceptanceEstablished"] is False


def test_duplicate_gate_and_cyclic_owner_dependencies_are_rejected(manifest):
    duplicated = copy.deepcopy(manifest)
    duplicated["gateRequirements"].append(duplicated["gateRequirements"][0])
    with pytest.raises(CircuitContractError):
        compile_manifest(duplicated)

    cyclic = copy.deepcopy(manifest)
    cyclic["stages"][0]["dependsOn"].append(cyclic["stages"][-1]["id"])
    with pytest.raises(CircuitContractError):
        compile_manifest(cyclic)
