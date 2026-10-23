from __future__ import annotations

import copy

import pytest

from ordivon_composition.cognitive_circuit_r1 import (
    CircuitContractError,
    canonical_digest,
    compile_manifest,
    evaluate_gate_results,
    validate_manifest,
)


def _digest(label: str) -> str:
    return canonical_digest({"fixture": label})


def valid_manifest() -> dict:
    return {
        "schemaVersion": 1,
        "kind": "ordivon.cognitive-circuit-manifest",
        "circuitId": "circuit:research-publication-r1",
        "objectiveRef": {
            "id": "objective:publish-verified-result",
            "digest": _digest("objective"),
        },
        "methodBindings": [
            {
                "id": "method:composition",
                "skillId": "project-ordivon-next/compositional-contracts",
                "instructionDigest": _digest("composition-skill"),
                "role": "advisory",
            }
        ],
        "capabilityBindings": [
            {
                "id": "capability:artifact-verify",
                "capability": "artifact.verify",
                "ownerId": "artifact",
                "sourceKind": "direct-owner",
                "bindingDigest": _digest("artifact-capability"),
                "truthBoundary": (
                    "Artifact owns carrier-format verification, not scientific claim truth."
                ),
            }
        ],
        "stages": [
            {
                "id": "stage:research",
                "ownerId": "research",
                "responsibility": "Produce a claim/evidence bundle.",
                "dependsOn": [],
                "methodBindings": ["method:composition"],
                "capabilityBindings": [],
                "inputs": ["objective"],
                "outputs": ["claim-evidence"],
            },
            {
                "id": "stage:artifact",
                "ownerId": "artifact",
                "responsibility": "Build and mechanically verify the publication carrier.",
                "dependsOn": ["stage:research"],
                "methodBindings": [],
                "capabilityBindings": ["capability:artifact-verify"],
                "inputs": ["claim-evidence"],
                "outputs": ["verified-carrier"],
            },
        ],
        "edges": [
            {
                "id": "edge:research-to-artifact",
                "from": {"stageId": "stage:research", "port": "claim-evidence"},
                "to": {"stageId": "stage:artifact", "port": "claim-evidence"},
                "contractRef": "contract:claim-evidence-carrier",
            }
        ],
        "gateRequirements": [
            {
                "id": "gate:claim-evidence-binding",
                "producerStageId": "stage:research",
                "consumerStageId": "stage:artifact",
                "assumption": (
                    "Artifact receives claim identifiers bound to the exact research evidence."
                ),
                "guarantee": ("Research emits claim identifiers and exact evidence references."),
                "verifierOwnerId": "research",
                "supportScope": "claim/evidence identity seam only",
                "required": True,
            }
        ],
        "unresolvedAssumptions": [],
        "nonClaims": [
            "Compilation does not grant execution authority.",
            "Composition-gate closure does not establish publication acceptance.",
        ],
    }


def gate_result(manifest: dict, standing: str = "SATISFIED") -> dict:
    compiled = compile_manifest(manifest)
    evidence = [] if standing == "UNKNOWN" else ["evidence:claim-binding-r1"]
    return {
        "schemaVersion": 1,
        "kind": "ordivon.composition-gate-result",
        "circuitId": manifest["circuitId"],
        "manifestDigest": compiled["manifestDigest"],
        "gateId": "gate:claim-evidence-binding",
        "verifierOwnerId": "research",
        "standing": standing,
        "evidenceRefs": evidence,
        "supportScope": "claim/evidence identity seam only",
        "nonClaims": ["This result does not establish artifact quality or publication acceptance."],
    }


def test_compile_is_deterministic_and_non_authoritative() -> None:
    manifest = valid_manifest()
    first = compile_manifest(manifest)
    second = compile_manifest(copy.deepcopy(manifest))

    assert first == second
    assert first["stageOrder"] == ["stage:research", "stage:artifact"]
    assert first["truthRole"] == "task-local-non-authoritative-composition-projection"
    assert "grants no Tool" in first["authorityBoundary"]
    assert "workflow" in first["authorityBoundary"]


def test_unknown_method_binding_fails_closed() -> None:
    manifest = valid_manifest()
    manifest["stages"][0]["methodBindings"] = ["method:missing"]

    with pytest.raises(CircuitContractError, match="unknown method bindings"):
        validate_manifest(manifest)


def test_dependency_cycle_fails_closed() -> None:
    manifest = valid_manifest()
    manifest["stages"][0]["dependsOn"] = ["stage:artifact"]

    with pytest.raises(CircuitContractError, match="dependency cycle"):
        validate_manifest(manifest)


def test_edge_requires_declared_ports_and_dependency() -> None:
    manifest = valid_manifest()
    manifest["stages"][1]["dependsOn"] = []

    with pytest.raises(CircuitContractError, match="requires stage:artifact to depend"):
        validate_manifest(manifest)


def test_cross_owner_gate_cannot_collapse_to_one_owner() -> None:
    manifest = valid_manifest()
    manifest["stages"][1]["ownerId"] = "research"

    with pytest.raises(CircuitContractError, match="must cross an owner boundary"):
        validate_manifest(manifest)


def test_satisfied_gate_closes_only_mechanical_composition() -> None:
    manifest = valid_manifest()
    projection = evaluate_gate_results(manifest, [gate_result(manifest)])

    assert projection["standing"] == "COMPOSITION_GATES_SATISFIED"
    assert projection["mechanicalClosure"] is True
    assert projection["domainAcceptanceEstablished"] is False


def test_unknown_or_missing_gate_remains_open() -> None:
    manifest = valid_manifest()

    missing = evaluate_gate_results(manifest, [])
    assert missing["standing"] == "COMPOSITION_GATES_OPEN"
    assert missing["missingGateIds"] == ["gate:claim-evidence-binding"]

    unknown = evaluate_gate_results(manifest, [gate_result(manifest, "UNKNOWN")])
    assert unknown["standing"] == "COMPOSITION_GATES_OPEN"
    assert unknown["unknownGateIds"] == ["gate:claim-evidence-binding"]


def test_unsatisfied_gate_fails_composition_closure() -> None:
    manifest = valid_manifest()
    projection = evaluate_gate_results(
        manifest,
        [gate_result(manifest, "UNSATISFIED")],
    )

    assert projection["standing"] == "COMPOSITION_GATES_UNSATISFIED"
    assert projection["mechanicalClosure"] is False


def test_stale_gate_result_is_rejected_by_manifest_digest() -> None:
    manifest = valid_manifest()
    result = gate_result(manifest)
    result["manifestDigest"] = _digest("different-manifest")

    with pytest.raises(CircuitContractError, match="stale/different manifest digest"):
        evaluate_gate_results(manifest, [result])


def test_gate_result_cannot_widen_support_scope() -> None:
    manifest = valid_manifest()
    result = gate_result(manifest)
    result["supportScope"] = "all research and publication semantics"

    with pytest.raises(CircuitContractError, match="support scope mismatch"):
        evaluate_gate_results(manifest, [result])


def test_unresolved_manifest_assumption_blocks_mechanical_closure() -> None:
    manifest = valid_manifest()
    manifest["unresolvedAssumptions"] = ["Venue-specific visual acceptance is unresolved."]
    result = gate_result(manifest)

    projection = evaluate_gate_results(manifest, [result])

    assert projection["standing"] == "COMPOSITION_GATES_OPEN"
    assert projection["mechanicalClosure"] is False
    assert projection["unresolvedAssumptions"] == [
        "Venue-specific visual acceptance is unresolved."
    ]


def test_private_workflow_or_retry_policy_is_not_in_manifest_contract() -> None:
    manifest = valid_manifest()
    manifest["workflowEngine"] = "ordivon-private"
    with pytest.raises(CircuitContractError, match="schema violation"):
        validate_manifest(manifest)

    manifest = valid_manifest()
    manifest["retryPolicy"] = {"attempts": 3}
    with pytest.raises(CircuitContractError, match="schema violation"):
        validate_manifest(manifest)
