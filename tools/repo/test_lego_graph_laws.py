from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest

from tools.repo import check_architecture_docs as module

ROOT = Path(__file__).resolve().parents[2]

OWNER_GRAPH_PLANS = (
    "services/runtime/planning/lego-plan-r1.json",
    "services/host/planning/lego-plan-r1.json",
    "services/harness/planning/lego-plan-r1.json",
    "platform/network/planning/lego-plan-r1.json",
)


@pytest.mark.parametrize("relative", OWNER_GRAPH_PLANS)
def test_owner_slice_relation_is_closed(relative: str) -> None:
    module.validate_owner_lego_graph(json.loads((ROOT / relative).read_text(encoding="utf-8")))


def test_host_node_kind_is_not_silently_untyped() -> None:
    plan = json.loads((ROOT / OWNER_GRAPH_PLANS[1]).read_text(encoding="utf-8"))
    plan["nodes"][0]["kind"] = ""
    with pytest.raises(module.ArchitectureDocsError, match="requires a type"):
        module.validate_owner_lego_graph(plan)


def test_host_node_identity_is_unique_even_without_registered_slices() -> None:
    plan = json.loads((ROOT / OWNER_GRAPH_PLANS[1]).read_text(encoding="utf-8"))
    plan["nodes"].append(copy.deepcopy(plan["nodes"][0]))
    with pytest.raises(module.ArchitectureDocsError, match="duplicate LEGO node"):
        module.validate_owner_lego_graph(plan)


@pytest.mark.parametrize("relative", (OWNER_GRAPH_PLANS[0], OWNER_GRAPH_PLANS[2], OWNER_GRAPH_PLANS[3]))
def test_owner_lego_refuses_unknown_slice_node(relative: str) -> None:
    plan = json.loads((ROOT / relative).read_text(encoding="utf-8"))
    plan["slices"][0]["nodeIds"].append("__UNKNOWN_PRODUCER__")
    with pytest.raises(module.ArchitectureDocsError, match="unknown LEGO slice node"):
        module.validate_owner_lego_graph(plan)


def test_unregistered_slice_cannot_hide_unbound_node() -> None:
    plan = json.loads((ROOT / OWNER_GRAPH_PLANS[0]).read_text(encoding="utf-8"))
    plan["slices"].append({"id": "UNREGISTERED", "nodeIds": ["UNKNOWN"]})
    with pytest.raises(module.ArchitectureDocsError, match="unknown LEGO slice node"):
        module.validate_owner_lego_graph(plan)


def test_unregistered_slice_ids_are_injective() -> None:
    plan = json.loads((ROOT / OWNER_GRAPH_PLANS[0]).read_text(encoding="utf-8"))
    extra = {"id": "UNREGISTERED", "nodeIds": [plan["nodes"][0]["id"]]}
    plan["slices"].extend([copy.deepcopy(extra), copy.deepcopy(extra)])
    with pytest.raises(module.ArchitectureDocsError, match="duplicate LEGO slice"):
        module.validate_owner_lego_graph(plan)


def test_slice_has_no_duplicate_node_refs() -> None:
    plan = json.loads((ROOT / OWNER_GRAPH_PLANS[0]).read_text(encoding="utf-8"))
    plan["slices"][0]["nodeIds"].append(plan["slices"][0]["nodeIds"][0])
    with pytest.raises(module.ArchitectureDocsError, match="duplicate LEGO slice node"):
        module.validate_owner_lego_graph(plan)
