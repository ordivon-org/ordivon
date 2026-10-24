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


def test_host_legacy_agent_service_cursor_proposal_is_retired() -> None:
    """An old proposed LEGO is not an owner merely because its R1 row survived."""
    legacy = json.loads((ROOT / OWNER_GRAPH_PLANS[1]).read_text(encoding="utf-8"))
    current = json.loads(
        (ROOT / "services/host/planning/lego-plan-r3.json").read_text(encoding="utf-8")
    )
    assert any(row["id"] == "U01" and row["name"] == "ScopeBoundCursor" for row in current["retained"])
    assert all(node["id"] != "O05" for node in legacy["nodes"])
    assert all(slice_["id"] != "OS1" for slice_ in legacy["slices"])
    assert legacy["gaps"] == []


@pytest.mark.parametrize("relative", OWNER_GRAPH_PLANS)
def test_owner_slice_relation_is_closed(relative: str) -> None:
    module.validate_owner_lego_graph(json.loads((ROOT / relative).read_text(encoding="utf-8")))


@pytest.mark.parametrize("relative", OWNER_GRAPH_PLANS)
def test_owner_node_whitespace_alias_does_not_mint_second_lego(relative: str) -> None:
    plan = json.loads((ROOT / relative).read_text(encoding="utf-8"))
    alias = copy.deepcopy(plan["nodes"][0])
    alias["id"] = " " + alias["id"] + " "
    plan["nodes"].append(alias)
    with pytest.raises(module.ArchitectureDocsError, match="non-canonical LEGO node identity"):
        module.validate_owner_lego_graph(plan)


def test_unregistered_slice_whitespace_alias_does_not_mint_second_slice() -> None:
    plan = json.loads((ROOT / OWNER_GRAPH_PLANS[0]).read_text(encoding="utf-8"))
    alias = copy.deepcopy(plan["slices"][0])
    alias["id"] = " " + alias["id"] + " "
    plan["slices"].append(alias)
    with pytest.raises(module.ArchitectureDocsError, match="non-canonical LEGO slice identity"):
        module.validate_owner_lego_graph(plan)


def test_direct_owner_dependency_check_rejects_whitespace_alias() -> None:
    plan = json.loads((ROOT / OWNER_GRAPH_PLANS[0]).read_text(encoding="utf-8"))
    alias = copy.deepcopy(plan["nodes"][0])
    alias["id"] = " " + alias["id"] + " "
    plan["nodes"].append(alias)
    with pytest.raises(module.ArchitectureDocsError, match="non-canonical LEGO node identity"):
        module.validate_owner_lego_dependencies(plan, "services/runtime")


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


@pytest.mark.parametrize("relative", OWNER_GRAPH_PLANS)
@pytest.mark.parametrize("bad_endpoint", ("from", "to"))
def test_every_owner_relation_refuses_unknown_endpoint_even_when_not_a_dependency(
    relative: str, bad_endpoint: str
) -> None:
    """DATA/STATE/EFFECT edges are relations too, never dangling free text."""
    plan = json.loads((ROOT / relative).read_text(encoding="utf-8"))
    malformed = copy.deepcopy(plan["edges"][0])
    malformed.update({"type": "OBSERVATION", bad_endpoint: "NOT_A_REGISTERED_LEGO"})
    plan["edges"].append(malformed)
    with pytest.raises(module.ArchitectureDocsError, match="unknown LEGO edge endpoint"):
        module.validate_owner_lego_graph(plan)


@pytest.mark.parametrize("relative", OWNER_GRAPH_PLANS)
def test_owner_graph_has_single_typed_relation_identity(relative: str) -> None:
    """Repeated (from, to, kind) triples do not create independent evidence."""
    plan = json.loads((ROOT / relative).read_text(encoding="utf-8"))
    plan["edges"].append(copy.deepcopy(plan["edges"][0]))
    with pytest.raises(module.ArchitectureDocsError, match="duplicate LEGO edge"):
        module.validate_owner_lego_graph(plan)


@pytest.mark.parametrize("invalid_kind", ("", "  ", 0, None))
def test_non_dependency_edge_cannot_hide_an_untyped_relation(invalid_kind: object) -> None:
    plan = json.loads((ROOT / OWNER_GRAPH_PLANS[0]).read_text(encoding="utf-8"))
    plan["edges"][0]["type"] = invalid_kind
    with pytest.raises(module.ArchitectureDocsError, match="LEGO edge requires a type"):
        module.validate_owner_lego_graph(plan)


def test_owner_feedback_edges_are_allowed_to_cycle_outside_dependencies() -> None:
    plan = json.loads((ROOT / OWNER_GRAPH_PLANS[3]).read_text(encoding="utf-8"))
    plan["edges"].append({"type": "OBSERVATION", "from": "N04", "to": "N02"})
    module.validate_owner_lego_graph(plan)


def test_same_owner_vertices_can_have_distinct_typed_relations() -> None:
    plan = json.loads((ROOT / OWNER_GRAPH_PLANS[1]).read_text(encoding="utf-8"))
    first = plan["edges"][0]
    plan["edges"].append(
        {"type": "OBSERVATION", "from": first["from"], "to": first["to"]}
    )
    module.validate_owner_lego_graph(plan)


@pytest.mark.parametrize(
    "relative",
    [*OWNER_GRAPH_PLANS, "platform/security/planning/lego-plan-r1.json"],
)
def test_registered_owner_relations_reject_unrecognised_typed_edges(relative: str) -> None:
    """A mistyped DEPENDENCY must not silently become an unvalidated edge kind."""
    plan = json.loads((ROOT / relative).read_text(encoding="utf-8"))
    plan["edges"][0]["type"] = "DEPENDENCIES"
    with pytest.raises(module.ArchitectureDocsError, match="unknown LEGO edge type"):
        module.validate_owner_lego_graph(plan)
    with pytest.raises(module.ArchitectureDocsError, match="unknown LEGO edge type"):
        module.validate_owner_lego_dependencies(plan, relative)


def test_security_owner_direct_dependency_entry_checks_all_non_dependency_edges() -> None:
    plan = json.loads(
        (ROOT / "platform/security/planning/lego-plan-r1.json").read_text(encoding="utf-8")
    )
    module.validate_owner_lego_graph(plan)
    module.validate_owner_lego_dependencies(plan, "platform/security")
    plan["edges"][0]["to"] = "MISSING_SECURITY_NODE"
    with pytest.raises(module.ArchitectureDocsError, match="unknown LEGO edge endpoint"):
        module.validate_owner_lego_dependencies(plan, "platform/security")
