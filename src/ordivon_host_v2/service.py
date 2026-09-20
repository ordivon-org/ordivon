from __future__ import annotations

import json
import time
from typing import Any

import psycopg
from psycopg.rows import dict_row

from .attention import build_attention_delta
from .canonical import canonical_digest
from .cursor import decode_cursor, encode_cursor
from .errors import ConflictError, TaskNotFound
from .models import Admission, CheckpointInput, MutationResult, TaskState, TaskView


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
        if row is None or int(row["schema_version"]) != 5:
            observed = None if row is None else int(row["schema_version"])
            raise RuntimeError(
                f"Host v2 schema is not at required version 5 (observed={observed}); "
                "run alembic upgrade head"
            )

    def status(self, detail: str = "summary", recent_limit: int = 5) -> dict[str, Any]:
        if detail not in {"summary", "integrity", "history"}:
            raise ValueError("detail must be summary, integrity, or history")
        if not 0 <= recent_limit <= 100:
            raise ValueError("recentLimit must be in [0,100]")
        observed_at_ms = time.time_ns() // 1_000_000
        with psycopg.connect(self.dsn, row_factory=dict_row) as conn:
            schema_row = conn.execute(
                "SELECT schema_version FROM host_v2_schema WHERE singleton"
            ).fetchone()
            if schema_row is None:
                raise RuntimeError("Host v2 schema is not initialized")
            schema_version = int(schema_row["schema_version"])
            state_rows = conn.execute(
                "SELECT state,count(*) AS value FROM tasks GROUP BY state"
            ).fetchall()
            tasks_by_state = {row["state"]: int(row["value"]) for row in state_rows}
            task_count = sum(tasks_by_state.values())
            terminal_count = tasks_by_state.get("completed", 0) + tasks_by_state.get("abandoned", 0)
            event_count = int(
                conn.execute("SELECT count(*) AS value FROM task_events").fetchone()["value"]
            )
            board_row = conn.execute(
                "SELECT count(*) AS messages,COALESCE(max(sequence),0) AS high FROM board_messages"
            ).fetchone()
            recent_rows = []
            if recent_limit:
                recent_rows = conn.execute(
                    "SELECT e.task_id,e.revision,e.event_type,e.created_at,e.checkpoint_digest,t.state "
                    "FROM task_events e JOIN tasks t USING(task_id) "
                    "ORDER BY e.created_at DESC,e.task_id DESC,e.revision DESC LIMIT %s",
                    (recent_limit,),
                ).fetchall()

            doctor = None
            if detail != "summary":
                checks: list[dict[str, Any]] = []

                def add_check(name: str, ok: bool, detail_value: str) -> None:
                    checks.append(
                        {"name": name, "status": "ok" if ok else "error", "detail": detail_value}
                    )

                add_check("postgres.schema", schema_version == 5, str(schema_version))
                current_checkpoint_bad = int(
                    conn.execute(
                        "SELECT count(*) AS value FROM tasks t LEFT JOIN checkpoints c "
                        "ON c.task_id=t.task_id AND c.revision=t.revision "
                        "WHERE c.task_id IS NULL OR c.checkpoint_digest<>t.current_checkpoint_digest"
                    ).fetchone()["value"]
                )
                add_check(
                    "task.current_checkpoint",
                    current_checkpoint_bad == 0,
                    f"invalid={current_checkpoint_bad}",
                )
                current_event_bad = int(
                    conn.execute(
                        "SELECT count(*) AS value FROM tasks t LEFT JOIN task_events e "
                        "ON e.task_id=t.task_id AND e.revision=t.revision "
                        "WHERE e.task_id IS NULL OR e.resulting_state<>t.state "
                        "OR e.checkpoint_digest<>t.current_checkpoint_digest"
                    ).fetchone()["value"]
                )
                add_check(
                    "task.current_event", current_event_bad == 0, f"invalid={current_event_bad}"
                )
                receipt_bad = int(
                    conn.execute(
                        "SELECT count(*) AS value FROM command_receipts WHERE response IS NULL"
                    ).fetchone()["value"]
                )
                add_check(
                    "command_receipts.complete", receipt_bad == 0, f"incomplete={receipt_bad}"
                )
                reply_bad = int(
                    conn.execute(
                        "SELECT count(*) AS value FROM board_messages c LEFT JOIN board_messages p "
                        "ON p.client_message_id=c.reply_to_client_message_id "
                        "WHERE c.reply_to_client_message_id IS NOT NULL AND p.client_message_id IS NULL"
                    ).fetchone()["value"]
                )
                add_check("board.reply_integrity", reply_bad == 0, f"dangling={reply_bad}")

                if detail == "history":
                    task_history_bad = int(
                        conn.execute(
                            "SELECT count(*) AS value FROM (SELECT t.task_id,t.revision,"
                            "count(DISTINCT c.revision) AS checkpoints,count(DISTINCT e.revision) AS events,"
                            "min(c.revision) AS cmin,max(c.revision) AS cmax,min(e.revision) AS emin,max(e.revision) AS emax "
                            "FROM tasks t LEFT JOIN checkpoints c USING(task_id) LEFT JOIN task_events e USING(task_id) "
                            "GROUP BY t.task_id,t.revision) x WHERE checkpoints<>revision OR events<>revision "
                            "OR cmin<>1 OR cmax<>revision OR emin<>1 OR emax<>revision"
                        ).fetchone()["value"]
                    )
                    add_check(
                        "task.history_contiguous",
                        task_history_bad == 0,
                        f"invalidTasks={task_history_bad}",
                    )
                    digest_bad = 0
                    for row in conn.execute(
                        "SELECT checkpoint_digest,payload FROM checkpoints ORDER BY task_id,revision"
                    ).fetchall():
                        payload = row["payload"]
                        if isinstance(payload, str):
                            payload = json.loads(payload)
                        if canonical_digest(payload) != row["checkpoint_digest"]:
                            digest_bad += 1
                    add_check(
                        "checkpoint.history_digest",
                        digest_bad == 0,
                        f"invalid={digest_bad}",
                    )
                doctor = {
                    "healthy": all(item["status"] == "ok" for item in checks),
                    "checks": checks,
                }

            tool_names = [
                "host.status",
                "attention.delta",
                "board.list",
                "board.search",
                "board.post",
                "task.observe",
                "task.list",
                "task.resume",
                "task.adopt",
                "task.checkpoint",
            ]
            return {
                "schemaVersion": 1,
                "kind": "ordivon.host-status",
                "observedAtMs": observed_at_ms,
                "detail": detail,
                "interface": {
                    "surfaceVersion": 9,
                    "toolCount": len(tool_names),
                    "toolNames": tool_names,
                    "readTools": [
                        "host.status",
                        "attention.delta",
                        "board.list",
                        "board.search",
                        "task.observe",
                        "task.list",
                        "task.resume",
                    ],
                    "writeTools": ["board.post", "task.adopt", "task.checkpoint"],
                    "runtimeProxy": False,
                },
                "authority": {
                    "journalBackend": "postgresql",
                    "journalSchema": schema_version,
                    "events": event_count,
                    "tasks": task_count,
                    "terminalTasks": terminal_count,
                    "tasksByState": tasks_by_state,
                    "leases": 0,
                },
                "board": {
                    "messages": int(board_row["messages"]),
                    "lastSequence": int(board_row["high"]),
                    "truthRole": "durable-collaboration-messages",
                },
                "deployment": {
                    "status": "not-observed",
                    "releaseId": None,
                    "deployedRevision": None,
                },
                "continuity": {
                    "active": tasks_by_state.get("open", 0),
                    "terminal": terminal_count,
                },
                "recentActivity": [
                    {
                        "taskId": row["task_id"],
                        "revision": int(row["revision"]),
                        "eventKind": row["event_type"],
                        "recordedAtMs": int(row["created_at"].timestamp() * 1000),
                        "ageMs": max(0, observed_at_ms - int(row["created_at"].timestamp() * 1000)),
                        "payloadDigest": row["checkpoint_digest"],
                        "causedByEventId": None,
                        "currentState": row["state"],
                    }
                    for row in recent_rows
                ],
                "doctor": doctor,
                "truthBoundary": {
                    "host": "authoritative for Host-v2 PostgreSQL continuity and collaboration state",
                    "deployment": "not observed by the Host-v2 semantic core",
                    "runtime": "not checked; Runtime remains independent physical authority",
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
                "INSERT INTO checkpoints(task_id,revision,checkpoint_digest,payload,writer_label) VALUES (%s,1,%s,%s::jsonb,%s)",
                (
                    task_id,
                    checkpoint_digest,
                    json.dumps(checkpoint.payload),
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
                "INSERT INTO checkpoints(task_id,revision,checkpoint_digest,payload,writer_label) VALUES (%s,%s,%s,%s::jsonb,%s)",
                (
                    task_id,
                    next_revision,
                    checkpoint_digest,
                    json.dumps(checkpoint.payload),
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
    ) -> tuple[list[dict[str, Any]], bool, str | None]:
        """Return one compact current-task inventory page without hydrating checkpoints."""
        if not 1 <= limit <= 500:
            raise ValueError("limit must be in [1,500]")
        scope = {
            "includeTerminal": include_terminal,
            "goalId": goal_id,
            "runtimeWorkspaceId": runtime_workspace_id,
        }
        clauses = [] if include_terminal else ["t.state='open'"]
        params: list[Any] = []
        if goal_id is not None:
            clauses.append("t.goal_id=%s")
            params.append(goal_id)
        if runtime_workspace_id is not None:
            clauses.append("c.payload #>> '{runtime,workspaceId}' = %s")
            params.append(runtime_workspace_id)
        if cursor is not None:
            position = decode_cursor(cursor, "task.list", scope)
            created_at = position.get("createdAt")
            task_id = position.get("taskId")
            if not isinstance(created_at, str) or not isinstance(task_id, str):
                raise ValueError("task.list cursor position is invalid")
            clauses.append(
                "(t.created_at < %s::timestamptz OR (t.created_at = %s::timestamptz AND t.task_id < %s))"
            )
            params.extend([created_at, created_at, task_id])
        where = "WHERE " + " AND ".join(clauses) if clauses else ""
        params.append(limit + 1)
        with psycopg.connect(self.dsn, row_factory=dict_row) as conn:
            rows = conn.execute(
                "SELECT t.task_id,t.goal_id,t.revision,t.state,t.created_at,"
                "c.checkpoint_digest,c.writer_label FROM tasks t "
                "JOIN checkpoints c ON c.task_id=t.task_id AND c.revision=t.revision "
                f"{where} ORDER BY t.created_at DESC,t.task_id DESC LIMIT %s",
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
            }
            for row in page
        ]
        next_cursor = None
        if has_more and page:
            last = page[-1]
            next_cursor = encode_cursor(
                "task.list",
                scope,
                {"createdAt": last["created_at"].isoformat(), "taskId": last["task_id"]},
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
        if isinstance(payload, str):
            payload = json.loads(payload)
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
        replay = json.loads(response) if isinstance(response, str) else dict(response)
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
            "UPDATE command_receipts SET response=%s::jsonb "
            "WHERE client_request_id=%s AND operation=%s AND request_digest=%s AND response IS NULL RETURNING client_request_id",
            (
                json.dumps(result.model_dump(mode="json"), separators=(",", ":")),
                client_request_id,
                operation,
                request_digest,
            ),
        ).fetchone()
        if updated is None:
            raise RuntimeError("idempotency claim could not be finalized")
