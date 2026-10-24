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


def test_deep_valid_dependency_dag_uses_iterative_owner_graph_operator() -> None:
    # A legitimate parallelizable owner graph is a finite DAG regardless of
    # Python's call-stack depth. The already-existing topological operator is
    # iterative; a second recursive DFS must not reject a valid representation.
    manifest = valid_manifest()
    exemplar = manifest["stages"][0]
    stages = []
    for index in range(1100):
        stage = copy.deepcopy(exemplar)
        stage["id"] = f"stage:chain-{index:04d}"
        stage["ownerId"] = f"owner-{index:04d}"
        stage["dependsOn"] = [] if index == 1099 else [f"stage:chain-{index + 1:04d}"]
        stages.append(stage)
    manifest["stages"] = stages
    manifest["edges"] = []
    manifest["gateRequirements"] = []
    compiled = compile_manifest(manifest)
    assert compiled["stageOrder"] == [stage["id"] for stage in reversed(stages)]
    assert compiled["requiredGateIds"] == []


def test_three_stage_graph_operator_matches_exhaustive_topological_oracle() -> None:
    # Exhaust all 2^6 directed edge subsets on three stages, without a new
    # model checker or Graph Owner. A legal DAG has some permutation respecting
    # each dependency; a cyclic graph has none. This oracle is deliberately
    # independent of the native Kahn implementation.
    from itertools import permutations

    identifiers = ["stage:a", "stage:b", "stage:c"]
    edges = [
        (target, source) for target in identifiers for source in identifiers if source != target
    ]
    template = valid_manifest()
    for mask in range(1 << len(edges)):
        relations = [edge for index, edge in enumerate(edges) if mask & (1 << index)]
        manifest = copy.deepcopy(template)
        stages = []
        for stage_id in identifiers:
            stage = copy.deepcopy(template["stages"][0])
            stage["id"] = stage_id
            stage["ownerId"] = stage_id.replace("stage:", "owner:")
            stage["dependsOn"] = [source for target, source in relations if target == stage_id]
            stages.append(stage)
        manifest["stages"] = stages
        manifest["edges"] = []
        manifest["gateRequirements"] = []

        valid_orders = [
            ordering
            for ordering in permutations(identifiers)
            if all(ordering.index(source) < ordering.index(target) for target, source in relations)
        ]
        if not valid_orders:
            with pytest.raises(CircuitContractError, match="dependency cycle"):
                compile_manifest(manifest)
            continue

        compiled = compile_manifest(manifest)
        assert tuple(compiled["stageOrder"]) in valid_orders
        reordered = copy.deepcopy(manifest)
        reordered["stages"].reverse()
        assert compile_manifest(reordered)["stageOrder"] == compiled["stageOrder"]


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


def test_distinct_producers_cannot_implicitly_merge_at_one_consumer_input() -> None:
    manifest = valid_manifest()
    manifest["stages"].append(
        {
            "id": "stage:quality",
            "ownerId": "qa",
            "responsibility": "Produce independent quality evidence.",
            "dependsOn": [],
            "methodBindings": [],
            "capabilityBindings": [],
            "inputs": ["objective"],
            "outputs": ["quality-evidence"],
        }
    )
    consumer = manifest["stages"][1]
    consumer["dependsOn"].append("stage:quality")
    manifest["edges"].append(
        {
            "id": "edge:quality-to-artifact",
            "from": {"stageId": "stage:quality", "port": "quality-evidence"},
            "to": {"stageId": "stage:artifact", "port": "claim-evidence"},
            "contractRef": "contract:quality-evidence",
        }
    )
    with pytest.raises(CircuitContractError, match="already receives"):
        compile_manifest(manifest)

    # Distinct explicitly authored ports compose without selecting a winner.
    consumer["inputs"].append("quality-evidence")
    manifest["edges"][-1]["to"]["port"] = "quality-evidence"
    compiled = compile_manifest(manifest)
    assert compiled["stageOrder"][-1] == "stage:artifact"


def test_cross_owner_gate_cannot_collapse_to_one_owner() -> None:
    manifest = valid_manifest()
    manifest["stages"][1]["ownerId"] = "research"

    with pytest.raises(CircuitContractError, match="must cross an owner boundary"):
        validate_manifest(manifest)


def test_task_local_gate_closure_does_not_claim_all_data_edges_are_verified() -> None:
    """A bounded R3-style verifier may consume a multi-edge pathway.

    Gate closure concerns only the declared target; treating each cross-owner
    data edge as requiring a separate Gate would reject the real
    Research->Artifact->Research consumer without proving anything stronger.
    """
    manifest = valid_manifest()
    manifest["stages"].append(
        {
            "id": "stage:independent",
            "ownerId": "qa",
            "responsibility": "Produce independent QA evidence.",
            "dependsOn": [],
            "methodBindings": [],
            "capabilityBindings": [],
            "inputs": [],
            "outputs": ["quality"],
        }
    )
    artifact = manifest["stages"][1]
    artifact["dependsOn"].append("stage:independent")
    artifact["inputs"].append("quality")
    manifest["edges"].append(
        {
            "id": "edge:qa-to-artifact",
            "from": {"stageId": "stage:independent", "port": "quality"},
            "to": {"stageId": "stage:artifact", "port": "quality"},
            "contractRef": "contract:quality",
        }
    )

    # Research's original gate still proves exactly its own supportScope,
    # not the newly introduced QA edge. Whole-graph equivalence is UNKNOWN.
    projection = evaluate_gate_results(manifest, [gate_result(manifest)])
    assert projection["standing"] == "COMPOSITION_GATES_SATISFIED"
    assert projection["mechanicalClosure"] is True
    assert projection["domainAcceptanceEstablished"] is False
    assert "all required task-local composition" in projection["claimBoundary"]


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


def test_composition_without_required_evidence_never_claims_mechanical_closure() -> None:
    """The empty conjunction is not evidence of a verified cross-owner boundary."""
    manifest = valid_manifest()
    manifest["gateRequirements"] = []
    projection = evaluate_gate_results(manifest, [])
    assert projection["requiredGateIds"] == []
    assert projection["standing"] == "COMPOSITION_GATES_OPEN"
    assert projection["mechanicalClosure"] is False
    assert projection["domainAcceptanceEstablished"] is False
