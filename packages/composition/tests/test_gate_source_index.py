"""Independent full-scan oracle for source-only sparse Gate readsets."""

import copy
import json
import random
from pathlib import Path

import pytest

from ordivon_composition.cognitive_circuit_r1 import canonical_digest, compile_manifest
from ordivon_composition.verification_impact import _GateSourceIndex, compare_gate_source_scopes


def scalar_scope(manifest, gate_id):
    gate = next(row for row in manifest["gateRequirements"] if row["id"] == gate_id)
    included = {gate["producerStageId"], gate["consumerStageId"]}
    # Independent fixed point over complete stage table.
    while True:
        expanded = included | {
            parent
            for stage in manifest["stages"]
            if stage["id"] in included
            for parent in stage["dependsOn"]
        }
        if expanded == included:
            break
        included = expanded
    stages = sorted(
        (row for row in manifest["stages"] if row["id"] in included), key=lambda row: row["id"]
    )
    scoped = {
        key: manifest[key]
        for key in ("schemaVersion", "kind", "circuitId", "objectiveRef", "nonClaims")
    }
    scoped["unresolvedAssumptions"] = sorted(manifest["unresolvedAssumptions"])
    scoped["stages"] = stages
    for table in ("methodBindings", "capabilityBindings"):
        ids = {ref for stage in stages for ref in stage[table]}
        scoped[table] = sorted(
            (row for row in manifest[table] if row["id"] in ids), key=lambda row: row["id"]
        )
    scoped["incomingEdges"] = sorted(
        (edge for edge in manifest["edges"] if edge["to"]["stageId"] in included),
        key=lambda row: row["id"],
    )
    scoped["upstreamGates"] = sorted(
        (row for row in manifest["gateRequirements"] if row["consumerStageId"] in included),
        key=lambda row: row["id"],
    )
    return canonical_digest(scoped)


def admission_profiles():
    root = Path(__file__).resolve().parents[1] / "profiles/admission"
    return [json.loads(p.read_text()) for p in sorted(root.glob("*-circuit-r1.json"))]


def independent_branches(n):
    result = copy.deepcopy(admission_profiles()[0])
    template = copy.deepcopy(result)
    for field in ("stages", "edges", "gateRequirements"):
        result[field] = []
    for i in range(n):

        def ref(x):
            return f"{x}-{i}"

        for stage in template["stages"]:
            row = copy.deepcopy(stage)
            row["id"] = ref(row["id"])
            row["dependsOn"] = [ref(x) for x in row["dependsOn"]]
            result["stages"].append(row)
        for edge in template["edges"]:
            row = copy.deepcopy(edge)
            row["id"] = ref(row["id"])
            for direction in ("from", "to"):
                row[direction]["stageId"] = ref(row[direction]["stageId"])
            result["edges"].append(row)
        for gate in template["gateRequirements"]:
            row = copy.deepcopy(gate)
            for field in ("id", "producerStageId", "consumerStageId"):
                row[field] = ref(row[field])
            result["gateRequirements"].append(row)
    return result


@pytest.mark.parametrize("manifest", admission_profiles(), ids=lambda x: x["circuitId"])
def test_native_profile_scope_digests(manifest):
    compile_manifest(manifest)
    index = _GateSourceIndex(manifest)
    for gate in manifest["gateRequirements"]:
        assert index.digest(gate["id"]) == scalar_scope(manifest, gate["id"])


@pytest.mark.parametrize("seed", range(12))
def test_indexed_delta_matches_scan_on_reordered_sparse_graph(seed):
    rng = random.Random(seed)
    old = independent_branches(4)
    new = copy.deepcopy(old)
    # Mutate a stage, a gate membership or a capability contract; independently
    # shuffle every table. Changes must stay local except shared bindings.
    choice = seed % 4
    if choice == 0:
        rng.choice(new["stages"])["responsibility"] += " Changed."
    elif choice == 1:
        gate = copy.deepcopy(rng.choice(new["gateRequirements"]))
        gate["id"] += "-extra"
        new["gateRequirements"].append(gate)
    elif choice == 2:
        new["gateRequirements"].pop(rng.randrange(len(new["gateRequirements"])))
    else:
        rng.choice(new["capabilityBindings"])["truthBoundary"] += " Changed."
    for key in ("stages", "edges", "gateRequirements", "methodBindings", "capabilityBindings"):
        rng.shuffle(new[key])
    compile_manifest(old)
    compile_manifest(new)
    common = sorted(
        {row["id"] for row in old["gateRequirements"]}
        & {row["id"] for row in new["gateRequirements"]}
    )
    for manifest in (old, new):
        index = _GateSourceIndex(manifest)
        for gate in manifest["gateRequirements"]:
            assert index.digest(gate["id"]) == scalar_scope(manifest, gate["id"])
    changed = [gate for gate in common if scalar_scope(old, gate) != scalar_scope(new, gate)]
    observed = compare_gate_source_scopes(old, new)
    assert observed["changedGateIds"] == changed
    assert observed["unchangedGateIds"] == sorted(set(common) - set(changed))
    assert observed["proofReuseAdmissible"] is False
