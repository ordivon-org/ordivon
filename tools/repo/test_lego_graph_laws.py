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



def test_repo_source_territory_is_real_semantic_lego_not_the_entire_file_census() -> None:
    # One independently callable and version-bound responsibility: exact-cut
    # classification. Its 325 source members do NOT become 325 LEGO nodes.
    path = "tools/repo/planning/lego-plan-r1.json"
    plan = json.loads((ROOT / path).read_text(encoding="utf-8"))
    module.validate_owner_lego_graph(plan)
    module.validate_owner_lego_dependencies(plan, "tools/repo")
    nodes = {node["id"]: node for node in plan["nodes"]}
    region = nodes["RG3_REGION"]
    assert region["kind"] == "repository_source_classification"
    for field in ("responsibility", "inputs", "outputs", "behavioralContract",
                  "acceptance", "evidence", "consumerEvidence", "mustNotOwn"):
        assert region[field], field
    assert region["formalStanding"].endswith("IMPLEMENTATION_REFINEMENT_UNKNOWN")
    assert {(edge["from"], edge["to"], edge["type"])
            for edge in plan["edges"]} == {
                ("RG2_OWNER", "RG3_REGION", "DEPENDENCY"),
            }
    assert any(slice_["nodeIds"] == ["RG3_REGION"] for slice_ in plan["slices"])
    for source in region["evidence"]:
        assert (ROOT / "tools/repo" / source).is_file()
    graph = module.project_owner_lego_source_graph(ROOT)
    vertex = next(row for row in graph["vertices"]
                  if row["ref"] == f"{path}#RG3_REGION")
    assert vertex["sourceAnchors"]
    assert not vertex["unresolvedSourceEvidence"]
    assert "ACTUAL_CONSUMER" in graph["excluded"]["unverifiedFacets"]
    assert "FORMAL_PROOF" in graph["excluded"]["unverifiedFacets"]



def test_host_legacy_agent_service_cursor_proposal_is_retired() -> None:
    """An old proposed LEGO is not an owner merely because its R1 row survived."""
    legacy = json.loads((ROOT / OWNER_GRAPH_PLANS[1]).read_text(encoding="utf-8"))
    current = json.loads(
        (ROOT / "services/host/planning/lego-plan-r3.json").read_text(encoding="utf-8")
    )
    # No real caller imports cursor.py; its R3 retained row was a ghost consumer.
    assert all(row["id"] != "U01" for row in current["retained"])
    assert "ScopeBoundCursor" in current["retired"]
    assert not (ROOT / "services/host/src/ordivon_host_v2/cursor.py").exists()
    assert all(node["id"] != "O05" for node in legacy["nodes"])
    assert all(slice_["id"] != "OS1" for slice_ in legacy["slices"])
    assert all("ScopeBoundCursor" not in gap for gap in legacy["gaps"])


def test_network_unconsumed_future_profile_slice_is_retired_without_removing_active_nodes() -> None:
    # NS1 is an unregistered prospective duplicate of N05's implemented
    # optional-profile contract. NS2, unlike NS1, has a live issue consumer.
    plan = json.loads(
        (ROOT / "platform/network/planning/lego-plan-r1.json").read_text(encoding="utf-8")
    )
    assert {item["id"] for item in plan["slices"]} == {"NS2"}
    assert {"N01", "N05"} <= {item["id"] for item in plan["nodes"]}
    profile = next(item for item in plan["nodes"] if item["id"] == "N05")
    assert "Adding a profile does not redefine generic Network acceptance." in profile["acceptance"]
    module.validate_owner_lego_graph(plan)



def test_network_recursive_consumer_contracts_remain_source_bound_not_installed_truth() -> None:
    # Three independent consumer-facing seams discovered inside the historical
    # N02 data-plane / N05 profile coarse nodes. A source witness is not live truth.
    relative = "platform/network/planning/lego-plan-r1.json"
    plan = json.loads((ROOT / relative).read_text(encoding="utf-8"))
    nodes = {row["id"]: row for row in plan["nodes"]}
    assert nodes["N02"]["behavioralContract"]
    expected = {
        "N06": ("N02", "COMPOSITION", "consumers/x-reality/config/egress.json"),
        "N07": ("N05", "SPECIALIZATION", "consumers/developer-egress/profile.sh"),
        "N08": ("N02", "OBSERVATION", "consumers/supply-chain/ready.sh"),
    }
    for identity, (parent, relation, real_source) in expected.items():
        node = nodes[identity]
        for field in ("responsibility", "inputs", "outputs", "behavioralContract",
                      "acceptance", "consumerEvidence"):
            assert node[field], (identity, field)
        assert real_source in node["evidence"]
        assert (ROOT / "platform/network" / real_source).is_file()
        assert any(edge["from"] == parent and edge["to"] == identity and
                   edge["type"] == relation for edge in plan["edges"])
    view = module.project_owner_lego_source_graph(ROOT)
    for identity in expected:
        ref = f"{relative}#{identity}"
        vertex = next(item for item in view["vertices"] if item["ref"] == ref)
        assert vertex["sourceAnchors"]
        assert vertex["sourceCoverageStanding"] == "DECLARED_SOURCE_MEMBERSHIP_PARTIAL"
        assert not vertex["unresolvedSourceEvidence"]
    assert "ACTUAL_CONSUMER" in view["excluded"]["unverifiedFacets"]



def test_gateway_recursive_source_contracts_are_non_authoritative_and_consumer_bound() -> None:
    """The Gateway's generic R1 has distinct owner routing, observations and effects.

    The Windows GW* R2 carrier is a deployment profile, not another source
    identity for G00-G09. These source anchors do not assert live effects.
    """
    relative = "services/gateway/planning/lego-plan-r1.json"
    plan = json.loads((ROOT / relative).read_text(encoding="utf-8"))
    module.validate_owner_lego_graph(plan)
    module.validate_owner_lego_dependencies(plan, "services/gateway")
    identities = {item["id"] for item in plan["nodes"]}
    assert identities == {"G00", "G01", "G02", "G03", "G04", "G05", "G06", "G07", "G08", "G09"}
    assert plan["truthRole"] == "planning-projection-not-project-truth"
    checks = {
        "G01": ("routes.py", "test_gateway_service.py"),
        "G02": ("service.py", "test_capability_projection.py"),
        "G03": ("service.py", "test_gateway_service.py"),
        "G04": ("service.py", "test_gateway_service.py"),
        "G05": ("service.py", "test_gateway_service.py"),
        "G06": ("capability_authz.py", "test_capability_authz_middleware.py"),
        "G07": ("access_auth.py", "test_access_auth.py"),
        "G08": ("research_routes.py", "test_research_capability_resolution.py"),
        "G09": ("external_worker.py", "test_external_pull_worker.py"),
    }
    for node in plan["nodes"]:
        assert all(node.get(field) for field in (
            "responsibility", "inputs", "outputs", "behavioralContract", "acceptance",
        ))
        assert node["consumerEvidence"]
    for identity, (source_basename, test_basename) in checks.items():
        node = next(item for item in plan["nodes"] if item["id"] == identity)
        assert any(path.endswith(source_basename) for path in node["evidence"])
        assert any(path.endswith(test_basename) for path in node["evidence"])
        assert any(e["from"] == "G00" and e["to"] == identity and e["type"] == "COMPOSITION"
                   for e in plan["edges"])
    view = module.project_owner_lego_source_graph(ROOT)
    for identity in identities:
        vertex = next(v for v in view["vertices"] if v["ref"] == f"{relative}#{identity}")
        assert vertex["sourceAnchors"] and not vertex["unresolvedSourceEvidence"]
        assert vertex["sourceCoverageStanding"] == "DECLARED_SOURCE_MEMBERSHIP_PARTIAL"
    assert "ACTUAL_CONSUMER" in view["excluded"]["unverifiedFacets"]
    assert "FORMAL_PROOF" in view["excluded"]["unverifiedFacets"]
    broken = copy.deepcopy(plan)
    broken["edges"].append({"from": "G06", "to": "MISSING_PROVIDER", "type": "CONTROL"})
    with pytest.raises(module.ArchitectureDocsError, match="unknown LEGO edge endpoint"):
        module.validate_owner_lego_graph(broken)



def test_preservation_recursive_profile_bindings_are_source_only_and_fail_closed() -> None:
    """Qualified local source, storage route and fixity schedule are not AIP truth."""
    relative = "capabilities/preservation/planning/lego-plan-r1.json"
    document = json.loads((ROOT / relative).read_text(encoding="utf-8"))
    module.validate_owner_lego_graph(document)
    module.validate_owner_lego_dependencies(document, "capabilities/preservation")
    assert {item["id"] for item in document["nodes"]} == {
        "PV00", "PV01", "PV02", "PV03",
    }
    for node in document["nodes"]:
        assert all(node[field] for field in (
            "responsibility", "inputs", "outputs", "behavioralContract", "acceptance",
            "evidence", "consumerEvidence",
        ))
        assert node["state"] == "SOURCE_QUALIFIED_NOT_INSTALLED"
    assert any(edge["from"] == "PV02" and edge["to"] == "PV03"
               and edge["type"] == "DEPENDENCY" for edge in document["edges"])
    boundary = json.loads((ROOT / "capabilities/preservation/SOURCE_BOUNDARY.json")
                          .read_text(encoding="utf-8"))
    assert "planning/lego-plan-r1.json" in boundary["includedPaths"]
    assert "planning/**" not in boundary["includedPaths"]
    graph = module.project_owner_lego_source_graph(ROOT)
    for identity in ("PV00", "PV01", "PV02", "PV03"):
        vertex = next(v for v in graph["vertices"] if v["ref"] == f"{relative}#{identity}")
        assert vertex["sourceAnchors"] and not vertex["unresolvedSourceEvidence"]
        assert vertex["sourceCoverageStanding"] == "DECLARED_SOURCE_MEMBERSHIP_PARTIAL"
    assert "ACTUAL_CONSUMER" in graph["excluded"]["unverifiedFacets"]
    wrong = copy.deepcopy(document)
    wrong["edges"].append({
        "from": "PV03", "to": "PV_NONEXISTENT", "type": "DEPENDENCY",
    })
    with pytest.raises(module.ArchitectureDocsError, match="unknown LEGO edge endpoint"):
        module.validate_owner_lego_graph(wrong)


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


@pytest.mark.parametrize(
    "relative", (*OWNER_GRAPH_PLANS, "platform/security/planning/lego-plan-r1.json")
)
@pytest.mark.parametrize("alias_form", ("zero_width_joiner", "fullwidth_first_letter"))
def test_owner_identity_cannot_be_forked_by_unicode_lookalikes(
    relative: str, alias_form: str
) -> None:
    """A visible LEGO identity must not silently mint a second opaque node."""
    plan = json.loads((ROOT / relative).read_text(encoding="utf-8"))
    ghost = copy.deepcopy(plan["nodes"][0])
    original = ghost["id"]
    ghost["id"] = (
        original[0] + "\u200d" + original[1:]
        if alias_form == "zero_width_joiner"
        else chr(ord(original[0]) + 0xFEE0) + original[1:]
    )
    plan["nodes"].append(ghost)
    with pytest.raises(module.ArchitectureDocsError, match="non-canonical LEGO node identity"):
        module.validate_owner_lego_graph(plan)
    # The direct dependency path must share the SAME identity equivalence.
    with pytest.raises(module.ArchitectureDocsError, match="non-canonical LEGO node identity"):
        module.validate_owner_lego_dependencies(plan, relative)


@pytest.mark.parametrize("alias_form", ("zero_width_joiner", "fullwidth_first_letter"))
def test_owner_slice_identity_cannot_use_unicode_lookalikes(alias_form: str) -> None:
    plan = json.loads((ROOT / OWNER_GRAPH_PLANS[0]).read_text(encoding="utf-8"))
    ghost = copy.deepcopy(plan["slices"][0])
    original = ghost["id"]
    ghost["id"] = (
        original[0] + "\u200d" + original[1:]
        if alias_form == "zero_width_joiner"
        else chr(ord(original[0]) + 0xFEE0) + original[1:]
    )
    plan["slices"].append(ghost)
    with pytest.raises(module.ArchitectureDocsError, match="non-canonical LEGO slice identity"):
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


@pytest.mark.parametrize(
    ("blockers", "status"),
    [
        (["RW1", "RW2"], "BLOCKED_ON_RW1_RW2"),
        (["MISSING_SLICE"], "BLOCKED_ON_MISSING_SLICE"),
        ([], "BLOCKED_ON_RW1"),
    ],
)
def test_blocked_slice_requires_unresolved_registered_prerequisite(
    blockers: list[str], status: str,
) -> None:
    """A supposedly blocked LEGO must have a real, unfinished dependency."""
    plan = json.loads((ROOT / OWNER_GRAPH_PLANS[0]).read_text(encoding="utf-8"))
    target = next(row for row in plan["slices"] if row["id"] == "RW4")
    target["blockers"] = blockers
    target["status"] = status
    with pytest.raises(module.ArchitectureDocsError, match="invalid LEGO blocking prerequisites"):
        module.validate_owner_lego_graph(plan)



@pytest.mark.parametrize("cycle", ("self", "mutual"))
def test_blocked_slice_dependency_cycle_is_rejected(cycle: str) -> None:
    """A valid-looking incomplete blocker cannot justify circular deadlock."""
    plan = json.loads((ROOT / OWNER_GRAPH_PLANS[0]).read_text(encoding="utf-8"))
    by_id = {item["id"]: item for item in plan["slices"]}
    if cycle == "self":
        by_id["RW4"]["status"] = "BLOCKED_ON_RW4"
        by_id["RW4"]["blockers"] = ["RW4"]
    else:
        by_id["RW5"]["status"] = "BLOCKED_ON_RW6"
        by_id["RW5"]["blockers"] = ["RW6"]
        by_id["RW6"]["status"] = "BLOCKED_ON_RW5"
        by_id["RW6"]["blockers"] = ["RW5"]
    with pytest.raises(module.ArchitectureDocsError, match="cyclic LEGO slice blockers"):
        module.validate_owner_lego_graph(plan)


def test_blocked_slice_rejects_partially_completed_prerequisite() -> None:
    """Every asserted BLOCKED_ON prerequisite must still be unresolved."""
    plan = json.loads((ROOT / OWNER_GRAPH_PLANS[0]).read_text(encoding="utf-8"))
    slices = {item["id"]: item for item in plan["slices"]}
    assert slices["RW2"]["status"] == "COMPLETE"
    assert slices["RW4"]["status"] != "COMPLETE"
    slices["RW5"]["blockers"] = ["RW2", "RW4"]
    slices["RW5"]["status"] = "BLOCKED_ON_RW2_RW4"
    with pytest.raises(module.ArchitectureDocsError, match="invalid LEGO blocking prerequisites"):
        module.validate_owner_lego_graph(plan)


def test_registered_runtime_blockers_contain_only_unresolved_prerequisites() -> None:
    """Do not keep a completed milestone masquerading as a present blocker."""
    plan = json.loads((ROOT / OWNER_GRAPH_PLANS[0]).read_text(encoding="utf-8"))
    status = {item["id"]: item["status"] for item in plan["slices"]}
    for item in plan["slices"]:
        if item["status"].startswith("BLOCKED_ON_"):
            assert item["blockers"]
            assert all(status[dep] != "COMPLETE" for dep in item["blockers"])
    module.validate_owner_lego_graph(plan)


@pytest.mark.parametrize("bad_version", [True, 1.0, "1", 2, None])
@pytest.mark.parametrize("relative", OWNER_GRAPH_PLANS)
def test_owner_lego_plan_requires_exact_schema_integer(
    relative: str, bad_version: object
) -> None:
    """A future or bool-coerced schema must not be admitted as R2.1."""
    plan = json.loads((ROOT / relative).read_text(encoding="utf-8"))
    plan["schemaVersion"] = bad_version
    with pytest.raises(module.ArchitectureDocsError, match="schemaVersion"):
        module.validate_owner_lego_graph(plan)


@pytest.mark.parametrize("bad_version", [True, 1.0, "1", 2, None])
def test_direct_owner_dependency_gate_requires_exact_schema_integer(
    bad_version: object,
) -> None:
    """Direct prerequisite consumers must not bypass the typed Owner version."""
    plan = json.loads((ROOT / OWNER_GRAPH_PLANS[0]).read_text(encoding="utf-8"))
    plan["schemaVersion"] = bad_version
    with pytest.raises(module.ArchitectureDocsError, match="schemaVersion"):
        module.validate_owner_lego_dependencies(plan, OWNER_GRAPH_PLANS[0])


@pytest.mark.parametrize(
    "relative",
    (OWNER_GRAPH_PLANS[0], OWNER_GRAPH_PLANS[2], OWNER_GRAPH_PLANS[3],
     "platform/security/planning/lego-plan-r1.json"),
)
@pytest.mark.parametrize("illegal_status", ["VERFIED", "BLOCKED", "COMPLTE", "", None, 123])
def test_all_owner_slices_reject_untyped_or_misspelled_state(
    relative: str, illegal_status: object
) -> None:
    """Even unregistered planning slices cannot invent a status and pass current admission."""
    plan = json.loads((ROOT / relative).read_text(encoding="utf-8"))
    plan["slices"][0]["status"] = illegal_status
    with pytest.raises(module.ArchitectureDocsError, match="invalid LEGO slice status"):
        module.validate_owner_lego_graph(plan)


@pytest.mark.parametrize("status", ["PROPOSED", "IN_PROGRESS", "IMPLEMENTED", "VERIFIED", "COMPLETE", "RETIRED"])
def test_owner_slice_known_lifecycle_states_remain_well_typed(status: str) -> None:
    plan = json.loads((ROOT / OWNER_GRAPH_PLANS[3]).read_text(encoding="utf-8"))
    plan["slices"][0]["status"] = status
    module.validate_owner_lego_graph(plan)


DOMAIN_GRAPH_PLANS = (
    "domains/game/planning/lego-plan-r1.json",
    "capabilities/media/planning/lego-plan-r1.json",
)


@pytest.mark.parametrize("relative", DOMAIN_GRAPH_PLANS)
def test_active_domain_owner_plans_are_covered_by_current_repository_graph_admission(
    relative: str,
) -> None:
    """Mature Owner Graph maths must guard Game/Media without domain-specific solvers."""
    assert relative in module.OWNER_LEGO_PLANS
    plan = json.loads((ROOT / relative).read_text(encoding="utf-8"))
    module.validate_owner_lego_graph(plan)
    module.validate_owner_lego_dependencies(plan, relative.split("/planning/", 1)[0])


@pytest.mark.parametrize("relative", DOMAIN_GRAPH_PLANS)
def test_active_domain_owner_illegal_status_cannot_masquerade_as_an_admitted_slice(
    relative: str,
) -> None:
    plan = json.loads((ROOT / relative).read_text(encoding="utf-8"))
    plan["slices"][0]["status"] = "VERFIED"
    with pytest.raises(module.ArchitectureDocsError, match="invalid LEGO slice status"):
        module.validate_owner_lego_graph(plan)


@pytest.mark.parametrize("relative", DOMAIN_GRAPH_PLANS)
def test_active_domain_owner_dangling_dependency_fails_current_admission(
    relative: str,
) -> None:
    plan = json.loads((ROOT / relative).read_text(encoding="utf-8"))
    node = plan["nodes"][0]
    node["dependencies"].append("__NO_ACTUAL_PRODUCER__")
    with pytest.raises(module.ArchitectureDocsError, match="unknown LEGO dependency"):
        module.validate_owner_lego_dependencies(plan, relative.split("/planning/", 1)[0])


@pytest.mark.parametrize(
    "relative",
    (
        "services/runtime/planning/lego-plan-r1.json",
        "services/harness/planning/lego-plan-r1.json",
        "domains/game/planning/lego-plan-r1.json",
        "capabilities/media/planning/lego-plan-r1.json",
    ),
)
def test_repository_owner_graph_source_bound_before_loading(
    relative: str,
) -> None:
    """An Owner plan must not bypass the same existing SourceCut guard as its census."""
    from unittest.mock import patch

    original = module._source_bound_file

    def reject_forged_owner_plan(root: Path, path: str, label: str) -> Path:
        if path == relative:
            raise module.ArchitectureDocsError(
                f"registered Owner LEGO plan escapes SourceCut: {relative}"
            )
        return original(root, path, label)

    with (
        patch.object(module, "_source_bound_file", side_effect=reject_forged_owner_plan),
        pytest.raises(
            module.ArchitectureDocsError, match="registered Owner LEGO plan escapes SourceCut"
        ),
    ):
        module.validate_repository(ROOT)


def test_repo_mechanics_owner_plan_is_always_structurally_admitted() -> None:
    """A Repo Owner projection cannot omit typed node kind even with valid census links."""
    from unittest.mock import patch

    relative = "tools/repo/planning/lego-plan-r1.json"
    plan = json.loads((ROOT / relative).read_text(encoding="utf-8"))
    plan["nodes"][0]["kind"] = ""
    loader = module._load_json

    def tamper_registered_plan(path: Path):
        if Path(path) == ROOT / relative:
            return plan
        return loader(path)

    with (
        patch.object(module, "_load_json", side_effect=tamper_registered_plan),
        pytest.raises(module.ArchitectureDocsError, match="requires a type"),
    ):
        module.validate_repository(ROOT)

def test_current_owner_plan_inventory_is_closed_without_another_registry(
    tmp_path: Path,
) -> None:
    """New plan declarations cannot silently evade registered Owner graph laws."""
    for relative in (*module.OWNER_LEGO_PLANS, *module.OWNER_LEGO_PLAN_PROJECTIONS):
        candidate = tmp_path / relative
        candidate.parent.mkdir(parents=True, exist_ok=True)
        candidate.write_text("{}")
    module.validate_owner_plan_inventory(tmp_path)

    forged = tmp_path / "domains/new-unregistered-owner/planning/lego-plan-r1.json"
    forged.parent.mkdir(parents=True)
    forged.write_text("{}")
    with pytest.raises(module.ArchitectureDocsError, match="unregistered="):
        module.validate_owner_plan_inventory(tmp_path)
    forged.unlink()

    missing = tmp_path / module.OWNER_LEGO_PLANS[0]
    missing.unlink()
    with pytest.raises(module.ArchitectureDocsError, match="missing="):
        module.validate_owner_plan_inventory(tmp_path)


def test_owner_r2_r3_plan_carriers_are_not_invisible_to_inventory(tmp_path: Path) -> None:
    """A newly authored R2/R3 source carrier cannot bypass R1-only glob checks."""
    for relative in module.OWNER_LEGO_PLANS:
        candidate = tmp_path / relative
        candidate.parent.mkdir(parents=True, exist_ok=True)
        candidate.write_text("{}", encoding="utf-8")
    for relative in getattr(module, "OWNER_LEGO_PLAN_PROJECTIONS", ()):
        candidate = tmp_path / relative
        candidate.parent.mkdir(parents=True, exist_ok=True)
        candidate.write_text("{}", encoding="utf-8")

    undeclared = tmp_path / "domains/research/planning/lego-plan-r2.json"
    undeclared.parent.mkdir(parents=True)
    undeclared.write_text("{}", encoding="utf-8")
    with pytest.raises(module.ArchitectureDocsError, match="unregistered="):
        module.validate_owner_plan_inventory(tmp_path)
    undeclared.unlink()

    # Once a source carrier is registered, its silent deletion must also fail.
    for relative in module.OWNER_LEGO_PLAN_PROJECTIONS:
        missing = tmp_path / relative
        missing.unlink()
        with pytest.raises(module.ArchitectureDocsError, match="missing="):
            module.validate_owner_plan_inventory(tmp_path)
        missing.write_text("{}", encoding="utf-8")


@pytest.mark.parametrize(
    ("carrier", "field", "bad", "message"),
    [
        ("capabilities/artifact/planning/lego-plan-r2.json", "schemaVersion", True, "schemaVersion drift"),
        ("services/host/planning/lego-plan-r3.json", "schemaVersion", 2, "schemaVersion drift"),
        ("services/gateway/planning/lego-plan-windows-carrier-r2.json", "schemaVersion", 2, "schemaVersion drift"),
        ("capabilities/artifact/planning/lego-plan-r2.json", "kind", "other-kind", "kind drift"),
        ("services/host/planning/lego-plan-r3.json", "truthRole", "", "truthRole missing"),
        ("services/gateway/planning/lego-plan-windows-carrier-r2.json", "project", {}, "identity missing"),
    ],
)
def test_non_r1_owner_carriers_have_typed_source_envelopes(
    tmp_path: Path, carrier: str, field: str, bad: object, message: str
) -> None:
    # Reuse the actual owner projections rather than inventing a third
    # universal LEGO document schema for heterogeneous native versions.
    for relative in module.OWNER_LEGO_PLAN_PROJECTIONS:
        candidate = tmp_path / relative
        candidate.parent.mkdir(parents=True, exist_ok=True)
        candidate.write_bytes((ROOT / relative).read_bytes())
    module.validate_owner_plan_projection_carriers(tmp_path)
    target = tmp_path / carrier
    content = json.loads(target.read_text(encoding="utf-8"))
    content[field] = bad
    target.write_text(json.dumps(content), encoding="utf-8")
    with pytest.raises(module.ArchitectureDocsError, match=message):
        module.validate_owner_plan_projection_carriers(tmp_path)


def test_actual_repository_owner_plan_inventory_is_source_closed() -> None:
    module.validate_owner_plan_inventory(ROOT)


@pytest.mark.parametrize(
    "relative",
    (
        "services/runtime/planning/lego-plan-r1.json",
        "platform/security/planning/lego-plan-r1.json",
        "domains/game/planning/lego-plan-r1.json",
        "capabilities/media/planning/lego-plan-r1.json",
        "tools/repo/planning/lego-plan-r1.json",
    ),
)
def test_retired_slice_cannot_qualify_an_active_blocking_prerequisite(
    relative: str,
) -> None:
    """A retired producer is not a live unmet prerequisite for an active slice."""
    plan = json.loads((ROOT / relative).read_text(encoding="utf-8"))
    producer, consumer = plan["slices"][:2]
    producer["status"] = "RETIRED"
    consumer["blockers"] = [producer["id"]]
    consumer["status"] = f"BLOCKED_ON_{producer['id']}"
    with pytest.raises(module.ArchitectureDocsError, match="invalid LEGO blocking prerequisites"):
        module.validate_owner_lego_graph(plan)



@pytest.mark.parametrize("relative", module.OWNER_LEGO_PLANS)
def test_owner_project_source_evidence_is_current_source_bound(relative: str) -> None:
    plan = json.loads((ROOT / relative).read_text(encoding="utf-8"))
    module.validate_owner_lego_source_evidence(ROOT, relative, plan)


@pytest.mark.parametrize("relative", module.OWNER_LEGO_PLANS)
def test_owner_project_source_evidence_rejects_retired_paths(relative: str) -> None:
    plan = json.loads((ROOT / relative).read_text(encoding="utf-8"))
    plan["project"]["sourceEvidence"][0] = "docs/RETIRED_NONEXISTENT_LEGO_PROOF.md"
    with pytest.raises(module.ArchitectureDocsError, match="Owner LEGO sourceEvidence escapes SourceCut"):
        module.validate_owner_lego_source_evidence(ROOT, relative, plan)


def test_owner_project_source_evidence_rejects_traversal_and_duplicate_carriers() -> None:
    relative = "services/runtime/planning/lego-plan-r1.json"
    plan = json.loads((ROOT / relative).read_text(encoding="utf-8"))
    plan["project"]["sourceEvidence"][0] = "../../../../README.md"
    with pytest.raises(module.ArchitectureDocsError, match="invalid Owner LEGO sourceEvidence path"):
        module.validate_owner_lego_source_evidence(ROOT, relative, plan)
    plan["project"]["sourceEvidence"] = ["README.md", "README.md"]
    with pytest.raises(module.ArchitectureDocsError, match="invalid or duplicate Owner LEGO sourceEvidence"):
        module.validate_owner_lego_source_evidence(ROOT, relative, plan)


@pytest.mark.parametrize(
    "alias",
    (
        "services/host/README.md",
        "./README.md",
        "docs//HOST_V2_R6_CLEANUP.md",
    ),
)
def test_owner_evidence_alias_cannot_mint_duplicate_provenance(alias: str) -> None:
    """One SourceCut file must not become independent proofs via spelling aliases."""
    relative = "services/host/planning/lego-plan-r1.json"
    plan = json.loads((ROOT / relative).read_text(encoding="utf-8"))
    plan["project"]["sourceEvidence"].append(alias)
    with pytest.raises(module.ArchitectureDocsError, match="non-canonical|duplicate"):
        module.validate_owner_lego_source_evidence(ROOT, relative, plan)


def test_owner_evidence_rejects_mixed_absolute_and_relative_representations() -> None:
    relative = "services/host/planning/lego-plan-r1.json"
    plan = json.loads((ROOT / relative).read_text(encoding="utf-8"))
    plan["project"]["sourceEvidence"] = ["README.md", "services/host/README.md"]
    with pytest.raises(module.ArchitectureDocsError, match="duplicate"):
        module.validate_owner_lego_source_evidence(ROOT, relative, plan)

def test_native_owner_source_projection_is_scoped_and_deterministic() -> None:
    first = module.project_owner_lego_source_graph(ROOT)
    assert first == module.project_owner_lego_source_graph(ROOT)
    assert first["truthRole"] == "DERIVED_READ_ONLY_SOURCE_PLANNING_NOT_LEGO_TRUTH"
    assert "ACTUAL_CONSUMER" in first["excluded"]["unverifiedFacets"]
    assert "CROSS_OWNER_RELATION_CLOSURE" in first["excluded"]["unverifiedFacets"]
    assert all(row["sha256"].startswith("sha256:") for row in first["sourcePlans"])
    names = {row["ref"] for row in first["vertices"]}
    assert all(row["from"] in names and row["to"] in names for row in first["relations"])
    assert len(names) == len(first["vertices"])
    assert any("NODE_DEPENDENCIES" in row["declaredBy"] for row in first["relations"])
    assert all("#" in row["ref"] for row in first["vertices"])
    # The CLI is the existing checker; no persistent graph DB or second registry.
    assert module.main(["--project-owner-graphs"]) == 0


def test_native_git_sourcecut_graph_ignores_mutable_worktree_plan(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Git source identity must bind projected node bytes, not only plan hashes."""
    import subprocess

    sha = subprocess.check_output(["git", "-C", str(ROOT), "rev-parse", "HEAD"], text=True).strip()
    baseline = module.project_owner_lego_source_graph(ROOT, source_revision=sha)
    assert baseline["sourceCut"] == sha
    original = module._load_json
    chosen = module.OWNER_LEGO_PLANS[0]

    def mutable_substitution(path: Path, *, source_bytes=None):
        result = original(path) if source_bytes is None else original(path, source_bytes=source_bytes)
        if path.relative_to(ROOT).as_posix() == chosen and source_bytes is None:
            result["nodes"][0]["id"] = "forged worktree identity"
        return result

    monkeypatch.setattr(module, "_load_json", mutable_substitution)
    assert module.project_owner_lego_source_graph(ROOT, source_revision=sha) == baseline



def test_immutable_owner_plan_projection_ignores_local_git_blob_replace(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
) -> None:
    """Git replace must not rewrite claims for the same exact commit SHA."""
    import subprocess

    def git(*args: str, input_bytes: bytes | None = None) -> str:
        result = subprocess.check_output(
            ["git", "-c", "maintenance.auto=false", "-C", str(tmp_path), *args],
            input=input_bytes, stderr=subprocess.PIPE,
        )
        return result.decode("ascii").strip()

    git("init", "-q", "-b", "main")
    git("config", "user.name", "SourceCut Falsifier")
    git("config", "user.email", "sourcecut@local.invalid")
    owner_plan = "services/runtime/planning/lego-plan-r1.json"
    original = (ROOT / owner_plan).read_bytes()
    plan = json.loads(original)
    for name in [owner_plan, *plan["project"]["sourceEvidence"]]:
        path = tmp_path / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes((ROOT / name).read_bytes())
    # Include the immutable registration SourceCut in the synthetic repo:
    # historical graph queries must not borrow the current process's plan list.
    registry = tmp_path / "tools/repo/check_architecture_docs.py"
    registry.parent.mkdir(parents=True, exist_ok=True)
    registry.write_text(f"OWNER_LEGO_PLANS = ({owner_plan!r},)\n")
    git("add", ".")
    git("commit", "-qm", "immutable owner-plan source cut")
    source_cut = git("rev-parse", "HEAD")
    monkeypatch.setattr(module, "OWNER_LEGO_PLANS", (owner_plan,))
    expected = module.project_owner_lego_source_graph(tmp_path, source_revision=source_cut)
    old_blob = git("rev-parse", source_cut + ":" + owner_plan)
    other = json.loads(original)
    other["nodes"][0]["kind"] = "REPLACEMENT_NOT_PART_OF_GIT_COMMIT"
    replacement_blob = git(
        "hash-object", "-w", "--stdin", input_bytes=json.dumps(other).encode()
    )
    git("replace", old_blob, replacement_blob)
    assert git("cat-file", "blob", old_blob) != original.decode()
    actual = module.project_owner_lego_source_graph(tmp_path, source_revision=source_cut)
    assert actual == expected

    # Registration is source-qualified: after a registered plan disappears,
    # its absence must fail closed rather than being treated as an empty owner.
    git("replace", "-d", old_blob)
    git("rm", owner_plan)
    git("commit", "-qm", "registered LEGO plan absent")
    missing_cut = git("rev-parse", "HEAD")
    with pytest.raises(module.ArchitectureDocsError, match="Owner plan absent/nonregular"):
        module.project_owner_lego_source_graph(tmp_path, source_revision=missing_cut)


def test_git_sourcecut_evidence_carriers_match_exact_git_tree(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import subprocess

    from tools.repo.source_history_legos import current_tree

    sha = subprocess.check_output(["git", "-C", str(ROOT), "rev-parse", "HEAD"], text=True).strip()
    identity = current_tree(ROOT, sha)
    projection = module.project_owner_lego_source_graph(ROOT, source_revision=sha)
    carriers = projection["sourceEvidenceCarriers"]
    assert carriers
    assert all(item["gitBlobIdentity"] == identity[item["path"]] for item in carriers)
    assert len({item["path"] for item in carriers}) == len(carriers)
    assert "INSTALLED" in projection["excluded"]["unverifiedFacets"]

    # The Git-only mode must remain reconstructable even when the current
    # worktree is unavailable/untrusted. Do not infer installed source bytes.
    def refuse_worktree(*_args, **_kwargs):
        raise AssertionError("immutable Git projection attempted worktree read")
    monkeypatch.setattr(module, "_source_bound_file", refuse_worktree)
    assert module.project_owner_lego_source_graph(ROOT, source_revision=sha) == projection


def test_git_sourcecut_rejects_unqualified_revision_and_symlink_carrier(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import subprocess

    from tools.repo import source_history_legos

    sha = subprocess.check_output(["git", "-C", str(ROOT), "rev-parse", "HEAD"], text=True).strip()
    with pytest.raises(module.ArchitectureDocsError, match="exact 40-hex"):
        module.project_owner_lego_source_graph(ROOT, source_revision="HEAD")
    with pytest.raises(module.ArchitectureDocsError, match="cannot resolve exact Git"):
        module.project_owner_lego_source_graph(ROOT, source_revision="0" * 40)

    original = source_history_legos.current_tree
    plan_path = module.OWNER_LEGO_PLANS[0]
    def fake_tree(repo: Path, revision: str):
        result = original(repo, revision)
        result[plan_path] = "120000:blob:" + "0" * 40
        return result
    monkeypatch.setattr(source_history_legos, "current_tree", fake_tree)
    with pytest.raises(module.ArchitectureDocsError, match="absent/nonregular"):
        module.project_owner_lego_source_graph(ROOT, source_revision=sha)


def test_native_owner_source_projection_qualifies_local_ids() -> None:
    projection = module.project_owner_lego_source_graph(ROOT)
    owners = {ref.split("#", 1)[0] for ref in (row["ref"] for row in projection["vertices"])}
    assert set(module.OWNER_LEGO_PLANS) == owners
    for edge in projection["relations"]:
        # R1 edges are Owner-local declarations, not invented cross-owner consumers.
        assert edge["from"].split("#", 1)[0] == edge["to"].split("#", 1)[0]


def test_native_owner_source_projection_rejects_unvalidated_node_source(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    original = module._load_json
    owner = module.OWNER_LEGO_PLANS[0]

    def corrupted(path: Path, *, source_bytes: bytes | None = None) -> dict:
        result = original(path, source_bytes=source_bytes)
        if path.relative_to(ROOT).as_posix() == owner:
            result["nodes"][0]["id"] = "invalid identity"
        return result

    monkeypatch.setattr(module, "_load_json", corrupted)
    with pytest.raises(module.ArchitectureDocsError, match="non-canonical LEGO node"):
        module.project_owner_lego_source_graph(ROOT)


def test_source_snapshot_strict_parser_preserves_captured_bytes_and_guards(tmp_path: Path) -> None:
    """Exact projection bytes must be parsed by the existing strict Owner parser."""
    source = tmp_path / "owner.json"
    source.write_bytes(b'{"value":"B-after-capture"}')
    # The file can change after capture: do not parse it a second time.
    assert module._load_json(source, source_bytes=b'{"value":"A-at-capture"}') == {
        "value": "A-at-capture"
    }
    # Avoid trading ABA consistency for an unsafe default JSON decoder.
    with pytest.raises(module.ArchitectureDocsError, match="duplicate JSON object key"):
        module._load_json(source, source_bytes=b'{"value":1,"value":2}')
    with pytest.raises(module.ArchitectureDocsError, match="non-finite JSON constant"):
        module._load_json(source, source_bytes=b'{"value":NaN}')
    with pytest.raises(module.ArchitectureDocsError, match="unrepresentable JSON number"):
        module._load_json(source, source_bytes=b'{"value":1e999}')


def test_projection_passes_exact_captured_bytes_into_strict_parser(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The hash input and validator's decoded bytes are identical."""
    original = module._load_json
    seen: list[bytes] = []

    def strict_decode(path: Path, *, source_bytes: bytes | None = None) -> dict:
        if path.relative_to(ROOT).as_posix() in module.OWNER_LEGO_PLANS:
            assert source_bytes is not None
            seen.append(source_bytes)
        return original(path, source_bytes=source_bytes)

    monkeypatch.setattr(module, "_load_json", strict_decode)
    graph = module.project_owner_lego_source_graph(ROOT)
    assert len(seen) == len(module.OWNER_LEGO_PLANS)
    import hashlib
    assert [x["sha256"] for x in graph["sourcePlans"]] == [
        "sha256:" + hashlib.sha256(x).hexdigest() for x in seen
    ]

def test_node_source_anchors_are_exact_immutable_git_membership_not_consumer_proof() -> None:
    import subprocess

    from tools.repo.source_history_legos import current_tree

    sha = subprocess.check_output(["git", "-C", str(ROOT), "rev-parse", "HEAD"], text=True).strip()
    tree = current_tree(ROOT, sha)
    projection = module.project_owner_lego_source_graph(ROOT, source_revision=sha)
    rels = projection["nodeSourceRelations"]
    assert rels and len(rels) >= 150  # bounded existing Owner plan evidence
    nodes = {vertex["ref"]: vertex for vertex in projection["vertices"]}
    assert all(
        relation["sourceIdentity"] == tree[relation["toSourcePath"]]
        and relation["qualification"] == "GIT_BLOB_MEMBERSHIP_ONLY"
        and relation["type"] == "EVIDENCE"
        and relation["from"] in nodes
        for relation in rels
    )
    assert len({(e["from"], e["toSourcePath"]) for e in rels}) == len(rels)
    assert set(module.OWNER_LEGO_PLANS) == {
        row["from"].split("#")[0] for row in rels
    }
    assert any(
        a.get("declaredSymbolUnverified", "").startswith("test_")
        for node in nodes.values() for a in node["sourceAnchors"]
    )
    assert all(
        row["sourceCoverageStanding"] == "DECLARED_SOURCE_MEMBERSHIP_PARTIAL"
        for row in nodes.values()
    )
    assert any(
        len(row["declaredEvidence"]) > len(row["sourceAnchors"])
        for row in nodes.values()
    )
    assert "ACTUAL_CONSUMER" in projection["excluded"]["unverifiedFacets"]
    assert "FORMAL_PROOF" in projection["excluded"]["unverifiedFacets"]


def test_node_source_anchors_prefer_owner_context_over_root_alias() -> None:
    from tools.repo.check_architecture_docs import _node_declared_source_anchors

    owner = "services/host"
    graph = {
        "services/host/README.md": "100644:blob:" + "a" * 40,
        "README.md": "100644:blob:" + "b" * 40,
        "tools/repo/check_sql_dialects.py": "100644:blob:" + "c" * 40,
    }
    anchors, unresolved = _node_declared_source_anchors(
        ROOT, owner,
        ["README.md", "tools/repo/check_sql_dialects.py", "not/the/source.py"],
        git_tree=graph,
    )
    assert [x["path"] for x in anchors] == [
        "services/host/README.md", "tools/repo/check_sql_dialects.py"
    ]
    assert unresolved == ["not/the/source.py"]


def test_node_source_anchors_do_not_promote_untrusted_evidence_text_or_symbols() -> None:
    from tools.repo.check_architecture_docs import _node_declared_source_anchors
    expected = "100644:blob:" + "a" * 40
    anchors, unresolved = _node_declared_source_anchors(
        ROOT, "services/runtime",
        ["tests/proof.py::test_property", "tests/proof.py::fake extra",
         "../../private.env", "job-xyz passed", "unavailable.rs"],
        git_tree={"services/runtime/tests/proof.py": expected},
    )
    assert anchors == [{
        "path": "services/runtime/tests/proof.py",
        "sourceIdentity": expected,
        "qualification": "GIT_BLOB_MEMBERSHIP_ONLY",
        "declaredSymbolUnverified": "test_property",
    }]
    assert unresolved == ["unavailable.rs"]
    # No source-level presence is equivalent to a test execution or formal proof.


def test_node_anchor_git_sourcecut_ignores_modified_worktree_and_no_worktree_read(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import subprocess

    sha = subprocess.check_output(["git", "-C", str(ROOT), "rev-parse", "HEAD"], text=True).strip()
    immutable = module.project_owner_lego_source_graph(ROOT, source_revision=sha)

    def refuse_read(*_args, **_kwargs):
        raise AssertionError("read from worktree while projecting an immutable Git source")
    monkeypatch.setattr(module, "_source_bound_file", refuse_read)
    assert module.project_owner_lego_source_graph(ROOT, source_revision=sha) == immutable

def test_declared_graph_impact_refuses_sibling_and_reversed_git_source_cuts(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A sibling branch comparison cannot be a temporal proof-impact Delta."""
    import subprocess

    repo = tmp_path
    source = repo / "source.txt"
    source.write_text("base\n", encoding="utf-8")

    def git(*args: str) -> str:
        return subprocess.check_output(
            ["git", "-C", str(repo), *args], text=True,
        ).strip()

    def commit(message: str) -> str:
        git("add", ".")
        git("-c", "user.name=GraphProof", "-c",
            "user.email=test@example.invalid", "commit", "-qm", message)
        return git("rev-parse", "HEAD")

    git("init", "-q")
    base = commit("base")
    git("checkout", "-qb", "sibling-a")
    source.write_text("sibling a\n", encoding="utf-8")
    a = commit("sibling a")
    git("checkout", "-qb", "sibling-b", base)
    source.write_text("sibling b\n", encoding="utf-8")
    b = commit("sibling b")

    def no_projection(*_args, **_kwargs):
        raise AssertionError("projecting planning graph before temporal Git guard")
    monkeypatch.setattr(module, "project_owner_lego_source_graph", no_projection)
    for before, after in ((a, b), (b, a), (a, base), ("HEAD", b)):
        with pytest.raises(ValueError, match="sourceCut ancestry"):
            module.project_owner_lego_source_change(
                before_revision=before, after_revision=after, root=repo,
            )


def test_graph_source_delta_reads_literal_git_paths_not_replacement_tree(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A replace-ref must not hide changed paths in a planning proof delta."""
    import subprocess

    repo = tmp_path
    path = repo / "contract.txt"
    path.write_text("old", encoding="utf-8")

    def git(*args: str) -> str:
        return subprocess.check_output(
            ["git", "-C", str(repo), *args], text=True,
        ).strip()

    git("init", "-q")
    git("config", "user.name", "Proof")
    git("config", "user.email", "proof@example.invalid")
    git("add", ".")
    git("-c", "user.name=Proof", "-c", "user.email=proof@example.invalid",
        "commit", "-qm", "before")
    before = git("rev-parse", "HEAD")
    path.write_text("new", encoding="utf-8")
    git("add", ".")
    git("-c", "user.name=Proof", "-c", "user.email=proof@example.invalid",
        "commit", "-qm", "after")
    after = git("rev-parse", "HEAD")

    tree = git("rev-parse", after + "^{tree}")
    forged = subprocess.check_output(
        ["git", "-C", str(repo), "commit-tree", tree],
        input=b"same as after, different source object\n",
    ).decode("ascii").strip()
    git("replace", before, forged)
    assert git("diff", "--name-only", before, after) == ""
    assert git("--no-replace-objects", "diff", "--name-only", before, after) == "contract.txt"

    def bounded_graph(root: Path, *, source_revision: str):
        return {
            "kind": "ordivon.owner-lego-planning-source-projection",
            "sourceCut": source_revision,
            "sourcePlans": [], "vertices": [], "relations": [],
        }
    monkeypatch.setattr(module, "project_owner_lego_source_graph", bounded_graph)
    result = module.project_owner_lego_source_change(
        before_revision=before, after_revision=after, root=repo,
    )
    assert result["changedGitPaths"] == ["contract.txt"]
    assert result["unindexedChangedPaths"] == ["contract.txt"]
    assert result["proofReuseAdmissible"] is False




def test_plan_contract_only_change_rechecks_all_declared_lego(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A changed acceptance contract must not disappear from source impact.

    Existing vertex projection omits slices, acceptance and nextAction.
    If one Git plan changes only there, all of that plan's contracts require
    requalification even when no vertex or typed edge appears changed.
    """
    import hashlib
    import subprocess

    root = tmp_path
    plan_path = "tools/repo/planning/lego-plan-r1.json"
    target = root / plan_path
    target.parent.mkdir(parents=True)
    target.write_text('{"acceptance":"old"}\n', encoding="utf-8")

    def git(*args: str) -> str:
        return subprocess.check_output(
            ["git", "-C", str(root), *args], text=True,
        ).strip()

    git("init", "-q")
    git("add", ".")
    git("-c", "user.name=GraphTest", "-c",
        "user.email=test@example.invalid", "commit", "-qm", "before")
    before = git("rev-parse", "HEAD")
    target.write_text('{"acceptance":"stronger"}\n', encoding="utf-8")
    git("add", ".")
    git("-c", "user.name=GraphTest", "-c",
        "user.email=test@example.invalid", "commit", "-qm", "after")
    after = git("rev-parse", "HEAD")

    refs = [f"{plan_path}#{node}" for node in ("RG1_SOURCE", "RG2_OWNER")]
    def projected(_root: Path, *, source_revision: str) -> dict:
        assert _root == root
        plan_bytes = subprocess.check_output([
            "git", "--no-replace-objects", "-C", str(root), "show",
            f"{source_revision}:{plan_path}",
        ])
        return {
            "sourceCut": source_revision,
            "sourcePlans": [{"path": plan_path,
                             "sha256": "sha256:" + hashlib.sha256(plan_bytes).hexdigest()}],
            "vertices": [{"ref": ref, "declaredKind": "contract",
                           "declaredEvidence": [], "sourceAnchors": []}
                          for ref in refs],
            "relations": [],
        }

    monkeypatch.setattr(module, "project_owner_lego_source_graph", projected)
    delta = module.project_owner_lego_source_change(
        before_revision=before, after_revision=after, root=root,
    )
    assert delta["changedGitPaths"] == [plan_path]
    assert delta["sourcePlanChangedPaths"] == [plan_path]
    assert delta["directChangedRefs"] == refs
    assert {row["ref"]: row["sourceImpactStanding"]
            for row in delta["standingByDeclaredNode"]} == {
                ref: "RECHECK_REQUIRED" for ref in refs
            }
    assert delta["proofReuseAdmissible"] is False


def test_declared_source_delta_is_real_git_diff_with_dependency_closure(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    import subprocess

    from tools.repo.source_history_legos import current_tree

    repo = tmp_path
    code = repo / "services/runtime/docs/runtime.md"
    code.parent.mkdir(parents=True)
    code.write_text("original contract\n", encoding="utf-8")

    def git(*args: str) -> str:
        return subprocess.check_output(
            ["git", "-C", str(repo), *args], text=True
        ).strip()

    git("init", "-q")
    git("add", ".")
    git("-c", "user.name=GraphTest", "-c", "user.email=test@example.invalid",
        "commit", "-qm", "base")
    before = git("rev-parse", "HEAD")
    original = current_tree(repo, before)["services/runtime/docs/runtime.md"]
    code.write_text("revised contract\n", encoding="utf-8")
    git("add", ".")
    git("-c", "user.name=GraphTest", "-c", "user.email=test@example.invalid",
        "commit", "-qm", "changed")
    after = git("rev-parse", "HEAD")
    current = current_tree(repo, after)["services/runtime/docs/runtime.md"]
    assert original != current

    refs = [f"services/runtime/planning/lego-plan-r1.json#{i}" for i in ("R01", "R02", "R03", "R04")]
    def graph(sha: str):
        return {
            "kind": "ordivon.owner-lego-planning-source-projection",
            "sourceCut": sha,
            "sourcePlans": [{"path": "services/runtime/planning/lego-plan-r1.json",
                             "sha256": "sha256:" + "1" * 64}],
            "vertices": [
                {"ref": refs[0], "declaredKind": "capacity",
                 "declaredEvidence": ["docs/runtime.md"],
                 "sourceAnchors": [{"path": "services/runtime/docs/runtime.md",
                                    "sourceIdentity": original if sha == before else current,
                                    "qualification": "GIT_BLOB_MEMBERSHIP_ONLY"}]},
                {"ref": refs[1], "declaredKind": "consumer",
                 "declaredEvidence": [], "sourceAnchors": []},
                {"ref": refs[2], "declaredKind": "independent",
                 "declaredEvidence": [], "sourceAnchors": []},
                {"ref": refs[3], "declaredKind": "compatibilityPeer",
                 "declaredEvidence": [], "sourceAnchors": []},
            ],
            "relations": [
                {"from": refs[0], "type": "DEPENDENCY", "to": refs[1],
                 "declaredBy": ["NODE_DEPENDENCIES"]},
                {"from": refs[1], "type": "DATA", "to": refs[2],
                 "declaredBy": ["TYPED_EDGE"]},
                # Compatibility has no formally established source-influence
                # polarity. Source changes in target must conservatively
                # invalidate the candidate on the "from" end as UNKNOWN.
                {"from": refs[3], "type": "COMPATIBILITY", "to": refs[0],
                 "declaredBy": ["TYPED_EDGE"]},
            ],
        }
    monkeypatch.setattr(
        module, "project_owner_lego_source_graph",
        lambda _root, *, source_revision: graph(source_revision),
    )
    result = module.project_owner_lego_source_change(
        before_revision=before, after_revision=after, root=repo,
    )
    assert result["changedGitPaths"] == ["services/runtime/docs/runtime.md"]
    assert result["directChangedRefs"] == [refs[0]]
    assert result["unindexedChangedPaths"] == []
    assert {x["ref"]: x["sourceImpactStanding"] for x in result["standingByDeclaredNode"]} == {
        refs[0]: "RECHECK_REQUIRED",
        refs[1]: "RECHECK_REQUIRED",
        refs[2]: "UNKNOWN",
        refs[3]: "UNKNOWN",
    }
    assert result["potentialRelationInfluenceRefs"] == [refs[2], refs[3]]
    assert result["proofReuseAdmissible"] is False


def test_declared_graph_relation_deletion_invalidates_both_old_and_new_endpoints(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    import subprocess

    repo = tmp_path
    (repo / "plans").mkdir()
    record = repo / "plans/graph.json"
    record.write_text("old", encoding="utf-8")
    def git(*args: str) -> str:
        return subprocess.check_output(
            ["git", "-C", str(repo), *args], text=True,
        ).strip()
    git("init", "-q")
    git("add", ".")
    git("-c", "user.name=GraphTest", "-c", "user.email=test@example.invalid",
        "commit", "-qm", "base")
    before = git("rev-parse", "HEAD")
    record.write_text("new", encoding="utf-8")
    git("add", ".")
    git("-c", "user.name=GraphTest", "-c", "user.email=test@example.invalid",
        "commit", "-qm", "new")
    after = git("rev-parse", "HEAD")
    refs = ["services/runtime/planning/lego-plan-r1.json#" + name for name in ("A", "B", "C")]
    def graph(sha: str):
        return {
            "sourceCut": sha,
            "sourcePlans": [],
            "vertices": [
                {"ref": ref, "declaredKind": "source", "declaredEvidence": [],
                 "sourceAnchors": []}
                for ref in refs
            ],
            "relations": (
                [{"from": refs[0], "to": refs[1], "type": "DEPENDENCY",
                  "declaredBy": ["TYPED_EDGE"]}]
                if sha == before else []
            ),
        }
    monkeypatch.setattr(
        module, "project_owner_lego_source_graph",
        lambda _root, *, source_revision: graph(source_revision),
    )
    result = module.project_owner_lego_source_change(
        before_revision=before, after_revision=after, root=repo,
    )
    # Graph-only change: no source anchor can conceal a removed prerequisite.
    assert result["changedDeclaredRelationCount"] == 1
    assert refs[0] in result["directChangedRefs"] and refs[1] in result["directChangedRefs"]
    assert result["proofReuseAdmissible"] is False
    assert result["unindexedChangedPaths"] == ["plans/graph.json"]


def test_git_qualified_harness_h01_syntax_importers_are_real_source_edges(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import subprocess

    from tools.repo.source_history_legos import current_tree

    rev = subprocess.check_output(
        ["git", "-C", str(ROOT), "rev-parse", "HEAD"], text=True,
    ).strip()
    target = "services/harness/src/ordivon_harness/ordivon/events.py"
    result = module.project_node_python_import_syntax(
        source_revision=rev,
        node_ref="services/harness/planning/lego-plan-r1.json#H01",
        target_source=target,
    )
    assert result["targetGitBlobIdentity"] == current_tree(ROOT, rev)[target]
    assert result["targetPythonModule"] == "ordivon_harness.ordivon.events"
    imports = {row["sourcePath"]: row for row in result["candidateImporters"]}
    assert {
        "services/harness/src/ordivon_harness/ordivon/loop.py",
        "services/harness/src/ordivon_harness/domain_tools.py",
        "services/harness/src/ordivon_harness/independent_result.py",
        "services/harness/tests/test_trace_type_refinement.py",
    } <= set(imports)
    assert all(
        row["gitBlobIdentity"] == current_tree(ROOT, rev)[path]
        for path, row in imports.items()
    )
    trace = imports["services/harness/src/ordivon_harness/ordivon/loop.py"]
    assert {entry["name"] for entry in trace["importSyntax"]} == {
        "HarnessRunEvent", "HarnessTrace", "TraceRecorder",
    }
    assert all(
        entry["targetDefinitionStanding"] == "SOURCE_TOP_LEVEL_DEFINED"
        for entry in trace["importSyntax"]
    )
    assert "externalConsumersCovered" in result["scanBoundary"]
    assert result["scanBoundary"]["externalConsumersCovered"] is False
    assert "NOT_RUNTIME_CONSUMER_TRUTH" in result["truthRole"]

    # Immutable Git source qualification cannot be replaced with current
    # mutable checkout bytes or an attractive Agent-generated source snippet.
    def reject_worktree(*_args, **_kwargs):
        raise AssertionError("source importer scan attempted mutable worktree read")
    monkeypatch.setattr(module, "_source_bound_file", reject_worktree)
    assert module.project_node_python_import_syntax(
        source_revision=rev,
        node_ref=result["declaredNodeRef"],
        target_source=target,
    ) == result


def test_ast_imports_reject_comments_strings_dynamic_and_unresolved_symbols(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    import subprocess

    from tools.repo.source_history_legos import current_tree

    root = tmp_path
    source = root / "services/harness/src/pkg"
    source.mkdir(parents=True)
    (source / "target.py").write_text("class Real: pass\n", encoding="utf-8")
    (source / "consumer.py").write_text("from .target import Real\n", encoding="utf-8")
    (source / "__init__.py").write_text("from .target import Real\n", encoding="utf-8")
    (source / "dead.py").write_text("if False:\n    from .target import Real\n", encoding="utf-8")
    (source / "comment.py").write_text(
        "# from .target import Real\n"
        "comment = 'from .target import Real'\n",
        encoding="utf-8",
    )
    (source / "dynamic.py").write_text(
        "import importlib\nname='pkg.target'\nimportlib.import_module(name)\n",
        encoding="utf-8",
    )
    (source / "missing.py").write_text("from .target import NotDefined\n", encoding="utf-8")

    def git(*args: str) -> str:
        return subprocess.check_output(
            ["git", "-C", str(root), *args], text=True,
        ).strip()
    git("init", "-q")
    git("add", ".")
    git("-c", "user.name=GraphTest", "-c", "user.email=test@example.invalid",
        "commit", "-qm", "source")
    rev = git("rev-parse", "HEAD")
    target = "services/harness/src/pkg/target.py"
    plan_ref = "services/harness/planning/lego-plan-r1.json#H01"
    blob = current_tree(root, rev)[target]
    def fixture_graph(_root, *, source_revision):
        assert source_revision == rev
        return {
            "vertices": [
                {"ref": plan_ref, "sourceAnchors": [
                    {"path": target, "sourceIdentity": blob}
                ]}
            ],
        }
    monkeypatch.setattr(module, "project_owner_lego_source_graph", fixture_graph)
    result = module.project_node_python_import_syntax(
        source_revision=rev, node_ref=plan_ref, target_source=target, root=root,
    )
    got = {row["sourcePath"].rsplit("/", 1)[1]: row for row in result["candidateImporters"]}
    assert set(got) == {"__init__.py", "consumer.py", "dead.py", "missing.py"}
    assert got["consumer.py"]["importSyntax"][0]["targetDefinitionStanding"] == "SOURCE_TOP_LEVEL_DEFINED"
    assert got["missing.py"]["importSyntax"][0]["targetDefinitionStanding"] == "UNRESOLVED_OR_REEXPORTED"
    # Dead imports are still only *syntax*, never EXECUTED consumers.
    assert got["dead.py"]["qualification"] == "PYTHON_AST_IMPORT_SYNTAX_ONLY_NOT_EXECUTION"
    assert result["scanBoundary"]["dynamicImportsResolved"] is False
    with pytest.raises(module.ArchitectureDocsError, match="not node-anchored"):
        module.project_node_python_import_syntax(
            source_revision=rev, node_ref=plan_ref,
            target_source="services/harness/src/pkg/consumer.py", root=root,
        )


def test_exact_git_python_importer_evidence_ignores_mutable_git_replace(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The same immutable commit may not produce different consumer edges."""
    import subprocess
    from tools.repo.source_history_legos import current_tree

    root = tmp_path
    pkg = root / "services/harness/src/pkg"
    pkg.mkdir(parents=True)
    target = pkg / "target.py"
    importer = pkg / "consumer.py"
    target.write_text("class Real: pass\n", encoding="utf-8")
    importer.write_text("from .target import Real\n", encoding="utf-8")

    def git(*args: str, input_bytes: bytes | None = None) -> str:
        return subprocess.check_output(
            ["git", "-C", str(root), *args],
            input=input_bytes, stderr=subprocess.PIPE,
        ).decode("ascii").strip()

    git("init", "-q", "-b", "main")
    git("add", ".")
    git("-c", "user.name=GraphTest", "-c", "user.email=test@example.invalid",
        "commit", "-qm", "source consumer")
    cut = git("rev-parse", "HEAD")
    source_path = "services/harness/src/pkg/target.py"
    consumer_path = "services/harness/src/pkg/consumer.py"
    ref = "services/harness/planning/lego-plan-r1.json#H01"
    original_blob = current_tree(root, cut)[consumer_path].split(":")[-1]
    monkeypatch.setattr(
        module, "project_owner_lego_source_graph",
        lambda _root, *, source_revision: {"vertices": [{
            "ref": ref, "sourceAnchors": [{"path": source_path,
            "sourceIdentity": current_tree(root, source_revision)[source_path]}],
        }]},
    )
    initial = module.project_node_python_import_syntax(
        source_revision=cut, node_ref=ref, target_source=source_path, root=root,
    )
    assert [row["sourcePath"] for row in initial["candidateImporters"]] == [consumer_path]
    replacement = git("hash-object", "-w", "--stdin",
                      input_bytes=b"answer = 'not an importer'\n")
    git("replace", original_blob, replacement)
    # Show the negative control is real: ambient Git can see new bytes.
    assert git("cat-file", "blob", original_blob) != (
        "from .target import Real"
    )
    after = module.project_node_python_import_syntax(
        source_revision=cut, node_ref=ref, target_source=source_path, root=root,
    )
    assert after == initial


def test_python_import_delta_real_git_separates_source_and_relation_changes(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A consumer can change while its import edge remains byte-for-byte."""
    import subprocess
    from tools.repo.source_history_legos import current_tree

    root = tmp_path
    pkg = root / "services/harness/src/pkg"
    pkg.mkdir(parents=True)
    target = pkg / "target.py"
    consumer = pkg / "consumer.py"
    unrelated = pkg / "unrelated.py"
    target.write_text("class Real: pass\n", encoding="utf-8")
    consumer.write_text("from .target import Real\nanswer = 1\n", encoding="utf-8")
    unrelated.write_text("answer = 1\n", encoding="utf-8")

    def git(*args: str) -> str:
        return subprocess.check_output(
            ["git", "-C", str(root), *args], text=True,
        ).strip()
    git("init", "-q")
    def record(label: str) -> str:
        git("add", ".")
        git("-c", "user.name=GraphTest", "-c", "user.email=test@example.invalid",
            "commit", "-qm", label)
        return git("rev-parse", "HEAD")
    base = record("base")
    consumer.write_text("from .target import Real\nanswer = 2\n", encoding="utf-8")
    body_changed = record("consumer body changed")
    consumer.write_text("answer = 2\n", encoding="utf-8")
    import_removed = record("removed import")
    consumer.write_text("from .target import Real\nanswer = 2\n", encoding="utf-8")
    import_added = record("reintroduced import")
    target.write_text("class Replaced: pass\n", encoding="utf-8")
    target_changed = record("target contract changed")
    unrelated.write_text("answer = 3\n", encoding="utf-8")
    unrelated_changed = record("unrelated source changed")
    target_rel = "services/harness/src/pkg/target.py"
    ref = "services/harness/planning/lego-plan-r1.json#H01"

    def source_graph(_root: Path, *, source_revision: str):
        blob = current_tree(root, source_revision)[target_rel]
        return {"vertices": [
            {"ref": ref, "sourceAnchors": [
                {"path": target_rel, "sourceIdentity": blob},
            ]},
        ]}
    monkeypatch.setattr(module, "project_owner_lego_source_graph", source_graph)

    def change(before: str, after: str) -> dict:
        return module.project_node_python_import_delta(
            before_revision=before, after_revision=after,
            node_ref=ref, target_source=target_rel, root=root,
        )

    body = change(base, body_changed)
    assert body["targetBlobChanged"] is False
    assert body["sourceRelationStanding"] == "RECHECK_REQUIRED"
    assert body["changedCandidateImporters"][0]["sourceChangeStanding"] == (
        "IMPORTER_BYTES_CHANGED_RELATION_STABLE"
    )
    assert body["changedCandidateImporters"][0]["addedImportSyntax"] == []
    assert body["changedCandidateImporters"][0]["removedImportSyntax"] == []

    removed = change(body_changed, import_removed)
    assert removed["afterCandidateImporterCount"] == 0
    assert removed["sourceRelationStanding"] == "RECHECK_REQUIRED"
    assert removed["changedCandidateImporters"][0]["removedImportSyntax"][0]["name"] == "Real"

    added = change(import_removed, import_added)
    assert added["changedCandidateImporters"][0]["addedImportSyntax"][0]["name"] == "Real"

    target_delta = change(import_added, target_changed)
    assert target_delta["targetBlobChanged"] is True
    assert target_delta["sourceRelationStanding"] == "RECHECK_REQUIRED"
    assert target_delta["changedCandidateImporters"][0]["addedImportSyntax"][0][
        "targetDefinitionStanding"
    ] == "UNRESOLVED_OR_REEXPORTED"

    unrelated_delta = change(target_changed, unrelated_changed)
    assert unrelated_delta["sourceRelationStanding"] == "NO_DECLARED_SOURCE_RELATION_CHANGE"
    assert unrelated_delta["changedCandidateImporters"] == []
    assert unrelated_delta["proofReuseAdmissible"] is False

    same = change(target_changed, target_changed)
    assert same["sourceRelationStanding"] == "NO_DECLARED_SOURCE_RELATION_CHANGE"


def test_python_import_delta_lost_target_is_unknown_not_no_consumer(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    import subprocess
    from tools.repo.source_history_legos import current_tree
    root = tmp_path
    folder = root / "services/harness/src/pkg"
    folder.mkdir(parents=True)
    source = folder / "target.py"
    source.write_text("class Real: pass\n", encoding="utf-8")
    consumer = folder / "consumer.py"
    consumer.write_text("from .target import Real\n", encoding="utf-8")

    def git(*args: str) -> str:
        return subprocess.check_output(["git", "-C", str(root), *args], text=True).strip()
    git("init", "-q")
    git("add", ".")
    git("-c", "user.name=GraphTest", "-c", "user.email=test@example.invalid",
        "commit", "-qm", "base")
    before = git("rev-parse", "HEAD")
    source.unlink()
    git("add", "-A")
    git("-c", "user.name=GraphTest", "-c", "user.email=test@example.invalid",
        "commit", "-qm", "target removed")
    after = git("rev-parse", "HEAD")
    path = "services/harness/src/pkg/target.py"
    node = "services/harness/planning/lego-plan-r1.json#H01"
    def projected(_root: Path, *, source_revision: str):
        old = source_revision == before
        return {"vertices": [{
            "ref": node,
            "sourceAnchors": (
                [{"path": path, "sourceIdentity": current_tree(root, before)[path]}]
                if old else []
            ),
        }]}
    monkeypatch.setattr(module, "project_owner_lego_source_graph", projected)
    result = module.project_node_python_import_delta(
        before_revision=before, after_revision=after,
        node_ref=node, target_source=path, root=root,
    )
    assert result["sourceRelationStanding"] == "UNKNOWN"
    assert result["unresolvedCut"] == "after"
    assert result["proofReuseAdmissible"] is False


def test_real_harness_h01_upstream_static_readset_is_git_qualified() -> None:
    import subprocess
    from tools.repo.source_history_legos import current_tree
    sha = subprocess.check_output(["git", "-C", str(ROOT), "rev-parse", "HEAD"], text=True).strip()
    result = module.project_node_python_import_syntax(
        source_revision=sha,
        node_ref="services/harness/planning/lego-plan-r1.json#H01",
        target_source="services/harness/src/ordivon_harness/ordivon/events.py",
    )
    tree = current_tree(ROOT, sha)
    upstream = {row["sourcePath"]: row for row in result["upstreamLocalSourceFiles"]}
    for path in (
        "services/harness/src/anc_canonical/__init__.py",
        "services/harness/src/anc_canonical/canonical.py",
        "services/harness/src/ordivon_harness/__init__.py",
        "services/harness/src/ordivon_harness/ordivon/__init__.py",
    ):
        assert upstream[path]["gitBlobIdentity"] == tree[path]
    assert result["upstreamInvalidSyntaxPaths"] == []
    assert result["upstreamStaticReadsetQualification"].startswith("PARTIAL_GIT_STATIC")
    assert "dataclasses" in result["externalImportAssumptions"]
    assert "collections" in result["externalImportAssumptions"]
    assert "ACTUAL_CONSUMER" not in result["truthRole"]


def test_upstream_local_import_dependency_change_invalidates_with_stable_target_and_consumer(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    import subprocess
    from tools.repo.source_history_legos import current_tree
    root = tmp_path
    src = root / "services/harness/src"
    pkg = src / "pkg"
    pkg.mkdir(parents=True)
    (pkg / "__init__.py").write_text("from .canonical import pack\n", encoding="utf-8")
    (pkg / "canonical.py").write_text("def pack(x): return x\n", encoding="utf-8")
    (pkg / "events.py").write_text("from pkg import pack\nclass Event: pass\n", encoding="utf-8")
    (pkg / "consumer.py").write_text("from .events import Event\n", encoding="utf-8")
    def git(*args: str) -> str:
        return subprocess.check_output(["git", "-C", str(root), *args], text=True).strip()
    git("init", "-q")
    def commit(msg: str) -> str:
        git("add", ".")
        git("-c", "user.name=GraphTest", "-c", "user.email=test@example.invalid",
            "commit", "-qm", msg)
        return git("rev-parse", "HEAD")
    before = commit("baseline")
    (pkg / "canonical.py").write_text("def pack(x): return (x,)\n", encoding="utf-8")
    upstream_changed = commit("same event source upstream implementation changes")
    (pkg / "__init__.py").write_text("from .canonical import pack\n# init source changes\n", encoding="utf-8")
    init_changed = commit("parent init bytes change")
    ref = "services/harness/planning/lego-plan-r1.json#H01"
    target = "services/harness/src/pkg/events.py"
    def graph(_root: Path, *, source_revision: str):
        return {"vertices": [{"ref": ref, "sourceAnchors": [{
            "path": target,
            "sourceIdentity": current_tree(root, source_revision)[target],
        }]}]}
    monkeypatch.setattr(module, "project_owner_lego_source_graph", graph)
    def inspect(old: str, new: str) -> dict:
        return module.project_node_python_import_delta(
            before_revision=old, after_revision=new,
            node_ref=ref, target_source=target, root=root,
        )
    impacted = inspect(before, upstream_changed)
    assert impacted["targetBlobChanged"] is False
    assert impacted["changedCandidateImporters"] == []
    assert impacted["sourceRelationStanding"] == "RECHECK_REQUIRED"
    assert [r["sourcePath"] for r in impacted["changedUpstreamLocalSourceFiles"]] == [
        "services/harness/src/pkg/canonical.py",
    ]
    assert impacted["proofReuseAdmissible"] is False
    initializer = inspect(upstream_changed, init_changed)
    assert initializer["sourceRelationStanding"] == "RECHECK_REQUIRED"
    assert [r["sourcePath"] for r in initializer["changedUpstreamLocalSourceFiles"]] == [
        "services/harness/src/pkg/__init__.py",
    ]
    same = inspect(init_changed, init_changed)
    assert same["sourceRelationStanding"] == "NO_DECLARED_SOURCE_RELATION_CHANGE"
    assert same["changedUpstreamLocalSourceFiles"] == []
    assert same["proofReuseAdmissible"] is False



def test_phase1_web_cross_security_effect_and_http_lego_boundaries() -> None:
    """Verify source-semantic roles separately: policy ≠ effect ≠ HTTP rails."""
    plan = json.loads(
        (ROOT / "apps/web/planning/lego-plan-r1.json").read_text(encoding="utf-8")
    )
    nodes = {n["id"]: n for n in plan["nodes"]}
    assert set(nodes) == {f"W0{i}" for i in range(1, 7)}
    module.validate_owner_lego_graph(plan)
    module.validate_owner_lego_dependencies(plan, "apps/web")
    module.validate_owner_lego_source_evidence(
        ROOT, "apps/web/planning/lego-plan-r1.json", plan
    )
    source = (ROOT / "apps/web/src/app.ts").read_text(encoding="utf-8")
    server = (ROOT / "apps/web/src/server.ts").read_text(encoding="utf-8")
    store = (ROOT / "apps/web/src/store.ts").read_text(encoding="utf-8")
    authority = (ROOT / "apps/web/src/agent-authority.ts").read_text(encoding="utf-8")
    for observed in (
        "async function verifiedAgent(", "async function admitAgentEffect(",
        "store.resolveAgentGrant(", "store.commitAgentCanaryCreate(",
        "store.commitAgentCanaryPublish(",
    ):
        assert observed in source
    assert "SecurityContractAdmissionEvaluator" in authority
    for effect in ("commitAgentCanaryCreate(", "commitAgentCanaryPublish(",
                   "resolveAgentEffectReplay(", "putEffectApproval("):
        assert effect in store
    assert 'import { createWebApp } from "./app.ts";' in server
    assert "await createWebApp(" in server

    assert {"W03", "W04"} <= set(nodes["W05"]["dependencies"])
    assert {f"W0{i}" for i in range(1, 6)} == set(nodes["W06"]["dependencies"])
    assert {edge["from"] for edge in plan["edges"]
            if edge["to"] == "W06" and edge["type"] == "COMPOSITION"} == {
                f"W0{i}" for i in range(1, 6)
            }
    for node in nodes.values():
        assert all(node.get(key) for key in
                   ("inputs", "outputs", "behavioralContract", "acceptance", "evidence"))
        assert "UNKNOWN" in node["sourceStanding"]
        for witness in node["consumerBindings"]:
            assert witness["standing"] in {
                "SOURCE_HANDLER_OR_TEST_NOT_INSTALLED",
                "SOURCE_BOOTSTRAP_ONLY", "STATIC_TEST_ONLY",
            }
            assert (ROOT / witness["path"]).is_file()
    # This is a source-only claim: CI cannot elevate it to installed/domain PASS.
    assert all("DEPLOYED_CURRENTNESS_UNKNOWN" in n["sourceStanding"] for n in nodes.values())

def test_skills_r21_semantic_node_consumer_source_falsification() -> None:
    """A new Skills LEGO must point to a real source-defined consumer surface.

    This is a source/symbol negative control, NOT dynamic client/installed proof.
    """
    import ast
    import copy

    plan = json.loads(
        (ROOT / "platform/skills/planning/lego-plan-r1.json").read_text(encoding="utf-8")
    )

    def qualify_source_symbols(candidate: dict) -> None:
        for node in candidate["nodes"]:
            assert all(node[key] for key in (
                "id", "responsibility", "inputs", "outputs",
                "behavioralContract", "acceptance", "formalObligations",
            ))
            assert node["actualConsumers"]
            for consumer in node["actualConsumers"]:
                relative = Path(consumer["path"])
                assert not relative.is_absolute() and ".." not in relative.parts
                path = ROOT / "platform/skills" / relative
                assert path.is_file()
                names = {
                    ast_node.name for ast_node in ast.walk(
                        ast.parse(path.read_text(encoding="utf-8"))
                    )
                    if isinstance(
                        ast_node, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)
                    )
                }
                assert consumer["symbol"] in names, (
                    f"{node['id']} has no such static consumer entrypoint: "
                    f"{consumer['path']}::{consumer['symbol']}"
                )
                assert consumer["standing"] in {
                    "SOURCE_STATIC_CALL",
                    "SOURCE_STATIC_FUNCTION; EXTERNAL_CLIENT_SOURCE_UNRESOLVED",
                }

    qualify_source_symbols(plan)
    falsified = copy.deepcopy(plan)
    falsified["nodes"][3]["actualConsumers"][0]["symbol"] = "NOT_REAL_CONSUMER"
    with pytest.raises(AssertionError, match="no such static consumer entrypoint"):
        qualify_source_symbols(falsified)


def test_gateway_new_recipes_and_optional_worker_have_distinct_native_consumers() -> None:
    import ast

    plan = json.loads(
        (ROOT / "services/gateway/planning/lego-plan-r1.json").read_text(encoding="utf-8")
    )
    native = {
        "G08": [
            ("src/ordivon_gateway/service.py", "GatewayService", "capability_resolve"),
            ("tests/test_research_capability_resolution.py", None,
             "test_research_resolve_binds_exact_current_skill_without_executing_it"),
        ],
        "G09": [
            ("src/ordivon_gateway/external_worker.py", "ExternalPullWorkerTransport", "claim"),
            ("src/ordivon_gateway/external_worker.py", "ExternalPullWorkerTransport", "complete"),
            ("tests/test_external_pull_worker.py", None,
             "test_duplicate_completion_is_idempotent_but_changed_completion_conflicts"),
        ],
    }
    for identity, sources in native.items():
        lego = next(item for item in plan["nodes"] if item["id"] == identity)
        assert lego["inputs"] and lego["outputs"] and lego["behavioralContract"]
        assert lego["environmentQualification"]["installed"] == "UNKNOWN"
        assert lego["formalObligations"]
        for path, cls_name, method in sources:
            source = ROOT / "services/gateway" / path
            assert source.is_file()
            syntax = ast.parse(source.read_text(encoding="utf-8"))
            member = syntax.body
            if cls_name is not None:
                owner = next(
                    (item for item in syntax.body
                     if isinstance(item, ast.ClassDef) and item.name == cls_name),
                    None,
                )
                assert owner is not None
                member = owner.body
            assert any(
                isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef))
                and item.name == method for item in member
            ), (identity, path, method)
    assert any(
        edge["from"] == "G09" and edge["to"] == "G03"
        and edge["type"] == "ADAPTATION"
        and "Optional" in edge["label"]
        for edge in plan["edges"]
    )
    assert not any(
        edge["from"] == "G08" and edge["to"] == "G03" and edge["type"] == "AUTHORITY"
        for edge in plan["edges"]
    )


def test_next_r21_crossdomain_consumers_are_actual_source_symbols() -> None:
    """Qualify declared Next cross-domain consumers against source syntax.

    Names in strings, missing aliases, or fabricated functions must not
    receive even SOURCE_STATIC qualification. This is not execution proof.
    """
    import ast
    import copy

    plan = json.loads(
        (ROOT / "meta/next/planning/lego-plan-r1.json").read_text(encoding="utf-8")
    )

    def qualify(candidate: dict) -> None:
        assert candidate["kind"] == "ordivon.project-lego-plan"
        assert {row["id"] for row in candidate["nodes"]} == {"NX01", "NX02", "NX03", "NX04"}
        for node in candidate["nodes"]:
            for key in ("responsibility", "inputs", "outputs", "behavioralContract", "acceptance", "formalObligations"):
                assert node[key], (node["id"], key)
            assert node["consumerBindings"], node["id"]
            for row in node["consumerBindings"]:
                relative = Path(row["path"])
                assert not relative.is_absolute() and ".." not in relative.parts
                source = ROOT / "meta/next" / relative
                tree = ast.parse(source.read_text(encoding="utf-8"))
                defined = {
                    n.name for n in ast.walk(tree)
                    if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))
                }
                imported = {
                    alias.asname or alias.name.split(".")[0]
                    for n in ast.walk(tree)
                    if isinstance(n, (ast.ImportFrom, ast.Import))
                    for alias in n.names
                }
                called = set()
                for call in ast.walk(tree):
                    if not isinstance(call, ast.Call):
                        continue
                    if isinstance(call.func, ast.Name):
                        called.add(call.func.id)
                    elif isinstance(call.func, ast.Attribute) and isinstance(call.func.value, ast.Name):
                        called.add(call.func.value.id)
                for name in row["symbols"]:
                    assert name in defined | imported, (row["path"], name)
                    assert name in called, (row["path"], f"not syntactically called: {name}")
                assert "SOURCE" in row["standing"]

    qualify(plan)
    forged = copy.deepcopy(plan)
    forged["nodes"][1]["consumerBindings"][0]["symbols"] = ["made_up_lego_consumer"]
    with pytest.raises(AssertionError):
        qualify(forged)



def test_agent_native_one_lego_compact_inspection_preserves_source_and_unknown() -> None:
    """A consumer can inspect one real LEGO without re-reading the full graph."""
    import subprocess
    revision = subprocess.check_output(
        ["git", "-C", str(ROOT), "rev-parse", "HEAD"], text=True,
    ).strip()
    ref = "services/gateway/planning/lego-plan-r1.json#G06"
    result = module.inspect_owner_lego_contract(
        source_revision=revision, node_ref=ref, root=ROOT,
    )
    graph = module.project_owner_lego_source_graph(ROOT, source_revision=revision)
    assert result["ref"] == ref
    assert result["sourceCut"] == revision
    assert result["truthRole"] == "SOURCE_PLAN_DECLARATION_ONLY_NOT_RUNTIME_OR_FORMAL_TRUTH"
    assert result["declaredRoles"]["responsibility"]
    assert result["declaredRoles"]["behavioralContract"]
    assert not result["missingRoles"]
    assert result["sourceAnchors"]
    assert not result["unresolvedSourceEvidence"]
    assert "FORMAL_PROOF" in result["unverifiedFacets"]
    assert "ACTUAL_CONSUMER" in result["unverifiedFacets"]
    assert "INSTALLED" in result["unverifiedFacets"]
    assert result["proofReuseAdmissible"] is False
    assert len(json.dumps(result)) < len(json.dumps(graph)) // 3
    assert all(ref in (x["from"], x["to"]) for x in result["incidentRelations"])

    for invalid in ("services/gateway/planning/lego-plan-r1.json#NONEXISTENT",
                    "../../etc/passwd#G06",
                    "tools/repo/owners.toml#gateway"):
        with pytest.raises(module.ArchitectureDocsError, match="not registered"):
            module.inspect_owner_lego_contract(
                source_revision=revision, node_ref=invalid, root=ROOT
            )
    with pytest.raises(module.ArchitectureDocsError, match="exact 40-hex"):
        module.inspect_owner_lego_contract(
            source_revision="HEAD", node_ref=ref, root=ROOT
        )

def test_agent_compact_source_impact_keeps_unknown_unindexed_and_finite_proof_scope() -> None:
    """Omitted NO_DECLARED_HIT rows never become implicit proof-reuse admission."""
    original = {
        "kind": "ordivon.owner-lego-declared-source-change",
        "beforeSourceCut": "a" * 40,
        "afterSourceCut": "b" * 40,
        "changedGitPaths": ["extensions/ordivon-control-plane/plugin.json"],
        "unindexedChangedPaths": ["extensions/ordivon-control-plane/plugin.json"],
        "proofReuseAdmissible": False,
        "nonClaims": ["NO_DECLARED_HIT does not prove a consumer unchanged."],
        "standingByDeclaredNode": [
            {"ref": "R1", "sourceImpactStanding": "NO_DECLARED_HIT"},
            {"ref": "R2", "sourceImpactStanding": "UNKNOWN"},
            {"ref": "R3", "sourceImpactStanding": "RECHECK_REQUIRED"},
            {"ref": "R4", "sourceImpactStanding": "NO_DECLARED_HIT"},
        ],
    }
    snapshot = copy.deepcopy(original)
    result = module._select_agent_source_impact(original)
    assert original == snapshot
    assert result["proofReuseAdmissible"] is False
    assert result["unindexedChangedPaths"] == original["unindexedChangedPaths"]
    assert result["nonClaims"] == original["nonClaims"]
    assert result["omittedNoDeclaredHitCount"] == 2
    assert result["omittedStanding"] == "NO_DECLARED_HIT"
    assert result["sourceImpactProjection"] == "CHANGED_OR_UNKNOWN_ONLY"
    assert result["standingByDeclaredNode"] == original["standingByDeclaredNode"][1:3]
    assert result["beforeSourceCut"] == original["beforeSourceCut"]
    assert result["afterSourceCut"] == original["afterSourceCut"]


def test_agent_compact_source_impact_does_not_discard_new_unknown_categories() -> None:
    sample = {
        "proofReuseAdmissible": False,
        "standingByDeclaredNode": [
            {"ref": "R1", "sourceImpactStanding": "NO_DECLARED_HIT"},
            {"ref": "R2", "sourceImpactStanding": "SOME_NEW_UNKNOWN"},
            {"ref": "R3", "sourceImpactStanding": "UNKNOWN"},
        ],
    }
    result = module._select_agent_source_impact(sample)
    assert [x["ref"] for x in result["standingByDeclaredNode"]] == ["R2", "R3"]
    assert result["omittedNoDeclaredHitCount"] == 1


def test_agent_compact_source_impact_cli_rejects_unqualified_usage(
    capsys: pytest.CaptureFixture[str],
) -> None:
    for args in (
        ["--agent-impact"],
        ["--project-owner-graphs", "--agent-impact"],
        ["--project-owner-graphs", "--agent-impact", "--source-revision", "x" * 40],
    ):
        assert module.main(args) == 2
        assert "--agent-impact requires" in capsys.readouterr().out


def test_agent_compact_source_impact_cli_keeps_exact_native_change(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str],
) -> None:
    sample = {
        "kind": "ordivon.owner-lego-declared-source-change",
        "changedGitPaths": ["a.py"],
        "unindexedChangedPaths": ["a.py"],
        "proofReuseAdmissible": False,
        "standingByDeclaredNode": [
            {"ref": "one", "sourceImpactStanding": "NO_DECLARED_HIT"},
            {"ref": "two", "sourceImpactStanding": "UNKNOWN"},
        ],
    }
    monkeypatch.setattr(module, "project_owner_lego_source_change", lambda **kw: copy.deepcopy(sample))
    args = [
        "--project-owner-graphs", "--source-revision", "b" * 40,
        "--compare-source-revision", "a" * 40,
    ]
    assert module.main(args + ["--agent-impact"]) == 0
    compact = json.loads(capsys.readouterr().out)
    assert compact["unindexedChangedPaths"] == ["a.py"]
    assert compact["proofReuseAdmissible"] is False
    assert compact["standingByDeclaredNode"] == [{"ref": "two", "sourceImpactStanding": "UNKNOWN"}]
    assert compact["omittedNoDeclaredHitCount"] == 1
    assert module.main(args) == 0
    normal = json.loads(capsys.readouterr().out)
    assert normal == sample

def test_agent_native_source_path_to_owner_to_single_contract() -> None:
    """Path lookup is an exact-source address, not an inferred effect owner."""
    import subprocess

    revision = subprocess.check_output(
        ["git", "-C", str(ROOT), "rev-parse", "HEAD"], text=True,
    ).strip()
    path = "services/gateway/src/ordivon_gateway/routes.py"
    result = module.inspect_owner_source_path(
        source_revision=revision, source_path=path, root=ROOT,
    )
    assert result["sourceCut"] == revision
    assert result["sourceIdentity"].startswith("100644:blob:")
    assert result["sourceMembershipStanding"] == "TRACKED_SOURCE"
    assert [owner["name"] for owner in result["ownerPartitions"]] == ["gateway"]
    assert result["ownerPartitions"][0]["verifyTask"] == "gateway:verify"
    assert result["legoDiscoveryStanding"] == "DECLARED_ANCHOR_PARTIAL"
    assert result["consumerProofStanding"] == "UNKNOWN"
    assert result["proofReuseAdmissible"] is False
    assert "ACTUAL_CONSUMER" in result["unverifiedFacets"]
    assert "FORMAL_PROOF" in result["unverifiedFacets"]
    assert "INSTALLED" in result["unverifiedFacets"]
    refs = {item["ref"] for item in result["declaredLegoAnchors"]}
    assert "services/gateway/planning/lego-plan-r1.json#G01" in refs
    for ref in refs:
        detailed = module.inspect_owner_lego_contract(
            source_revision=revision, node_ref=ref, root=ROOT,
        )
        assert detailed["declaredRoles"]["responsibility"]
        assert detailed["proofReuseAdmissible"] is False
    assert len(json.dumps(result)) < len(json.dumps(
        module.project_owner_lego_source_graph(ROOT, source_revision=revision)
    )) // 3


def test_agent_native_unknown_path_does_not_upgrade_no_consumer() -> None:
    import subprocess

    revision = subprocess.check_output(
        ["git", "-C", str(ROOT), "rev-parse", "HEAD"], text=True,
    ).strip()
    missing = module.inspect_owner_source_path(
        source_revision=revision,
        source_path="services/gateway/src/unseen_dynamic_consumer.py",
        root=ROOT,
    )
    assert missing["sourceIdentity"] is None
    assert missing["sourceMembershipStanding"] == "ABSENT_AT_SOURCECUT"
    assert missing["legoDiscoveryStanding"] == "UNKNOWN_UNINDEXED"
    assert missing["declaredLegoAnchors"] == []
    assert missing["consumerProofStanding"] == "UNKNOWN"
    assert missing["ownerPartitions"][0]["name"] == "gateway"

    # The two-file portable Agent Plugin is a Repo partition, not an
    # autonomous runtime or control-plane authority.
    plugin = module.inspect_owner_source_path(
        source_revision=revision,
        source_path="extensions/ordivon-control-plane/plugin.json",
        root=ROOT,
    )
    assert plugin["ownerPartitions"][0]["name"] == "control-plugin"
    assert plugin["sourceIdentity"].startswith("100644:blob:")
    assert plugin["legoDiscoveryStanding"] == "UNKNOWN_UNINDEXED"
    assert plugin["proofReuseAdmissible"] is False


def test_agent_native_path_rejects_unqualified_identity_or_mode() -> None:
    import subprocess

    revision = subprocess.check_output(
        ["git", "-C", str(ROOT), "rev-parse", "HEAD"], text=True,
    ).strip()
    for candidate in ("", "/services/gateway/a.py", "../services/runtime/a.py",
                      "services/gateway/../host/test.py",
                      "services//gateway/a.py", "services\\gateway\\a.py"):
        with pytest.raises(module.ArchitectureDocsError, match="canonical"):
            module.inspect_owner_source_path(
                source_revision=revision, source_path=candidate, root=ROOT,
            )
    with pytest.raises(module.ArchitectureDocsError, match="exact 40-hex"):
        module.inspect_owner_source_path(
            source_revision="origin/main",
            source_path="services/gateway/README.md", root=ROOT,
        )
    bad_mode = module.main([
        "--inspect-owner-path", "services/gateway/README.md",
        "--source-revision", revision, "--compare-source-revision", revision,
    ])
    assert bad_mode == 2


def test_agent_native_portable_plugin_manifest_is_a_native_contract_carrier() -> None:
    """A portable two-file Plugin has a native schema; no extra LEGO plan file."""
    import subprocess

    cut = subprocess.check_output(
        ["git", "-C", str(ROOT), "rev-parse", "HEAD"], text=True
    ).strip()
    manifest = module.inspect_owner_source_path(
        source_revision=cut,
        source_path="extensions/ordivon-control-plane/plugin.json",
        root=ROOT,
    )
    assert manifest["ownerPartitions"][0]["name"] == "control-plugin"
    assert manifest["legoDiscoveryStanding"] == "UNKNOWN_UNINDEXED"
    assert manifest["nativeContractCarrier"] == {
        "standing": "NATIVE_JSON_SCHEMA_DECLARATION_ONLY",
        "schemaUri": "https://agent-plugins.org/schemas/1.0.0/plugin.schema.json",
        "sourceIdentity": manifest["sourceIdentity"],
        "declaredPackageName": "ordivon-control-plane",
    }
    assert manifest["proofReuseAdmissible"] is False
    assert manifest["consumerProofStanding"] == "UNKNOWN"
    declared = module.inspect_owner_source_path(
        source_revision=cut,
        source_path="extensions/ordivon-control-plane/mcp.json",
        root=ROOT,
    )
    assert declared["nativeContractCarrier"]["schemaUri"] == (
        "https://agent-plugins.org/schemas/1.0.0/mcp.schema.json"
    )
    assert declared["nativeContractCarrier"]["declaredMcpServerKeys"] == [
        "ordivon-gateway"
    ]
    assert "DECLARED_ANCHOR_PARTIAL" == declared["legoDiscoveryStanding"]
    # Native declarative fact and existing R2.1 plan anchor are independent.
    assert declared["proofReuseAdmissible"] is False
    assert sorted(p.name for p in (ROOT / "extensions/ordivon-control-plane").iterdir()) == [
        "mcp.json", "plugin.json"
    ]


def test_agent_native_json_schema_source_query_never_infers_consumers() -> None:
    """Typed noncarrier and vanished files never become installed authority."""
    import subprocess

    cut = subprocess.check_output(
        ["git", "-C", str(ROOT), "rev-parse", "HEAD"], text=True
    ).strip()
    plain = module.inspect_owner_source_path(
        source_revision=cut,
        source_path="services/gateway/src/ordivon_gateway/routes.py",
        root=ROOT,
    )
    assert plain["nativeContractCarrier"] is None
    assert plain["gitEntryStanding"] == "REGULAR_BLOB"
    missing = module.inspect_owner_source_path(
        source_revision=cut,
        source_path="extensions/ordivon-control-plane/missing.json",
        root=ROOT,
    )
    assert missing["nativeContractCarrier"] is None
    assert missing["gitEntryStanding"] == "ABSENT_FROM_GIT_CUT"
    assert missing["legoDiscoveryStanding"] == "UNKNOWN_UNINDEXED"
    assert missing["consumerProofStanding"] == "UNKNOWN"
    assert missing["proofReuseAdmissible"] is False



def test_native_schema_hint_refuses_symlink_and_gitlink_bytes() -> None:
    """A Git tracked symlink is not the regular JSON implementation it targets."""
    assert module._project_native_json_schema_source(
        ROOT, "extensions/ordivon-control-plane/plugin.json",
        "120000:blob:" + "0" * 40,
    ) is None
    assert module._project_native_json_schema_source(
        ROOT, "extensions/ordivon-control-plane/plugin.json",
        "160000:commit:" + "0" * 40,
    ) is None
    assert module._project_native_json_schema_source(
        ROOT, "extensions/ordivon-control-plane/plugin.json",
        None,
    ) is None
    import subprocess
    cut = subprocess.check_output(
        ["git", "-C", str(ROOT), "rev-parse", "HEAD"], text=True,
    ).strip()
    with pytest.raises(module.ArchitectureDocsError, match="canonical"):
        module.inspect_owner_source_path(
            source_revision=cut, source_path="extensions/" + chr(0) + "/plugin.json",
            root=ROOT,
        )


def test_one_lego_inspection_preserves_all_existing_consumer_claim_carriers() -> None:
    """Three *source declaration* shapes cannot vanish into an empty consumer list."""
    import subprocess

    cut = subprocess.check_output(
        ["git", "-C", str(ROOT), "rev-parse", "HEAD"], text=True,
    ).strip()
    cases = [
        ("platform/skills/planning/lego-plan-r1.json#SK03", "actualConsumers", "skills_resolve"),
        ("packages/composition/planning/lego-plan-r1.json#C01", "consumerBindings", None),
        ("services/gateway/planning/lego-plan-r1.json#G01", "consumerEvidence", None),
    ]
    for ref, claim_kind, expected_symbol in cases:
        view = module.inspect_owner_lego_contract(
            source_revision=cut, node_ref=ref, root=ROOT,
        )
        claim = view["declaredConsumerClaims"]
        assert set(claim) == {"consumerEvidence", "actualConsumers", "consumerBindings"}
        assert claim[claim_kind], (ref, claim_kind)
        if expected_symbol:
            assert any(row.get("symbol") == expected_symbol for row in claim[claim_kind])
        assert view["consumerClaimQualification"] == "SOURCE_PLAN_DECLARATION_ONLY_NOT_VERIFIED_CONSUMPTION"
        assert view["consumerClosureStanding"] == "UNKNOWN"
        assert view["proofReuseAdmissible"] is False

    # Missing and empty evidence are not positive evidence of zero consumers.
    root = module.inspect_owner_lego_contract(
        source_revision=cut, node_ref="services/harness/planning/lego-plan-r1.json#H01", root=ROOT,
    )
    assert root["declaredConsumerClaims"] == {
        "consumerEvidence": None, "actualConsumers": None, "consumerBindings": None,
    }
    assert root["consumerClosureStanding"] == "UNKNOWN"
