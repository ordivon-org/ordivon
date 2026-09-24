from __future__ import annotations

import os
from uuid import uuid4

import pytest

from ordivon_host_v2 import CheckpointInput, HostV2
from ordivon_host_v2.board import BoardStore
from ordivon_host_v2.canonical import canonical_digest
from ordivon_host_v2.legacy_cutover import (
    apply_cutover_plan,
    compile_cutover_plan,
    extract_legacy_snapshot,
)

DSN = os.environ.get("ORDIVON_HOST_V2_TEST_DSN")


def _sealed(body: dict) -> dict:
    value = dict(body)
    value["snapshotDigest"] = canonical_digest(value)
    return value


def test_cutover_compiler_preserves_work_history_but_does_not_infer_social_structure() -> None:
    snapshot = _sealed(
        {
            "schemaVersion": 1,
            "kind": "ordivon.host-legacy-collaboration-snapshot-r1",
            "sourceSchemaVersion": 8,
            "tasks": [
                {
                    "task_id": "task:open",
                    "goal_id": "goal:x",
                    "revision": 2,
                    "state": "open",
                    "current_checkpoint_digest": "sha256:old2",
                    "created_at": "2026-01-01T00:00:00+00:00",
                    "updated_at": "2026-01-02T00:00:00+00:00",
                },
                {
                    "task_id": "task:closed",
                    "goal_id": None,
                    "revision": 1,
                    "state": "completed",
                    "current_checkpoint_digest": "sha256:closed",
                    "created_at": "2026-01-01T00:00:00+00:00",
                    "updated_at": "2026-01-01T00:00:00+00:00",
                },
            ],
            "checkpoints": [
                {
                    "task_id": "task:open",
                    "revision": 1,
                    "checkpoint_digest": "sha256:old1",
                    "payload": {"objective": "o", "frontier": "f1"},
                    "writer_label": "agent-a",
                    "created_at": "2026-01-01T00:00:00+00:00",
                },
                {
                    "task_id": "task:open",
                    "revision": 2,
                    "checkpoint_digest": "sha256:old2",
                    "payload": {
                        "objective": "o",
                        "frontier": "f2",
                        "unresolved": ["u"],
                        "runtime": {
                            "workspaceId": "ws:x",
                            "relevantJobIds": ["job:x"],
                            "observedHeadRevision": "abc",
                        },
                    },
                    "writer_label": "agent-b",
                    "created_at": "2026-01-02T00:00:00+00:00",
                },
                {
                    "task_id": "task:closed",
                    "revision": 1,
                    "checkpoint_digest": "sha256:closed",
                    "payload": {},
                    "writer_label": None,
                    "created_at": "2026-01-01T00:00:00+00:00",
                },
            ],
            "taskEvents": [],
            "boardMessages": [
                {
                    "sequence": 1,
                    "client_message_id": "m1",
                    "author_label": "agent-a",
                    "message_kind": "note",
                    "topic": "analysis",
                    "message": "first",
                    "reply_to_client_message_id": None,
                    "task_id": "task:open",
                    "message_digest": "sha256:m1",
                    "recorded_at_ms": 1,
                    "created_at": "2026-01-02T00:00:00+00:00",
                },
                {
                    "sequence": 2,
                    "client_message_id": "m2",
                    "author_label": "agent-b",
                    "message_kind": "reply",
                    "topic": "analysis",
                    "message": "reply",
                    "reply_to_client_message_id": "m1",
                    "task_id": "task:open",
                    "message_digest": "sha256:m2",
                    "recorded_at_ms": 2,
                    "created_at": "2026-01-02T00:00:01+00:00",
                },
                {
                    "sequence": 3,
                    "client_message_id": "global",
                    "author_label": "agent-a",
                    "message_kind": "warning",
                    "topic": "global",
                    "message": "archive only",
                    "reply_to_client_message_id": None,
                    "task_id": None,
                    "message_digest": "sha256:g",
                    "recorded_at_ms": 3,
                    "created_at": "2026-01-02T00:00:02+00:00",
                },
                {
                    "sequence": 4,
                    "client_message_id": "closed-msg",
                    "author_label": "agent-a",
                    "message_kind": "note",
                    "topic": "done",
                    "message": "archive closed",
                    "reply_to_client_message_id": None,
                    "task_id": "task:closed",
                    "message_digest": "sha256:c",
                    "recorded_at_ms": 4,
                    "created_at": "2026-01-02T00:00:03+00:00",
                },
                {
                    "sequence": 5,
                    "client_message_id": "task-route-anchor-v1:open",
                    "author_label": "task-routing-anchor-v1",
                    "message_kind": "note",
                    "topic": "agent-native-collaboration-routing",
                    "message": "synthetic",
                    "reply_to_client_message_id": None,
                    "task_id": "task:open",
                    "message_digest": "sha256:a",
                    "recorded_at_ms": 5,
                    "created_at": "2026-01-02T00:00:04+00:00",
                },
            ],
            "mechanicalCounts": {"commandReceiptCount": 0},
            "truthBoundary": "legacy",
        }
    )
    plan = compile_cutover_plan(snapshot, active_task_ids={"task:open"})
    assert len(plan["works"]) == 2
    assert len(plan["workSnapshots"]) == 3
    assert plan["workRelations"] == []
    assert plan["participations"] == []
    assert plan["coordinationIntents"] == []
    assert plan["subscriptions"] == []
    assert plan["selection"] == {
        "legacyTaskCount": 2,
        "legacyCheckpointCount": 3,
        "legacyBoardMessageCount": 5,
        "explicitActiveTaskSelectionCount": 1,
        "activeTaskLinkedBoardMessagesImported": 2,
        "boardMessagesArchiveOnly": 3,
        "syntheticRouteAnchorsImported": 0,
    }
    assert len(plan["spaces"]) == 1
    assert len(plan["topics"]) == 1
    assert len(plan["messages"]) == 2
    assert plan["messages"][1]["messageKind"] == "note"
    assert len(plan["messageRelations"]) == 1
    assert plan["messageRelations"][0]["relation"] == "reply_to"
    assert all(row["actorKind"] in {"unknown", "service"} for row in plan["actors"])
    rev2 = next(row for row in plan["workSnapshots"] if row["revision"] == 2)
    assert "runtime:workspace:ws:x" in rev2["payload"]["referenceRefs"]
    assert "runtime:job:job:x" in rev2["payload"]["referenceRefs"]
    assert "git:observed-revision:abc" in rev2["payload"]["referenceRefs"]


def test_cutover_default_does_not_infer_active_social_graph_from_open_state() -> None:
    snapshot = _sealed(
        {
            "schemaVersion": 1,
            "kind": "ordivon.host-legacy-collaboration-snapshot-r1",
            "sourceSchemaVersion": 5,
            "tasks": [
                {
                    "task_id": "task:open-only",
                    "goal_id": None,
                    "revision": 1,
                    "state": "open",
                    "current_checkpoint_digest": "sha256:c",
                    "created_at": "2026-01-01T00:00:00+00:00",
                    "updated_at": "2026-01-01T00:00:00+00:00",
                }
            ],
            "checkpoints": [
                {
                    "task_id": "task:open-only",
                    "revision": 1,
                    "checkpoint_digest": "sha256:c",
                    "payload": {"objective": "o", "frontier": "f"},
                    "writer_label": "a",
                    "created_at": "2026-01-01T00:00:00+00:00",
                }
            ],
            "taskEvents": [],
            "boardMessages": [
                {
                    "sequence": 1,
                    "client_message_id": "m",
                    "author_label": "a",
                    "message_kind": "note",
                    "topic": "t",
                    "message": "do not infer active",
                    "reply_to_client_message_id": None,
                    "task_id": "task:open-only",
                    "message_digest": "sha256:m",
                    "recorded_at_ms": 1,
                    "created_at": "2026-01-01T00:00:00+00:00",
                }
            ],
            "mechanicalCounts": {},
            "truthBoundary": "legacy",
        }
    )
    plan = compile_cutover_plan(snapshot)
    assert plan["selection"]["explicitActiveTaskSelectionCount"] == 0
    assert plan["selection"]["activeTaskLinkedBoardMessagesImported"] == 0
    assert plan["messages"] == []
    assert plan["spaces"] == []
    assert plan["topics"] == []


def test_cutover_rejects_tampered_snapshot() -> None:
    snapshot = _sealed(
        {
            "schemaVersion": 1,
            "kind": "ordivon.host-legacy-collaboration-snapshot-r1",
            "sourceSchemaVersion": 8,
            "tasks": [],
            "checkpoints": [],
            "taskEvents": [],
            "boardMessages": [],
            "mechanicalCounts": {},
            "truthBoundary": "legacy",
        }
    )
    snapshot["tasks"].append({"task_id": "tamper"})
    with pytest.raises(ValueError, match="digest mismatch"):
        compile_cutover_plan(snapshot)


@pytest.mark.skipif(not DSN, reason="ORDIVON_HOST_V2_TEST_DSN not set")
def test_one_shot_cutover_applies_to_empty_swf_target_and_verifies() -> None:
    assert DSN is not None
    import psycopg

    with psycopg.connect(DSN, autocommit=True) as conn:
        conn.execute(
            "TRUNCATE attention_cursors,subscriptions,coordination_intents,message_relations,"
            "messages,topics,participations,space_subjects,spaces,work_relations,work_snapshots,"
            "works,actor_refs RESTART IDENTITY CASCADE"
        )
    host = HostV2(DSN)
    host.initialize()
    board = BoardStore(DSN)
    token = uuid4().hex
    task_id = f"task:cutover:{token}"
    host.adopt(
        task_id=task_id,
        goal_id=f"goal:cutover:{token}",
        checkpoint=CheckpointInput(
            payload={
                "objective": "migrate me",
                "frontier": "r1",
                "established": [],
                "unresolved": ["next"],
                "rejected": [],
                "constraints": [],
                "nextActions": ["continue"],
                "runtime": None,
            },
            writer_label="legacy-agent-a",
        ),
        client_request_id=f"adopt:{task_id}",
    )
    host.checkpoint(
        task_id=task_id,
        expected_revision=1,
        checkpoint=CheckpointInput(
            payload={
                "objective": "migrate me",
                "frontier": "r2",
                "established": ["one"],
                "unresolved": [],
                "rejected": [],
                "constraints": [],
                "nextActions": [],
                "runtime": None,
            },
            writer_label="legacy-agent-b",
        ),
        client_request_id=f"checkpoint:{task_id}",
    )
    board.post(
        client_message_id=f"cutover-msg:{token}",
        author_label="legacy-agent-a",
        message="coordination fact",
        message_kind="note",
        topic="matching",
        task_id=task_id,
    )

    snapshot = extract_legacy_snapshot(DSN)
    plan = compile_cutover_plan(snapshot, active_task_ids={task_id})
    receipt = apply_cutover_plan(DSN, snapshot, plan)
    assert receipt["standing"] == "PASS"
    assert receipt["targetCounts"]["works"] >= 1
    assert receipt["targetCounts"]["workSnapshots"] >= 2
    assert receipt["targetCounts"]["messages"] >= 1
    assert receipt["targetCounts"]["participations"] == 0
    assert receipt["targetCounts"]["subscriptions"] == 0
    assert HostV2(DSN).status(detail="history")["doctor"]["healthy"] is True
