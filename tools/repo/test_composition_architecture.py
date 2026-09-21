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
