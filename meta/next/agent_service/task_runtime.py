from __future__ import annotations

import json
import sqlite3
import time
import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .slice1 import AgentServiceSlice1, CarrierProviderAdapter, ServiceEventStore


def _now_ns() -> int:
    return time.time_ns()


def _id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex}"


def _canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


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


class RuntimeAdapter(ABC):
    """Mechanical execution seam. It never decides Agent Service Task success."""

    @abstractmethod
    def submit(self, client_request_id: str, execution: dict[str, Any]) -> RuntimeJobRef:
        raise NotImplementedError

    @abstractmethod
    def observe(self, job_id: str) -> RuntimeJobObservation:
        raise NotImplementedError


class TaskStore:
    def __init__(self, connection: sqlite3.Connection, events: ServiceEventStore) -> None:
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
        if not isinstance(required_revision_id, str) or not required_revision_id.strip():
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
            execution=json.loads(_canonical_json(execution)),
            acceptance=json.loads(_canonical_json(acceptance)),
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
                    _canonical_json(task.execution),
                    _canonical_json(task.acceptance),
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
                raise ValueError("runtime artifact acceptance requires kind/artifactKind/value")
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
            "SELECT runtime_job_id FROM service_assignments WHERE id = ?", (assignment_id,)
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
            "UPDATE service_assignments SET state = ? WHERE id = ?", (state, assignment_id)
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


class AssignmentPlanner:
    def __init__(
        self,
        connection: sqlite3.Connection,
        tasks: TaskStore,
        assignments: AssignmentStore,
        instances,
        events: ServiceEventStore,
    ) -> None:
        self._connection = connection
        self._tasks = tasks
        self._assignments = assignments
        self._instances = instances
        self._events = events

    def plan(self, task_id: str) -> Assignment:
        task = self._tasks.get(task_id)
        existing = self._assignments.get_by_task(task_id)
        if existing is not None:
            return existing
        if task.state != "PENDING":
            raise RuntimeError(f"task is not plannable from state {task.state}")
        candidates = [
            instance
            for instance in self._instances.list_all()
            if instance.state == "READY" and instance.revision_id == task.required_revision_id
        ]
        if not candidates:
            raise LookupError("no READY AgentInstance matches required revision")
        candidates.sort(key=lambda item: (item.created_at_ns, item.id))
        chosen = candidates[0]
        with self._connection:
            assignment = self._assignments.create_in_transaction(task.id, chosen.id)
            self._tasks.set_state_in_transaction(task.id, "ASSIGNED")
            self._events.append_in_transaction(
                "Task",
                task.id,
                "TASK_ASSIGNED",
                {"assignmentId": assignment.id, "agentInstanceId": chosen.id},
            )
        return assignment


@dataclass(frozen=True)
class SemanticVerdict:
    accepted: bool
    reason: str | None


class SemanticVerifier:
    def verify(self, acceptance: dict[str, Any], observation: RuntimeJobObservation) -> SemanticVerdict:
        if observation.semantic_completion_evaluated is not False:
            raise RuntimeError("Runtime crossed semantic-completion authority boundary")
        if not observation.execution_terminal:
            raise RuntimeError("semantic verification requires terminal Runtime evidence")
        if observation.status != "succeeded":
            return SemanticVerdict(False, f"runtime:{observation.status}")
        if observation.delivery_disposition != "committed":
            return SemanticVerdict(False, f"runtime:delivery:{observation.delivery_disposition}")
        kind = acceptance["kind"]
        expected = acceptance["value"]
        if kind == "stdout_contains":
            accepted = expected in observation.stdout_tail
        elif kind == "stdout_equals":
            accepted = expected == observation.stdout_tail
        else:
            raise ValueError("unsupported acceptance kind")
        return SemanticVerdict(
            accepted,
            None if accepted else f"acceptance:{kind}:not_satisfied",
        )


class AssignmentActivator:
    TERMINAL_TASKS = {"SUCCEEDED", "FAILED", "CANCELLED"}

    def __init__(
        self,
        connection: sqlite3.Connection,
        tasks: TaskStore,
        assignments: AssignmentStore,
        events: ServiceEventStore,
        runtime: RuntimeAdapter,
        verifier: SemanticVerifier,
    ) -> None:
        self._connection = connection
        self._tasks = tasks
        self._assignments = assignments
        self._events = events
        self._runtime = runtime
        self._verifier = verifier

    def activate(self, assignment_id: str) -> Assignment:
        assignment = self._assignments.get(assignment_id)
        task = self._tasks.get(assignment.task_id)
        if task.state in self.TERMINAL_TASKS:
            return assignment

        if assignment.runtime_job_id is None:
            # This external admission is replay-safe because the Assignment already durably owns
            # a stable Runtime clientRequestId before the call. Response loss replays the same Job.
            runtime_ref = self._runtime.submit(assignment.client_request_id, task.execution)
            with self._connection:
                self._assignments.bind_runtime_job_in_transaction(assignment.id, runtime_ref.job_id)
                self._tasks.set_state_in_transaction(task.id, "RUNNING")
                self._events.append_in_transaction(
                    "Task",
                    task.id,
                    "RUNTIME_JOB_BOUND",
                    {"assignmentId": assignment.id, "runtimeJobId": runtime_ref.job_id},
                )
            assignment = self._assignments.get(assignment.id)
            task = self._tasks.get(task.id)

        assert assignment.runtime_job_id is not None
        observation = self._runtime.observe(assignment.runtime_job_id)
        if observation.semantic_completion_evaluated is not False:
            raise RuntimeError("Runtime crossed semantic-completion authority boundary")
        if not observation.execution_terminal:
            return assignment

        verdict = self._verifier.verify(task.acceptance, observation)
        task_state = "SUCCEEDED" if verdict.accepted else "FAILED"
        assignment_state = "COMPLETED" if verdict.accepted else "FAILED"
        event_type = "TASK_SUCCEEDED" if verdict.accepted else "TASK_FAILED"
        with self._connection:
            self._tasks.set_state_in_transaction(
                task.id,
                task_state,
                failure_reason=verdict.reason,
            )
            self._assignments.set_state_in_transaction(assignment.id, assignment_state)
            self._events.append_in_transaction(
                "Task",
                task.id,
                event_type,
                {
                    "assignmentId": assignment.id,
                    "runtimeJobId": assignment.runtime_job_id,
                    "reason": verdict.reason,
                },
            )
        return self._assignments.get(assignment.id)


class AgentServiceR5:
    """R4 placement slice plus the R5 Task -> Assignment -> Runtime -> verification slice."""

    def __init__(self, placement: AgentServiceSlice1, runtime_adapter: RuntimeAdapter) -> None:
        self._placement = placement
        self._connection = placement._connection
        self._closed = False
        self.definitions = placement.definitions
        self.revisions = placement.revisions
        self.instances = placement.instances
        self.placements = placement.placements
        self.events = placement.events
        self.birth = placement.birth
        self.reconciler = placement.reconciler
        self.tasks = TaskStore(self._connection, self.events)
        self.assignments = AssignmentStore(self._connection)
        self.planner = AssignmentPlanner(
            self._connection,
            self.tasks,
            self.assignments,
            self.instances,
            self.events,
        )
        self.verifier = SemanticVerifier()
        self.activator = AssignmentActivator(
            self._connection,
            self.tasks,
            self.assignments,
            self.events,
            runtime_adapter,
            self.verifier,
        )

    @classmethod
    def open(
        cls,
        db_path: str | Path,
        *,
        carrier_adapter: CarrierProviderAdapter,
        runtime_adapter: RuntimeAdapter,
    ) -> "AgentServiceR5":
        placement = AgentServiceSlice1.open(db_path, carrier_adapter=carrier_adapter)
        cls._initialize_schema(placement._connection)
        return cls(placement, runtime_adapter)

    @staticmethod
    def _initialize_schema(connection: sqlite3.Connection) -> None:
        connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS service_tasks (
                id TEXT PRIMARY KEY,
                description TEXT NOT NULL,
                required_revision_id TEXT NOT NULL REFERENCES agent_revisions(id),
                execution_json TEXT NOT NULL,
                acceptance_json TEXT NOT NULL,
                state TEXT NOT NULL,
                failure_reason TEXT,
                created_at_ns INTEGER NOT NULL
            );

            CREATE TABLE IF NOT EXISTS service_assignments (
                id TEXT PRIMARY KEY,
                task_id TEXT NOT NULL UNIQUE REFERENCES service_tasks(id),
                agent_instance_id TEXT NOT NULL REFERENCES agent_instances(id),
                state TEXT NOT NULL,
                runtime_job_id TEXT,
                client_request_id TEXT NOT NULL UNIQUE,
                created_at_ns INTEGER NOT NULL
            );
            """
        )
        connection.commit()

    def close(self) -> None:
        if self._closed:
            return
        self._closed = True
        self._placement.close()
