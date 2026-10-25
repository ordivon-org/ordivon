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
    plans = {
        plan_path: json.loads((path.parents[3] / plan_path).read_text(encoding="utf-8"))
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
