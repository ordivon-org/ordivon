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
    # No real caller imports cursor.py; its R3 retained row was a ghost consumer.
    assert all(row["id"] != "U01" for row in current["retained"])
    assert "ScopeBoundCursor" in current["retired"]
    assert not (ROOT / "services/host/src/ordivon_host_v2/cursor.py").exists()
    assert all(node["id"] != "O05" for node in legacy["nodes"])
    assert all(slice_["id"] != "OS1" for slice_ in legacy["slices"])
    assert legacy["gaps"] == []


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
