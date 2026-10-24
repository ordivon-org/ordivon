"""Consumer invariants for the existing graphlib-backed LEGO DAG operator.

Deterministic seeded graph families provide bounded property coverage without
adding a second graph engine, third-party orchestrator, or unbounded fuzz task.
"""

import copy
import random
import sys

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


def test_deep_lego_dependency_chain_uses_mature_nonrecursive_graph_kernel() -> None:
    """A valid bounded task graph must not inherit Python's call-stack limit."""
    manifest = valid_manifest()
    count = max(1200, sys.getrecursionlimit() + 12)
    manifest["stages"] = [
        {
            "id": f"stage:{i:05}",
            "ownerId": "research",
            "responsibility": "Independent composable task node.",
            "dependsOn": [] if i == count - 1 else [f"stage:{i + 1:05}"],
            "methodBindings": [],
            "capabilityBindings": [],
            "inputs": [],
            "outputs": [],
        }
        for i in range(count)
    ]
    manifest["edges"] = []
    manifest["gateRequirements"] = []
    original_limit = sys.getrecursionlimit()
    try:
        # Force a deterministic interpreter boundary independent of test runner
        # settings (some owners raise the Python recursion limit globally).
        sys.setrecursionlimit(640)
        result = compile_manifest(manifest)
    finally:
        sys.setrecursionlimit(original_limit)
    assert len(result["stageOrder"]) == count
    assert result["stageOrder"][0] == f"stage:{count - 1:05}"
    assert result["stageOrder"][-1] == "stage:00000"


def test_existing_circuit_lexicographic_ready_order_is_preserved() -> None:
    """A canonical graph order is digest-bearing, not just any legal topo order."""
    manifest = valid_manifest()
    manifest["stages"] = [
        {
            "id": f"stage:{node}",
            "ownerId": "research",
            "responsibility": "Deterministic composition operator.",
            "dependsOn": predecessors,
            "methodBindings": [],
            "capabilityBindings": [],
            "inputs": [],
            "outputs": [],
        }
        for node, predecessors in [
            ("a", []),
            ("b", ["stage:a"]),
            ("c", []),
        ]
    ]
    manifest["edges"] = []
    manifest["gateRequirements"] = []
    assert compile_manifest(manifest)["stageOrder"] == [
        "stage:a",
        "stage:b",
        "stage:c",
    ]
