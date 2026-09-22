from __future__ import annotations

import io

import pytest

from scripts.experimental_episode_r1 import (
    EpisodeProjectionError,
    backfill,
    project_r5c_record,
    validate_episode,
)


def h(char: str) -> str:
    return "sha256:" + char * 64


def record(execution_id: str = "execution-1") -> dict:
    return {
        "run": {
            "execution_id": execution_id,
            "legacy_attempt_id": f"attempt:{execution_id}",
            "principal": "agent",
            "idempotency_key": f"idem:{execution_id}",
            "request_digest": "runtime-request-v1:" + h("1"),
            "operation_digest": h("2"),
            "workspace_id": "workspace-1",
            "workspace_snapshot": {
                "private": "must-not-escape",
                "sourceRevision": "abc",
            },
            "execution_plan": {
                "argv": ["secret-ish", "payload"],
                "environment": {"API_TOKEN": "must-not-escape"},
            },
            "execution_plan_digest": h("3"),
            "desired_state": "run",
            "resolution": "succeeded",
            "execution_state": "succeeded",
            "termination_intent": "natural",
            "launch_token_digest": h("4"),
            "bundle_path": "/private/runtime/path",
            "bundle_digest": h("5"),
            "boot_id": "boot-1",
            "unit_name": "unit-1",
            "invocation_id": "invoke-1",
            "control_group": "/cg",
            "main_pid": 123,
            "process_start_identity": "proc",
            "runner_start_digest": h("6"),
            "result_digest": h("7"),
            "exit_code": 0,
            "infrastructure_error_digest": None,
            "reservation_id": "reservation-1",
            "concurrency_limit": 2,
            "reservation_state": "released",
            "reservation_acquired_at": "2026-09-07T00:00:00+00:00",
            "reservation_released_at": "2026-09-07T00:00:02+00:00",
            "reservation_release_reason": "finished",
            "recovery_required": False,
            "recovery_reason_code": "none",
            "recovery_evidence_digest": h("8"),
            "recovery_observed_at": "2026-09-07T00:00:02+00:00",
            "created_at": "2026-09-07T00:00:00+00:00",
            "started_at": "2026-09-07T00:00:01+00:00",
            "finished_at": "2026-09-07T00:00:02+00:00",
            "execution_version": 4,
            "job_version": 2,
        },
        "events": [
            {
                "event_id": "event-1",
                "execution_id": execution_id,
                "legacy_attempt_id": f"attempt:{execution_id}",
                "sequence": 1,
                "event_type": "accepted",
                "origin": "runtime",
                "previous_state": None,
                "new_state": "accepted",
                "reason_code": "accepted",
                "data_digest": h("9"),
                "observed_at": "2026-09-07T00:00:00+00:00",
            },
            {
                "event_id": "event-2",
                "execution_id": execution_id,
                "legacy_attempt_id": f"attempt:{execution_id}",
                "sequence": 2,
                "event_type": "finished",
                "origin": "runtime",
                "previous_state": "running",
                "new_state": "succeeded",
                "reason_code": "exit-zero",
                "data_digest": h("a"),
                "observed_at": "2026-09-07T00:00:02+00:00",
            },
        ],
        "artifacts": [
            {
                "artifact_id": "artifact-1",
                "execution_id": execution_id,
                "legacy_attempt_id": f"attempt:{execution_id}",
                "kind": "stdout",
                "relative_path": "stdout.txt",
                "digest": h("b"),
                "media_type": "text/plain",
                "byte_length": 1234,
                "truncated": False,
                "created_at": "2026-09-07T00:00:02+00:00",
            }
        ],
    }


def test_r5_projection_is_deterministic_and_schema_valid() -> None:
    first = project_r5c_record(record())
    second = project_r5c_record(record())
    assert first == second
    validate_episode(first)
    assert first["episodeId"] == "episode:runtime-r5c:execution-1"
    assert first["evidenceSets"]["events"]["count"] == 2
    assert first["evidenceSets"]["artifacts"]["count"] == 1
    assert first["costObservations"]["artifactBytes"] == 1234


def test_episode_identity_is_stable_while_projection_digest_changes() -> None:
    before = project_r5c_record(record())
    changed = record()
    changed["artifacts"][0]["byte_length"] = 1235
    after = project_r5c_record(changed)
    assert before["episodeId"] == after["episodeId"]
    assert before["projectionDigest"] != after["projectionDigest"]


def test_sensitive_runtime_payloads_do_not_escape_projection() -> None:
    projected = project_r5c_record(record())
    serialized = repr(projected)
    assert "must-not-escape" not in serialized
    assert "secret-ish" not in serialized
    assert "workspace_snapshot" not in serialized
    assert "execution_plan" not in serialized
    assert "launch_token_digest" not in serialized


def test_raw_source_payload_still_changes_source_record_digest() -> None:
    before = project_r5c_record(record())
    changed = record()
    changed["run"]["workspace_snapshot"]["sourceRevision"] = "def"
    after = project_r5c_record(changed)
    assert before["episodeId"] == after["episodeId"]
    assert (
        before["anchor"]["sourceRecordDigest"] != after["anchor"]["sourceRecordDigest"]
    )


def test_cross_execution_event_and_artifact_fail_closed() -> None:
    bad_event = record()
    bad_event["events"][0]["execution_id"] = "other"
    with pytest.raises(EpisodeProjectionError, match="another execution"):
        project_r5c_record(bad_event)

    bad_artifact = record()
    bad_artifact["artifacts"][0]["execution_id"] = "other"
    with pytest.raises(EpisodeProjectionError, match="another execution"):
        project_r5c_record(bad_artifact)


def test_duplicate_event_sequence_fails_closed() -> None:
    bad = record()
    bad["events"][1]["sequence"] = 1
    with pytest.raises(EpisodeProjectionError, match="duplicate event sequence"):
        project_r5c_record(bad)


def test_bad_digest_and_negative_artifact_size_fail_closed() -> None:
    bad_digest = record()
    bad_digest["run"]["operation_digest"] = "not-a-digest"
    with pytest.raises(EpisodeProjectionError, match="SHA-256"):
        project_r5c_record(bad_digest)

    negative = record()
    negative["artifacts"][0]["byte_length"] = -1
    with pytest.raises(EpisodeProjectionError, match="negative"):
        project_r5c_record(negative)


def test_projection_digest_tampering_fails_closed() -> None:
    projected = project_r5c_record(record())
    projected["projectionDigest"] = h("c")
    with pytest.raises(EpisodeProjectionError, match="projectionDigest"):
        validate_episode(projected)


def test_backfill_reports_exact_cardinality_and_distributions() -> None:
    first = record("execution-1")
    second = record("execution-2")
    second["run"]["resolution"] = "failed"
    second["run"]["execution_state"] = "failed"
    sink = io.StringIO()
    summary = backfill([first, second], sink)
    assert summary["sourceRuns"] == 2
    assert summary["projectedEpisodes"] == 2
    assert summary["episodeIdentityCollisions"] == 0
    assert summary["eventRowsBound"] == 4
    assert summary["artifactRowsBound"] == 2
    assert summary["executionStateDistribution"] == {"failed": 1, "succeeded": 1}
    assert summary["resolutionDistribution"] == {"failed": 1, "succeeded": 1}
    assert summary["standing"] == "PASS_EXACT_ONE_EPISODE_PER_SOURCE_RUN"
    assert len(sink.getvalue().splitlines()) == 2


def test_repeated_source_execution_identity_is_reported_as_collision() -> None:
    summary = backfill([record(), record()])
    assert summary["sourceRuns"] == 2
    assert summary["projectedEpisodes"] == 2
    assert summary["episodeIdentityCollisions"] == 1
    assert summary["standing"] == "FAIL_IDENTITY_OR_CARDINALITY"
