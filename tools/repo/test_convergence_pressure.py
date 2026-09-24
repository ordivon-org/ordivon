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
