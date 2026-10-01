from __future__ import annotations

from copy import deepcopy

import pytest

from ordivon_agent import (
    AgentCognitiveDeltaError,
    project_agent_cognitive_delta,
    project_agent_cognitive_environment,
)


def work(revision: int = 1) -> dict:
    return {
        "workRef": "work:test:delta",
        "revision": revision,
        "snapshotDigest": "sha256:" + str(revision) * 64,
        "snapshot": {
            "objective": "resume with minimal invalidation",
            "frontier": f"frontier-{revision}",
            "established": [],
            "unresolved": [],
            "constraints": [],
            "nextActions": [],
            "referenceRefs": [],
        },
    }


def observation(version: int = 1, *, owner: str = "ordivon.runtime") -> dict:
    return {
        "schemaVersion": 1,
        "kind": "ordivon.living-owner-observation",
        "subjectRef": "runtime:workspace:ws-delta",
        "ownerRef": owner,
        "observedAt": f"2026-10-01T21:0{version}:00+08:00",
        "operation": "workspace.get",
        "standing": f"standing-{version}",
        "evidenceRefs": [],
        "attributes": {"version": version},
        "sourceRevision": f"r{version}",
        "sourceDigest": "sha256:" + str(version + 1) * 64,
        "truthBoundary": "owner observation only",
    }


def test_no_change_has_empty_delta() -> None:
    value = project_agent_cognitive_environment(work(), owner_observations=[observation()])
    delta = project_agent_cognitive_delta(value, deepcopy(value))
    assert delta["hasChanges"] is False
    assert delta["changedComponents"] == []
    assert delta["invalidatedProjectionSlices"] == []
    assert delta["fullRediscoveryRequired"] is False


def test_work_revision_invalidates_only_work_semantic_slice() -> None:
    before = project_agent_cognitive_environment(work(1), owner_observations=[observation()])
    after = project_agent_cognitive_environment(work(2), owner_observations=[observation()])
    delta = project_agent_cognitive_delta(before, after)

    assert delta["invalidatedProjectionSlices"] == ["work-semantic-continuity"]
    assert delta["changedComponents"][0]["ownerRef"] == "ordivon.host"


def test_owner_observation_change_is_owner_qualified() -> None:
    before = project_agent_cognitive_environment(work(), owner_observations=[observation(1)])
    after = project_agent_cognitive_environment(work(), owner_observations=[observation(2)])
    delta = project_agent_cognitive_delta(before, after)

    assert delta["invalidatedProjectionSlices"] == [
        "owner-observation:ordivon.runtime:runtime:workspace:ws-delta"
    ]
    row = delta["changedComponents"][0]
    assert row["disposition"] == "changed"
    assert row["ownerRef"] == "ordivon.runtime"
    assert delta["authority"]["semanticImpactAuthority"] is False


def test_removed_owner_observation_is_not_guessed_current() -> None:
    before = project_agent_cognitive_environment(work(), owner_observations=[observation()])
    after = project_agent_cognitive_environment(work())
    delta = project_agent_cognitive_delta(before, after)

    row = delta["changedComponents"][0]
    assert row["disposition"] == "removed"
    assert row["currentVersion"] is None


def test_unrelated_owner_observations_remain_distinct_slices() -> None:
    runtime = observation(1)
    git = observation(1, owner="ordivon.git")
    git["subjectRef"] = "git:ordivon@main"

    before = project_agent_cognitive_environment(work(), owner_observations=[runtime, git])
    runtime2 = observation(2)
    after = project_agent_cognitive_environment(work(), owner_observations=[runtime2, git])

    delta = project_agent_cognitive_delta(before, after)
    assert len(delta["invalidatedProjectionSlices"]) == 1
    assert "ordivon.runtime" in delta["invalidatedProjectionSlices"][0]


def test_different_work_identity_is_rejected() -> None:
    before = project_agent_cognitive_environment(work())
    other = work()
    other["workRef"] = "work:other"
    after = project_agent_cognitive_environment(other)

    with pytest.raises(AgentCognitiveDeltaError, match="stable Host Work"):
        project_agent_cognitive_delta(before, after)
