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
