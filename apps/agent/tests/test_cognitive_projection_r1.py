from __future__ import annotations

from copy import deepcopy

import pytest

from ordivon_agent.cognitive_projection_r1 import (
    AgentCognitiveProjectionError,
    project_agent_cognitive_environment,
)


def work() -> dict:
    return {
        "workRef": "work:test:1",
        "revision": 3,
        "snapshotDigest": "sha256:" + "1" * 64,
        "snapshot": {
            "objective": "orient one fresh agent",
            "frontier": "owner currentness is unresolved",
            "established": ["Host Work identity is durable semantic continuity"],
            "unresolved": ["current Runtime standing"],
            "constraints": ["projection is not authority"],
            "nextActions": ["read Runtime owner"],
            "referenceRefs": ["runtime:workspace:ws-test"],
        },
    }


def observation() -> dict:
    return {
        "schemaVersion": 1,
        "kind": "ordivon.living-owner-observation",
        "subjectRef": "runtime:workspace:ws-test",
        "ownerRef": "ordivon.runtime",
        "observedAt": "2026-10-01T21:00:00+08:00",
        "operation": "workspace.get",
        "standing": "available",
        "evidenceRefs": ["runtime:job:job-test"],
        "attributes": {"dirty": False},
        "sourceRevision": "abc123",
        "sourceDigest": "sha256:" + "2" * 64,
        "truthBoundary": "Runtime observation only",
    }


def run_view() -> dict:
    return {
        "schemaVersion": 1,
        "kind": "ordivon.agent-run-view",
        "truthRole": "derived-read-only-product-projection",
        "harnessRunId": "run-1",
        "contractDigest": "sha256:" + "3" * 64,
        "state": "running",
        "nativeStatus": "active",
        "revision": 4,
        "updatedAtMs": 1,
        "requestedModelId": "model",
        "caller": {"callerId": "caller", "callerRunRef": "work:test:1"},
        "recovery": {},
        "composition": {},
        "semanticAcceptance": {
            "establishedByHarness": False,
            "state": "not-established",
        },
        "externalLiveness": "not-probed",
        "proofBoundary": "derived run view only",
    }


def reentry() -> dict:
    return {
        "schemaVersion": 1,
        "kind": "ordivon.agent-cross-owner-reentry-projection",
        "truthRole": "derived-read-only-cross-owner-navigation-projection",
        "work": {"workRef": "work:test:1", "revision": 3},
        "harness": {
            "harnessRunId": "run-1",
            "runRevision": 4,
            "callerId": "caller",
            "callerRunRef": "work:test:1",
            "referenceRef": "harness:run:run-1",
        },
        "continuation": {
            "action": "continue-existing-run",
            "responseRehydrationRequired": False,
            "effectRedispatchAllowed": False,
        },
        "references": {
            "all": ["harness:run:run-1", "runtime:workspace:ws-test"],
            "runtime": ["runtime:workspace:ws-test"],
            "other": [],
        },
        "physicalRevalidationRequired": True,
        "proofBoundary": "navigation only",
    }


def test_projection_is_derived_and_owner_qualified() -> None:
    value = project_agent_cognitive_environment(
        work(),
        owner_observations=[observation()],
        agent_run_view=run_view(),
        cross_owner_reentry=reentry(),
    )

    assert value["kind"] == "ordivon.agent-cognitive-projection"
    assert value["truthRole"] == "derived-read-only-agent-cognitive-projection"
    assert value["authority"] == {
        "effectAuthority": False,
        "executionAuthority": False,
        "semanticAcceptanceAuthority": False,
        "domainTruthAuthority": False,
    }
    assert value["work"]["frontier"] == "owner currentness is unresolved"
    assert value["ownerObservations"][0]["ownerRef"] == "ordivon.runtime"
    assert [row["ownerRef"] for row in value["versionVector"]] == [
        "ordivon.harness",
        "ordivon.host",
        "ordivon.runtime",
    ]
    assert value["currentness"]["presentTenseClaimsRequireOwnerReadback"] is True
    assert value["projectionDigest"].startswith("sha256:")


def test_projection_is_deterministic_across_owner_observation_order() -> None:
    second = observation()
    second["ownerRef"] = "ordivon.git"
    second["subjectRef"] = "git:ordivon@main"
    second["operation"] = "git.rev-parse"
    second["standing"] = "85a1863d"
    second["evidenceRefs"] = []

    a = project_agent_cognitive_environment(work(), owner_observations=[observation(), second])
    b = project_agent_cognitive_environment(work(), owner_observations=[second, observation()])
    assert a["versionVector"] == b["versionVector"]
    # Output observation order stays caller-provided on purpose; digest therefore differs.
    # The current contract makes no set-order canonicalization claim for displayed evidence.


def test_duplicate_owner_subject_current_observation_is_rejected() -> None:
    with pytest.raises(AgentCognitiveProjectionError, match="at most one current observation"):
        project_agent_cognitive_environment(
            work(), owner_observations=[observation(), observation()]
        )


def test_work_snapshot_is_not_promoted_to_present_tense_truth() -> None:
    value = project_agent_cognitive_environment(work())
    assert value["ownerObservations"] == []
    assert value["currentness"]["missingOwnerObservationMeansUnknown"] is True
    assert "not automatically present-tense" in value["work"]["truthBoundary"]


def test_reentry_can_never_authorize_effect_redispatch() -> None:
    bad = reentry()
    bad["continuation"]["effectRedispatchAllowed"] = True
    with pytest.raises(AgentCognitiveProjectionError, match="must never authorize"):
        project_agent_cognitive_environment(work(), cross_owner_reentry=bad)


def test_reentry_must_match_work_identity() -> None:
    bad = reentry()
    bad["work"]["workRef"] = "work:other"
    with pytest.raises(AgentCognitiveProjectionError, match="different Host Work"):
        project_agent_cognitive_environment(work(), cross_owner_reentry=bad)


def test_harness_cannot_claim_semantic_acceptance() -> None:
    bad = run_view()
    bad["semanticAcceptance"]["establishedByHarness"] = True
    with pytest.raises(AgentCognitiveProjectionError, match="semantic acceptance"):
        project_agent_cognitive_environment(work(), agent_run_view=bad)


def test_projection_does_not_mutate_inputs() -> None:
    w = work()
    o = observation()
    before_w = deepcopy(w)
    before_o = deepcopy(o)
    project_agent_cognitive_environment(w, owner_observations=[o])
    assert w == before_w
    assert o == before_o
