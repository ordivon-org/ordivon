from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest

from tools.repo import check_architecture_docs as module

ROOT = Path(__file__).resolve().parents[2]

OWNER_GRAPH_PLANS = (
    "services/runtime/planning/lego-plan-r1.json",
    "services/host/planning/lego-plan-r2.json",
    "services/harness/planning/lego-plan-r1.json",
    "platform/network/planning/lego-plan-r1.json",
)


@pytest.mark.parametrize("relative", OWNER_GRAPH_PLANS)
def test_owner_lego_relation_is_total_and_source_bound(relative: str) -> None:
    """A node ID, typed edge or slice reference cannot dangle across Owners."""
    plan = json.loads((ROOT / relative).read_text(encoding="utf-8"))
    module.validate_owner_lego_graph(plan)


@pytest.mark.parametrize("relative", OWNER_GRAPH_PLANS)
def test_owner_lego_rejects_duplicate_node_identity(relative: str) -> None:
    plan = json.loads((ROOT / relative).read_text(encoding="utf-8"))
    plan["nodes"].append(copy.deepcopy(plan["nodes"][0]))
    with pytest.raises(module.ArchitectureDocsError, match="duplicate LEGO node"):
        module.validate_owner_lego_graph(plan)


@pytest.mark.parametrize(
    "relative",
    (
        "services/runtime/planning/lego-plan-r1.json",
        "services/harness/planning/lego-plan-r1.json",
        "platform/network/planning/lego-plan-r1.json",
    ),
)
def test_owner_lego_refuses_unknown_edge_endpoint(relative: str) -> None:
    plan = json.loads((ROOT / relative).read_text(encoding="utf-8"))
    plan["edges"][0]["to"] = "__UNKNOWN_EXTERNAL_STATE__"
    with pytest.raises(module.ArchitectureDocsError, match="unknown LEGO endpoint"):
        module.validate_owner_lego_graph(plan)


@pytest.mark.parametrize(
    "relative",
    (
        "services/runtime/planning/lego-plan-r1.json",
        "services/harness/planning/lego-plan-r1.json",
        "platform/network/planning/lego-plan-r1.json",
    ),
)
def test_owner_lego_refuses_unbound_slice_node(relative: str) -> None:
    plan = json.loads((ROOT / relative).read_text(encoding="utf-8"))
    plan["slices"][0]["nodeIds"].append("__UNKNOWN_PRODUCER__")
    with pytest.raises(module.ArchitectureDocsError, match="unknown LEGO slice node"):
        module.validate_owner_lego_graph(plan)


def test_owner_lego_state_relation_allows_cycles_not_dependency_dag_assumption() -> None:
    """Runtime lifecycle STATE edges may cycle; dependency DAGs are a different type."""
    plan = json.loads((ROOT / OWNER_GRAPH_PLANS[0]).read_text(encoding="utf-8"))
    plan["edges"].append(
        {"from": plan["nodes"][0]["id"], "to": plan["nodes"][0]["id"], "type": "STATE", "label": "retry"}
    )
    module.validate_owner_lego_graph(plan)
