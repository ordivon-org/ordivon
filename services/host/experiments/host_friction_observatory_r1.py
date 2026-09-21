from __future__ import annotations

import argparse
import json
import math
import os
import statistics
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import psycopg
from psycopg.rows import dict_row

from ordivon_host_v2 import BoardStore, HostV2


def encoded_size(value: Any) -> int:
    return len(
        json.dumps(
            value,
            sort_keys=True,
            separators=(",", ":"),
            default=str,
        ).encode("utf-8")
    )


def percentile(values: list[float | int], q: float) -> float | None:
    if not values:
        return None
    ordered = sorted(float(v) for v in values)
    position = (len(ordered) - 1) * q
    lower = math.floor(position)
    upper = math.ceil(position)
    if lower == upper:
        return round(ordered[lower], 3)
    fraction = position - lower
    return round(
        ordered[lower] * (1.0 - fraction) + ordered[upper] * fraction,
        3,
    )


def distribution(values: list[int]) -> dict[str, Any]:
    if not values:
        return {"count": 0}
    return {
        "count": len(values),
        "mean": round(statistics.mean(values), 3),
        "p50": percentile(values, 0.50),
        "p90": percentile(values, 0.90),
        "p99": percentile(values, 0.99),
        "max": max(values),
    }


def percentage(numerator: int, denominator: int) -> float | None:
    if denominator == 0:
        return None
    return round(100.0 * numerator / denominator, 3)


def task_summary_wire(task: Any) -> dict[str, Any]:
    return {
        "task_id": task.task_id,
        "goal_id": task.goal_id,
        "revision": task.revision,
        "state": task.state.value,
        "checkpoint_digest": task.checkpoint_digest,
        "writer_label": task.writer_label,
    }


def task_resume_wire(task: Any) -> dict[str, Any]:
    return {
        "schemaVersion": 4,
        "kind": "ordivon.host-external-continuity-resume",
        "task": task_summary_wire(task),
        "checkpoint": task.checkpoint,
        "writerLabel": task.writer_label,
        "truthBoundary": (
            "semantic working claim only; foreign Runtime/Git/domain references "
            "must be revalidated"
        ),
    }


def task_list_wire(
    tasks: list[dict[str, Any]],
    has_more: bool,
    next_cursor: str | None,
) -> dict[str, Any]:
    return {
        "schemaVersion": 4,
        "kind": "ordivon.host-task-list",
        "itemView": "basic",
        "tasks": tasks,
        "hasMore": has_more,
        "nextCursor": next_cursor,
        "truthBoundary": (
            "compact continuity inventory only; use task.resume for exact checkpoint "
            "content; not work priority, owner standing, or domain truth"
        ),
    }


def read_rows(conn: psycopg.Connection[Any]) -> dict[str, Any]:
    open_tasks = conn.execute(
        """
        SELECT
            t.task_id,
            t.goal_id,
            t.revision,
            t.created_at,
            t.updated_at,
            t.current_checkpoint_digest,
            c.payload
        FROM tasks t
        JOIN checkpoints c
          ON c.task_id=t.task_id AND c.revision=t.revision
        WHERE t.state='open'
        ORDER BY t.task_id
        """
    ).fetchall()

    board_counts = conn.execute(
        """
        SELECT
            count(*) AS total,
            count(*) FILTER (WHERE task_id IS NOT NULL) AS routed,
            count(*) FILTER (WHERE task_id IS NULL) AS unrouted,
            count(*) FILTER (WHERE reply_to_client_message_id IS NULL) AS roots,
            count(*) FILTER (WHERE reply_to_client_message_id IS NOT NULL) AS replies
        FROM board_messages
        """
    ).fetchone()
    assert board_counts is not None

    reply_integrity = conn.execute(
        """
        SELECT
            count(*) AS replies,
            count(*) FILTER (
                WHERE p.task_id IS NOT NULL AND c.task_id IS NULL
            ) AS lost_route,
            count(*) FILTER (
                WHERE p.task_id IS NOT NULL AND c.task_id IS DISTINCT FROM p.task_id
            ) AS conflicting_route,
            count(*) FILTER (
                WHERE p.task_id IS NULL AND c.task_id IS NOT NULL
            ) AS route_introduced
        FROM board_messages c
        JOIN board_messages p
          ON p.client_message_id=c.reply_to_client_message_id
        """
    ).fetchone()
    assert reply_integrity is not None

    board_by_task = {
        row["task_id"]: row
        for row in conn.execute(
            """
            SELECT
                task_id,
                count(*) AS messages,
                max(created_at) AS last_board_at
            FROM board_messages
            WHERE task_id IS NOT NULL
            GROUP BY task_id
            """
        ).fetchall()
    }

    last_seven_days = conn.execute(
        """
        SELECT
            count(*) AS total,
            count(*) FILTER (WHERE task_id IS NOT NULL) AS routed,
            count(*) FILTER (WHERE task_id IS NULL) AS unrouted
        FROM board_messages
        WHERE created_at >= now() - interval '7 days'
        """
    ).fetchone()
    assert last_seven_days is not None

    return {
        "openTasks": open_tasks,
        "boardCounts": board_counts,
        "replyIntegrity": reply_integrity,
        "boardByTask": board_by_task,
        "lastSevenDays": last_seven_days,
    }


def age_bucket(seconds: float) -> str:
    hour = 3600
    day = 24 * hour
    if seconds < hour:
        return "<1h"
    if seconds < 6 * hour:
        return "1-6h"
    if seconds < day:
        return "6-24h"
    if seconds < 3 * day:
        return "1-3d"
    if seconds < 7 * day:
        return "3-7d"
    if seconds < 14 * day:
        return "7-14d"
    return ">=14d"


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Read-only production friction observatory for Host v2."
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("planning/host-friction-observatory-r1.json"),
    )
    args = parser.parse_args()

    dsn = os.environ["ORDIVON_HOST_V2_DSN"]
    host = HostV2(dsn)
    board = BoardStore(dsn)
    observed_at = datetime.now(UTC)

    with psycopg.connect(dsn, row_factory=dict_row) as conn, conn.transaction():
        conn.execute("SET TRANSACTION ISOLATION LEVEL REPEATABLE READ, READ ONLY")
        rows = read_rows(conn)

    open_tasks = rows["openTasks"]
    board_counts = rows["boardCounts"]
    reply_integrity = rows["replyIntegrity"]
    board_by_task = rows["boardByTask"]
    recent_board = rows["lastSevenDays"]

    task_count = len(open_tasks)
    goals = Counter(row["goal_id"] for row in open_tasks)
    singleton_goals = sum(count == 1 for count in goals.values())
    multi_goals = sum(count > 1 for count in goals.values())
    tasks_in_multi_goals = sum(count for count in goals.values() if count > 1)

    age_buckets = Counter()
    board_after_checkpoint_buckets = Counter()
    with_board = 0
    board_after_checkpoint = 0
    no_routed_board = 0

    exact_checkpoint_digests = Counter()
    exact_objectives = Counter()
    exact_frontiers = Counter()
    exact_next_actions = Counter()

    for row in open_tasks:
        age_seconds = max(
            0.0,
            (observed_at - row["updated_at"].astimezone(UTC)).total_seconds(),
        )
        age_buckets[age_bucket(age_seconds)] += 1
        exact_checkpoint_digests[row["current_checkpoint_digest"]] += 1
        payload = row["payload"]
        if isinstance(payload, dict):
            objective = payload.get("objective")
            if isinstance(objective, str) and objective.strip():
                exact_objectives[objective.strip().casefold()] += 1
            frontier = payload.get("frontier")
            if isinstance(frontier, str) and frontier.strip():
                exact_frontiers[frontier.strip().casefold()] += 1
            next_actions = payload.get("nextActions")
            if isinstance(next_actions, list) and next_actions:
                exact_next_actions[
                    json.dumps(next_actions, sort_keys=True, separators=(",", ":"))
                ] += 1

        board_row = board_by_task.get(row["task_id"])
        if board_row is None:
            no_routed_board += 1
            continue
        with_board += 1
        if board_row["last_board_at"] > row["updated_at"]:
            board_after_checkpoint += 1
            lag_seconds = (
                board_row["last_board_at"] - row["updated_at"]
            ).total_seconds()
            board_after_checkpoint_buckets[age_bucket(max(0.0, lag_seconds))] += 1

    # Product task.list is ordered by creation time, default page size 50.
    created_order = sorted(
        open_tasks,
        key=lambda row: (row["created_at"], row["task_id"]),
        reverse=True,
    )
    updated_order = sorted(
        open_tasks,
        key=lambda row: (row["updated_at"], row["task_id"]),
        reverse=True,
    )
    created_rank = {row["task_id"]: index + 1 for index, row in enumerate(created_order)}
    pages = {
        task_id: ((rank - 1) // 50) + 1 for task_id, rank in created_rank.items()
    }
    global_calls_to_exact_resume = [page + 1 for page in pages.values()]
    top_updated = updated_order[: min(50, len(updated_order))]
    top_updated_pages = [pages[row["task_id"]] for row in top_updated]

    # Measure current wire-sized product projections by using the same service paths.
    page_sizes: list[int] = []
    cumulative_page_sizes: list[int] = []
    listed_tasks: list[dict[str, Any]] = []
    cursor = None
    cumulative = 0
    while True:
        page, has_more, cursor = host.list_task_summaries_page(
            limit=50,
            cursor=cursor,
        )
        size = encoded_size(task_list_wire(page, has_more, cursor))
        page_sizes.append(size)
        cumulative += size
        cumulative_page_sizes.append(cumulative)
        listed_tasks.extend(page)
        if not has_more:
            break

    resume_size_by_task: dict[str, int] = {}
    observe_sizes: list[int] = []
    for task in listed_tasks:
        resumed = host.resume(task["task_id"], task["revision"])
        resume_size_by_task[task["task_id"]] = encoded_size(task_resume_wire(resumed))
        observe_sizes.append(
            encoded_size(host.observe(task["task_id"], task["revision"], event_limit=5))
        )

    resume_sizes = list(resume_size_by_task.values())
    global_inventory_plus_resume_bytes = [
        cumulative_page_sizes[pages[task_id] - 1] + resume_size_by_task[task_id]
        for task_id in pages
    ]

    goal_page_wire_sizes: dict[str | None, int] = {}
    for goal_id in goals:
        page, has_more, next_cursor = host.list_task_summaries_page(
            goal_id=goal_id,
            limit=50,
        )
        if has_more:
            raise RuntimeError(
                f"goal {goal_id!r} exceeded the one-page measurement assumption"
            )
        goal_page_wire_sizes[goal_id] = encoded_size(
            task_list_wire(page, has_more, next_cursor)
        )
    goal_known_plus_resume_bytes = [
        goal_page_wire_sizes[row["goal_id"]] + resume_size_by_task[row["task_id"]]
        for row in open_tasks
    ]

    status = host.status(detail="summary")
    last_sequence = int(status["board"]["lastSequence"])
    attention = host.attention_delta(
        after_sequence=max(0, last_sequence - 100),
        limit=100,
    )
    latest_board = board.list(limit=50)

    duplicate_counts = {
        "checkpointDigest": sum(
            1 for count in exact_checkpoint_digests.values() if count > 1
        ),
        "objective": sum(1 for count in exact_objectives.values() if count > 1),
        "frontier": sum(1 for count in exact_frontiers.values() if count > 1),
        "nextActions": sum(1 for count in exact_next_actions.values() if count > 1),
    }

    result = {
        "schemaVersion": 1,
        "kind": "ordivon.host-friction-observatory",
        "truthRole": (
            "read-only observational measurement; not priority, duplicate-work judgment, "
            "semantic completion, or foreign-owner truth"
        ),
        "observedAt": observed_at.isoformat(),
        "population": {
            "openTasks": task_count,
            "goalsWithOpenTasks": len(goals),
            "boardMessages": int(board_counts["total"]),
        },
        "navigation": {
            "currentProductPaths": {
                "exactTaskIdToExactCheckpointCalls": 1,
                "goalKnownInventoryToExactCheckpointCalls": 2,
                "exactRoutedBoardMessageToExactCheckpointCalls": 2,
                "attentionCursorHitToExactCheckpointCalls": 2,
                "lexicalBoardSearchHitToExactCheckpointCalls": 3,
            },
            "globalTaskListDefaultLimit": 50,
            "globalTaskListPages": len(page_sizes),
            "globalListPagePosition": distribution(list(pages.values())),
            "globalInventoryCallsUntilExactResume": distribution(
                global_calls_to_exact_resume
            ),
            "top50RecentlyUpdatedCreatedOrderPages": {
                "distribution": dict(sorted(Counter(top_updated_pages).items())),
                "beyondFirstPage": sum(page > 1 for page in top_updated_pages),
                "beyondFirstPagePercent": percentage(
                    sum(page > 1 for page in top_updated_pages),
                    len(top_updated_pages),
                ),
                "maxPage": max(top_updated_pages) if top_updated_pages else None,
            },
        },
        "payload": {
            "taskList": {
                "pageBytes": page_sizes,
                "totalBytesForAllOpenTasks": sum(page_sizes),
                "meanPageBytes": round(statistics.mean(page_sizes), 3),
            },
            "taskResumeBytes": distribution(resume_sizes),
            "taskObserveBytes": distribution(observe_sizes),
            "globalInventoryPlusResumeBytesPerUniformOpenTask": distribution(
                global_inventory_plus_resume_bytes
            ),
            "goalKnownInventoryPlusResumeBytesPerOpenTask": distribution(
                goal_known_plus_resume_bytes
            ),
            "attentionLatest100Sequences": {
                "wireBytes": encoded_size(attention),
                "messages": attention["summary"]["newMessageCount"],
                "routedMessages": attention["summary"]["routedMessageCount"],
                "unroutedMessages": attention["summary"]["unroutedMessageCount"],
                "routedTasks": attention["summary"]["routedTaskCount"],
            },
            "boardLatest50WireBytes": encoded_size(latest_board),
        },
        "lifecyclePressure": {
            "openTaskAgeBuckets": dict(age_buckets),
            "openTasksAtLeast14DaysOld": age_buckets[">=14d"],
            "openTasksAtLeast14DaysOldPercent": percentage(
                age_buckets[">=14d"], task_count
            ),
            "openTasksWithoutRoutedBoardMessages": no_routed_board,
            "openTasksWithRoutedBoardMessages": with_board,
            "openTasksWithBoardNewerThanCheckpoint": board_after_checkpoint,
            "boardNewerThanCheckpointPercentOfRoutedOpenTasks": percentage(
                board_after_checkpoint,
                with_board,
            ),
            "boardNewerThanCheckpointLagBuckets": dict(
                board_after_checkpoint_buckets
            ),
        },
        "parallelismPressure": {
            "singletonGoals": singleton_goals,
            "multiTaskGoals": multi_goals,
            "tasksInMultiTaskGoals": tasks_in_multi_goals,
            "tasksInMultiTaskGoalsPercent": percentage(
                tasks_in_multi_goals,
                task_count,
            ),
            "maxOpenTasksInOneGoal": max(goals.values()) if goals else 0,
            "openTaskCountByGoalCardinality": dict(
                sorted(Counter(goals.values()).items())
            ),
            "strictExactDuplicateCandidateGroups": duplicate_counts,
            "strictDuplicateEvidence": (
                "none under exact current checkpoint digest/objective/frontier/"
                "nextActions equality; parallel Goal membership is not duplicate-work proof"
            ),
        },
        "boardRouting": {
            "allTime": {
                "messages": int(board_counts["total"]),
                "routed": int(board_counts["routed"]),
                "unrouted": int(board_counts["unrouted"]),
                "routedPercent": percentage(
                    int(board_counts["routed"]),
                    int(board_counts["total"]),
                ),
            },
            "lastSevenDays": {
                "messages": int(recent_board["total"]),
                "routed": int(recent_board["routed"]),
                "unrouted": int(recent_board["unrouted"]),
                "routedPercent": percentage(
                    int(recent_board["routed"]),
                    int(recent_board["total"]),
                ),
            },
            "replyRouteIntegrity": {
                "replies": int(reply_integrity["replies"]),
                "lostRoute": int(reply_integrity["lost_route"]),
                "conflictingRoute": int(reply_integrity["conflicting_route"]),
                "routeIntroducedMidThread": int(reply_integrity["route_introduced"]),
            },
        },
        "observabilityBoundary": {
            "hostCanObserve": [
                "durable Task/Checkpoint/Board state",
                "revision fences and committed receipts",
                "Board-to-Task routing integrity",
            ],
            "hostCannotEstablish": [
                "actual fresh-Agent Host call count across a client session",
                "duplicate semantic work",
                "whether an old open Task should be abandoned",
                "foreign-owner revalidation count",
                "client-visible stale tool catalog",
            ],
            "naturalOwners": {
                "agentToolCallLifecycle": "Harness event model",
                "crossProcessCorrelation": "OpenTelemetry/W3C Trace Context",
                "semanticDuplicateOrStaleWorkJudgment": "domain/goal owner",
                "clientToolCatalogFreshness": "MCP connector/client cache",
            },
        },
    }

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
