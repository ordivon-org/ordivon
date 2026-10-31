"""Source-bound typed issue LEGO registration; existing Owner only."""

import copy
import json
from pathlib import Path

import pytest

from tools.repo.test_architecture_docs import formal_issue_inputs, module


def test_repository_owner_identity_and_source_provenance_share_existing_lego_owner() -> None:
    """Link the already implemented owner-law and SourceCut-law, not a new registry."""
    census, plans = formal_issue_inputs()
    plan_path = "tools/repo/planning/lego-plan-r1.json"
    assert {issue["id"] for issue in census["issues"] if issue["naturalOwner"] == "tools/repo"}
    for issue_id, slice_id in (("TYPE-01", "RG2"), ("FORMAL-02", "RG3")):
        issue = next(issue for issue in census["issues"] if issue["id"] == issue_id)
        assert issue["registration"] == {
            "state": "LINKED",
            "ownerPlan": plan_path,
            "slice": slice_id,
        }
        assert sum(
            x["ownerPlan"] == plan_path and x["slice"] == slice_id
            for x in census["registrations"]
        ) == 1
    plan = plans[plan_path]
    assert len({n["id"] for n in plan["nodes"]}) == len(plan["nodes"])
    assert {s["id"] for s in plan["slices"]} >= {"RG1", "RG2", "RG3"}
    module.validate_formal_issue_census(census, plans)


def test_oct25_dependency_updater_issue_links_existing_rg2_witness() -> None:
    """A stale Renovate-only inference must not erase actual Dependabot consumers."""
    path = Path(__file__).resolve().parents[2] / (
        "docs/architecture/evidence/FORMAL_LEGO_ISSUE_CENSUS_20261025_R1.json"
    )
    census = json.loads(path.read_text(encoding="utf-8"))
    plan_path = "tools/repo/planning/lego-plan-r1.json"
    # The census also has a Runtime RW1 registration. Positive graph admission
    # must supply *every* exact registered Owner projection, not pretend the
    # Repo RG2 subset constitutes the whole provenance/consumer relation.
    plans = {
        owner_plan: json.loads(
            (path.parents[3] / owner_plan).read_text(encoding="utf-8")
        )
        for owner_plan in {row["ownerPlan"] for row in census["registrations"]}
    }
    issue = next(row for row in census["issues"] if row["id"] == "DEPS-RENOVATE-20261025")
    assert issue["registration"] == {
        "state": "LINKED",
        "ownerPlan": plan_path,
        "slice": "RG2",
    }
    assert "LATEST_RELEASE_VERIFICATION_UNKNOWN" in issue["standing"]
    assert "test_all_tracked_npm_and_cargo_manifests_have_one_update_owner" in (
        " ".join(issue["requalification"]["nativeConsumers"])
    )
    module.validate_formal_issue_census(census, plans)

    # Negative CEGAR control: deleting the exact RG2 link is invalid even
    # though another RG1 registration remains present.
    weakened = copy.deepcopy(census)
    weakened["registrations"] = [
        row for row in weakened["registrations"] if row["slice"] != "RG2"
    ]
    with pytest.raises(module.ArchitectureDocsError, match="unknown owner-local LEGO"):
        module.validate_formal_issue_census(weakened, plans)


def test_oct25_workspace_issue_reuses_rw1_not_incomplete_rw0() -> None:
    """A native lifecycle guard is not a proof that unique Git work has no consumers."""
    root = Path(__file__).resolve().parents[2]
    census = json.loads((root / "docs/architecture/evidence/FORMAL_LEGO_ISSUE_CENSUS_20261025_R1.json").read_text(encoding="utf-8"))
    repo_plan = "tools/repo/planning/lego-plan-r1.json"
    runtime_plan = "services/runtime/planning/lego-plan-r1.json"
    plans = {name: json.loads((root / name).read_text(encoding="utf-8")) for name in (repo_plan, runtime_plan)}
    issue = next(row for row in census["issues"] if row["id"] == "RT-WS-20261025")
    assert issue["registration"] == {
        "state": "LINKED", "ownerPlan": runtime_plan, "slice": "RW1",
    }
    rw1 = next(row for row in plans[runtime_plan]["slices"] if row["id"] == "RW1")
    assert rw1["status"] == "COMPLETE" and "R02" in rw1["nodeIds"]
    assert "UNKNOWN" in issue["requalification"]["residualUnknown"]
    module.validate_formal_issue_census(census, plans)

    # Negative CEGAR control: an orphaned requalified issue is invalid even
    # if RG1/RG2 Repo registration still passes unchanged.
    weakened = copy.deepcopy(census)
    weakened["registrations"] = [
        r for r in weakened["registrations"] if r["ownerPlan"] != runtime_plan
    ]
    with pytest.raises(module.ArchitectureDocsError, match="unknown owner-local LEGO"):
        module.validate_formal_issue_census(weakened, plans)



def test_database_cutover_census_cannot_claim_admission_without_real_owner_effect() -> None:
    """CEGAR: passing static source docs must not authorize PostgreSQL cutover."""
    root = Path(__file__).resolve().parents[2]
    census = json.loads(
        (root / "docs/architecture/evidence/FORMAL_LEGO_ISSUE_CENSUS_20261025_R1.json")
        .read_text(encoding="utf-8")
    )
    plans = {
        owner_plan: json.loads((root / owner_plan).read_text(encoding="utf-8"))
        for owner_plan in {row["ownerPlan"] for row in census["registrations"]}
    }
    database = [item for item in census["issues"] if item["problemClass"] == "DATABASE_AUTHORITY_CONVERGENCE"]
    assert len(database) == 4
    for issue in database:
        latest = issue["latestRequalification"]
        assert latest["cutoverAdmission"] == "NOT_ADMITTED"
        assert latest["nativeConsumerEvidence"]
        for path in latest["nativeConsumerEvidence"]:
            assert (Path(__file__).resolve().parents[2] / path).is_file()
    module.validate_formal_issue_census(census, plans)
    weakened = copy.deepcopy(census)
    target = next(i for i in weakened["issues"] if i["id"] == "DB-PG-CAPITAL-20261026")
    target["latestRequalification"]["cutoverAdmission"] = "ADMITTED"
    with pytest.raises(module.ArchitectureDocsError, match="falsely admits PG cutover"):
        module.validate_formal_issue_census(weakened, plans)


def test_oct26_new_cross_owner_frontiers_remain_explicitly_unknown() -> None:
    """Missing consumer/formal/Skill proofs must not be reclassified as passed by taxonomy."""
    root = Path(__file__).resolve().parents[2]
    census = json.loads((root / "docs/architecture/evidence/FORMAL_LEGO_ISSUE_CENSUS_20261025_R1.json").read_text(encoding="utf-8"))
    cases = {
        "RT-CONSUMER-CLAIM-20261026": "services/runtime",
        "SKILL-DISCOVERY-SCIENCE-20261026": "platform/skills",
        "COMPOSITION-IMPLEMENTATION-BRIDGE-20261026": "packages/composition",
    }
    plans = {
        row["ownerPlan"]: json.loads((root / row["ownerPlan"]).read_text(encoding="utf-8"))
        for row in census["registrations"]
    }
    for issue_id, owner in cases.items():
        issue = next(i for i in census["issues"] if i["id"] == issue_id)
        assert issue["naturalOwner"] == owner
        assert issue["registration"]["state"] == "UNREGISTERED"
        assert issue["requalification"]["proofStanding"] == "UNKNOWN"
        assert issue["requalification"]["sourceCut"] == "c8cec7d7ee8ebcfcecf1893ac32a894b71051339"
    module.validate_formal_issue_census(census, plans)

    # Red control: a future agent cannot attach a missing obligation to a
    # fabricated Owner plan merely by naming an existing verified subsystem.
    weakened = copy.deepcopy(census)
    bad = next(i for i in weakened["issues"] if i["id"] == "RT-CONSUMER-CLAIM-20261026")
    bad["registration"] = {
        "state": "LINKED", "ownerPlan": "services/runtime/planning/lego-plan-r1.json",
        "slice": "RW999"
    }
    with pytest.raises(module.ArchitectureDocsError, match="unknown owner-local LEGO"):
        module.validate_formal_issue_census(weakened, plans)

def test_oct26_distinct_windows_and_gateway_problem_lego_gaps() -> None:
    """Keep only non-overlapping source-backed issues; forbid forged owner proof."""
    root = Path(__file__).resolve().parents[2]
    census = json.loads((root / "docs/architecture/evidence/FORMAL_LEGO_ISSUE_CENSUS_20261025_R1.json").read_text(encoding="utf-8"))
    plans = {r["ownerPlan"]: json.loads((root / r["ownerPlan"]).read_text(encoding="utf-8")) for r in census["registrations"]}
    unique_ids = {"WIN-EXEC-CONTEXT-20261026", "GW-SKILLS-ROUTE-20261026"}
    new = {row["id"]: row for row in census["issues"] if row["id"] in unique_ids}
    assert set(new) == unique_ids
    for row in new.values():
        assert row["registration"]["state"] == "UNREGISTERED"
        assert row["requalification"]["sourceCut"] == "db6f4e56544de72613992471d449dba85081819a"
        assert row["representation"]["requiredWitness"] and row["formalObligation"]
    module.validate_formal_issue_census(census, plans)
    fake = copy.deepcopy(census)
    next(x for x in fake["issues"] if x["id"] == "WIN-EXEC-CONTEXT-20261026")["registration"] = {
        "state": "LINKED",
        "ownerPlan": "services/runtime/planning/lego-plan-r1.json",
        "slice": "NOT_PROVED_R21_WINDOWS_ENV",
    }
    with pytest.raises(module.ArchitectureDocsError, match="unknown owner-local LEGO"):
        module.validate_formal_issue_census(fake, plans)


def test_nov01_typed_issue_census_reuses_existing_owners_without_proof_promotion() -> None:
    """Current time-scoped evidence must bind registered Owners; UNKNOWN stays explicit."""
    root = Path(__file__).resolve().parents[2]
    census = json.loads(
        (root / "docs/architecture/evidence/FORMAL_LEGO_ISSUE_CENSUS_20261101_R1.json")
        .read_text(encoding="utf-8")
    )
    plans = {
        record["ownerPlan"]: json.loads((root / record["ownerPlan"]).read_text(encoding="utf-8"))
        for record in census["registrations"]
    }
    assert len(census["issues"]) == 6
    assert {entry["id"] for entry in census["issues"]} == {
        "GIT-CURRENTNESS-20261101", "PR-CONVERGENCE-20261101",
        "WORKTREE-CONSUMER-20261101", "DEPS-CURRENTNESS-20261101",
        "FORMAL-R21-REFINEMENT-20261101", "PG-CONSUMER-SUBTRACTION-20261101",
    }
    assert census["truthRole"] == "time-scoped-audit-evidence-not-registry-or-admission"
    assert "UNKNOWN" in next(
        entry["standing"] for entry in census["issues"]
        if entry["id"] == "FORMAL-R21-REFINEMENT-20261101"
    )
    module.validate_formal_issue_census(census, plans)

    # Never let an attractive free-form issue invent a verified Owner slice.
    bad = copy.deepcopy(census)
    target = next(row for row in bad["issues"] if row["id"] == "FORMAL-R21-REFINEMENT-20261101")
    target["registration"] = {
        "state": "LINKED",
        "ownerPlan": "packages/composition/planning/lego-plan-r1.json",
        "slice": "R21-RUST-REFINED",
    }
    with pytest.raises(module.ArchitectureDocsError, match="unknown owner-local LEGO"):
        module.validate_formal_issue_census(bad, plans)

    bad = copy.deepcopy(census)
    bad["source"]["protectedGithubMain"] = "not-a-git-sha"
    with pytest.raises(module.ArchitectureDocsError, match="invalid Git source revision"):
        module.validate_formal_issue_census(bad, plans)


def test_nov1_r2_problem_classes_are_finite_and_r21_refinement_links_cr21() -> None:
    root = Path(__file__).resolve().parents[2]
    path = root / "docs/architecture/evidence/FORMAL_LEGO_ISSUE_CENSUS_20261101_R2.json"
    census = json.loads(path.read_text(encoding="utf-8"))
    plans = {
        row["ownerPlan"]: json.loads((root / row["ownerPlan"]).read_text(encoding="utf-8"))
        for row in census["registrations"]
    }
    issue = next(
        row for row in census["issues"]
        if row["id"] == "FORMAL-R21-REFINEMENT-20261101-R2"
    )
    assert issue["registration"] == {
        "state": "LINKED",
        "ownerPlan": "packages/composition/planning/lego-plan-r1.json",
        "slice": "CR21",
    }
    cr21 = next(
        row for row in plans["packages/composition/planning/lego-plan-r1.json"]["slices"]
        if row["id"] == "CR21"
    )
    assert cr21["status"] == "PROPOSED"
    assert set(cr21["nodeIds"]) == {"C01", "C02", "C03", "C04", "C05", "C06"}
    module.validate_formal_issue_census(census, plans)

    typo = copy.deepcopy(census)
    typo["issues"][0]["problemClass"] = "SOURCE_GRAPH_INTEGRIT"
    with pytest.raises(
        module.ArchitectureDocsError, match="unknown formal issue problemClass"
    ):
        module.validate_formal_issue_census(typo, plans)


def test_nov1_r2_host_cross_schema_relation_remains_unknown() -> None:
    root = Path(__file__).resolve().parents[2]
    path = root / "docs/architecture/evidence/FORMAL_LEGO_ISSUE_CENSUS_20261101_R2.json"
    census = json.loads(path.read_text(encoding="utf-8"))
    plans = {
        row["ownerPlan"]: json.loads((root / row["ownerPlan"]).read_text(encoding="utf-8"))
        for row in census["registrations"]
    }
    host = next(
        row for row in census["issues"]
        if row["id"] == "HOST-PLAN-REFINEMENT-20261101"
    )
    assert host["problemClass"] == "OWNER_PLAN_REFINEMENT"
    assert host["registration"] == {
        "state": "LINKED",
        "ownerPlan": "services/host/planning/lego-plan-r1.json",
        "slice": "HR3ALIGN",
    }
    assert "SEMANTIC_REFINEMENT_UNKNOWN" in host["standing"]
    module.validate_formal_issue_census(census, plans)


def test_nov1_r2_closed_dependency_issue_is_time_scoped_not_permanent_latest_claim() -> None:
    root = Path(__file__).resolve().parents[2]
    census = json.loads(
        (root / "docs/architecture/evidence/FORMAL_LEGO_ISSUE_CENSUS_20261101_R2.json")
        .read_text(encoding="utf-8")
    )
    issue = next(
        row for row in census["issues"]
        if row["id"] == "DEPS-CURRENTNESS-20261101-R2"
    )
    assert issue["standing"].startswith("CLOSED_CURRENT_")
    assert "time-scoped" in issue["formalObligation"]
    assert issue["decision"].startswith("No dependency action")
