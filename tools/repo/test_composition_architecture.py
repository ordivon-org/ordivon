from __future__ import annotations

import copy
import importlib.util
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
GRAPH = ROOT / "docs" / "architecture" / "ordivon-composition-architecture-lego-r1.json"
MODULE_PATH = ROOT / "tools" / "repo" / "check_composition_architecture.py"

spec = importlib.util.spec_from_file_location("check_composition_architecture", MODULE_PATH)
assert spec is not None and spec.loader is not None
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def load_graph() -> dict:
    value = json.loads(GRAPH.read_text(encoding="utf-8"))
    assert isinstance(value, dict)
    return value


def test_current_composition_graph_is_valid() -> None:
    module.validate_graph(load_graph())


def test_duplicate_node_id_fails_closed() -> None:
    value = load_graph()
    value["nodes"].append(copy.deepcopy(value["nodes"][0]))
    with pytest.raises(module.CompositionArchitectureError, match="duplicate node id"):
        module.validate_graph(value)


def test_unknown_dependency_fails_closed() -> None:
    value = load_graph()
    value["nodes"][0]["dependsOn"] = ["DOES_NOT_EXIST"]
    with pytest.raises(module.CompositionArchitectureError, match="unknown dependencies"):
        module.validate_graph(value)


def test_cycle_fails_closed() -> None:
    value = load_graph()
    first = value["nodes"][0]["id"]
    second = value["nodes"][1]["id"]
    value["nodes"][0]["dependsOn"] = [second]
    value["nodes"][1]["dependsOn"] = [first]
    with pytest.raises(module.CompositionArchitectureError, match="dependency cycle"):
        module.validate_graph(value)


@pytest.mark.parametrize("cycle", [False, True])
def test_long_dependency_chain_uses_nonrecursive_mature_graph_kernel(
    cycle: bool,
) -> None:
    """A deep, bounded owner-DAG must not depend on Python recursion depth."""
    value = load_graph()
    exemplar = copy.deepcopy(value["nodes"][0])
    predecessor = exemplar["id"]
    for index in range(2048):
        node = copy.deepcopy(exemplar)
        node["id"] = f"DEEP{index:04d}"
        node["wave"] = "W1"
        node["dependsOn"] = [predecessor]
        value["nodes"].append(node)
        predecessor = node["id"]
    if cycle:
        value["nodes"][-2048]["dependsOn"] = [predecessor]
        with pytest.raises(module.CompositionArchitectureError, match="dependency cycle"):
            module.validate_graph(value)
    else:
        module.validate_graph(value)


def test_gateway_truth_boundary_must_remain_non_authoritative() -> None:
    value = load_graph()
    gateway = next(node for node in value["nodes"] if node["owner"] == "gateway")
    gateway["authorityBoundary"] = "Gateway owns canonical task and domain truth."
    with pytest.raises(module.CompositionArchitectureError, match="non-authoritative"):
        module.validate_graph(value)


def test_on_demand_node_cannot_enter_critical_path() -> None:
    value = load_graph()
    on_demand = next(node["id"] for node in value["nodes"] if node["wave"] == "W6_ON_DEMAND")
    value["criticalPath"].append(on_demand)
    with pytest.raises(module.CompositionArchitectureError, match="on-demand"):
        module.validate_graph(value)

def test_initial_parallel_set_rejects_duplicate_nodes() -> None:
    value = load_graph()
    value["initialParallelSet"].append(value["initialParallelSet"][0])
    with pytest.raises(module.CompositionArchitectureError, match="duplicate initialParallelSet"):
        module.validate_graph(value)


@pytest.mark.parametrize("dependent", ["G02", "P01"])
def test_initial_parallel_set_must_be_dependency_antichain(dependent: str) -> None:
    value = load_graph()
    # G02 depends directly on G01; P01 depends on G01 transitively.
    assert "G01" in value["initialParallelSet"]
    value["initialParallelSet"].append(dependent)
    with pytest.raises(module.CompositionArchitectureError, match="parallel dependency"):
        module.validate_graph(value)


def test_on_demand_node_cannot_be_initial_parallel_work() -> None:
    value = load_graph()
    value["initialParallelSet"] = ["O01"]
    with pytest.raises(module.CompositionArchitectureError, match="on-demand"):
        module.validate_graph(value)



def test_lego21_dependency_edge_is_unique() -> None:
    """A typed graph edge is a relation, not a counted multiset of imports."""
    value = load_graph()
    node = next(n for n in value["nodes"] if n["id"] == "G02")
    node["dependsOn"] = ["G01", "G01"]
    with pytest.raises(module.CompositionArchitectureError, match="duplicate dependencies"):
        module.validate_graph(value)


def test_lego21_critical_path_is_topological_order() -> None:
    """A claimed execution order cannot list a consumer before its prerequisite."""
    value = load_graph()
    order = value["criticalPath"]
    i, j = order.index("G01"), order.index("G02")
    order[i], order[j] = order[j], order[i]
    with pytest.raises(module.CompositionArchitectureError, match="criticalPath dependency order"):
        module.validate_graph(value)



def test_lego21_critical_path_rejects_transitive_noncritical_prerequisite() -> None:
    """Scheduling depends on transitive reachability, not only listed edges."""
    value = load_graph()
    intermediary = copy.deepcopy(value["nodes"][0])
    intermediary["id"] = "INTERMEDIARY"
    intermediary["owner"] = "runtime"
    intermediary["dependsOn"] = ["G01"]
    value["nodes"].append(intermediary)
    consumer = next(node for node in value["nodes"] if node["id"] == "G02")
    consumer["dependsOn"] = ["INTERMEDIARY"]
    critical = value["criticalPath"]
    a, b = critical.index("G01"), critical.index("G02")
    critical[a], critical[b] = critical[b], critical[a]
    with pytest.raises(module.CompositionArchitectureError, match="criticalPath dependency order"):
        module.validate_graph(value)
