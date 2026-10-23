from __future__ import annotations

from scripts.experimental_episode_harness_r1 import (
    backfill_harness_rsi,
    project_harness_rsi_record,
)
from scripts.experimental_episode_r1 import validate_episode


def receipt(name: str = "p5") -> dict:
    return {
        "schemaVersion": 1,
        "kind": f"ordivon.harness-rsi-{name}-acceptance",
        "status": "accepted",
        "baseRevision": "a" * 40,
        "implementationRevision": "b" * 40,
        "researchOutcome": "bounded-improvement",
        "modelId": "deepseek-v4-flash",
        "acceptedDiscovery": {
            "runtimeJobId": "job-01-test",
            "observationCount": 8,
            "p4ObservationBaseline": 203,
            "observationReductionFactor": 25.375,
        },
        "providerCost": {
            "measurementRuntimeJobId": "job-02-test",
            "completedProviderCalls": 12,
            "totalTokens": 239953,
        },
    }


def test_harness_receipt_projects_into_shared_episode_core() -> None:
    episode = project_harness_rsi_record(
        receipt(), source_name="harness-rsi-p5-fixture.json"
    )
    validate_episode(episode)
    assert episode["profileId"] == "harness-rsi-acceptance-v1"
    assert episode["episodeId"] == "episode:harness-rsi:harness-rsi-p5-fixture"
    refs = {
        row["objectId"] for row in episode["ownerRefs"] if row["ownerId"] == "runtime"
    }
    assert refs == {"job-01-test", "job-02-test"}
    measures = {row["name"]: row["value"] for row in episode["measures"]}
    assert measures["harness.acceptedDiscovery.observationCount"] == 8
    assert measures["harness.providerCost.totalTokens"] == 239953


def test_harness_projection_does_not_copy_scope_or_nested_receipt_payload() -> None:
    source = receipt()
    source["scope"] = "long source prose that should remain in owner evidence"
    source["acceptedDiscovery"]["privatePayload"] = {"secret": "do-not-copy"}
    episode = project_harness_rsi_record(
        source, source_name="harness-rsi-p5-fixture.json"
    )
    serialized = repr(episode)
    assert "long source prose" not in serialized
    assert "do-not-copy" not in serialized


def test_harness_episode_identity_stays_stable_when_receipt_changes() -> None:
    before = project_harness_rsi_record(
        receipt(), source_name="harness-rsi-p5-fixture.json"
    )
    changed = receipt()
    changed["acceptedDiscovery"]["observationCount"] = 9
    after = project_harness_rsi_record(
        changed, source_name="harness-rsi-p5-fixture.json"
    )
    assert before["episodeId"] == after["episodeId"]
    assert before["projectionDigest"] != after["projectionDigest"]
    assert (
        before["anchor"]["sourceRecordDigest"] != after["anchor"]["sourceRecordDigest"]
    )


def test_harness_backfill_detects_unique_episode_identities() -> None:
    first = receipt("p4")
    second = receipt("p5")
    episodes, summary = backfill_harness_rsi(
        [
            ("harness-rsi-p4.json", first),
            ("harness-rsi-p5.json", second),
        ]
    )
    assert len(episodes) == 2
    assert summary["projectedEpisodes"] == 2
    assert summary["episodeIdentityCollisions"] == 0
    assert summary["citedRuntimeJobCount"] == 2
    assert summary["standing"] == "PASS_HARNESS_RSI_EPISODE_PROJECTION"
