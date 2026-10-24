"""Consumer invariants for the existing graphlib-backed LEGO DAG operator.

Deterministic seeded graph families provide bounded property coverage without
adding a second graph engine, third-party orchestrator, or unbounded fuzz task.
"""

import copy
import random

import pytest
from test_cognitive_circuit_r1 import valid_manifest

from ordivon_composition import cognitive_circuit_r1 as compiler
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


def test_long_acyclic_lego_dependency_chain_is_valid_without_recursion() -> None:
    # The schema permits unbounded stage counts. A legal dependency chain must
    # not be rejected by the Python call-stack limit of a handwritten DFS.
    manifest = valid_manifest()
    manifest["edges"] = []
    manifest["gateRequirements"] = []
    manifest["stages"] = [
        {
            "id": f"stage:{n:04}",
            "ownerId": "research",
            "responsibility": f"Independent consumer {n}",
            "dependsOn": [f"stage:{n - 1:04}"] if n else [],
            "methodBindings": [],
            "capabilityBindings": [],
            "inputs": [],
            "outputs": [],
        }
        for n in range(1500)
    ]
    projection = compile_manifest(manifest)
    assert projection["stageOrder"] == [f"stage:{n:04}" for n in range(1500)]


def test_long_dependency_chain_cycle_fails_as_contract_error() -> None:
    manifest = _manifest_for_seed(2)
    manifest["stages"] = [
        {
            "id": f"stage:{n:04}",
            "ownerId": "research",
            "responsibility": f"Independent consumer {n}",
            "dependsOn": [f"stage:{n - 1:04}"] if n else [],
            "methodBindings": [],
            "capabilityBindings": [],
            "inputs": [],
            "outputs": [],
        }
        for n in range(1500)
    ]
    manifest["stages"][0]["dependsOn"] = ["stage:1499"]
    with pytest.raises(CircuitContractError, match="dependency cycle"):
        compile_manifest(manifest)


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


def test_all_three_node_directed_graphs_match_permutation_oracle() -> None:
    """Bounded exhaustive LEGO graph proof independent of graphlib's algorithm.

    All 2^(3*2) labeled directed loop-free relations are enumerated. A graph
    is a DAG iff a permutation can place each producer before its consumer.
    The production graphlib operator must accept exactly those cases and
    project their lexicographically minimal valid ordering.
    """
    from itertools import permutations

    names = ("stage:a", "stage:b", "stage:c")
    possible_edges = [(target, source) for target in names for source in names if target != source]
    template = valid_manifest()
    dag_count = 0
    cycle_count = 0
    for mask in range(1 << len(possible_edges)):
        edges = [edge for index, edge in enumerate(possible_edges) if mask & (1 << index)]
        manifest = copy.deepcopy(template)
        stages = []
        for name in names:
            stage = copy.deepcopy(template["stages"][0])
            stage.update(
                id=name,
                ownerId=name.replace("stage:", "owner:"),
                dependsOn=[source for target, source in edges if target == name],
            )
            stages.append(stage)
        manifest["stages"] = stages
        manifest["edges"] = []
        manifest["gateRequirements"] = []

        valid_orders = [
            permutation
            for permutation in permutations(names)
            if all(
                permutation.index(source) < permutation.index(target) for target, source in edges
            )
        ]
        if not valid_orders:
            cycle_count += 1
            with pytest.raises(CircuitContractError, match="dependency cycle"):
                compile_manifest(manifest)
            continue

        dag_count += 1
        expected = list(min(valid_orders))
        assert compile_manifest(manifest)["stageOrder"] == expected
        manifest["stages"].reverse()
        assert compile_manifest(manifest)["stageOrder"] == expected

    assert (dag_count, cycle_count) == (25, 39)


def test_compile_discharges_dag_validation_once_not_twice(monkeypatch: pytest.MonkeyPatch) -> None:
    """One canonical validated linear extension feeds the compiled projection.

    The public standalone validation contract still returns None. A compiled
    manifest must not repeat its already-validated graph kernel unnecessarily.
    """
    native = compiler._topological_order
    calls: list[int] = []

    def bound_once(rows: list[dict]) -> list[str]:
        calls.append(len(rows))
        return native(rows)

    monkeypatch.setattr(compiler, "_topological_order", bound_once)
    manifest = _manifest_for_seed(13)
    assert compiler.validate_manifest(manifest) is None
    calls.clear()
    compiled = compiler.compile_manifest(manifest)
    _assert_valid_topological_projection(manifest, compiled["stageOrder"])
    assert calls == [len(manifest["stages"])]
