from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
MODULE_PATH = ROOT / "tools" / "repo" / "convergence_pressure.py"
spec = importlib.util.spec_from_file_location("convergence_pressure", MODULE_PATH)
assert spec is not None and spec.loader is not None
pressure = importlib.util.module_from_spec(spec)
spec.loader.exec_module(pressure)


def queue_projection() -> dict:
    return {
        "coverage": {"queueAttributedPullRequests": 1},
        "metrics": {
            "requeues": 0,
            "unsuccessfulMergeGroupRuns": 0,
            "observedPeakQueueDepthLowerBound": 1,
        },
    }


def test_owner_cost_corpus_expands_rows_without_admitting_control() -> None:
    payload = {
        "kind": "ordivon.convergence-owner-cost-episode-corpus",
        "episodes": [
            {
                "kind": "ordivon.convergence-owner-cost-episode",
                "candidateSha": "a" * 40,
                "result": "PASS",
                "totalSeconds": 10.0,
            },
            {
                "kind": "ordivon.convergence-owner-cost-episode",
                "candidateSha": "a" * 40,
                "result": "PASS",
                "totalSeconds": 20.0,
            },
            {
                "kind": "ordivon.convergence-owner-cost-episode",
                "candidateSha": "b" * 40,
                "result": "PASS",
                "totalSeconds": 30.0,
            },
        ],
    }
    rows = pressure.owner_cost_rows([payload])
    assert len(rows) == 3
    assessment = pressure.assess(queue_projection(), owner_cost_episodes=rows)
    gates = {row["gate"]: row for row in assessment["gates"]}
    assert gates["LONG_TAIL_OWNER"]["status"] == "INSUFFICIENT_EVIDENCE"
    assert gates["LONG_TAIL_OWNER"]["evidence"] == {
        "ownerCostEpisodes": 3,
        "ownerCostCandidates": 2,
        "successfulMeasuredOwnerCostEpisodes": 3,
    }
    assert gates["PREDICTOR_DATA"]["evidence"]["ownerCostEpisodes"] == 3
    assert gates["PREDICTOR_DATA"]["evidence"]["ownerCostCandidates"] == 2
    assert assessment["controlsAdmitted"] == []


def test_owner_cost_loader_accepts_legacy_observation() -> None:
    rows = pressure.owner_cost_rows(
        [
            {
                "kind": "ordivon.convergence-owner-cost-observation",
                "measuredCandidate": "a" * 40,
            }
        ]
    )
    assert len(rows) == 1


def test_owner_cost_loader_rejects_unknown_kind() -> None:
    with pytest.raises(ValueError, match="unsupported owner-cost evidence kind"):
        pressure.owner_cost_rows([{"kind": "ordivon.not-owner-cost"}])


def test_ci_waste_cannot_be_proven_from_aggregate_without_run_evidence() -> None:
    # CI-02: an aggregate alone is not a provider/consumer witness.
    fake = {"metrics": {"runs": 1, "explicitAvoidableWasteRuns": 1,
                        "unclassifiedTerminalRuns": 0}}
    result = pressure.assess(queue_projection(), fake)
    gate = next(g for g in result["gates"] if g["gate"] == "CI_WASTE")
    assert gate["status"] == "INSUFFICIENT_EVIDENCE"
    assert result["controlsAdmitted"] == []


def test_ci_waste_rejects_summary_that_disagrees_with_source_runs() -> None:
    fake = {
        "metrics": {"runs": 2, "explicitAvoidableWasteRuns": 1,
                    "unclassifiedTerminalRuns": 0},
        "runs": [
            {"runId": 41, "runAttempt": 1, "status": "completed",
             "economicOutcome": "USEFUL", "economicReason": "normal build"},
            {"runId": 42, "runAttempt": 1, "status": "completed",
             "economicOutcome": "FAILED_PRODUCTIVELY",
             "economicReason": "valid consumer bug"},
        ],
    }
    result = pressure.assess(queue_projection(), fake)
    assert next(g for g in result["gates"] if g["gate"] == "CI_WASTE")["status"] == "INSUFFICIENT_EVIDENCE"
    assert result["controlsAdmitted"] == []


def test_ci_waste_unfinished_or_duplicate_run_cannot_admit_controls() -> None:
    row = {"runId": 51, "runAttempt": 1, "status": "in_progress",
           "economicOutcome": "AVOIDABLE_WASTE", "economicReason": "pending cannot prove waste"}
    fake = {"metrics": {"runs": 1, "explicitAvoidableWasteRuns": 1,
                        "unclassifiedTerminalRuns": 0}, "runs": [row]}
    result = pressure.assess(queue_projection(), fake)
    assert next(g for g in result["gates"] if g["gate"] == "CI_WASTE")["status"] == "INSUFFICIENT_EVIDENCE"
    assert result["controlsAdmitted"] == []

    completed = {**row, "status": "completed"}
    duplicate = {**fake, "metrics": {**fake["metrics"], "runs": 2,
                                     "explicitAvoidableWasteRuns": 2},
                 "runs": [completed, dict(completed)]}
    result = pressure.assess(queue_projection(), duplicate)
    assert next(g for g in result["gates"] if g["gate"] == "CI_WASTE")["status"] == "INSUFFICIENT_EVIDENCE"
    assert result["controlsAdmitted"] == []

def pr_source_snapshot(*rows: dict) -> dict:
    return {
        "kind": "ordivon.gh-pr-sourcecut-snapshot",
        "observedAt": "2026-10-25T14:20:00Z",
        "coverage": {"complete": True, "stateFilter": "all"},
        "pullRequests": list(rows),
    }


def pr_row(number: int, *, base: str = "a" * 40,
           head: str = "e" * 40, state: str = "MERGED") -> dict:
    return {
        "number": number, "baseRefOid": base,
        "headRefOid": head, "state": state,
    }


def test_exact_same_source_cut_flags_real_duplicate_pr_candidate_without_deletion() -> None:
    # Recorded observation: two distinct merged PRs #705/#707 used exactly
    # the same base and head, regardless of their different titles.
    same_base = "62b999c713797e2e075c30234b92fb8b360aeb52"
    same_head = "e327afceca437771d7a81037083ab2a63b226328"
    proof = pressure.pr_source_duplication_gate(
        pr_source_snapshot(
            pr_row(705, base=same_base, head=same_head),
            pr_row(707, base=same_base, head=same_head),
        )
    )
    assert proof["status"] == "PROVEN"
    assert proof["evidence"]["duplicateGroups"] == [{
        "baseRefOid": same_base,
        "headRefOid": same_head,
        "pullRequests": [
            {"number": 705, "state": "MERGED"},
            {"number": 707, "state": "MERGED"},
        ],
    }]
    assert proof["evidence"]["deleteAuthority"] == "NONE"
    assert proof["allowedExperiments"] == []


def test_same_head_different_base_is_not_equivalent_pr_source_cut() -> None:
    proof = pressure.pr_source_duplication_gate(
        pr_source_snapshot(
            pr_row(1, base="a" * 40, head="b" * 40),
            pr_row(2, base="c" * 40, head="b" * 40),
        )
    )
    assert proof["status"] == "NOT_PROVEN"
    assert proof["evidence"]["duplicateGroups"] == []


def test_duplicate_or_malformed_provider_identity_fails_closed() -> None:
    bad_cases = [
        pr_source_snapshot(pr_row(3), pr_row(3)),
        pr_source_snapshot(pr_row(True)),
        pr_source_snapshot(pr_row(3, head="unresolved")),
        pr_source_snapshot(pr_row(3, state="READY")),
        {"kind": "ordivon.gh-pr-sourcecut-snapshot", "pullRequests": []},
    ]
    for payload in bad_cases:
        evidence = pressure.pr_source_duplication_gate(payload)
        assert evidence["status"] == "INSUFFICIENT_EVIDENCE"
        assert evidence["allowedExperiments"] == []


def test_assessment_uses_existing_gate_without_control_grant() -> None:
    evidence = pr_source_snapshot(pr_row(705), pr_row(707))
    result = pressure.assess(queue_projection(), pr_source_snapshot=evidence)
    gate = next(x for x in result["gates"] if x["gate"] == "PR_SOURCE_DUPLICATION")
    assert gate["status"] == "PROVEN"
    assert result["controlsAdmitted"] == []

def test_incomplete_provider_snapshot_cannot_prove_absence_but_can_prove_collision() -> None:
    partial = pr_source_snapshot(pr_row(4, head="d" * 40))
    partial["coverage"]["complete"] = False
    result = pressure.pr_source_duplication_gate(partial)
    assert result["status"] == "INSUFFICIENT_EVIDENCE"
    collision = pressure.pr_source_duplication_gate(
        {**partial, "pullRequests": [pr_row(4), pr_row(5)]}
    )
    assert collision["status"] == "PROVEN"
    assert collision["evidence"]["deleteAuthority"] == "NONE"


def test_pr_observation_time_must_have_valid_offset() -> None:
    for when in ("2026-10-25T14:20:00", "yesterday", ""):
        data = pr_source_snapshot(pr_row(1))
        data["observedAt"] = when
        result = pressure.pr_source_duplication_gate(data)
        assert result["status"] == "INSUFFICIENT_EVIDENCE"
