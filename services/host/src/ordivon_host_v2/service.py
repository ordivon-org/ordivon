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
    ) -> MutationResult:
        request = {
            "operation": "adopt",
            "taskId": task_id,
            "checkpoint": checkpoint.payload,
            "writerLabel": checkpoint.writer_label,
        }
        request_digest = canonical_digest(request)
        checkpoint_digest = canonical_digest(checkpoint.payload)
        with psycopg.connect(self.dsn, row_factory=dict_row) as conn, conn.transaction():
            replay = self._receipt(conn, client_request_id, "adopt", request_digest)
            if replay is not None:
                return MutationResult.model_validate(replay)

            current = conn.execute(
                "SELECT task_id, revision, state, current_checkpoint_digest FROM tasks WHERE task_id=%s FOR UPDATE",
                (task_id,),
            ).fetchone()
            if current is not None:
                initial = conn.execute(
                    "SELECT checkpoint_digest, payload, writer_label FROM checkpoints WHERE task_id=%s AND revision=1",
                    (task_id,),
                ).fetchone()
                if initial is None or initial["checkpoint_digest"] != checkpoint_digest:
                    raise ConflictError(
                        "task_id already exists with a different initial checkpoint"
                    )
                result = MutationResult(
                    admission=Admission.EXISTING,
                    task=self._resume_in_tx(conn, task_id, None),
                )
                self._record_receipt(conn, client_request_id, "adopt", request_digest, result)
                return result

            conn.execute(
                "INSERT INTO tasks(task_id, revision, state, current_checkpoint_digest) VALUES (%s,1,'open',%s)",
                (task_id, checkpoint_digest),
            )
            conn.execute(
                "INSERT INTO checkpoints(task_id, revision, checkpoint_digest, payload, writer_label) VALUES (%s,1,%s,%s::jsonb,%s)",
                (
                    task_id,
                    checkpoint_digest,
                    json.dumps(checkpoint.payload),
                    checkpoint.writer_label,
                ),
            )
            conn.execute(
                "INSERT INTO task_events(task_id, revision, event_type, request_digest, checkpoint_digest, resulting_state) VALUES (%s,1,'adopt',%s,%s,'open')",
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
            replay = self._receipt(conn, client_request_id, "checkpoint", request_digest)
            if replay is not None:
                return MutationResult.model_validate(replay)

            current = conn.execute(
                "SELECT task_id, revision, state, current_checkpoint_digest FROM tasks WHERE task_id=%s FOR UPDATE",
                (task_id,),
            ).fetchone()
            if current is None:
                raise TaskNotFound(task_id)

            current_revision = int(current["revision"])
            next_revision = expected_revision + 1

            if current_revision == next_revision:
                prior = conn.execute(
                    "SELECT c.checkpoint_digest, e.resulting_state FROM checkpoints c JOIN task_events e USING(task_id, revision) WHERE c.task_id=%s AND c.revision=%s",
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
                "UPDATE tasks SET revision=%s, state=%s, current_checkpoint_digest=%s, updated_at=clock_timestamp() WHERE task_id=%s AND revision=%s AND state='open' RETURNING revision",
                (next_revision, state.value, checkpoint_digest, task_id, expected_revision),
            ).fetchone()
            if updated is None:
                raise ConflictError("same-revision transition lost concurrency race")

            conn.execute(
                "INSERT INTO checkpoints(task_id, revision, checkpoint_digest, payload, writer_label) VALUES (%s,%s,%s,%s::jsonb,%s)",
                (
                    task_id,
                    next_revision,
                    checkpoint_digest,
                    json.dumps(checkpoint.payload),
                    checkpoint.writer_label,
                ),
            )
            conn.execute(
                "INSERT INTO task_events(task_id, revision, event_type, request_digest, checkpoint_digest, resulting_state) VALUES (%s,%s,'checkpoint',%s,%s,%s)",
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

    def list_tasks(self, *, include_terminal: bool = False, limit: int = 100) -> Sequence[TaskView]:
        where = "" if include_terminal else "WHERE state='open'"
        with psycopg.connect(self.dsn, row_factory=dict_row) as conn:
            rows = conn.execute(
                f"SELECT task_id, revision FROM tasks {where} ORDER BY updated_at DESC, task_id LIMIT %s",
                (limit,),
            ).fetchall()
            return tuple(
                self._resume_in_tx(conn, row["task_id"], int(row["revision"])) for row in rows
            )

    def _resume_in_tx(
        self, conn: psycopg.Connection[dict[str, Any]], task_id: str, revision: int | None
    ) -> TaskView:
        if revision is None:
            task = conn.execute(
                "SELECT task_id, revision, state, current_checkpoint_digest FROM tasks WHERE task_id=%s",
                (task_id,),
            ).fetchone()
            if task is None:
                raise TaskNotFound(task_id)
            target_revision = int(task["revision"])
            state = TaskState(task["state"])
        else:
            event = conn.execute(
                "SELECT resulting_state FROM task_events WHERE task_id=%s AND revision=%s",
                (task_id, revision),
            ).fetchone()
            if event is None:
                raise ConflictError(f"task {task_id} has no revision {revision}")
            target_revision = revision
            state = TaskState(event["resulting_state"])

        cp = conn.execute(
            "SELECT checkpoint_digest, payload, writer_label FROM checkpoints WHERE task_id=%s AND revision=%s",
            (task_id, target_revision),
        ).fetchone()
        if cp is None:
            raise RuntimeError("checkpoint history is not revision coherent")
        payload = cp["payload"]
        if isinstance(payload, str):
            payload = json.loads(payload)
        return TaskView(
            task_id=task_id,
            revision=target_revision,
            state=state,
            checkpoint_digest=cp["checkpoint_digest"],
            checkpoint=payload,
            writer_label=cp["writer_label"],
        )

    @staticmethod
    def _receipt(
        conn: psycopg.Connection[dict[str, Any]],
        client_request_id: str,
        operation: str,
        request_digest: str,
    ) -> dict[str, Any] | None:
        row = conn.execute(
            "SELECT operation, request_digest, response FROM command_receipts WHERE client_request_id=%s",
            (client_request_id,),
        ).fetchone()
        if row is None:
            return None
        if row["operation"] != operation or row["request_digest"] != request_digest:
            raise ConflictError("client_request_id was already used for different content")
        response = row["response"]
        return json.loads(response) if isinstance(response, str) else response

    @staticmethod
    def _record_receipt(
        conn: psycopg.Connection[dict[str, Any]],
        client_request_id: str,
        operation: str,
        request_digest: str,
        result: MutationResult,
    ) -> None:
        conn.execute(
            "INSERT INTO command_receipts(client_request_id, operation, request_digest, response) VALUES (%s,%s,%s,%s::jsonb)",
            (
                client_request_id,
                operation,
                request_digest,
                json.dumps(result.model_dump(mode="json"), separators=(",", ":")),
            ),
        )
