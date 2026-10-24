"""Source-bound typed issue LEGO registration; existing Owner only."""

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
