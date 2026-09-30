from __future__ import annotations

import hashlib
from typing import Any

import psycopg
from psycopg.rows import dict_row
from psycopg.types.json import Jsonb

from .canonical import canonical_digest

CUTOVER_KIND = "ordivon.host-social-work-fabric-cutover-plan-r1"
MIGRATOR_ACTOR_REF = "actor:service:swf-legacy-cutover-r1"


def _stable(prefix: str, value: str, length: int = 32) -> str:
    digest = hashlib.sha256(value.encode("utf-8")).hexdigest()[:length]
    return f"{prefix}:{digest}"


def legacy_actor_ref(label: str | None) -> str:
    marker = "__unattributed__" if label is None else label
    return _stable("actor:legacy-label", marker)


def legacy_work_ref(task_id: str) -> str:
    return _stable("work:legacy-task", task_id)


def legacy_space_ref(task_id: str) -> str:
    return _stable("space:legacy-task", task_id)


def legacy_topic_ref(task_id: str, topic: str) -> str:
    return _stable("topic:legacy-task", f"{task_id}\0{topic}")


def legacy_message_ref(client_message_id: str) -> str:
    return _stable("message:legacy-board", client_message_id)


def _iso(value: Any) -> str:
    if hasattr(value, "isoformat"):
        return value.isoformat()
    return str(value)


def _json_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    for row in rows:
        item: dict[str, Any] = {}
        for key, value in row.items():
            if hasattr(value, "isoformat"):
                item[key] = value.isoformat()
            else:
                item[key] = value
        result.append(item)
    return result


def extract_legacy_snapshot(dsn: str) -> dict[str, Any]:
    """Read one revision-coherent archive snapshot without mutating either legacy or SWF rows."""
    with psycopg.connect(dsn, row_factory=dict_row) as conn, conn.transaction():
        conn.execute("SET TRANSACTION ISOLATION LEVEL REPEATABLE READ, READ ONLY")
        schema = conn.execute(
            "SELECT schema_version FROM host_v2_schema WHERE singleton"
        ).fetchone()
        observed = None if schema is None else int(schema["schema_version"])
        if observed not in {5, 8}:
            raise RuntimeError(
                "legacy extraction requires schema 5 live source or schema 8 staging database "
                f"(observed={observed})"
            )
        tasks = _json_rows(
            conn.execute(
                "SELECT task_id,goal_id,revision,state,current_checkpoint_digest,created_at,updated_at "
                "FROM tasks ORDER BY task_id"
            ).fetchall()
        )
        checkpoints = _json_rows(
            conn.execute(
                "SELECT task_id,revision,checkpoint_digest,payload,writer_label,created_at "
                "FROM checkpoints ORDER BY task_id,revision"
            ).fetchall()
        )
        task_events = _json_rows(
            conn.execute(
                "SELECT task_id,revision,event_type,request_digest,checkpoint_digest,resulting_state,created_at "
                "FROM task_events ORDER BY task_id,revision"
            ).fetchall()
        )
        board = _json_rows(
            conn.execute(
                "SELECT sequence,client_message_id,author_label,message_kind,topic,message,"
                "reply_to_client_message_id,task_id,message_digest,recorded_at_ms,created_at "
                "FROM board_messages ORDER BY sequence"
            ).fetchall()
        )
        mechanical = {
            "commandReceiptCount": int(
                conn.execute("SELECT count(*) AS value FROM command_receipts").fetchone()["value"]
            )
        }
    body = {
        "schemaVersion": 1,
        "kind": "ordivon.host-legacy-collaboration-snapshot-r1",
        "sourceSchemaVersion": observed,
        "tasks": tasks,
        "checkpoints": checkpoints,
        "taskEvents": task_events,
        "boardMessages": board,
        "mechanicalCounts": mechanical,
        "truthBoundary": "immutable legacy Host semantic/collaboration snapshot; no foreign owner truth is asserted",
    }
    body["snapshotDigest"] = canonical_digest(body)
    return body


def _string_list(payload: dict[str, Any], key: str) -> list[str]:
    value = payload.get(key, [])
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, str) and item.strip()]


def _runtime_refs(payload: dict[str, Any]) -> list[str]:
    runtime = payload.get("runtime")
    if not isinstance(runtime, dict):
        return []
    refs: list[str] = []
    workspace = runtime.get("workspaceId")
    if isinstance(workspace, str) and workspace:
        refs.append(f"runtime:workspace:{workspace}")
    jobs = runtime.get("relevantJobIds")
    if isinstance(jobs, list):
        refs.extend(f"runtime:job:{job}" for job in jobs if isinstance(job, str) and job)
    head = runtime.get("observedHeadRevision")
    if isinstance(head, str) and head:
        refs.append(f"git:observed-revision:{head}")
    return refs


def _snapshot_payload(
    *,
    task_id: str,
    goal_id: str | None,
    checkpoint_digest: str,
    payload: dict[str, Any],
) -> dict[str, Any]:
    objective = payload.get("objective")
    frontier = payload.get("frontier")
    refs = [
        f"legacy:task:{task_id}",
        f"legacy:checkpoint-digest:{checkpoint_digest}",
    ]
    if goal_id:
        refs.append(f"legacy:goal:{goal_id}")
    refs.extend(_runtime_refs(payload))
    return {
        "objective": objective
        if isinstance(objective, str) and objective.strip()
        else "LEGACY_UNSPECIFIED_OBJECTIVE",
        "frontier": frontier
        if isinstance(frontier, str) and frontier.strip()
        else "LEGACY_UNSPECIFIED_FRONTIER",
        "established": _string_list(payload, "established"),
        "unresolved": _string_list(payload, "unresolved"),
        "rejected": _string_list(payload, "rejected"),
        "constraints": _string_list(payload, "constraints"),
        "nextActions": _string_list(payload, "nextActions"),
        "referenceRefs": sorted(set(refs)),
    }


def compile_cutover_plan(
    snapshot: dict[str, Any], *, active_task_ids: set[str] | None = None
) -> dict[str, Any]:
    expected_digest = snapshot.get("snapshotDigest")
    without_digest = dict(snapshot)
    without_digest.pop("snapshotDigest", None)
    if expected_digest != canonical_digest(without_digest):
        raise ValueError("legacy snapshot digest mismatch")
    tasks = snapshot.get("tasks")
    checkpoints = snapshot.get("checkpoints")
    board = snapshot.get("boardMessages")
    if (
        not isinstance(tasks, list)
        or not isinstance(checkpoints, list)
        or not isinstance(board, list)
    ):
        raise ValueError("legacy snapshot is missing task/checkpoint/board arrays")

    cps_by_task: dict[str, list[dict[str, Any]]] = {}
    for cp in checkpoints:
        cps_by_task.setdefault(cp["task_id"], []).append(cp)

    actor_rows: dict[str, dict[str, Any]] = {
        MIGRATOR_ACTOR_REF: {"actorRef": MIGRATOR_ACTOR_REF, "actorKind": "service"}
    }
    for cp in checkpoints:
        ref = legacy_actor_ref(cp.get("writer_label"))
        actor_rows[ref] = {"actorRef": ref, "actorKind": "unknown"}
    works: list[dict[str, Any]] = []
    snapshots: list[dict[str, Any]] = []
    work_map: dict[str, str] = {}
    for task in tasks:
        task_id = task["task_id"]
        work_ref = legacy_work_ref(task_id)
        work_map[task_id] = work_ref
        cps = sorted(cps_by_task.get(task_id, []), key=lambda row: int(row["revision"]))
        if len(cps) != int(task["revision"]) or [int(row["revision"]) for row in cps] != list(
            range(1, int(task["revision"]) + 1)
        ):
            raise ValueError(f"legacy task history is not contiguous: {task_id}")
        target_cps: list[dict[str, Any]] = []
        for cp in cps:
            raw = cp["payload"] if isinstance(cp.get("payload"), dict) else {}
            mapped = _snapshot_payload(
                task_id=task_id,
                goal_id=task.get("goal_id"),
                checkpoint_digest=cp["checkpoint_digest"],
                payload=raw,
            )
            row = {
                "workRef": work_ref,
                "revision": int(cp["revision"]),
                "snapshotDigest": canonical_digest(mapped),
                "payload": mapped,
                "writerActorRef": legacy_actor_ref(cp.get("writer_label")),
                "createdAt": cp["created_at"],
            }
            target_cps.append(row)
            snapshots.append(row)
        current = target_cps[-1]
        works.append(
            {
                "workRef": work_ref,
                "legacyTaskId": task_id,
                "workKind": "legacy-task",
                "state": task["state"],
                "currentRevision": int(task["revision"]),
                "currentSnapshotDigest": current["snapshotDigest"],
                "createdByActorRef": MIGRATOR_ACTOR_REF,
                "createdAt": task["created_at"],
                "updatedAt": task["updated_at"],
            }
        )

    open_tasks = {row["task_id"] for row in tasks if row["state"] == "open"}
    selected_tasks = set() if active_task_ids is None else set(active_task_ids)
    unknown_selected = selected_tasks - set(work_map)
    if unknown_selected:
        raise ValueError(
            f"active Task selection contains unknown legacy Tasks: {sorted(unknown_selected)}"
        )
    nonopen_selected = selected_tasks - open_tasks
    if nonopen_selected:
        raise ValueError(
            f"active Task selection contains non-open legacy Tasks: {sorted(nonopen_selected)}"
        )
    selected = [
        row
        for row in board
        if row.get("task_id") in selected_tasks
        and not (
            str(row.get("client_message_id", "")).startswith("task-route-anchor-v1:")
            and row.get("author_label") == "task-routing-anchor-v1"
        )
    ]
    selected_by_id = {row["client_message_id"]: row for row in selected}
    for msg in selected:
        ref = legacy_actor_ref(msg.get("author_label"))
        actor_rows[ref] = {"actorRef": ref, "actorKind": "unknown"}

    space_tasks = sorted({row["task_id"] for row in selected})
    spaces = [
        {
            "spaceRef": legacy_space_ref(task_id),
            "purpose": "migrated legacy task collaboration",
            "createdByActorRef": MIGRATOR_ACTOR_REF,
            "subjectRefs": [work_map[task_id], f"legacy:task:{task_id}"],
        }
        for task_id in space_tasks
    ]
    topic_keys = sorted({(row["task_id"], row.get("topic") or "general") for row in selected})
    topics = [
        {
            "topicRef": legacy_topic_ref(task_id, topic),
            "spaceRef": legacy_space_ref(task_id),
            "title": topic,
            "state": "open",
            "createdByActorRef": MIGRATOR_ACTOR_REF,
        }
        for task_id, topic in topic_keys
    ]
    messages: list[dict[str, Any]] = []
    relations: list[dict[str, Any]] = []
    for row in selected:
        task_id = row["task_id"]
        topic = row.get("topic") or "general"
        msg_ref = legacy_message_ref(row["client_message_id"])
        kind = row["message_kind"] if row["message_kind"] != "reply" else "note"
        messages.append(
            {
                "messageRef": msg_ref,
                "legacyClientMessageId": row["client_message_id"],
                "clientRequestId": f"cutover:{msg_ref}",
                "spaceRef": legacy_space_ref(task_id),
                "topicRef": legacy_topic_ref(task_id, topic),
                "authorActorRef": legacy_actor_ref(row.get("author_label")),
                "messageKind": kind,
                "body": row["message"],
                "recordedAtMs": int(row["recorded_at_ms"]),
                "createdAt": row["created_at"],
            }
        )
        parent_id = row.get("reply_to_client_message_id")
        if parent_id:
            parent = selected_by_id.get(parent_id)
            if parent is not None:
                target = legacy_message_ref(parent_id)
                same_axis = (
                    parent.get("task_id") == task_id and (parent.get("topic") or "general") == topic
                )
                relation = "reply_to" if same_axis else "references"
            else:
                target = f"legacy-board-client:{parent_id}"
                relation = "references"
            relations.append(
                {
                    "sourceMessageRef": msg_ref,
                    "relation": relation,
                    "targetRef": target,
                    "createdByActorRef": MIGRATOR_ACTOR_REF,
                }
            )

    plan = {
        "schemaVersion": 1,
        "kind": CUTOVER_KIND,
        "sourceSnapshotDigest": expected_digest,
        "actors": sorted(actor_rows.values(), key=lambda row: row["actorRef"]),
        "works": sorted(works, key=lambda row: row["workRef"]),
        "workSnapshots": sorted(snapshots, key=lambda row: (row["workRef"], row["revision"])),
        "workRelations": [],
        "spaces": sorted(spaces, key=lambda row: row["spaceRef"]),
        "participations": [],
        "topics": sorted(topics, key=lambda row: row["topicRef"]),
        "messages": sorted(messages, key=lambda row: row["recordedAtMs"]),
        "messageRelations": sorted(
            relations, key=lambda row: (row["sourceMessageRef"], row["relation"], row["targetRef"])
        ),
        "coordinationIntents": [],
        "subscriptions": [],
        "selection": {
            "legacyTaskCount": len(tasks),
            "legacyCheckpointCount": len(checkpoints),
            "legacyBoardMessageCount": len(board),
            "explicitActiveTaskSelectionCount": len(selected_tasks),
            "activeTaskLinkedBoardMessagesImported": len(selected),
            "boardMessagesArchiveOnly": len(board) - len(selected),
            "syntheticRouteAnchorsImported": 0,
        },
        "nonClaims": [
            "Legacy author labels become ActorKind=unknown and do not establish authenticated identity.",
            "Message authorship does not infer Participation, Subscription, ownership, assignment, or authority.",
            "Legacy Task/Goal structure does not infer WorkRelation edges.",
            "No Board message enters the Social Graph from Task state alone; an explicit open-Task cutover manifest is required.",
            "Unselected Board history remains represented only by the immutable legacy snapshot.",
        ],
    }
    plan["planDigest"] = canonical_digest(plan)
    return plan


def _assert_empty_target(conn: psycopg.Connection[dict[str, Any]]) -> None:
    tables = (
        "work_snapshots",
        "work_relations",
        "works",
        "space_subjects",
        "participations",
        "topics",
        "messages",
        "message_relations",
        "coordination_intents",
        "subscriptions",
        "attention_cursors",
    )
    nonempty = []
    for table in tables:
        count = int(conn.execute(f"SELECT count(*) AS value FROM {table}").fetchone()["value"])
        if count:
            nonempty.append(f"{table}={count}")
    actor_count = int(conn.execute("SELECT count(*) AS value FROM actor_refs").fetchone()["value"])
    if actor_count:
        nonempty.append(f"actor_refs={actor_count}")
    if nonempty:
        raise RuntimeError("cutover target must be empty: " + ", ".join(nonempty))


def apply_cutover_plan(dsn: str, snapshot: dict[str, Any], plan: dict[str, Any]) -> dict[str, Any]:
    if plan.get("planDigest") != canonical_digest(
        {k: v for k, v in plan.items() if k != "planDigest"}
    ):
        raise ValueError("cutover plan digest mismatch")
    if plan.get("sourceSnapshotDigest") != snapshot.get("snapshotDigest"):
        raise ValueError("cutover plan is not bound to supplied snapshot")
    with psycopg.connect(dsn, row_factory=dict_row) as conn, conn.transaction():
        conn.execute("SET TRANSACTION ISOLATION LEVEL SERIALIZABLE")
        schema = conn.execute(
            "SELECT schema_version FROM host_v2_schema WHERE singleton"
        ).fetchone()
        if schema is None or int(schema["schema_version"]) != 8:
            raise RuntimeError("cutover apply requires schema 8")
        _assert_empty_target(conn)
        for actor in plan["actors"]:
            conn.execute(
                "INSERT INTO actor_refs(actor_ref,actor_kind) VALUES (%s,%s)",
                (actor["actorRef"], actor["actorKind"]),
            )
        snapshots_by_work: dict[str, list[dict[str, Any]]] = {}
        for row in plan["workSnapshots"]:
            snapshots_by_work.setdefault(row["workRef"], []).append(row)
        for work in plan["works"]:
            conn.execute(
                "INSERT INTO works(work_ref,kind,state,current_revision,current_snapshot_digest,"
                "created_by_actor_ref,created_at,updated_at) VALUES (%s,%s,%s,%s,%s,%s,%s,%s)",
                (
                    work["workRef"],
                    work["workKind"],
                    work["state"],
                    work["currentRevision"],
                    work["currentSnapshotDigest"],
                    work["createdByActorRef"],
                    work["createdAt"],
                    work["updatedAt"],
                ),
            )
            for cp in snapshots_by_work[work["workRef"]]:
                conn.execute(
                    "INSERT INTO work_snapshots(work_ref,revision,snapshot_digest,payload,writer_actor_ref,created_at) "
                    "VALUES (%s,%s,%s,%s,%s,%s)",
                    (
                        cp["workRef"],
                        cp["revision"],
                        cp["snapshotDigest"],
                        Jsonb(cp["payload"]),
                        cp["writerActorRef"],
                        cp["createdAt"],
                    ),
                )
        for space in plan["spaces"]:
            conn.execute(
                "INSERT INTO spaces(space_ref,purpose,created_by_actor_ref) VALUES (%s,%s,%s)",
                (space["spaceRef"], space["purpose"], space["createdByActorRef"]),
            )
            for subject in space["subjectRefs"]:
                conn.execute(
                    "INSERT INTO space_subjects(space_ref,subject_ref) VALUES (%s,%s)",
                    (space["spaceRef"], subject),
                )
        for topic in plan["topics"]:
            conn.execute(
                "INSERT INTO topics(topic_ref,space_ref,title,state,created_by_actor_ref) VALUES (%s,%s,%s,%s,%s)",
                (
                    topic["topicRef"],
                    topic["spaceRef"],
                    topic["title"],
                    topic["state"],
                    topic["createdByActorRef"],
                ),
            )
        for message in plan["messages"]:
            message_digest = canonical_digest(
                {
                    "messageRef": message["messageRef"],
                    "spaceRef": message["spaceRef"],
                    "topicRef": message["topicRef"],
                    "authorActorRef": message["authorActorRef"],
                    "messageKind": message["messageKind"],
                    "body": message["body"],
                    "recordedAtMs": message["recordedAtMs"],
                }
            )
            conn.execute(
                "INSERT INTO messages(message_ref,client_request_id,space_ref,topic_ref,author_actor_ref,"
                "message_kind,body,message_digest,recorded_at_ms,created_at) "
                "VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)",
                (
                    message["messageRef"],
                    message["clientRequestId"],
                    message["spaceRef"],
                    message["topicRef"],
                    message["authorActorRef"],
                    message["messageKind"],
                    message["body"],
                    message_digest,
                    message["recordedAtMs"],
                    message["createdAt"],
                ),
            )
        for relation in plan["messageRelations"]:
            conn.execute(
                "INSERT INTO message_relations(source_message_ref,relation,target_ref,created_by_actor_ref) "
                "VALUES (%s,%s,%s,%s)",
                (
                    relation["sourceMessageRef"],
                    relation["relation"],
                    relation["targetRef"],
                    relation["createdByActorRef"],
                ),
            )
    return verify_cutover(dsn, snapshot, plan)


def verify_cutover(dsn: str, snapshot: dict[str, Any], plan: dict[str, Any]) -> dict[str, Any]:
    errors: list[str] = []
    with psycopg.connect(dsn, row_factory=dict_row) as conn, conn.transaction():
        conn.execute("SET TRANSACTION ISOLATION LEVEL REPEATABLE READ, READ ONLY")
        actual = {
            "actors": int(
                conn.execute("SELECT count(*) AS value FROM actor_refs").fetchone()["value"]
            ),
            "works": int(conn.execute("SELECT count(*) AS value FROM works").fetchone()["value"]),
            "workSnapshots": int(
                conn.execute("SELECT count(*) AS value FROM work_snapshots").fetchone()["value"]
            ),
            "spaces": int(conn.execute("SELECT count(*) AS value FROM spaces").fetchone()["value"]),
            "topics": int(conn.execute("SELECT count(*) AS value FROM topics").fetchone()["value"]),
            "messages": int(
                conn.execute("SELECT count(*) AS value FROM messages").fetchone()["value"]
            ),
            "messageRelations": int(
                conn.execute("SELECT count(*) AS value FROM message_relations").fetchone()["value"]
            ),
            "participations": int(
                conn.execute("SELECT count(*) AS value FROM participations").fetchone()["value"]
            ),
            "coordinationIntents": int(
                conn.execute("SELECT count(*) AS value FROM coordination_intents").fetchone()[
                    "value"
                ]
            ),
            "subscriptions": int(
                conn.execute("SELECT count(*) AS value FROM subscriptions").fetchone()["value"]
            ),
        }
        expected = {
            "actors": len(plan["actors"]),
            "works": len(plan["works"]),
            "workSnapshots": len(plan["workSnapshots"]),
            "spaces": len(plan["spaces"]),
            "topics": len(plan["topics"]),
            "messages": len(plan["messages"]),
            "messageRelations": len(plan["messageRelations"]),
            "participations": 0,
            "coordinationIntents": 0,
            "subscriptions": 0,
        }
        if actual != expected:
            errors.append(f"target counts differ: actual={actual} expected={expected}")
        for work in plan["works"]:
            row = conn.execute(
                "SELECT state,current_revision,current_snapshot_digest FROM works WHERE work_ref=%s",
                (work["workRef"],),
            ).fetchone()
            if row is None:
                errors.append(f"missing work {work['workRef']}")
                continue
            if (
                row["state"] != work["state"]
                or int(row["current_revision"]) != int(work["currentRevision"])
                or row["current_snapshot_digest"] != work["currentSnapshotDigest"]
            ):
                errors.append(f"current Work standing differs for {work['workRef']}")
    return {
        "schemaVersion": 1,
        "kind": "ordivon.host-social-work-fabric-cutover-verification-r1",
        "sourceSnapshotDigest": snapshot["snapshotDigest"],
        "planDigest": plan["planDigest"],
        "standing": "PASS" if not errors else "FAIL",
        "errors": errors,
        "targetCounts": actual,
        "selection": plan["selection"],
        "nonClaims": plan["nonClaims"],
    }
