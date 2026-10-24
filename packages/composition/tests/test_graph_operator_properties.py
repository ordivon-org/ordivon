"""Consumer invariants for the existing graphlib-backed LEGO DAG operator.

Deterministic seeded graph families provide bounded property coverage without
adding a second graph engine, third-party orchestrator, or unbounded fuzz task.
"""

import copy
import random

import pytest
from test_cognitive_circuit_r1 import valid_manifest

from ordivon_composition.cognitive_circuit_r1 import (
    CircuitContractError,
    compile_manifest,
)


def _manifest_for_seed(seed: int) -> dict:
    rng = random.Random(seed)
    result = valid_manifest()
    count = 24
    stages = []
    for index in range(count):
        available = [f"stage:{previous:02d}" for previous in range(index)]
        parents = [parent for parent in available if rng.random() < 0.22]
        if index == count - 1 and "stage:00" not in parents:
            parents.append("stage:00")
        stages.append(
            {
                "id": f"stage:{index:02d}",
                "ownerId": "research",
                "responsibility": f"Verify independent operator {index}.",
                "dependsOn": parents,
                "methodBindings": [],
                "capabilityBindings": [],
                "inputs": [],
                "outputs": [],
            }
        )
    result["stages"] = stages
    result["edges"] = []
    result["gateRequirements"] = []
    return result


def _assert_valid_topological_projection(manifest: dict, order: list[str]) -> None:
    stages = manifest["stages"]
    expected = {stage["id"] for stage in stages}
    assert len(order) == len(expected)
    assert set(order) == expected
    positions = {stage_id: index for index, stage_id in enumerate(order)}
    for stage in stages:
        for parent in stage["dependsOn"]:
            assert positions[parent] < positions[stage["id"]]


@pytest.mark.parametrize("seed", list(range(8)))
def test_seeded_dag_family_is_deterministic_and_respects_every_edge(seed: int):
    manifest = _manifest_for_seed(seed)
    baseline = compile_manifest(manifest)
    expected_order = baseline["stageOrder"]
    _assert_valid_topological_projection(manifest, expected_order)
    rng = random.Random(seed + 1337)
    for _ in range(6):
        reshuffled = copy.deepcopy(manifest)
        rng.shuffle(reshuffled["stages"])
        for stage in reshuffled["stages"]:
            rng.shuffle(stage["dependsOn"])
        actual = compile_manifest(reshuffled)
        _assert_valid_topological_projection(reshuffled, actual["stageOrder"])
        assert actual["stageOrder"] == expected_order


@pytest.mark.parametrize("seed", [0, 7, 23])
def test_added_cycle_and_unknown_dependency_fail_closed(seed: int):
    manifest = _manifest_for_seed(seed)
    cyclic = copy.deepcopy(manifest)
    cyclic["stages"][0]["dependsOn"] = ["stage:23"]
    with pytest.raises(CircuitContractError, match="dependency cycle"):
        compile_manifest(cyclic)
    unknown = copy.deepcopy(manifest)
    unknown["stages"][12]["dependsOn"] = ["stage:missing"]
    with pytest.raises(CircuitContractError, match="depends on unknown stages"):
        compile_manifest(unknown)


def test_ready_successor_precedes_unrelated_late_root() -> None:
    """Canonical topological priority must survive replacing the DAG engine."""
    manifest = _manifest_for_seed(0)
    manifest["stages"] = [
        {**manifest["stages"][0], "id": "stage:z", "dependsOn": []},
        {**manifest["stages"][1], "id": "stage:a", "dependsOn": []},
        {**manifest["stages"][2], "id": "stage:b", "dependsOn": ["stage:a"]},
    ]
    assert compile_manifest(manifest)["stageOrder"] == [
        "stage:a",
        "stage:b",
        "stage:z",
    ]
