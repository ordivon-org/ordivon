from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from agent_service.slice1 import ProviderObservation
from agent_service.task_runtime import (
    AgentServiceR5,
    RuntimeJobObservation,
    RuntimeJobRef,
)


class ReadyCarrier:
    def ensure(self, placement_id: str, agent_instance_id: str, revision_id: str) -> None:
        return None

    def retire(self, placement_id: str, agent_instance_id: str) -> None:
        return None

    def observe(self, placement_id: str) -> ProviderObservation:
        return ProviderObservation(
            placement_id=placement_id,
            state="READY",
            evidence_ref="test://carrier/ready",
        )


class FakeRuntime:
    def __init__(self) -> None:
        self.submissions: list[tuple[str, dict]] = []
        self.jobs: dict[str, RuntimeJobObservation] = {}
        self.by_request: dict[str, str] = {}

    def submit(self, client_request_id: str, execution: dict) -> RuntimeJobRef:
        self.submissions.append((client_request_id, execution))
        job_id = self.by_request.setdefault(client_request_id, f"job-{len(self.by_request) + 1}")
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


class AgentServiceTaskRuntimeTests(unittest.TestCase):
    def _open(self, db: Path, runtime: FakeRuntime) -> AgentServiceR5:
        service = AgentServiceR5.open(
            db,
            carrier_adapter=ReadyCarrier(),
            runtime_adapter=runtime,
        )
        self.addCleanup(service.close)
        return service

    def _ready_agent(self, service: AgentServiceR5):
        definition = service.definitions.create("worker")
        revision = service.revisions.create(definition.id, {"harness": "test"})
        instance = service.instances.create("request-worker-1", revision.id)
        service.reconciler.reconcile(instance.id)
        self.assertEqual(service.instances.get(instance.id).state, "READY")
        return revision, instance

    def _task(self, service: AgentServiceR5, revision_id: str, marker: str = "SEMANTIC_OK"):
        return service.tasks.create(
            description="produce the expected semantic marker",
            required_revision_id=revision_id,
            execution={
                "workspaceId": "ws-test",
                "executable": "/usr/bin/python3",
                "args": ["-c", f"print({marker!r})"],
                "cwdRelative": ".",
                "env": {},
            },
            acceptance={"kind": "stdout_contains", "value": marker},
        )

    def test_planner_assigns_only_ready_matching_agent(self) -> None:
        runtime = FakeRuntime()
        with tempfile.TemporaryDirectory() as tmp:
            service = self._open(Path(tmp) / "service.db", runtime)
            revision, instance = self._ready_agent(service)
            task = self._task(service, revision.id)

            assignment = service.planner.plan(task.id)

            self.assertEqual(assignment.agent_instance_id, instance.id)
            self.assertEqual(service.tasks.get(task.id).state, "ASSIGNED")
            self.assertTrue(assignment.client_request_id.startswith("agent-service:assignment:"))

    def test_planner_fails_closed_without_ready_matching_agent(self) -> None:
        runtime = FakeRuntime()
        with tempfile.TemporaryDirectory() as tmp:
            service = self._open(Path(tmp) / "service.db", runtime)
            definition = service.definitions.create("worker")
            revision = service.revisions.create(definition.id, {"harness": "test"})
            service.instances.create("request-worker-1", revision.id)  # still PROVISIONING
            task = self._task(service, revision.id)

            with self.assertRaises(LookupError):
                service.planner.plan(task.id)

            self.assertEqual(service.tasks.get(task.id).state, "PENDING")
            self.assertEqual(service.assignments.list_all(), [])

    def test_activation_binds_one_runtime_job_and_does_not_create_new_task_on_replay(self) -> None:
        runtime = FakeRuntime()
        with tempfile.TemporaryDirectory() as tmp:
            service = self._open(Path(tmp) / "service.db", runtime)
            revision, _ = self._ready_agent(service)
            task = self._task(service, revision.id)
            assignment = service.planner.plan(task.id)

            first = service.activator.activate(assignment.id)
            second = service.activator.activate(assignment.id)

            self.assertEqual(first.runtime_job_id, second.runtime_job_id)
            self.assertEqual(len(runtime.by_request), 1)
            self.assertEqual(len(service.tasks.list_all()), 1)
            self.assertEqual(service.tasks.get(task.id).state, "RUNNING")

    def test_exit_zero_does_not_imply_task_success(self) -> None:
        runtime = FakeRuntime()
        with tempfile.TemporaryDirectory() as tmp:
            service = self._open(Path(tmp) / "service.db", runtime)
            revision, _ = self._ready_agent(service)
            task = self._task(service, revision.id, marker="EXPECTED")
            assignment = service.planner.plan(task.id)
            active = service.activator.activate(assignment.id)
            assert active.runtime_job_id is not None
            runtime.jobs[active.runtime_job_id] = RuntimeJobObservation(
                job_id=active.runtime_job_id,
                status="succeeded",
                execution_terminal=True,
                delivery_disposition="committed",
                semantic_completion_evaluated=False,
                stdout_tail="WRONG\n",
                stderr_tail="",
                artifacts=(),
            )

            service.activator.activate(assignment.id)

            finished = service.tasks.get(task.id)
            self.assertEqual(finished.state, "FAILED")
            self.assertEqual(finished.failure_reason, "acceptance:stdout_contains:not_satisfied")

    def test_task_succeeds_only_after_semantic_acceptance(self) -> None:
        runtime = FakeRuntime()
        with tempfile.TemporaryDirectory() as tmp:
            service = self._open(Path(tmp) / "service.db", runtime)
            revision, _ = self._ready_agent(service)
            task = self._task(service, revision.id, marker="EXPECTED")
            assignment = service.planner.plan(task.id)
            active = service.activator.activate(assignment.id)
            assert active.runtime_job_id is not None
            runtime.jobs[active.runtime_job_id] = RuntimeJobObservation(
                job_id=active.runtime_job_id,
                status="succeeded",
                execution_terminal=True,
                delivery_disposition="committed",
                semantic_completion_evaluated=False,
                stdout_tail="prefix EXPECTED suffix\n",
                stderr_tail="",
                artifacts=("attempt.stdout",),
            )

            service.activator.activate(assignment.id)

            self.assertEqual(service.tasks.get(task.id).state, "SUCCEEDED")

    def test_runtime_failure_is_mechanical_failure_evidence_not_semantic_success(self) -> None:
        runtime = FakeRuntime()
        with tempfile.TemporaryDirectory() as tmp:
            service = self._open(Path(tmp) / "service.db", runtime)
            revision, _ = self._ready_agent(service)
            task = self._task(service, revision.id)
            assignment = service.planner.plan(task.id)
            active = service.activator.activate(assignment.id)
            assert active.runtime_job_id is not None
            runtime.jobs[active.runtime_job_id] = RuntimeJobObservation(
                job_id=active.runtime_job_id,
                status="failed",
                execution_terminal=True,
                delivery_disposition="committed",
                semantic_completion_evaluated=False,
                stdout_tail="SEMANTIC_OK\n",
                stderr_tail="boom\n",
                artifacts=(),
            )

            service.activator.activate(assignment.id)

            task_after = service.tasks.get(task.id)
            self.assertEqual(task_after.state, "FAILED")
            self.assertEqual(task_after.failure_reason, "runtime:failed")

    def test_runtime_must_not_claim_semantic_completion(self) -> None:
        runtime = FakeRuntime()
        with tempfile.TemporaryDirectory() as tmp:
            service = self._open(Path(tmp) / "service.db", runtime)
            revision, _ = self._ready_agent(service)
            task = self._task(service, revision.id)
            assignment = service.planner.plan(task.id)
            active = service.activator.activate(assignment.id)
            assert active.runtime_job_id is not None
            runtime.jobs[active.runtime_job_id] = RuntimeJobObservation(
                job_id=active.runtime_job_id,
                status="succeeded",
                execution_terminal=True,
                delivery_disposition="committed",
                semantic_completion_evaluated=True,
                stdout_tail="SEMANTIC_OK\n",
                stderr_tail="",
                artifacts=(),
            )

            with self.assertRaises(RuntimeError):
                service.activator.activate(assignment.id)

            self.assertEqual(service.tasks.get(task.id).state, "RUNNING")

    def test_assignment_intent_survives_service_restart_before_runtime_submit(self) -> None:
        runtime = FakeRuntime()
        with tempfile.TemporaryDirectory() as tmp:
            db = Path(tmp) / "service.db"
            first = self._open(db, runtime)
            revision, _ = self._ready_agent(first)
            task = self._task(first, revision.id)
            assignment = first.planner.plan(task.id)
            stable_request_id = assignment.client_request_id
            first.close()

            second = AgentServiceR5.open(db, carrier_adapter=ReadyCarrier(), runtime_adapter=runtime)
            self.addCleanup(second.close)
            recovered = second.assignments.get(assignment.id)
            second.activator.activate(recovered.id)

            self.assertEqual(runtime.submissions[0][0], stable_request_id)
            self.assertEqual(len(runtime.by_request), 1)

    def test_assignment_recovery_replays_same_runtime_request_after_lost_job_binding(self) -> None:
        runtime = FakeRuntime()
        with tempfile.TemporaryDirectory() as tmp:
            service = self._open(Path(tmp) / "service.db", runtime)
            revision, _ = self._ready_agent(service)
            task = self._task(service, revision.id)
            assignment = service.planner.plan(task.id)

            first_ref = runtime.submit(assignment.client_request_id, task.execution)
            self.assertEqual(first_ref.job_id, "job-1")
            # Simulate response loss / service crash before runtimeJobId was persisted.

            recovered = service.activator.activate(assignment.id)

            self.assertEqual(recovered.runtime_job_id, "job-1")
            self.assertEqual(len(runtime.by_request), 1)
            self.assertEqual(runtime.submissions[-1][0], assignment.client_request_id)

    def test_task_events_preserve_assignment_runtime_and_semantic_history(self) -> None:
        runtime = FakeRuntime()
        with tempfile.TemporaryDirectory() as tmp:
            service = self._open(Path(tmp) / "service.db", runtime)
            revision, _ = self._ready_agent(service)
            task = self._task(service, revision.id, marker="EXPECTED")
            assignment = service.planner.plan(task.id)
            active = service.activator.activate(assignment.id)
            assert active.runtime_job_id is not None
            runtime.jobs[active.runtime_job_id] = RuntimeJobObservation(
                job_id=active.runtime_job_id,
                status="succeeded",
                execution_terminal=True,
                delivery_disposition="committed",
                semantic_completion_evaluated=False,
                stdout_tail="EXPECTED\n",
                stderr_tail="",
                artifacts=(),
            )
            service.activator.activate(assignment.id)

            self.assertEqual(
                [event.event_type for event in service.events.list_for("Task", task.id)],
                [
                    "TASK_CREATED",
                    "TASK_ASSIGNED",
                    "RUNTIME_JOB_BOUND",
                    "TASK_SUCCEEDED",
                ],
            )


if __name__ == "__main__":
    unittest.main()
