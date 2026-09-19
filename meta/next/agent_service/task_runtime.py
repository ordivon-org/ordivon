from __future__ import annotations

import json
import sqlite3
import time
import uuid
from dataclasses import dataclass
from typing import Any

from .slice1 import ServiceEventStore


def _now_ns() -> int:
    return time.time_ns()


def _id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex}"


@dataclass(frozen=True)
class AgentTask:
    id: str
    description: str
    required_revision_id: str
    execution: dict[str, Any]
    acceptance: dict[str, Any]
    state: str
    failure_reason: str | None
    created_at_ns: int


@dataclass(frozen=True)
class Assignment:
    id: str
    task_id: str
    agent_instance_id: str
    state: str
    runtime_job_id: str | None
    client_request_id: str
    created_at_ns: int


@dataclass(frozen=True)
class RuntimeJobRef:
    job_id: str


@dataclass(frozen=True)
class RuntimeArtifactDescriptor:
    artifact_id: str
    kind: str


@dataclass(frozen=True)
class RuntimeJobObservation:
    job_id: str
    status: str
    execution_terminal: bool
    delivery_disposition: str
    semantic_completion_evaluated: bool
    stdout_tail: str
    stderr_tail: str
    artifacts: tuple[str, ...]
    artifact_descriptors: tuple[RuntimeArtifactDescriptor, ...] = ()


def _require_runtime_provider(provider: Any) -> Any:
    for method_name in ("submit", "observe"):
        if not callable(getattr(provider, method_name, None)):
            raise TypeError(f"runtime provider must expose callable {method_name}()")
    return provider


class TaskStore:
    def __init__(
        self, connection: sqlite3.Connection, events: ServiceEventStore
    ) -> None:
        self._connection = connection
        self._events = events

    def create(
        self,
        *,
        description: str,
        required_revision_id: str,
        execution: dict[str, Any],
        acceptance: dict[str, Any],
    ) -> AgentTask:
        if not isinstance(description, str) or not description.strip():
            raise ValueError("task description must not be empty")
        if (
            not isinstance(required_revision_id, str)
            or not required_revision_id.strip()
        ):
            raise ValueError("required_revision_id must not be empty")
        if not isinstance(execution, dict) or not execution:
            raise ValueError("task execution must be a non-empty object")
        self._validate_acceptance(acceptance)
        revision = self._connection.execute(
            "SELECT 1 FROM agent_revisions WHERE id = ?", (required_revision_id,)
        ).fetchone()
        if revision is None:
            raise KeyError(required_revision_id)
        task = AgentTask(
            id=_id("task"),
            description=description.strip(),
            required_revision_id=required_revision_id,
            execution=json.loads(
                json.dumps(
                    execution, sort_keys=True, separators=(",", ":"), ensure_ascii=False
                )
            ),
            acceptance=json.loads(
                json.dumps(
                    acceptance,
                    sort_keys=True,
                    separators=(",", ":"),
                    ensure_ascii=False,
                )
            ),
            state="PENDING",
            failure_reason=None,
            created_at_ns=_now_ns(),
        )
        with self._connection:
            self._connection.execute(
                """
                INSERT INTO service_tasks(
                    id, description, required_revision_id, execution_json, acceptance_json,
                    state, failure_reason, created_at_ns
                ) VALUES (?, ?, ?, ?, ?, ?, NULL, ?)
                """,
                (
                    task.id,
                    task.description,
                    task.required_revision_id,
                    json.dumps(
                        task.execution,
                        sort_keys=True,
                        separators=(",", ":"),
                        ensure_ascii=False,
                    ),
                    json.dumps(
                        task.acceptance,
                        sort_keys=True,
                        separators=(",", ":"),
                        ensure_ascii=False,
                    ),
                    task.state,
                    task.created_at_ns,
                ),
            )
            self._events.append_in_transaction(
                "Task",
                task.id,
                "TASK_CREATED",
                {"requiredRevisionId": task.required_revision_id},
            )
        return task

    @staticmethod
    def _validate_acceptance(acceptance: dict[str, Any]) -> None:
        if not isinstance(acceptance, dict):
            raise ValueError("task acceptance must be an object")
        kind = acceptance.get("kind")
        if kind in {"stdout_contains", "stdout_equals"}:
            if set(acceptance) != {"kind", "value"}:
                raise ValueError("stdout acceptance requires exactly kind/value")
        elif kind == "runtime_artifact_text_contains":
            if set(acceptance) != {"kind", "artifactKind", "value"}:
                raise ValueError(
                    "runtime artifact acceptance requires kind/artifactKind/value"
                )
            artifact_kind = acceptance.get("artifactKind")
            if not isinstance(artifact_kind, str) or not artifact_kind.strip():
                raise ValueError("artifactKind must be a non-empty string")
        else:
            raise ValueError("unsupported task acceptance kind")
        value = acceptance.get("value")
        if not isinstance(value, str) or not value:
            raise ValueError("task acceptance value must be a non-empty string")

    def get(self, task_id: str) -> AgentTask:
        row = self._connection.execute(
            """
            SELECT id, description, required_revision_id, execution_json, acceptance_json,
                   state, failure_reason, created_at_ns
            FROM service_tasks WHERE id = ?
            """,
            (task_id,),
        ).fetchone()
        if row is None:
            raise KeyError(task_id)
        return self._from_row(row)

    def list_all(self) -> list[AgentTask]:
        rows = self._connection.execute(
            """
            SELECT id, description, required_revision_id, execution_json, acceptance_json,
                   state, failure_reason, created_at_ns
            FROM service_tasks ORDER BY created_at_ns, id
            """
        ).fetchall()
        return [self._from_row(row) for row in rows]

    def set_state_in_transaction(
        self, task_id: str, state: str, *, failure_reason: str | None = None
    ) -> None:
        cursor = self._connection.execute(
            "UPDATE service_tasks SET state = ?, failure_reason = ? WHERE id = ?",
            (state, failure_reason, task_id),
        )
        if cursor.rowcount != 1:
            raise KeyError(task_id)

    @staticmethod
    def _from_row(row: sqlite3.Row) -> AgentTask:
        return AgentTask(
            id=row["id"],
            description=row["description"],
            required_revision_id=row["required_revision_id"],
            execution=json.loads(row["execution_json"]),
            acceptance=json.loads(row["acceptance_json"]),
            state=row["state"],
            failure_reason=row["failure_reason"],
            created_at_ns=row["created_at_ns"],
        )


class AssignmentStore:
    def __init__(self, connection: sqlite3.Connection) -> None:
        self._connection = connection

    def get(self, assignment_id: str) -> Assignment:
        row = self._connection.execute(
            """
            SELECT id, task_id, agent_instance_id, state, runtime_job_id,
                   client_request_id, created_at_ns
            FROM service_assignments WHERE id = ?
            """,
            (assignment_id,),
        ).fetchone()
        if row is None:
            raise KeyError(assignment_id)
        return self._from_row(row)

    def get_by_task(self, task_id: str) -> Assignment | None:
        row = self._connection.execute(
            """
            SELECT id, task_id, agent_instance_id, state, runtime_job_id,
                   client_request_id, created_at_ns
            FROM service_assignments WHERE task_id = ?
            """,
            (task_id,),
        ).fetchone()
        return None if row is None else self._from_row(row)

    def list_all(self) -> list[Assignment]:
        rows = self._connection.execute(
            """
            SELECT id, task_id, agent_instance_id, state, runtime_job_id,
                   client_request_id, created_at_ns
            FROM service_assignments ORDER BY created_at_ns, id
            """
        ).fetchall()
        return [self._from_row(row) for row in rows]

    def create_in_transaction(self, task_id: str, agent_instance_id: str) -> Assignment:
        assignment_id = _id("assign")
        value = Assignment(
            id=assignment_id,
            task_id=task_id,
            agent_instance_id=agent_instance_id,
            state="ASSIGNED",
            runtime_job_id=None,
            client_request_id=f"agent-service:assignment:{assignment_id}:run:v1",
            created_at_ns=_now_ns(),
        )
        self._connection.execute(
            """
            INSERT INTO service_assignments(
                id, task_id, agent_instance_id, state, runtime_job_id,
                client_request_id, created_at_ns
            ) VALUES (?, ?, ?, ?, NULL, ?, ?)
            """,
            (
                value.id,
                value.task_id,
                value.agent_instance_id,
                value.state,
                value.client_request_id,
                value.created_at_ns,
            ),
        )
        return value

    def bind_runtime_job_in_transaction(self, assignment_id: str, job_id: str) -> None:
        row = self._connection.execute(
            "SELECT runtime_job_id FROM service_assignments WHERE id = ?",
            (assignment_id,),
        ).fetchone()
        if row is None:
            raise KeyError(assignment_id)
        existing = row["runtime_job_id"]
        if existing is not None and existing != job_id:
            raise RuntimeError("assignment is already bound to a different Runtime Job")
        self._connection.execute(
            "UPDATE service_assignments SET runtime_job_id = ?, state = 'ACTIVE' WHERE id = ?",
            (job_id, assignment_id),
        )

    def set_state_in_transaction(self, assignment_id: str, state: str) -> None:
        cursor = self._connection.execute(
            "UPDATE service_assignments SET state = ? WHERE id = ?",
            (state, assignment_id),
        )
        if cursor.rowcount != 1:
            raise KeyError(assignment_id)

    @staticmethod
    def _from_row(row: sqlite3.Row) -> Assignment:
        return Assignment(
            id=row["id"],
            task_id=row["task_id"],
            agent_instance_id=row["agent_instance_id"],
            state=row["state"],
            runtime_job_id=row["runtime_job_id"],
            client_request_id=row["client_request_id"],
            created_at_ns=row["created_at_ns"],
        )


@dataclass(frozen=True)
class SemanticVerdict:
    accepted: bool
    reason: str | None
