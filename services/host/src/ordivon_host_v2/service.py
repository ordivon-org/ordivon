from __future__ import annotations

import json
from collections.abc import Sequence
from typing import Any

import psycopg
from psycopg.rows import dict_row

from .canonical import canonical_digest
from .errors import ConflictError, TaskNotFound
from .models import Admission, CheckpointInput, HostStatus, MutationResult, TaskState, TaskView
from .schema import SCHEMA_SQL


class HostV2:
    def __init__(self, dsn: str) -> None:
        self.dsn = dsn

    def initialize(self) -> None:
        with psycopg.connect(self.dsn, autocommit=True) as conn:
            conn.execute(SCHEMA_SQL)

    def status(self) -> HostStatus:
        with psycopg.connect(self.dsn, row_factory=dict_row) as conn:
            row = conn.execute(
                "SELECT schema_version FROM host_v2_schema WHERE singleton"
            ).fetchone()
            if row is None:
                raise RuntimeError("Host v2 schema is not initialized")
            return HostStatus(schema_version=int(row["schema_version"]))

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
            self._activity(conn, "task.adopt", task_id, 1, {"goalId": goal_id})
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
            self._activity(conn, "task.checkpoint", task_id, next_revision, {"state": state.value})
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
            namespaces = conn.execute(
                "SELECT namespace,task_revision,payload_digest FROM extension_history "
                "WHERE task_id=%s AND task_revision<=%s ORDER BY namespace,task_revision DESC",
                (task_id, task.revision),
            ).fetchall()
            latest: dict[str, dict[str, Any]] = {}
            for row in namespaces:
                latest.setdefault(
                    row["namespace"],
                    {
                        "namespace": row["namespace"],
                        "taskRevision": int(row["task_revision"]),
                        "payloadDigest": row["payload_digest"],
                    },
                )
            return {
                "schemaVersion": 3,
                "kind": "ordivon.host-task-observation",
                "task": task.model_dump(mode="json"),
                "handoff": self._handoff(task),
                "extensionNamespaces": list(latest.values()),
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

    def list_tasks(
        self,
        *,
        include_terminal: bool = False,
        limit: int = 100,
        goal_id: str | None = None,
        runtime_workspace_id: str | None = None,
    ) -> Sequence[TaskView]:
        clauses = [] if include_terminal else ["t.state='open'"]
        params: list[Any] = []
        if goal_id is not None:
            clauses.append("t.goal_id=%s")
            params.append(goal_id)
        if runtime_workspace_id is not None:
            clauses.append("c.payload #>> '{runtime,workspaceId}' = %s")
            params.append(runtime_workspace_id)
        where = "WHERE " + " AND ".join(clauses) if clauses else ""
        params.append(limit)
        with psycopg.connect(self.dsn, row_factory=dict_row) as conn:
            rows = conn.execute(
                "SELECT t.task_id,t.revision FROM tasks t "
                "JOIN checkpoints c ON c.task_id=t.task_id AND c.revision=t.revision "
                f"{where} ORDER BY t.updated_at DESC,t.task_id LIMIT %s",
                params,
            ).fetchall()
            return tuple(
                self._resume_in_tx(conn, row["task_id"], int(row["revision"])) for row in rows
            )

    def attention_delta(self, *, after_sequence: int, limit: int = 100) -> dict[str, Any]:
        if after_sequence < 0 or not 1 <= limit <= 500:
            raise ValueError("invalid attention delta bounds")
        with psycopg.connect(self.dsn, row_factory=dict_row) as conn:
            rows = conn.execute(
                "SELECT sequence,activity_kind,subject_id,task_revision,payload,created_at FROM activity_log "
                "WHERE sequence>%s ORDER BY sequence ASC LIMIT %s",
                (after_sequence, limit),
            ).fetchall()
            high_row = conn.execute(
                "SELECT COALESCE(max(sequence),0) AS value FROM activity_log"
            ).fetchone()
            assert high_row is not None
            high = int(high_row["value"])
            next_after = int(rows[-1]["sequence"]) if rows else after_sequence
            return {
                "schemaVersion": 3,
                "kind": "ordivon.host-attention-delta",
                "requestedAfterSequence": after_sequence,
                "events": [
                    {
                        "sequence": int(row["sequence"]),
                        "activityKind": row["activity_kind"],
                        "subjectId": row["subject_id"],
                        "taskRevision": row["task_revision"],
                        "payload": dict(row["payload"]),
                        "createdAt": row["created_at"].isoformat(),
                    }
                    for row in rows
                ],
                "lastSequence": high,
                "nextAfterSequence": next_after,
                "hasMore": next_after < high,
                "truthBoundary": "change navigation only; not priority, assignment, ownership, or domain truth",
            }

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
    def _handoff(task: TaskView) -> dict[str, Any]:
        return {
            "taskId": task.task_id,
            "taskRevision": task.revision,
            "state": task.state.value,
            "goalId": task.goal_id,
            "nextAdmissible": ["checkpoint"] if task.state is TaskState.OPEN else [],
            "truthBoundary": "navigation capsule only; not current external-owner truth",
        }

    @staticmethod
    def _activity(
        conn: psycopg.Connection[dict[str, Any]],
        kind: str,
        subject_id: str,
        task_revision: int | None,
        payload: dict[str, Any],
    ) -> None:
        conn.execute(
            "INSERT INTO activity_log(activity_kind,subject_id,task_revision,payload) VALUES (%s,%s,%s,%s::jsonb)",
            (kind, subject_id, task_revision, json.dumps(payload, separators=(",", ":"))),
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
