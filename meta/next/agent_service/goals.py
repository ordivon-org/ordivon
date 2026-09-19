from __future__ import annotations

from typing import Any

import hashlib
import sqlite3
import time
import uuid
from dataclasses import dataclass
from pathlib import Path

from .evidence import AgentServiceR6
from .slice1 import ServiceEvent, ServiceEventStore
from .task_runtime import Assignment, AssignmentPlanner, AgentTask, TaskStore


def _now_ns() -> int:
    return time.time_ns()


def _id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex}"


@dataclass(frozen=True)
class Goal:
    id: str
    description: str
    state: str
    failure_reason: str | None
    created_at_ns: int


class GoalStore:
    def __init__(self, connection: sqlite3.Connection, events: ServiceEventStore) -> None:
        self._connection = connection
        self._events = events

    def create(self, description: str) -> Goal:
        if not isinstance(description, str) or not description.strip():
            raise ValueError("goal description must not be empty")
        goal = Goal(
            id=_id("goal"),
            description=description.strip(),
            state="PENDING",
            failure_reason=None,
            created_at_ns=_now_ns(),
        )
        with self._connection:
            self._connection.execute(
                "INSERT INTO service_goals(id, description, state, failure_reason, created_at_ns) VALUES (?, ?, 'PENDING', NULL, ?)",
                (goal.id, goal.description, goal.created_at_ns),
            )
            self._events.append_in_transaction(
                "Goal",
                goal.id,
                "GOAL_CREATED",
                {"description": goal.description},
            )
        return goal

    def get(self, goal_id: str) -> Goal:
        row = self._connection.execute(
            "SELECT id, description, state, failure_reason, created_at_ns FROM service_goals WHERE id = ?",
            (goal_id,),
        ).fetchone()
        if row is None:
            raise KeyError(goal_id)
        return Goal(
            id=row["id"],
            description=row["description"],
            state=row["state"],
            failure_reason=row["failure_reason"],
            created_at_ns=row["created_at_ns"],
        )

    def set_state_in_transaction(
        self, goal_id: str, state: str, failure_reason: str | None = None
    ) -> None:
        cursor = self._connection.execute(
            "UPDATE service_goals SET state = ?, failure_reason = ? WHERE id = ?",
            (state, failure_reason, goal_id),
        )
        if cursor.rowcount != 1:
            raise KeyError(goal_id)


class GoalGraphMutationGuard:
    """Freeze Goal graph structure once semantic execution starts."""

    def __init__(self, connection: sqlite3.Connection, goals: GoalStore, tasks: TaskStore) -> None:
        self._connection = connection
        self._goals = goals
        self._tasks = tasks

    def assert_mutable(self, goal_id: str) -> None:
        goal = self._goals.get(goal_id)
        if goal.state != "PENDING":
            raise RuntimeError(f"Goal graph is frozen once Goal state is {goal.state}")
        rows = self._connection.execute(
            "SELECT task_id FROM goal_task_links WHERE goal_id = ? ORDER BY ordinal, task_id",
            (goal_id,),
        ).fetchall()
        if any(self._tasks.get(row["task_id"]).state != "PENDING" for row in rows):
            raise RuntimeError("Goal graph is frozen once any linked Task leaves PENDING")


class GoalTaskLinkStore:
    """Durable Goal-to-Task membership and stable Goal-local ordering."""

    def __init__(
        self,
        connection: sqlite3.Connection,
        goals: GoalStore,
        tasks: TaskStore,
        mutation_guard: GoalGraphMutationGuard,
    ) -> None:
        self._connection = connection
        self._goals = goals
        self._tasks = tasks
        self._guard = mutation_guard

    def attach(self, goal_id: str, task_id: str) -> None:
        self._guard.assert_mutable(goal_id)
        self._tasks.get(task_id)
        existing = self._connection.execute(
            "SELECT goal_id FROM goal_task_links WHERE task_id = ?", (task_id,)
        ).fetchone()
        if existing is not None:
            if existing["goal_id"] != goal_id:
                raise ValueError("Task is already attached to a different Goal")
            return
        row = self._connection.execute(
            "SELECT COALESCE(MAX(ordinal), 0) AS max_ordinal FROM goal_task_links WHERE goal_id = ?",
            (goal_id,),
        ).fetchone()
        ordinal = int(row["max_ordinal"]) + 1
        with self._connection:
            self._connection.execute(
                "INSERT INTO goal_task_links(goal_id, task_id, ordinal, created_at_ns) VALUES (?, ?, ?, ?)",
                (goal_id, task_id, ordinal, _now_ns()),
            )

    def goal_for_task(self, task_id: str) -> Goal:
        row = self._connection.execute(
            "SELECT goal_id FROM goal_task_links WHERE task_id = ?", (task_id,)
        ).fetchone()
        if row is None:
            raise LookupError(f"Task {task_id} is not attached to a Goal")
        return self._goals.get(row["goal_id"])

    def tasks_for_goal(self, goal_id: str) -> list[AgentTask]:
        self._goals.get(goal_id)
        rows = self._connection.execute(
            "SELECT task_id FROM goal_task_links WHERE goal_id = ? ORDER BY ordinal, task_id",
            (goal_id,),
        ).fetchall()
        return [self._tasks.get(row["task_id"]) for row in rows]


class TaskDependencyStore:
    """Durable same-Goal DAG edges with cycle rejection."""

    def __init__(
        self,
        connection: sqlite3.Connection,
        links: GoalTaskLinkStore,
        mutation_guard: GoalGraphMutationGuard,
    ) -> None:
        self._connection = connection
        self._links = links
        self._guard = mutation_guard

    def dependencies_of(self, task_id: str) -> list[str]:
        self._links.goal_for_task(task_id)
        rows = self._connection.execute(
            "SELECT depends_on_task_id FROM task_dependencies WHERE task_id = ? ORDER BY created_at_ns, depends_on_task_id",
            (task_id,),
        ).fetchall()
        return [row["depends_on_task_id"] for row in rows]

    def add(self, task_id: str, depends_on_task_id: str) -> None:
        if task_id == depends_on_task_id:
            raise ValueError("Task cannot depend on itself")
        goal = self._links.goal_for_task(task_id)
        self._guard.assert_mutable(goal.id)
        dependency_goal = self._links.goal_for_task(depends_on_task_id)
        if goal.id != dependency_goal.id:
            raise ValueError("Task dependencies must remain inside one Goal")
        if self._reachable(depends_on_task_id, task_id):
            raise ValueError("Task dependency would create a cycle")
        with self._connection:
            self._connection.execute(
                "INSERT OR IGNORE INTO task_dependencies(task_id, depends_on_task_id, created_at_ns) VALUES (?, ?, ?)",
                (task_id, depends_on_task_id, _now_ns()),
            )

    def _reachable(self, start_task_id: str, target_task_id: str) -> bool:
        stack = [start_task_id]
        seen: set[str] = set()
        while stack:
            current = stack.pop()
            if current == target_task_id:
                return True
            if current in seen:
                continue
            seen.add(current)
            rows = self._connection.execute(
                "SELECT depends_on_task_id FROM task_dependencies WHERE task_id = ?",
                (current,),
            ).fetchall()
            stack.extend(row["depends_on_task_id"] for row in rows)
        return False


class TaskReadinessProjector:
    """Derived Task readiness: no persisted READY/BLOCKED state."""

    def __init__(
        self, tasks: TaskStore, links: GoalTaskLinkStore, dependencies: TaskDependencyStore
    ) -> None:
        self._tasks = tasks
        self._links = links
        self._dependencies = dependencies

    def is_ready(self, task_id: str) -> bool:
        task = self._tasks.get(task_id)
        self._links.goal_for_task(task_id)
        if task.state != "PENDING":
            return False
        return all(
            self._tasks.get(dep).state == "SUCCEEDED"
            for dep in self._dependencies.dependencies_of(task_id)
        )

    def ready_tasks(self, goal_id: str) -> list[AgentTask]:
        return [task for task in self._links.tasks_for_goal(goal_id) if self.is_ready(task.id)]


class GoalTaskGraph:
    """Compatibility facade over the four R7 graph bricks."""

    def __init__(
        self,
        links: GoalTaskLinkStore,
        dependencies: TaskDependencyStore,
        readiness: TaskReadinessProjector,
        mutation_guard: GoalGraphMutationGuard,
    ) -> None:
        self.links = links
        self.dependencies = dependencies
        self.readiness = readiness
        self.mutation_guard = mutation_guard

    def attach(self, goal_id: str, task_id: str) -> None:
        self.links.attach(goal_id, task_id)

    def goal_for_task(self, task_id: str) -> Goal:
        return self.links.goal_for_task(task_id)

    def tasks_for_goal(self, goal_id: str) -> list[AgentTask]:
        return self.links.tasks_for_goal(goal_id)

    def dependencies_of(self, task_id: str) -> list[str]:
        return self.dependencies.dependencies_of(task_id)

    def add_dependency(self, task_id: str, depends_on_task_id: str) -> None:
        self.dependencies.add(task_id, depends_on_task_id)

    def is_ready(self, task_id: str) -> bool:
        return self.readiness.is_ready(task_id)

    def ready_tasks(self, goal_id: str) -> list[AgentTask]:
        return self.readiness.ready_tasks(goal_id)


class GoalAssignmentPlanner:
    def __init__(self, readiness: TaskReadinessProjector, planner: AssignmentPlanner) -> None:
        self._readiness = readiness
        self._planner = planner

    def plan(self, task_id: str) -> Assignment:
        if not self._readiness.is_ready(task_id):
            raise LookupError("Task is blocked by dependencies or is not PENDING")
        return self._planner.plan(task_id)


class GoalReconciler:
    def __init__(
        self,
        connection: sqlite3.Connection,
        goals: GoalStore,
        links: GoalTaskLinkStore,
        events: ServiceEventStore,
    ) -> None:
        self._connection = connection
        self._goals = goals
        self._links = links
        self._events = events

    def reconcile(self, goal_id: str) -> Goal:
        current = self._goals.get(goal_id)
        tasks = self._links.tasks_for_goal(goal_id)
        derived_state = "PENDING"
        reason: str | None = None
        failed = next((task for task in tasks if task.state in {"FAILED", "CANCELLED"}), None)
        if failed is not None:
            derived_state = "FAILED"
            reason = f"task:{failed.id}:{failed.state}:{failed.failure_reason or ''}".rstrip(":")
        elif tasks and all(task.state == "SUCCEEDED" for task in tasks):
            derived_state = "SUCCEEDED"
        elif any(task.state != "PENDING" for task in tasks):
            derived_state = "RUNNING"

        if current.state == derived_state and current.failure_reason == reason:
            return current
        if current.state in {"SUCCEEDED", "FAILED"}:
            raise RuntimeError("terminal Goal state cannot be reinterpreted")

        event_type = {
            "PENDING": "GOAL_PENDING",
            "RUNNING": "GOAL_RUNNING",
            "SUCCEEDED": "GOAL_SUCCEEDED",
            "FAILED": "GOAL_FAILED",
        }[derived_state]
        with self._connection:
            self._goals.set_state_in_transaction(goal_id, derived_state, reason)
            self._events.append_in_transaction(
                "Goal",
                goal_id,
                event_type,
                {
                    "state": derived_state,
                    "failureReason": reason,
                    "taskCount": len(tasks),
                },
            )
        return self._goals.get(goal_id)


@dataclass(frozen=True)
class BoardMessageRef:
    client_message_id: str
    provider_sequence: int | None = None




@dataclass(frozen=True)
class BoardProjectionReceipt:
    id: str
    service_event_id: str
    goal_id: str
    client_message_id: str
    provider_sequence: int | None
    created_at_ns: int


def _board_projection_receipt_from_event(event: ServiceEvent) -> BoardProjectionReceipt:
    if (
        event.aggregate_type != "BoardProjection"
        or event.event_type != "BoardProjectionCommitted"
    ):
        raise ValueError("event is not a Board projection receipt")
    payload = event.payload
    if payload.get("sourceEventId") != event.aggregate_id:
        raise RuntimeError("Board projection source-event identity mismatch")
    goal_id = payload.get("goalId")
    client_message_id = payload.get("clientMessageId")
    provider_sequence = payload.get("providerSequence")
    if not isinstance(goal_id, str) or not goal_id:
        raise RuntimeError("Board projection receipt lacks goal identity")
    if not isinstance(client_message_id, str) or not client_message_id:
        raise RuntimeError("Board projection receipt lacks client message identity")
    if provider_sequence is not None and not isinstance(provider_sequence, int):
        raise RuntimeError("Board projection provider sequence must be integer or null")
    return BoardProjectionReceipt(
        id=event.id,
        service_event_id=event.aggregate_id,
        goal_id=goal_id,
        client_message_id=client_message_id,
        provider_sequence=provider_sequence,
        created_at_ns=event.created_at_ns,
    )


def _board_projection_receipt_get_by_event(
    events: ServiceEventStore,
    service_event_id: str,
) -> BoardProjectionReceipt | None:
    history = events.list_for("BoardProjection", service_event_id)
    receipts = [item for item in history if item.event_type == "BoardProjectionCommitted"]
    if not receipts:
        return None
    if len(receipts) != 1:
        raise RuntimeError("Board projection receipt stream contains multiple committed receipts")
    return _board_projection_receipt_from_event(receipts[0])


def _board_projection_receipt_create(
    events: ServiceEventStore,
    source_event: ServiceEvent,
    goal_id: str,
    message: BoardMessageRef,
) -> BoardProjectionReceipt:
    event = events.append_once(
        "BoardProjection",
        source_event.id,
        "BoardProjectionCommitted",
        {
            "sourceEventId": source_event.id,
            "goalId": goal_id,
            "clientMessageId": message.client_message_id,
            "providerSequence": message.provider_sequence,
        },
    )
    return _board_projection_receipt_from_event(event)


class GoalBoardProjector:
    """Append-only projection of Goal semantic events into a collaboration Board."""

    TOPIC = "agent-service-goal-projection"
    AUTHOR = "agent-service-board-projector-v1"

    def __init__(
        self,
        goals: GoalStore,
        events: ServiceEventStore,
        adapter: Any | None,
    ) -> None:
        self._goals = goals
        self._events = events
        if adapter is not None and not callable(getattr(adapter, "post", None)):
            raise TypeError("board provider must expose callable post()")
        self._adapter = adapter

    @staticmethod
    def _event_state(event: ServiceEvent) -> str:
        if event.event_type == "GOAL_CREATED":
            return "PENDING"
        value = event.payload.get("state")
        if isinstance(value, str):
            return value
        mapping = {
            "GOAL_PENDING": "PENDING",
            "GOAL_RUNNING": "RUNNING",
            "GOAL_SUCCEEDED": "SUCCEEDED",
            "GOAL_FAILED": "FAILED",
        }
        try:
            return mapping[event.event_type]
        except KeyError as error:
            raise RuntimeError(f"unsupported Goal projection event: {event.event_type}") from error

    def _project_event(self, goal_id: str, event: ServiceEvent) -> BoardProjectionReceipt:
        if self._adapter is None:
            raise RuntimeError("no board provider configured")
        existing = _board_projection_receipt_get_by_event(self._events, event.id)
        if existing is not None:
            return existing
        self._goals.get(goal_id)
        event_state = self._event_state(event)
        digest = hashlib.sha256(event.id.encode("utf-8")).hexdigest()
        client_message_id = f"agent-service-goal-event-v1:{digest}"
        text = (
            f"AGENT SERVICE GOAL PROJECTION v1 / goal={goal_id} / event={event.event_type} "
            f"/ eventState={event_state} / sourceEvent={event.id}. "
            "Projection only; Agent Service remains the semantic Goal/Task authority."
        )
        posted = self._adapter.post(
            client_message_id=client_message_id,
            author_label=self.AUTHOR,
            message=text,
            topic=self.TOPIC,
        )
        if posted.client_message_id != client_message_id:
            raise RuntimeError("Board provider returned mismatched client message identity")
        return _board_projection_receipt_create(self._events, event, goal_id, posted)

    def project_latest(self, goal_id: str) -> BoardProjectionReceipt:
        events = self._events.list_for("Goal", goal_id)
        if not events:
            raise LookupError(f"Goal {goal_id} has no semantic events")
        return self._project_event(goal_id, events[-1])

    def project_pending(self, goal_id: str) -> list[BoardProjectionReceipt]:
        events = self._events.list_for("Goal", goal_id)
        if not events:
            raise LookupError(f"Goal {goal_id} has no semantic events")
        receipts: list[BoardProjectionReceipt] = []
        for event in events:
            receipts.append(self._project_event(goal_id, event))
        return receipts


def _initialize_schema(connection: sqlite3.Connection) -> None:
    legacy_board_projection_receipts = connection.execute(
        "SELECT 1 FROM sqlite_master "
        "WHERE type = 'table' AND name = 'board_projection_receipts'"
    ).fetchone()
    if legacy_board_projection_receipts is not None:
        raise RuntimeError(
            "legacy board_projection_receipts schema is unsupported; "
            "perform explicit destructive migration before opening this revision"
        )
    connection.executescript(
        """
        CREATE TABLE IF NOT EXISTS service_goals (
            id TEXT PRIMARY KEY,
            description TEXT NOT NULL,
            state TEXT NOT NULL,
            failure_reason TEXT,
            created_at_ns INTEGER NOT NULL
        );

        CREATE TABLE IF NOT EXISTS goal_task_links (
            goal_id TEXT NOT NULL REFERENCES service_goals(id),
            task_id TEXT NOT NULL UNIQUE REFERENCES service_tasks(id),
            ordinal INTEGER NOT NULL,
            created_at_ns INTEGER NOT NULL,
            PRIMARY KEY(goal_id, task_id),
            UNIQUE(goal_id, ordinal)
        );

        CREATE TABLE IF NOT EXISTS task_dependencies (
            task_id TEXT NOT NULL REFERENCES service_tasks(id),
            depends_on_task_id TEXT NOT NULL REFERENCES service_tasks(id),
            created_at_ns INTEGER NOT NULL,
            PRIMARY KEY(task_id, depends_on_task_id),
            CHECK(task_id <> depends_on_task_id)
        );

        """
    )
    connection.commit()


class AgentServiceR7:
    """R7 composition: Goal/DAG/convergence/Board projection above R6 durable Task truth."""

    def __init__(self, r6: AgentServiceR6, board_adapter: Any | None) -> None:
        self._r6 = r6
        self._connection = r6._connection
        self.definitions = r6.definitions
        self.revisions = r6.revisions
        self.instances = r6.instances
        self.placements = r6.placements
        self.events = r6.events
        self.reconciler = r6.reconciler
        self.tasks = r6.tasks
        self.assignments = r6.assignments
        self.planner = r6.planner
        self.execution_activator = r6.execution_activator
        self.completion = r6.completion
        self.goals = GoalStore(self._connection, self.events)
        self.goal_graph_guard = GoalGraphMutationGuard(self._connection, self.goals, self.tasks)
        self.goal_task_links = GoalTaskLinkStore(
            self._connection, self.goals, self.tasks, self.goal_graph_guard
        )
        self.task_dependencies = TaskDependencyStore(
            self._connection, self.goal_task_links, self.goal_graph_guard
        )
        self.task_readiness = TaskReadinessProjector(
            self.tasks, self.goal_task_links, self.task_dependencies
        )
        self.task_graph = GoalTaskGraph(
            self.goal_task_links,
            self.task_dependencies,
            self.task_readiness,
            self.goal_graph_guard,
        )
        self.goal_planner = GoalAssignmentPlanner(self.task_readiness, self.planner)
        self.goal_reconciler = GoalReconciler(
            self._connection, self.goals, self.goal_task_links, self.events
        )
        self.board_projector = GoalBoardProjector(
            self.goals,
            self.events,
            board_adapter,
        )

    @classmethod
    def open(
        cls,
        db_path: str | Path,
        *,
        carrier_adapter: Any,
        runtime_adapter: Any,
        artifact_reader: Any,
        board_adapter: Any | None = None,
    ) -> "AgentServiceR7":
        r6 = AgentServiceR6.open(
            db_path,
            carrier_adapter=carrier_adapter,
            runtime_adapter=runtime_adapter,
            artifact_reader=artifact_reader,
        )
        cls._initialize_schema(r6._connection)
        return cls(r6, board_adapter)

    @staticmethod
    def _initialize_schema(connection: sqlite3.Connection) -> None:
        _initialize_schema(connection)

    def close(self) -> None:
        self._r6.close()
