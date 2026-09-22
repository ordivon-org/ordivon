from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest

from scripts.social_fabric_r1 import SocialFabricError, compile_projection

ROOT = Path(__file__).resolve().parents[1]
DOGFOOD = ROOT / "evidence/acceptance/social-fabric-r1-dogfood-cut-20260923.json"


def _snapshot() -> dict:
    return {
        "schemaVersion": 1,
        "kind": "ordivon.social-fabric-owner-cut",
        "observedAt": "2026-09-23T02:57:00+08:00",
        "host": {
            "tasks": [
                {
                    "taskId": "task:test",
                    "goalId": "goal:test",
                    "revision": 2,
                    "state": "open",
                    "checkpointDigest": "sha256:" + "1" * 64,
                    "runtime": {
                        "workspaceId": "ws-test",
                        "relevantJobIds": ["job-test"],
                        "observedHeadRevision": "old-head",
                    },
                    "implementationCommitRef": "candidate-commit",
                }
            ]
        },
        "runtime": {
            "workspaces": [
                {
                    "workspaceId": "ws-test",
                    "sourceRepo": "/repo",
                    "sourceRevision": "base",
                    "currentHeadRevision": "new-head",
                    "dirty": True,
                },
                {
                    "workspaceId": "ws-unreferenced",
                    "sourceRepo": "/repo",
                    "sourceRevision": "base",
                    "currentHeadRevision": "other-head",
                    "dirty": False,
                },
            ],
            "closedWorkspaces": [],
        },
        "git": {
            "mainRevision": "main-head",
            "knownAncestorOfMain": {"candidate-commit": True},
        },
        "gateway": {
            "capabilities": [
                {"capability": "continuity.external", "available": True},
                {"capability": "execution.linux", "available": False},
            ]
        },
    }


def test_projection_is_deterministic_and_keeps_truth_boundaries() -> None:
    first = compile_projection(_snapshot())
    second = compile_projection(copy.deepcopy(_snapshot()))
    assert first == second
    assert first["truthRole"] == "rebuildable-cross-owner-projection"
    assert first["sourceSnapshotDigest"].startswith("sha256:")
    assert first["commonOperatingPicture"]["linkedTaskCount"] == 1
    assert first["commonOperatingPicture"]["availableCapabilities"] == [
        "continuity.external"
    ]
    assert first["nonClaims"]


def test_head_drift_and_merged_open_task_are_detected_without_mutation() -> None:
    result = compile_projection(_snapshot())
    codes = {row["code"] for row in result["reconciliation"]["findings"]}
    assert "CHECKPOINT_WORKSPACE_HEAD_DRIFT" in codes
    assert "MERGED_IMPLEMENTATION_TASK_OPEN" in codes
    assert "WORKSPACE_WITHOUT_SELECTED_TASK_REFERENCE" in codes


def test_closed_workspace_reference_is_distinct_from_unknown_absence() -> None:
    snapshot = _snapshot()
    snapshot["runtime"]["workspaces"] = []
    snapshot["runtime"]["closedWorkspaces"] = [
        {"workspaceId": "ws-test", "standing": "CLOSED"}
    ]
    result = compile_projection(snapshot)
    codes = {row["code"] for row in result["reconciliation"]["findings"]}
    assert "TASK_REFERENCES_CLOSED_WORKSPACE" in codes
    assert "TASK_WORKSPACE_MISSING_FROM_CUT" not in codes


def test_missing_workspace_is_not_silently_treated_as_closed() -> None:
    snapshot = _snapshot()
    snapshot["runtime"]["workspaces"] = []
    snapshot["runtime"]["closedWorkspaces"] = []
    result = compile_projection(snapshot)
    codes = {row["code"] for row in result["reconciliation"]["findings"]}
    assert "TASK_WORKSPACE_MISSING_FROM_CUT" in codes


def test_completed_task_with_dirty_workspace_is_attention_not_domain_failure() -> None:
    snapshot = _snapshot()
    snapshot["host"]["tasks"][0]["state"] = "completed"
    result = compile_projection(snapshot)
    finding = next(
        row
        for row in result["reconciliation"]["findings"]
        if row["code"] == "COMPLETED_TASK_DIRTY_WORKSPACE"
    )
    assert finding["severity"] == "warning"
    assert "domain verdict" in finding["truthBoundary"]


def test_duplicate_owner_identity_fails_closed() -> None:
    snapshot = _snapshot()
    snapshot["runtime"]["workspaces"].append(
        copy.deepcopy(snapshot["runtime"]["workspaces"][0])
    )
    with pytest.raises(
        SocialFabricError, match="duplicate runtime.workspaces identity"
    ):
        compile_projection(snapshot)


def test_unknown_git_ancestry_does_not_invent_merge() -> None:
    snapshot = _snapshot()
    snapshot["git"]["knownAncestorOfMain"] = {}
    result = compile_projection(snapshot)
    codes = {row["code"] for row in result["reconciliation"]["findings"]}
    assert "MERGED_IMPLEMENTATION_TASK_OPEN" not in codes


def test_real_local_dogfood_cut_exposes_checkpoint_workspace_drift() -> None:
    snapshot = json.loads(DOGFOOD.read_text(encoding="utf-8"))
    result = compile_projection(snapshot)
    codes = [row["code"] for row in result["reconciliation"]["findings"]]
    assert result["commonOperatingPicture"]["selectedTaskCount"] == 5
    assert result["commonOperatingPicture"]["selectedWorkspaceCount"] == 4
    assert result["commonOperatingPicture"]["linkedTaskCount"] == 4
    assert result["commonOperatingPicture"]["closedWorkspaceReferenceCount"] == 1
    assert codes.count("CHECKPOINT_WORKSPACE_HEAD_DRIFT") >= 2
    assert "TASK_REFERENCES_CLOSED_WORKSPACE" in codes
