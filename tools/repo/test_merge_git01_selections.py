"""Owner-native algebraic regression: reconcile concurrent GIT-01 evidence without loss."""

from __future__ import annotations

import copy
import itertools
import json
from pathlib import Path

import pytest

from tools.repo.merge_git01_selections import MergeConflict, merge_selections


def claim(index: int, witness: str | None = None) -> dict:
    return {
        "localCommit": f"{index:040x}",
        "owner": "services/runtime",
        "consumer": f"Native owner consumer {index}",
        "remoteWitness": witness or f"Native proof {index}",
        "evidenceScope": "NATIVE_CONSUMER_PASS",
        "disposition": "SKIP_DUPLICATE_CHERRY_PICK",
        "evaluatedRemoteMain": f"{100+index:040x}",
    }


def census(*items: dict, local="old-main", remote="remote-main") -> dict:
    return {
        "registrations": [{"ownerPlan": "preserved"}],
        "issues": [
            {"id": "GIT-01", "consumerSourceCut": {"localMain": local, "remoteMain": remote},
             "consumerSelections": list(items), "registration": {"ownerPlan": "tools/repo"}},
            {"id": "GIT-02", "consumerSelections": [claim(99)]},
        ],
    }


def selections(document: dict) -> list[dict]:
    return next(x for x in document["issues"] if x["id"] == "GIT-01")["consumerSelections"]


def test_parallel_union_preserves_current_non_git01_and_all_distinct_claims() -> None:
    current = census(claim(1), claim(2))
    candidate = census(claim(2), claim(3), claim(4), remote="older-protected-main")
    before_current = copy.deepcopy(current)
    before_candidate = copy.deepcopy(candidate)
    merged = merge_selections(current, candidate)
    assert [x["localCommit"] for x in selections(merged)] == [f"{v:040x}" for v in (1, 2, 3, 4)]
    assert merged["registrations"] == current["registrations"]
    assert merged["issues"][1] == current["issues"][1]
    assert merged["issues"][0]["consumerSourceCut"] == current["issues"][0]["consumerSourceCut"]
    assert current == before_current and candidate == before_candidate


def test_union_is_semantically_associative_commutative_idempotent() -> None:
    a, b, c = (census(*[claim(i) for i in ids]) for ids in ((1, 2), (2, 3), (3, 4)))
    expected = {claim(i)["localCommit"]: claim(i) for i in (1, 2, 3, 4)}
    for permutation in itertools.permutations((a, b, c)):
        result = merge_selections(merge_selections(permutation[0], permutation[1]), permutation[2])
        assert {i["localCommit"]: i for i in selections(result)} == expected
        assert merge_selections(result, result) == result


def test_conflicting_witness_for_same_sha_fails_closed() -> None:
    with pytest.raises(MergeConflict, match="conflicting proof"):
        merge_selections(census(claim(1)), census(claim(1, "weaker or altered proof")))


def test_inconsistent_local_main_cannot_union_unrelated_history() -> None:
    with pytest.raises(MergeConflict, match="localMain"):
        merge_selections(census(claim(1)), census(claim(2), local="unrelated-main"))


@pytest.mark.parametrize("bad", ["not-sha", "", "ABCDEF" * 7, "z" * 40])
def test_reject_malformed_commit_identity(bad: str) -> None:
    broken = claim(2)
    broken["localCommit"] = bad
    with pytest.raises(MergeConflict, match="localCommit"):
        merge_selections(census(claim(1)), census(broken))


def test_duplicate_sha_inside_one_input_is_refused_not_silently_collapsed() -> None:
    with pytest.raises(MergeConflict, match="duplicate"):
        merge_selections(census(claim(1), claim(1)), census(claim(2)))


def test_only_existing_git01_owner_is_selected() -> None:
    candidate = census(claim(3))
    candidate["issues"].append({"id": "GIT-03", "consumerSelections": [claim(900)]})
    result = merge_selections(census(claim(1)), candidate)
    assert {i["id"] for i in result["issues"]} == {"GIT-01", "GIT-02"}


def test_legacy_claim_without_optional_evaluated_remote_cut_remains_valid() -> None:
    historical = claim(1)
    del historical["evaluatedRemoteMain"]
    merged = merge_selections(census(historical), census(claim(2)))
    assert len(selections(merged)) == 2
    assert "evaluatedRemoteMain" not in selections(merged)[0]


def test_evidence_union_refuses_unsafe_history_deletion_claim() -> None:
    bad = claim(7)
    bad["sourceQualification"] = {"branchDeletionAllowed": True}
    with pytest.raises(MergeConflict, match="branchDeletionAllowed"):
        merge_selections(census(claim(1)), census(bad))


@pytest.mark.parametrize("bad", [[], "not-an-object", {"branchDeletionAllowed": 1}])
def test_evidence_union_refuses_malformed_source_qualification(bad: object) -> None:
    item = claim(7)
    item["sourceQualification"] = bad
    with pytest.raises(MergeConflict, match="sourceQualification|branchDeletionAllowed"):
        merge_selections(census(claim(1)), census(item))


def test_evidence_union_refuses_whitespace_only_witness() -> None:
    item = claim(7)
    item["remoteWitness"] = "   "
    with pytest.raises(MergeConflict, match="remoteWitness"):
        merge_selections(census(claim(1)), census(item))


def test_evidence_union_refuses_cross_cohort_historical_identity_overlap() -> None:
    left = claim(1)
    left["historicalCohort"] = [f"{101:040x}"]
    right = claim(2)
    right["historicalCohort"] = [f"{101:040x}"]
    with pytest.raises(MergeConflict, match="historicalCohort"):
        merge_selections(census(left), census(right))


def test_evidence_union_refuses_duplicate_historical_cohort_members() -> None:
    item = claim(3)
    item["historicalCohort"] = [f"{201:040x}", f"{201:040x}"]
    with pytest.raises(MergeConflict, match="historicalCohort"):
        merge_selections(census(claim(1)), census(item))


def test_real_git01_owner_shards_recompose_with_one_canonical_join() -> None:
    """Only the native merge helper composes parallel Agent evidence."""
    root = Path(__file__).resolve().parents[2]
    original = json.loads((
        root / "docs/architecture/evidence/FORMAL_LEGO_ISSUE_CENSUS_20261024_R1.json"
    ).read_text(encoding="utf-8"))
    original_rows = selections(original)
    by_owner: dict[str, list[dict]] = {}
    for record in original_rows:
        by_owner.setdefault(record["owner"], []).append(record)
    assert len(by_owner) > 2

    empty = copy.deepcopy(original)
    selections(empty).clear()
    expected = {row["localCommit"]: row for row in original_rows}
    for owners in (list(by_owner), list(reversed(by_owner))):
        result = copy.deepcopy(empty)
        for owner in owners:
            candidate = copy.deepcopy(empty)
            selections(candidate).extend(copy.deepcopy(by_owner[owner]))
            result = merge_selections(result, candidate)
        actual = {row["localCommit"]: row for row in selections(result)}
        assert actual == expected
        assert merge_selections(result, result) == result
        assert result["registrations"] == original["registrations"]
    assert selections(original) == original_rows
