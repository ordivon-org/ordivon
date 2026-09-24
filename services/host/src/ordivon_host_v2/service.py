from __future__ import annotations

import time
from typing import Any

import psycopg
from psycopg.rows import dict_row
from psycopg.types.json import Jsonb

from .attention import build_attention_delta
from .canonical import canonical_digest
from .cursor import decode_cursor, encode_cursor
from .errors import ConflictError, TaskNotFound
from .models import Admission, CheckpointInput, MutationResult, TaskState, TaskView

REQUIRED_SCHEMA_VERSION = 8


class HostV2:
    def __init__(self, dsn: str) -> None:
        self.dsn = dsn

    def initialize(self) -> None:
        """Verify that Alembic already initialized the authority schema.

        Schema creation and migration are deliberately not owned by the running Host service.
        Production and tests must run ``alembic upgrade head`` before Host opens authority.
        """
        try:
            with psycopg.connect(self.dsn, row_factory=dict_row) as conn:
                row = conn.execute(
                    "SELECT schema_version FROM host_v2_schema WHERE singleton"
                ).fetchone()
        except psycopg.errors.UndefinedTable as exc:
            raise RuntimeError(
                "Host v2 schema is not initialized; run alembic upgrade head"
            ) from exc
        if row is None or int(row["schema_version"]) != REQUIRED_SCHEMA_VERSION:
            observed = None if row is None else int(row["schema_version"])
            raise RuntimeError(
                f"Host v2 schema is not at required version {REQUIRED_SCHEMA_VERSION} (observed={observed}); "
                "run alembic upgrade head"
            )

    def status(self, detail: str = "summary") -> dict[str, Any]:
        if detail not in {"summary", "integrity", "history"}:
            raise ValueError("detail must be summary, integrity, or history")
        observed_at_ms = time.time_ns() // 1_000_000
        with psycopg.connect(self.dsn, row_factory=dict_row) as conn:
            schema_row = conn.execute(
                "SELECT schema_version FROM host_v2_schema WHERE singleton"
            ).fetchone()
            if schema_row is None:
                raise RuntimeError("Host v2 schema is not initialized")
            schema_version = int(schema_row["schema_version"])

            actor_count = int(
                conn.execute("SELECT count(*) AS value FROM actor_refs").fetchone()["value"]
            )
            work_state_rows = conn.execute(
                "SELECT state,count(*) AS value FROM works GROUP BY state"
            ).fetchall()
            works_by_state = {row["state"]: int(row["value"]) for row in work_state_rows}
            work_count = sum(works_by_state.values())
            snapshot_count = int(
                conn.execute("SELECT count(*) AS value FROM work_snapshots").fetchone()["value"]
            )
            space_count = int(
                conn.execute("SELECT count(*) AS value FROM spaces").fetchone()["value"]
            )
            topic_count = int(
                conn.execute("SELECT count(*) AS value FROM topics").fetchone()["value"]
            )
            message_count = int(
                conn.execute("SELECT count(*) AS value FROM messages").fetchone()["value"]
            )
            subscription_count = int(
                conn.execute("SELECT count(*) AS value FROM subscriptions").fetchone()["value"]
            )
            change_high = int(
                conn.execute("SELECT value FROM swf_change_clock WHERE singleton").fetchone()[
                    "value"
                ]
            )

            doctor = None
            if detail != "summary":
                checks: list[dict[str, Any]] = []

                def add_check(name: str, ok: bool, detail_value: str) -> None:
                    checks.append(
                        {"name": name, "status": "ok" if ok else "error", "detail": detail_value}
                    )

                add_check(
                    "postgres.schema",
                    schema_version == REQUIRED_SCHEMA_VERSION,
                    str(schema_version),
                )
                current_snapshot_bad = int(
                    conn.execute(
                        "SELECT count(*) AS value FROM works w LEFT JOIN work_snapshots s "
                        "ON s.work_ref=w.work_ref AND s.revision=w.current_revision "
                        "WHERE s.work_ref IS NULL OR s.snapshot_digest<>w.current_snapshot_digest"
                    ).fetchone()["value"]
                )
                add_check(
                    "work.current_snapshot",
                    current_snapshot_bad == 0,
                    f"invalid={current_snapshot_bad}",
                )
                message_topic_bad = int(
                    conn.execute(
                        "SELECT count(*) AS value FROM messages m JOIN topics t USING(topic_ref) "
                        "WHERE m.space_ref<>t.space_ref"
                    ).fetchone()["value"]
                )
                add_check(
                    "social.message_topic_space",
                    message_topic_bad == 0,
                    f"invalid={message_topic_bad}",
                )
                reply_bad = int(
                    conn.execute(
                        "SELECT count(*) AS value FROM message_relations r "
                        "JOIN messages s ON s.message_ref=r.source_message_ref "
                        "LEFT JOIN messages t ON t.message_ref=r.target_ref "
                        "WHERE r.relation='reply_to' AND "
                        "(t.message_ref IS NULL OR s.space_ref<>t.space_ref OR s.topic_ref<>t.topic_ref)"
                    ).fetchone()["value"]
                )
                add_check(
                    "social.reply_integrity",
                    reply_bad == 0,
                    f"invalid={reply_bad}",
                )
                cursor_bad = int(
                    conn.execute(
                        "SELECT count(*) AS value FROM attention_cursors WHERE cursor>%s",
                        (change_high,),
                    ).fetchone()["value"]
                )
                add_check(
                    "attention.cursor_bounds",
                    cursor_bad == 0,
                    f"invalid={cursor_bad};high={change_high}",
                )
                receipt_bad = int(
                    conn.execute(
                        "SELECT count(*) AS value FROM command_receipts WHERE response IS NULL"
                    ).fetchone()["value"]
                )
                add_check(
                    "command_receipts.complete",
                    receipt_bad == 0,
                    f"incomplete={receipt_bad}",
                )

                if detail == "history":
                    history_bad = int(
                        conn.execute(
                            "SELECT count(*) AS value FROM ("
                            "SELECT w.work_ref,w.current_revision,count(s.revision) AS snapshots,"
                            "min(s.revision) AS rmin,max(s.revision) AS rmax "
                            "FROM works w LEFT JOIN work_snapshots s USING(work_ref) "
                            "GROUP BY w.work_ref,w.current_revision"
                            ") x WHERE snapshots<>current_revision OR rmin<>1 OR rmax<>current_revision"
                        ).fetchone()["value"]
                    )
                    add_check(
                        "work.snapshot_history_contiguous",
                        history_bad == 0,
                        f"invalidWorks={history_bad}",
                    )
                    digest_bad = 0
                    for row in conn.execute(
                        "SELECT snapshot_digest,payload FROM work_snapshots ORDER BY work_ref,revision"
                    ).fetchall():
                        payload = row["payload"]
                        if (
                            not isinstance(payload, dict)
                            or canonical_digest(payload) != row["snapshot_digest"]
                        ):
                            digest_bad += 1
                    add_check(
                        "work.snapshot_history_digest",
                        digest_bad == 0,
                        f"invalid={digest_bad}",
                    )
                doctor = {
                    "healthy": all(item["status"] == "ok" for item in checks),
                    "checks": checks,
                }

            return {
                "schemaVersion": 3,
                "kind": "ordivon.host-status",
                "observedAtMs": observed_at_ms,
                "detail": detail,
                "authority": {
                    "journalBackend": "postgresql",
                    "journalSchema": schema_version,
                    "actorRefs": actor_count,
                    "works": work_count,
                    "worksByState": works_by_state,
                    "workSnapshots": snapshot_count,
                    "spaces": space_count,
                    "topics": topic_count,
                    "messages": message_count,
                    "subscriptions": subscription_count,
                    "changeHighSequence": change_high,
                },
                "doctor": doctor,
                "truthBoundary": {
                    "host": (
                        "authoritative only for Host Social Work Fabric semantic continuity and "
                        "collaboration records; Runtime, Git, Identity/Security, effect, and domain "
                        "truth are not checked"
                    )
                },
            }

    def adopt(
        self,
        *,
        task_id: str,
        checkpoint: CheckpointInput,
        client_request_id: str,
        goal_id: str | None = None,
    ) -> MutationResult:
        request = {
            "operation": "adopt",
            "taskId": task_id,
            "goalId": goal_id,
            "checkpoint": checkpoint.payload,
            "writerLabel": checkpoint.writer_label,
        }
        request_digest = canonical_digest(request)
        checkpoint_digest = canonical_digest(checkpoint.payload)
        with psycopg.connect(self.dsn, row_factory=dict_row) as conn, conn.transaction():
            replay = self._claim_receipt(conn, client_request_id, "adopt", request_digest)
            if replay is not None:
                return MutationResult.model_validate(replay)

            current = conn.execute(
                "SELECT task_id,goal_id,revision,state,current_checkpoint_digest FROM tasks WHERE task_id=%s FOR UPDATE",
                (task_id,),
            ).fetchone()
            if current is not None:
                initial = conn.execute(
                    "SELECT checkpoint_digest FROM checkpoints WHERE task_id=%s AND revision=1",
                    (task_id,),
                ).fetchone()
                if initial is None or initial["checkpoint_digest"] != checkpoint_digest:
                    raise ConflictError(
                        "task_id already exists with a different initial checkpoint"
                    )
                if goal_id is not None and current["goal_id"] not in {None, goal_id}:
                    raise ConflictError("task_id already exists with a different goal_id")
                result = MutationResult(
                    admission=Admission.EXISTING,
                    task=self._resume_in_tx(conn, task_id, None),
                )
                self._record_receipt(conn, client_request_id, "adopt", request_digest, result)
                return result

            conn.execute(
                "INSERT INTO tasks(task_id,goal_id,revision,state,current_checkpoint_digest) VALUES (%s,%s,1,'open',%s)",
                (task_id, goal_id, checkpoint_digest),
            )
            conn.execute(
                "INSERT INTO checkpoints(task_id,revision,checkpoint_digest,payload,writer_label) VALUES (%s,1,%s,%s,%s)",
                (
                    task_id,
                    checkpoint_digest,
                    Jsonb(checkpoint.payload),
                    checkpoint.writer_label,
                ),
            )
            conn.execute(
                "INSERT INTO task_events(task_id,revision,event_type,request_digest,checkpoint_digest,resulting_state) VALUES (%s,1,'adopt',%s,%s,'open')",
                (task_id, request_digest, checkpoint_digest),
            )
            result = MutationResult(
                admission=Admission.COMMITTED,
                task=self._resume_in_tx(conn, task_id, 1),
            )
            self._record_receipt(conn, client_request_id, "adopt", request_digest, result)
            return result

    def checkpoint(
        self,
        *,
        task_id: str,
        expected_revision: int,
        checkpoint: CheckpointInput,
        client_request_id: str,
        state: TaskState = TaskState.OPEN,
    ) -> MutationResult:
        request = {
            "operation": "checkpoint",
            "taskId": task_id,
            "expectedRevision": expected_revision,
            "checkpoint": checkpoint.payload,
            "writerLabel": checkpoint.writer_label,
            "state": state.value,
        }
        request_digest = canonical_digest(request)
        checkpoint_digest = canonical_digest(checkpoint.payload)
        with psycopg.connect(self.dsn, row_factory=dict_row) as conn, conn.transaction():
            replay = self._claim_receipt(conn, client_request_id, "checkpoint", request_digest)
            if replay is not None:
                return MutationResult.model_validate(replay)

            current = conn.execute(
                "SELECT task_id,revision,state,current_checkpoint_digest FROM tasks WHERE task_id=%s FOR UPDATE",
                (task_id,),
            ).fetchone()
            if current is None:
                raise TaskNotFound(task_id)

            current_revision = int(current["revision"])
            next_revision = expected_revision + 1
            if current_revision == next_revision:
                prior = conn.execute(
                    "SELECT c.checkpoint_digest,e.resulting_state FROM checkpoints c JOIN task_events e USING(task_id,revision) WHERE c.task_id=%s AND c.revision=%s",
                    (task_id, next_revision),
                ).fetchone()
                if (
                    prior is not None
                    and prior["checkpoint_digest"] == checkpoint_digest
                    and prior["resulting_state"] == state.value
                ):
                    result = MutationResult(
                        admission=Admission.EXISTING,
                        task=self._resume_in_tx(conn, task_id, next_revision),
                    )
                    self._record_receipt(
                        conn, client_request_id, "checkpoint", request_digest, result
                    )
                    return result

            if current_revision != expected_revision:
                raise ConflictError(
                    f"expected revision {expected_revision}, current revision is {current_revision}"
                )
            if current["state"] != TaskState.OPEN.value:
                raise ConflictError("terminal task cannot be checkpointed or reopened")

            updated = conn.execute(
                "UPDATE tasks SET revision=%s,state=%s,current_checkpoint_digest=%s,updated_at=clock_timestamp() "
                "WHERE task_id=%s AND revision=%s AND state='open' RETURNING revision",
                (next_revision, state.value, checkpoint_digest, task_id, expected_revision),
            ).fetchone()
            if updated is None:
                raise ConflictError("same-revision transition lost concurrency race")

            conn.execute(
                "INSERT INTO checkpoints(task_id,revision,checkpoint_digest,payload,writer_label) VALUES (%s,%s,%s,%s,%s)",
                (
                    task_id,
                    next_revision,
                    checkpoint_digest,
                    Jsonb(checkpoint.payload),
                    checkpoint.writer_label,
                ),
            )
            conn.execute(
                "INSERT INTO task_events(task_id,revision,event_type,request_digest,checkpoint_digest,resulting_state) VALUES (%s,%s,'checkpoint',%s,%s,%s)",
                (task_id, next_revision, request_digest, checkpoint_digest, state.value),
            )
            result = MutationResult(
                admission=Admission.COMMITTED,
                task=self._resume_in_tx(conn, task_id, next_revision),
            )
            self._record_receipt(conn, client_request_id, "checkpoint", request_digest, result)
            return result

    def resume(self, task_id: str, expected_revision: int | None = None) -> TaskView:
        with psycopg.connect(self.dsn, row_factory=dict_row) as conn, conn.transaction():
            conn.execute("SET TRANSACTION ISOLATION LEVEL REPEATABLE READ, READ ONLY")
            return self._resume_in_tx(conn, task_id, expected_revision)

    def observe(
        self, task_id: str, expected_revision: int | None = None, event_limit: int = 5
    ) -> dict[str, Any]:
        if not 1 <= event_limit <= 100:
            raise ValueError("eventLimit must be in [1,100]")
        with psycopg.connect(self.dsn, row_factory=dict_row) as conn, conn.transaction():
            conn.execute("SET TRANSACTION ISOLATION LEVEL REPEATABLE READ, READ ONLY")
            task = self._resume_in_tx(conn, task_id, expected_revision)
            events = conn.execute(
                "SELECT revision,event_type,resulting_state,created_at FROM task_events "
                "WHERE task_id=%s AND revision<=%s ORDER BY revision DESC LIMIT %s",
                (task_id, task.revision, event_limit),
            ).fetchall()
            return {
                "schemaVersion": 3,
                "kind": "ordivon.host-task-observation",
                "task": task.model_dump(mode="json"),
                "recentEvents": [
                    {
                        "revision": int(row["revision"]),
                        "eventType": row["event_type"],
                        "state": row["resulting_state"],
                        "createdAt": row["created_at"].isoformat(),
                    }
                    for row in events
                ],
                "truthBoundary": "Host continuity mechanics only; checkpoint claims and foreign references require owner-native revalidation",
            }

    def list_task_summaries_page(
        self,
        *,
        include_terminal: bool = False,
        limit: int = 100,
        goal_id: str | None = None,
        runtime_workspace_id: str | None = None,
        cursor: str | None = None,
        sort_key: str = "created",
    ) -> tuple[list[dict[str, Any]], bool, str | None]:
        """Return one compact current-task inventory page without hydrating checkpoints."""
        if not 1 <= limit <= 500:
            raise ValueError("limit must be in [1,500]")
        if sort_key not in {"created", "updated"}:
            raise ValueError("sortKey must be created or updated")
        scope = {
            "includeTerminal": include_terminal,
            "goalId": goal_id,
            "runtimeWorkspaceId": runtime_workspace_id,
        }
        if sort_key != "created":
            scope["sortKey"] = sort_key
        clauses = [] if include_terminal else ["t.state='open'"]
        params: list[Any] = []
        if goal_id is not None:
            clauses.append("t.goal_id=%s")
            params.append(goal_id)
        if runtime_workspace_id is not None:
            clauses.append("c.payload #>> '{runtime,workspaceId}' = %s")
            params.append(runtime_workspace_id)
        sort_column = "created_at" if sort_key == "created" else "updated_at"
        cursor_field = "createdAt" if sort_key == "created" else "updatedAt"
        if cursor is not None:
            position = decode_cursor(cursor, "task.list", scope)
            sort_value = position.get(cursor_field)
            task_id = position.get("taskId")
            if not isinstance(sort_value, str) or not isinstance(task_id, str):
                raise ValueError("task.list cursor position is invalid")
            clauses.append(
                f"(t.{sort_column} < %s::timestamptz OR "
                f"(t.{sort_column} = %s::timestamptz AND t.task_id < %s))"
            )
            params.extend([sort_value, sort_value, task_id])
        where = "WHERE " + " AND ".join(clauses) if clauses else ""
        params.append(limit + 1)
        with psycopg.connect(self.dsn, row_factory=dict_row) as conn:
            rows = conn.execute(
                "SELECT t.task_id,t.goal_id,t.revision,t.state,t.created_at,t.updated_at,"
                "c.checkpoint_digest,c.writer_label FROM tasks t "
                "JOIN checkpoints c ON c.task_id=t.task_id AND c.revision=t.revision "
                f"{where} ORDER BY t.{sort_column} DESC,t.task_id DESC LIMIT %s",
                params,
            ).fetchall()
        has_more = len(rows) > limit
        page = rows[:limit]
        tasks = [
            {
                "task_id": row["task_id"],
                "goal_id": row["goal_id"],
                "revision": int(row["revision"]),
                "state": row["state"],
                "checkpoint_digest": row["checkpoint_digest"],
                "writer_label": row["writer_label"],
                "created_at": row["created_at"].isoformat(),
                "updated_at": row["updated_at"].isoformat(),
            }
            for row in page
        ]
        next_cursor = None
        if has_more and page:
            last = page[-1]
            next_cursor = encode_cursor(
                "task.list",
                scope,
                {cursor_field: last[sort_column].isoformat(), "taskId": last["task_id"]},
            )
        return tasks, has_more, next_cursor

    def attention_delta(self, *, after_sequence: int, limit: int = 100) -> dict[str, Any]:
        return build_attention_delta(self.dsn, after_sequence=after_sequence, limit=limit)

    def _resume_in_tx(
        self, conn: psycopg.Connection[dict[str, Any]], task_id: str, revision: int | None
    ) -> TaskView:
        if revision is None:
            task = conn.execute(
                "SELECT task_id,goal_id,revision,state,current_checkpoint_digest FROM tasks WHERE task_id=%s",
                (task_id,),
            ).fetchone()
            if task is None:
                raise TaskNotFound(task_id)
            target_revision = int(task["revision"])
            state = TaskState(task["state"])
            goal_id = task["goal_id"]
        else:
            event = conn.execute(
                "SELECT e.resulting_state,t.goal_id FROM task_events e JOIN tasks t USING(task_id) "
                "WHERE e.task_id=%s AND e.revision=%s",
                (task_id, revision),
            ).fetchone()
            if event is None:
                raise ConflictError(f"task {task_id} has no revision {revision}")
            target_revision = revision
            state = TaskState(event["resulting_state"])
            goal_id = event["goal_id"]

        cp = conn.execute(
            "SELECT checkpoint_digest,payload,writer_label FROM checkpoints WHERE task_id=%s AND revision=%s",
            (task_id, target_revision),
        ).fetchone()
        if cp is None:
            raise RuntimeError("checkpoint history is not revision coherent")
        payload = cp["payload"]
        if not isinstance(payload, dict):
            raise RuntimeError("checkpoint payload is not a PostgreSQL jsonb object")
        return TaskView(
            task_id=task_id,
            goal_id=goal_id,
            revision=target_revision,
            state=state,
            checkpoint_digest=cp["checkpoint_digest"],
            checkpoint=payload,
            writer_label=cp["writer_label"],
        )

    @staticmethod
    def _claim_receipt(
        conn: psycopg.Connection[dict[str, Any]],
        client_request_id: str,
        operation: str,
        request_digest: str,
    ) -> dict[str, Any] | None:
        claimed = conn.execute(
            "INSERT INTO command_receipts(client_request_id,operation,request_digest,response) "
            "VALUES (%s,%s,%s,NULL) ON CONFLICT (client_request_id) DO NOTHING RETURNING client_request_id",
            (client_request_id, operation, request_digest),
        ).fetchone()
        if claimed is not None:
            return None
        row = conn.execute(
            "SELECT operation,request_digest,response FROM command_receipts WHERE client_request_id=%s",
            (client_request_id,),
        ).fetchone()
        if row is None:
            raise RuntimeError("idempotency claim disappeared after conflict arbitration")
        if row["operation"] != operation or row["request_digest"] != request_digest:
            raise ConflictError("client_request_id was already used for different content")
        response = row["response"]
        if response is None:
            raise RuntimeError("committed idempotency claim is missing its response")
        if not isinstance(response, dict):
            raise RuntimeError("idempotency response is not a PostgreSQL jsonb object")
        replay = dict(response)
        replay["admission"] = Admission.EXISTING.value
        return replay

    @staticmethod
    def _record_receipt(
        conn: psycopg.Connection[dict[str, Any]],
        client_request_id: str,
        operation: str,
        request_digest: str,
        result: MutationResult,
    ) -> None:
        updated = conn.execute(
            "UPDATE command_receipts SET response=%s "
            "WHERE client_request_id=%s AND operation=%s AND request_digest=%s AND response IS NULL RETURNING client_request_id",
            (
                Jsonb(result.model_dump(mode="json")),
                client_request_id,
                operation,
                request_digest,
            ),
        ).fetchone()
        if updated is None:
            raise RuntimeError("idempotency claim could not be finalized")
