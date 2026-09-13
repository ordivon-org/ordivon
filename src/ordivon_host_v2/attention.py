from __future__ import annotations

from collections import defaultdict
from typing import Any

import psycopg
from psycopg.rows import dict_row

from .board import task_route_anchor_task_id

_MAX_MESSAGES = 100
_MAX_ROUTE_DEPTH = 16


def build_attention_delta(dsn: str, *, after_sequence: int, limit: int = 100) -> dict[str, Any]:
    """Project Board delta into exact Task re-entry coordinates without priority inference."""
    if type(after_sequence) is not int or after_sequence < 0:
        raise ValueError("afterSequence must be a non-negative integer")
    if type(limit) is not int or not 1 <= limit <= _MAX_MESSAGES:
        raise ValueError(f"limit must be in [1,{_MAX_MESSAGES}]")

    with psycopg.connect(dsn, row_factory=dict_row) as conn, conn.transaction():
        conn.execute("SET TRANSACTION ISOLATION LEVEL REPEATABLE READ, READ ONLY")
        high_row = conn.execute(
            "SELECT COALESCE(max(sequence),0) AS value FROM board_messages"
        ).fetchone()
        assert high_row is not None
        high = int(high_row["value"])
        rows = conn.execute(
            "SELECT * FROM board_messages WHERE sequence>%s AND sequence<=%s "
            "ORDER BY sequence ASC LIMIT %s",
            (after_sequence, high, limit + 1),
        ).fetchall()
        has_more = len(rows) > limit
        visible = rows[:limit]
        next_after = (
            int(visible[-1]["sequence"]) if has_more and visible else max(after_sequence, high)
        )

        route_cache: dict[str, tuple[str | None, int | None, str]] = {}
        by_task: dict[str, list[dict[str, Any]]] = defaultdict(list)
        unrouted: list[dict[str, Any]] = []
        for row in visible:
            task_id, depth, standing = _route_task(conn, row, route_cache)
            compact = _compact_message(row, depth, standing)
            if task_id is None:
                unrouted.append(compact)
            else:
                by_task[task_id].append(compact)

        routed_tasks: list[dict[str, Any]] = []
        missing_tasks: list[dict[str, Any]] = []
        for task_id, messages in by_task.items():
            task = conn.execute(
                "SELECT task_id,goal_id,revision,state,current_checkpoint_digest,updated_at "
                "FROM tasks WHERE task_id=%s",
                (task_id,),
            ).fetchone()
            if task is None:
                missing_tasks.append(
                    {
                        "taskId": task_id,
                        "messageCount": len(messages),
                        "latestBoardSequence": max(int(m["sequence"]) for m in messages),
                        "reason": "task-route-anchor-resolves-but-current-task-is-absent",
                    }
                )
                continue
            checkpoint = conn.execute(
                "SELECT checkpoint_digest,payload,writer_label FROM checkpoints "
                "WHERE task_id=%s AND revision=%s",
                (task_id, task["revision"]),
            ).fetchone()
            if checkpoint is None:
                raise RuntimeError("current task checkpoint is missing")
            runtime_hint = (
                checkpoint["payload"].get("runtime")
                if isinstance(checkpoint["payload"], dict)
                else None
            )
            routed_tasks.append(
                {
                    "taskId": task_id,
                    "goalId": task["goal_id"],
                    "taskState": task["state"],
                    "taskRevision": int(task["revision"]),
                    "checkpointDigest": checkpoint["checkpoint_digest"],
                    "runtimeNavigationHint": runtime_hint,
                    "newBoardMessageCount": len(messages),
                    "newestBoardSequence": max(int(m["sequence"]) for m in messages),
                    "messages": sorted(messages, key=lambda m: int(m["sequence"])),
                    "reentry": {
                        "requiredBeforeActing": True,
                        "operation": "task.resume",
                        "taskId": task_id,
                        "expectedRevision": int(task["revision"]),
                        "reason": "Board collaboration does not update Task truth; resume the exact Host revision before acting",
                    },
                }
            )

    routed_tasks.sort(key=lambda row: (-int(row["newestBoardSequence"]), str(row["taskId"])))
    missing_tasks.sort(key=lambda row: (-int(row["latestBoardSequence"]), str(row["taskId"])))
    return {
        "schemaVersion": 2,
        "kind": "ordivon.host-current-attention-delta",
        "truthRole": "derived-non-authoritative-coordination-navigation",
        "boardFence": {
            "requestedAfterSequence": after_sequence,
            "lastSequence": high,
            "nextAfterSequence": next_after,
            "hasMore": has_more,
            "completeThroughNextAfterSequence": not has_more,
        },
        "summary": {
            "newMessageCount": len(visible),
            "routedTaskCount": len(routed_tasks),
            "routedMessageCount": sum(len(messages) for messages in by_task.values()),
            "unroutedMessageCount": len(unrouted),
            "missingTaskRouteCount": len(missing_tasks),
        },
        "routedTasks": routed_tasks,
        "missingTaskRoutes": missing_tasks,
        "unroutedMessages": unrouted,
        "truthBoundary": (
            "Board-derived navigation only; not priority, assignment, ownership, delivery, consumption, "
            "or domain truth. Exact task.resume re-entry is required before action."
        ),
    }


def _route_task(
    conn: psycopg.Connection[dict[str, Any]],
    message: dict[str, Any],
    cache: dict[str, tuple[str | None, int | None, str]],
) -> tuple[str | None, int | None, str]:
    parent = message.get("reply_to_client_message_id")
    if not isinstance(parent, str):
        return None, None, "NO_REPLY_PARENT"
    current = parent
    visited: set[str] = set()
    for depth in range(1, _MAX_ROUTE_DEPTH + 1):
        if current in visited:
            return None, None, "INVALID_CYCLE_GUARD"
        visited.add(current)
        cached = cache.get(current)
        if cached is not None:
            task_id, cached_depth, standing = cached
            if task_id is None or cached_depth is None:
                return None, None, standing
            return task_id, depth - 1 + cached_depth, standing
        row = conn.execute(
            "SELECT * FROM board_messages WHERE client_message_id=%s", (current,)
        ).fetchone()
        if row is None:
            cache[current] = (None, None, "PARENT_NOT_RESOLVABLE")
            return cache[current]
        task_id = task_route_anchor_task_id(row)
        if task_id is not None:
            cache[current] = (task_id, 1, "CANONICAL_TASK_ANCHOR_RESOLVED")
            return task_id, depth, "CANONICAL_TASK_ANCHOR_RESOLVED"
        next_parent = row.get("reply_to_client_message_id")
        if not isinstance(next_parent, str):
            cache[current] = (None, None, "NO_CANONICAL_TASK_ANCHOR_IN_BOUNDED_ANCESTRY")
            return cache[current]
        current = next_parent
    return None, None, "ROUTE_DEPTH_LIMIT_REACHED"


def _compact_message(
    row: dict[str, Any], route_depth: int | None, route_standing: str
) -> dict[str, Any]:
    return {
        "sequence": int(row["sequence"]),
        "clientMessageId": row["client_message_id"],
        "messageKind": row["message_kind"],
        "topic": row["topic"],
        "replyToClientMessageId": row["reply_to_client_message_id"],
        "recordedAtMs": int(row["recorded_at_ms"]),
        "messageDigest": row["message_digest"],
        "routeDepth": route_depth,
        "routeStanding": route_standing,
    }
