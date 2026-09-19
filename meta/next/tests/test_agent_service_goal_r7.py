from __future__ import annotations

from tests.agent_service_test_support import open_current

import tempfile
import unittest
from pathlib import Path

from agent_service.goals import BoardMessageRef, _board_projection_receipt_get_by_event
from agent_service.evidence import RuntimeArtifactPayload
from agent_service.slice1 import ProviderObservation
from agent_service.task_runtime import RuntimeJobObservation, RuntimeJobRef


class ReadyCarrier:
    def ensure(self, placement_id: str, agent_instance_id: str, revision_id: str) -> None:
        return None

    def retire(self, placement_id: str, agent_instance_id: str) -> None:
        return None

    def observe(self, placement_id: str) -> ProviderObservation:
        return ProviderObservation(placement_id=placement_id, state="READY", evidence_ref="test://ready")


class FakeRuntime:
    def __init__(self) -> None:
        self.by_request: dict[str, str] = {}
        self.jobs: dict[str, RuntimeJobObservation] = {}

    def submit(self, client_request_id: str, execution: dict) -> RuntimeJobRef:
        job_id = self.by_request.setdefault(client_request_id, f"job-{len(self.by_request)+1}")
        self.jobs.setdefault(
            job_id,
            RuntimeJobObservation(
                job_id=job_id,
                status="working",
                execution_terminal=False,
                delivery_disposition="committed",
                semantic_completion_evaluated=False,
                stdout_tail="",
                stderr_tail="",
                artifacts=(),
            ),
        )
        return RuntimeJobRef(job_id=job_id)

    def observe(self, job_id: str) -> RuntimeJobObservation:
        return self.jobs[job_id]


class NoopArtifactReader:
    def read(self, job_id: str, artifact_id: str) -> RuntimeArtifactPayload:
        raise AssertionError("artifact read not expected")


class FakeBoard:
    def __init__(self) -> None:
        self.messages: dict[str, BoardMessageRef] = {}
        self.calls: list[tuple[str, str, str, str]] = []
        self.fail_after_commit_once = False

    def post(self, *, client_message_id: str, author_label: str, message: str, topic: str) -> BoardMessageRef:
        self.calls.append((client_message_id, author_label, message, topic))
        existing = self.messages.get(client_message_id)
        if existing is None:
            existing = BoardMessageRef(client_message_id=client_message_id, provider_sequence=len(self.messages)+1)
            self.messages[client_message_id] = existing
            if self.fail_after_commit_once:
                self.fail_after_commit_once = False
                raise RuntimeError("simulated response loss after Board commit")
        return existing


class AgentServiceGoalR7Tests(unittest.TestCase):
    def _open(self, db: Path, board: FakeBoard | None = None) -> tuple[object, FakeRuntime]:
        runtime = FakeRuntime()
        service = open_current(
            db,
            carrier_adapter=ReadyCarrier(),
            runtime_adapter=runtime,
            artifact_reader=NoopArtifactReader(),
            board_adapter=board,
        )
        self.addCleanup(service.close)
        return service, runtime

    def _ready_revision(self, service: object) -> str:
        definition = service.definitions.create("worker")
        revision = service.revisions.create(definition.id, {"harness": "test"})
        instance = service.instances.create("request-r7-worker", revision.id)
        service.reconciler.reconcile(instance.id)
        return revision.id

    def _task(self, service: object, revision_id: str, label: str):
        return service.tasks.create(
            description=label,
            required_revision_id=revision_id,
            execution={
                "workspaceId": "ws-test",
                "executable": "/usr/bin/true",
                "args": [],
                "cwdRelative": ".",
                "env": {},
            },
            acceptance={"kind": "stdout_equals", "value": "OK"},
        )

    def test_goal_links_tasks_without_making_board_or_task_store_second_owner(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            service, _ = self._open(Path(tmp) / "service.db")
            revision_id = self._ready_revision(service)
            goal = service.goals.create("ship verified feature")
            first = self._task(service, revision_id, "first")
            second = self._task(service, revision_id, "second")

            service.task_graph.attach(goal.id, first.id)
            service.task_graph.attach(goal.id, second.id)

            self.assertEqual(service.goals.get(goal.id).state, "PENDING")
            self.assertEqual([task.id for task in service.task_graph.tasks_for_goal(goal.id)], [first.id, second.id])
            self.assertIsNone(service.task_graph.goal_for_task(first.id).failure_reason)

    def test_dependency_graph_rejects_cycle_and_cross_goal_edges(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            service, _ = self._open(Path(tmp) / "service.db")
            revision_id = self._ready_revision(service)
            g1 = service.goals.create("g1")
            g2 = service.goals.create("g2")
            a = self._task(service, revision_id, "a")
            b = self._task(service, revision_id, "b")
            c = self._task(service, revision_id, "c")
            service.task_graph.attach(g1.id, a.id)
            service.task_graph.attach(g1.id, b.id)
            service.task_graph.attach(g2.id, c.id)
            service.task_graph.add_dependency(b.id, a.id)

            with self.assertRaises(ValueError):
                service.task_graph.add_dependency(a.id, b.id)
            with self.assertRaises(ValueError):
                service.task_graph.add_dependency(a.id, c.id)

    def test_readiness_is_derived_from_dependencies_not_persisted_as_task_state(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            service, _ = self._open(Path(tmp) / "service.db")
            revision_id = self._ready_revision(service)
            goal = service.goals.create("goal")
            a = self._task(service, revision_id, "a")
            b = self._task(service, revision_id, "b")
            service.task_graph.attach(goal.id, a.id)
            service.task_graph.attach(goal.id, b.id)
            service.task_graph.add_dependency(b.id, a.id)

            self.assertTrue(service.task_graph.is_ready(a.id))
            self.assertFalse(service.task_graph.is_ready(b.id))
            self.assertEqual(service.tasks.get(b.id).state, "PENDING")

            with service._connection:
                service.tasks.set_state_in_transaction(a.id, "SUCCEEDED")

            self.assertTrue(service.task_graph.is_ready(b.id))
            self.assertEqual(service.tasks.get(b.id).state, "PENDING")

    def test_goal_planner_refuses_blocked_task_and_delegates_ready_task(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            service, _ = self._open(Path(tmp) / "service.db")
            revision_id = self._ready_revision(service)
            goal = service.goals.create("goal")
            a = self._task(service, revision_id, "a")
            b = self._task(service, revision_id, "b")
            service.task_graph.attach(goal.id, a.id)
            service.task_graph.attach(goal.id, b.id)
            service.task_graph.add_dependency(b.id, a.id)

            with self.assertRaises(LookupError):
                service.goal_planner.plan(b.id)

            assignment = service.goal_planner.plan(a.id)
            self.assertEqual(assignment.task_id, a.id)

    def test_goal_reconciler_derives_running_success_and_failure_from_tasks(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            service, _ = self._open(Path(tmp) / "service.db")
            revision_id = self._ready_revision(service)
            goal = service.goals.create("goal")
            a = self._task(service, revision_id, "a")
            b = self._task(service, revision_id, "b")
            service.task_graph.attach(goal.id, a.id)
            service.task_graph.attach(goal.id, b.id)

            self.assertEqual(service.goal_reconciler.reconcile(goal.id).state, "PENDING")
            with service._connection:
                service.tasks.set_state_in_transaction(a.id, "RUNNING")
            self.assertEqual(service.goal_reconciler.reconcile(goal.id).state, "RUNNING")
            with service._connection:
                service.tasks.set_state_in_transaction(a.id, "SUCCEEDED")
                service.tasks.set_state_in_transaction(b.id, "SUCCEEDED")
            self.assertEqual(service.goal_reconciler.reconcile(goal.id).state, "SUCCEEDED")

            goal2 = service.goals.create("goal2")
            c = self._task(service, revision_id, "c")
            service.task_graph.attach(goal2.id, c.id)
            with service._connection:
                service.tasks.set_state_in_transaction(c.id, "FAILED", failure_reason="semantic failure")
            failed = service.goal_reconciler.reconcile(goal2.id)
            self.assertEqual(failed.state, "FAILED")
            self.assertIn(c.id, failed.failure_reason or "")

    def test_goal_transition_event_is_not_duplicated_on_reconcile_replay(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            service, _ = self._open(Path(tmp) / "service.db")
            revision_id = self._ready_revision(service)
            goal = service.goals.create("goal")
            task = self._task(service, revision_id, "task")
            service.task_graph.attach(goal.id, task.id)
            with service._connection:
                service.tasks.set_state_in_transaction(task.id, "SUCCEEDED")

            service.goal_reconciler.reconcile(goal.id)
            service.goal_reconciler.reconcile(goal.id)

            event_types = [e.event_type for e in service.events.list_for("Goal", goal.id)]
            self.assertEqual(event_types, ["GOAL_CREATED", "GOAL_SUCCEEDED"])

    def test_board_projection_uses_deterministic_message_identity_and_survives_response_loss(self) -> None:
        board = FakeBoard()
        board.fail_after_commit_once = True
        with tempfile.TemporaryDirectory() as tmp:
            service, _ = self._open(Path(tmp) / "service.db", board)
            revision_id = self._ready_revision(service)
            goal = service.goals.create("goal")
            task = self._task(service, revision_id, "task")
            service.task_graph.attach(goal.id, task.id)
            with service._connection:
                service.tasks.set_state_in_transaction(task.id, "SUCCEEDED")
            service.goal_reconciler.reconcile(goal.id)

            with self.assertRaises(RuntimeError):
                service.board_projector.project_latest(goal.id)

            source_event = service.events.list_for("Goal", goal.id)[-1]
            self.assertIsNone(
                _board_projection_receipt_get_by_event(service.events, source_event.id)
            )
            first_client_id = board.calls[0][0]
            receipt = service.board_projector.project_latest(goal.id)

            self.assertEqual(board.calls[1][0], first_client_id)
            self.assertEqual(receipt.client_message_id, first_client_id)
            self.assertEqual(len(board.messages), 1)
            self.assertEqual(
                _board_projection_receipt_get_by_event(
                    service.events, source_event.id
                ).id,
                receipt.id,
            )

    def test_board_failure_never_rolls_back_or_redefines_goal_truth(self) -> None:
        board = FakeBoard()
        board.fail_after_commit_once = True
        with tempfile.TemporaryDirectory() as tmp:
            service, _ = self._open(Path(tmp) / "service.db", board)
            revision_id = self._ready_revision(service)
            goal = service.goals.create("goal")
            task = self._task(service, revision_id, "task")
            service.task_graph.attach(goal.id, task.id)
            with service._connection:
                service.tasks.set_state_in_transaction(task.id, "SUCCEEDED")
            service.goal_reconciler.reconcile(goal.id)

            with self.assertRaises(RuntimeError):
                service.board_projector.project_latest(goal.id)

            self.assertEqual(service.goals.get(goal.id).state, "SUCCEEDED")
            self.assertEqual(
                [e.event_type for e in service.events.list_for("Goal", goal.id)],
                ["GOAL_CREATED", "GOAL_SUCCEEDED"],
            )

    def test_goal_and_dag_survive_service_reconstruction(self) -> None:
        board = FakeBoard()
        with tempfile.TemporaryDirectory() as tmp:
            db = Path(tmp) / "service.db"
            first, _ = self._open(db, board)
            revision_id = self._ready_revision(first)
            goal = first.goals.create("goal")
            a = self._task(first, revision_id, "a")
            b = self._task(first, revision_id, "b")
            first.task_graph.attach(goal.id, a.id)
            first.task_graph.attach(goal.id, b.id)
            first.task_graph.add_dependency(b.id, a.id)
            first.close()

            second = open_current(
                db,
                carrier_adapter=ReadyCarrier(),
                runtime_adapter=FakeRuntime(),
                artifact_reader=NoopArtifactReader(),
                board_adapter=board,
            )
            self.addCleanup(second.close)

            self.assertEqual(second.goals.get(goal.id).description, "goal")
            self.assertEqual(second.task_graph.dependencies_of(b.id), [a.id])
            self.assertFalse(second.task_graph.is_ready(b.id))


if __name__ == "__main__":
    unittest.main()


class AgentServiceGoalGraphFreezeTests(unittest.TestCase):
    def _service(self, db: Path):
        runtime = FakeRuntime()
        service = open_current(
            db,
            carrier_adapter=ReadyCarrier(),
            runtime_adapter=runtime,
            artifact_reader=NoopArtifactReader(),
        )
        self.addCleanup(service.close)
        definition = service.definitions.create("worker-freeze")
        revision = service.revisions.create(definition.id, {"harness": "test"})
        instance = service.instances.create("request-r7-freeze", revision.id)
        service.reconciler.reconcile(instance.id)
        return service, revision.id

    def _task(self, service: object, revision_id: str, label: str):
        return service.tasks.create(
            description=label,
            required_revision_id=revision_id,
            execution={"workspaceId":"ws-test","executable":"/usr/bin/true","args":[],"cwdRelative":".","env":{}},
            acceptance={"kind":"stdout_equals","value":"OK"},
        )

    def test_goal_graph_freezes_after_any_linked_task_leaves_pending(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            service, revision_id = self._service(Path(tmp) / "service.db")
            goal = service.goals.create("frozen graph")
            a = self._task(service, revision_id, "a")
            b = self._task(service, revision_id, "b")
            c = self._task(service, revision_id, "c")
            service.task_graph.attach(goal.id, a.id)
            service.task_graph.attach(goal.id, b.id)
            with service._connection:
                service.tasks.set_state_in_transaction(a.id, "RUNNING")

            with self.assertRaises(RuntimeError):
                service.task_graph.attach(goal.id, c.id)
            with self.assertRaises(RuntimeError):
                service.task_graph.add_dependency(b.id, a.id)

    def test_terminal_goal_rejects_new_task_membership(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            service, revision_id = self._service(Path(tmp) / "service.db")
            goal = service.goals.create("terminal goal")
            a = self._task(service, revision_id, "a")
            service.task_graph.attach(goal.id, a.id)
            with service._connection:
                service.tasks.set_state_in_transaction(a.id, "SUCCEEDED")
            service.goal_reconciler.reconcile(goal.id)
            extra = self._task(service, revision_id, "extra")

            with self.assertRaises(RuntimeError):
                service.task_graph.attach(goal.id, extra.id)


class AgentServiceBoardCatchupTests(unittest.TestCase):
    def test_project_pending_catches_up_every_goal_event_in_order(self) -> None:
        board = FakeBoard()
        with tempfile.TemporaryDirectory() as tmp:
            runtime = FakeRuntime()
            service = open_current(
                Path(tmp) / "service.db",
                carrier_adapter=ReadyCarrier(),
                runtime_adapter=runtime,
                artifact_reader=NoopArtifactReader(),
                board_adapter=board,
            )
            self.addCleanup(service.close)
            definition = service.definitions.create("worker-board-catchup")
            revision = service.revisions.create(definition.id, {"harness":"test"})
            instance = service.instances.create("request-r7-board-catchup", revision.id)
            service.reconciler.reconcile(instance.id)
            goal = service.goals.create("catch up")
            task = service.tasks.create(
                description="task",
                required_revision_id=revision.id,
                execution={"workspaceId":"ws-test","executable":"/usr/bin/true","args":[],"cwdRelative":".","env":{}},
                acceptance={"kind":"stdout_equals","value":"OK"},
            )
            service.task_graph.attach(goal.id, task.id)
            with service._connection:
                service.tasks.set_state_in_transaction(task.id, "RUNNING")
            service.goal_reconciler.reconcile(goal.id)
            with service._connection:
                service.tasks.set_state_in_transaction(task.id, "SUCCEEDED")
            service.goal_reconciler.reconcile(goal.id)

            receipts = service.board_projector.project_pending(goal.id)

            self.assertEqual(len(receipts), 3)
            self.assertEqual(len(board.messages), 3)
            events = service.events.list_for("Goal", goal.id)
            self.assertEqual(
                [e.event_type for e in events],
                ["GOAL_CREATED", "GOAL_RUNNING", "GOAL_SUCCEEDED"],
            )
            self.assertEqual([r.service_event_id for r in receipts], [e.id for e in events])


class AgentServiceGoalLegoDecompositionTests(unittest.TestCase):
    def test_goal_graph_exposes_separate_membership_dependency_readiness_and_guard_bricks(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            runtime = FakeRuntime()
            service = open_current(
                Path(tmp) / "service.db",
                carrier_adapter=ReadyCarrier(),
                runtime_adapter=runtime,
                artifact_reader=NoopArtifactReader(),
            )
            self.addCleanup(service.close)
            definition = service.definitions.create("worker-lego")
            revision = service.revisions.create(definition.id, {"harness":"test"})
            instance = service.instances.create("request-r7-lego", revision.id)
            service.reconciler.reconcile(instance.id)
            goal = service.goals.create("lego")
            a = service.tasks.create(
                description="a",
                required_revision_id=revision.id,
                execution={"workspaceId":"ws-test","executable":"/usr/bin/true","args":[],"cwdRelative":".","env":{}},
                acceptance={"kind":"stdout_equals","value":"OK"},
            )
            b = service.tasks.create(
                description="b",
                required_revision_id=revision.id,
                execution={"workspaceId":"ws-test","executable":"/usr/bin/true","args":[],"cwdRelative":".","env":{}},
                acceptance={"kind":"stdout_equals","value":"OK"},
            )

            service.goal_task_links.attach(goal.id, a.id)
            service.goal_task_links.attach(goal.id, b.id)
            service.task_dependencies.add(b.id, a.id)

            self.assertEqual(service.goal_task_links.goal_for_task(a.id).id, goal.id)
            self.assertEqual(service.task_dependencies.dependencies_of(b.id), [a.id])
            self.assertTrue(service.task_readiness.is_ready(a.id))
            self.assertFalse(service.task_readiness.is_ready(b.id))
            self.assertIs(service.task_graph.links, service.goal_task_links)
            self.assertIs(service.task_graph.dependencies, service.task_dependencies)
            self.assertIs(service.task_graph.readiness, service.task_readiness)
            self.assertIs(service.task_graph.mutation_guard, service.goal_graph_guard)
