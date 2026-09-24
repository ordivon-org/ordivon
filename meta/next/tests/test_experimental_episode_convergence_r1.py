from __future__ import annotations

from scripts.experimental_episode_convergence_r1 import (
    CI_PROFILE,
    OWNER_COST_PROFILE,
    QUEUE_PROFILE,
    project_ci_run,
    project_convergence,
    project_owner_cost_corpus,
    project_owner_cost_episode,
    project_queue_episode,
)
from scripts.experimental_episode_r1 import validate_episode


def queue_projection() -> dict:
    return {
        "schemaVersion": 2,
        "kind": "ordivon.queue-observation-projection",
        "authority": {"queue": "GitHub Merge Queue"},
        "coverage": {"repository": "o/r"},
        "episodes": [
            {
                "schemaVersion": 1,
                "kind": "ordivon.queue-episode",
                "provider": "github",
                "repository": "o/r",
                "pr": 30,
                "prHeadSha": "a" * 40,
                "enqueueTimes": ["2026-09-23T00:00:00Z"],
                "removalTimes": ["2026-09-23T00:01:00Z"],
                "mergedAt": "2026-09-23T00:01:00Z",
                "mergeGroupRuns": [
                    {
                        "runId": 300,
                        "sha": "b" * 40,
                        "createdAt": "2026-09-23T00:00:18Z",
                        "status": "completed",
                        "conclusion": "success",
                        "requiredVerification": None,
                    }
                ],
            }
        ],
        "episodeMetrics": [
            {
                "pr": 30,
                "mergeGroupRuns": 1,
                "requeues": 0,
                "mergeGroupConclusion": "success",
                "queueDispatchSeconds": 18.0,
                "queueResidenceSeconds": 60.0,
                "endToEndQueueSeconds": 60.0,
                "runnerWaitSeconds": 3.0,
                "verificationSeconds": 40.0,
                "postVerificationMergeSeconds": 17.0,
            }
        ],
        "metrics": {},
    }


def ci_projection() -> dict:
    return {
        "schemaVersion": 1,
        "kind": "ordivon.ci-observation-projection",
        "coverage": {"repository": "o/r", "runs": 1},
        "runs": [
            {
                "schemaVersion": 1,
                "kind": "ordivon.ci-run-observation",
                "provider": "github",
                "repository": "o/r",
                "runId": 900,
                "workflowId": 1,
                "workflowName": "Monorepo Required",
                "event": "pull_request",
                "headSha": "c" * 40,
                "headBranch": "agent/x",
                "runAttempt": 1,
                "status": "completed",
                "conclusion": "cancelled",
                "createdAt": "2026-09-23T00:00:00Z",
                "startedAt": "2026-09-23T00:00:02Z",
                "updatedAt": "2026-09-23T00:00:52Z",
                "wallSeconds": 52.0,
                "terminationReason": "CANCELLED",
                "economicOutcome": "UNCLASSIFIED",
                "economicReason": "provider conclusion alone is insufficient",
                "jobs": [
                    {
                        "jobId": 901,
                        "name": "root-verification",
                        "status": "completed",
                        "conclusion": "cancelled",
                        "createdAt": "2026-09-23T00:00:01Z",
                        "startedAt": "2026-09-23T00:00:03Z",
                        "completedAt": "2026-09-23T00:00:50Z",
                        "runnerWaitSeconds": 2.0,
                        "executionSeconds": 47.0,
                        "steps": [
                            {
                                "number": 7,
                                "name": "Verify affected owners",
                                "status": "completed",
                                "conclusion": "success",
                                "startedAt": "2026-09-23T00:00:10Z",
                                "completedAt": "2026-09-23T00:00:40Z",
                                "durationSeconds": 30.0,
                            }
                        ],
                    }
                ],
            }
        ],
        "metrics": {},
    }


def owner_cost_corpus() -> dict:
    return {
        "schemaVersion": 1,
        "kind": "ordivon.convergence-owner-cost-episode-corpus",
        "truthRole": "measured-owner-qualification-cost-evidence-not-scheduling-policy",
        "episodes": [
            {
                "schemaVersion": 1,
                "kind": "ordivon.convergence-owner-cost-episode",
                "candidateSha": "d" * 40,
                "providerBaseSha": "e" * 40,
                "queueClass": "SCOPED",
                "changedPaths": ["services/runtime/a.rs"],
                "changedPathCount": 1,
                "directOwners": ["runtime"],
                "verificationOwners": ["runtime"],
                "ownerFanout": 1,
                "owner": "runtime",
                "verifyTask": "runtime:verify",
                "runnerWaitSeconds": 0.5,
                "setupSeconds": None,
                "buildSeconds": None,
                "testSeconds": None,
                "totalSeconds": 345.187,
                "result": "PASS",
                "evidenceRefs": ["runtime:job-1", "candidate:" + "d" * 40],
                "observationTimestamp": "2026-09-23T21:26:06.144Z",
            }
        ],
        "summary": {"candidateCount": 1, "episodeCount": 1},
    }


def test_queue_projection_reuses_shared_episode_contract() -> None:
    episode = project_queue_episode(
        queue_projection(), queue_projection()["episodes"][0]
    )
    validate_episode(episode)
    assert episode["profileId"] == QUEUE_PROFILE
    assert episode["episodeId"] == "episode:convergence-queue:o/r:pr:30"
    measures = {row["name"]: row["value"] for row in episode["measures"]}
    assert measures["queue.dispatch_seconds"] == 18.0
    assert measures["queue.verification_seconds"] == 40.0
    assert all("token" not in repr(row).lower() for row in episode["dimensions"])


def test_ci_projection_separates_termination_from_economic_outcome() -> None:
    episode = project_ci_run(ci_projection(), ci_projection()["runs"][0])
    validate_episode(episode)
    assert episode["profileId"] == CI_PROFILE
    dimensions = {row["name"]: row["value"] for row in episode["dimensions"]}
    assert dimensions["ci.termination_reason"] == "CANCELLED"
    assert dimensions["ci.economic_outcome"] == "UNCLASSIFIED"
    measures = {row["name"]: row["value"] for row in episode["measures"]}
    assert measures["ci.root_verification.execution_seconds"] == 47.0
    assert measures["ci.root_verification.step.verify_affected_owners.seconds"] == 30.0


def test_episode_identity_is_stable_but_projection_digest_tracks_change() -> None:
    before = project_ci_run(ci_projection(), ci_projection()["runs"][0])
    changed_projection = ci_projection()
    changed_projection["runs"][0]["economicOutcome"] = "AVOIDABLE_WASTE"
    after = project_ci_run(changed_projection, changed_projection["runs"][0])
    assert before["episodeId"] == after["episodeId"]
    assert before["projectionDigest"] != after["projectionDigest"]
    assert (
        before["anchor"]["sourceRecordDigest"] != after["anchor"]["sourceRecordDigest"]
    )


def test_bundle_is_deterministic_and_keeps_profiles_separate() -> None:
    first = project_convergence(queue_projection(), ci_projection())
    second = project_convergence(queue_projection(), ci_projection())
    assert first == second
    queue_rows, ci_rows, summary = first
    assert len(queue_rows) == 1
    assert len(ci_rows) == 1
    assert summary["episodeIdentityCollisions"] == 0
    assert summary["queueProfileId"] == QUEUE_PROFILE
    assert summary["ciProfileId"] == CI_PROFILE
    assert summary["standing"] == "PASS_CONVERGENCE_EPISODE_PROJECTION"


def test_queue_and_ci_repository_must_match() -> None:
    ci = ci_projection()
    ci["coverage"]["repository"] = "other/r"
    try:
        project_convergence(queue_projection(), ci)
    except ValueError as exc:
        assert "same repository" in str(exc)
    else:
        raise AssertionError("repository mismatch must fail closed")


def test_owner_cost_projection_reuses_shared_episode_contract() -> None:
    source = owner_cost_corpus()["episodes"][0]
    episode = project_owner_cost_episode(source)
    validate_episode(episode)
    assert episode["profileId"] == OWNER_COST_PROFILE
    assert episode["anchor"]["objectId"] == "d" * 40
    dimensions = {row["name"]: row["value"] for row in episode["dimensions"]}
    assert dimensions["owner_cost.queue_class"] == "SCOPED"
    assert dimensions["owner_cost.owner_fanout"] == 1
    measures = {row["name"]: row["value"] for row in episode["measures"]}
    assert measures["owner_cost.runner_wait_seconds"] == 0.5
    assert measures["owner_cost.total_seconds"] == 345.187
    assert "owner_cost.setup_seconds" not in measures
    assert any("setup phase attribution" in item for item in episode["unresolved"])


def test_owner_cost_corpus_is_deterministic_and_collision_free() -> None:
    first = project_owner_cost_corpus(owner_cost_corpus())
    second = project_owner_cost_corpus(owner_cost_corpus())
    assert first == second
    rows, summary = first
    assert len(rows) == 1
    assert summary["profileId"] == OWNER_COST_PROFILE
    assert summary["episodes"] == 1
    assert summary["candidates"] == 1
    assert summary["episodeIdentityCollisions"] == 0
    assert summary["standing"] == "PASS_OWNER_COST_EPISODE_PROJECTION"


def test_owner_cost_episode_identity_tracks_measurement_identity_not_enrichment() -> (
    None
):
    before_source = owner_cost_corpus()["episodes"][0]
    before = project_owner_cost_episode(before_source)
    enriched_source = owner_cost_corpus()["episodes"][0]
    enriched_source["buildSeconds"] = 100.0
    after = project_owner_cost_episode(enriched_source)
    assert before["episodeId"] == after["episodeId"]
    assert before["projectionDigest"] != after["projectionDigest"]
