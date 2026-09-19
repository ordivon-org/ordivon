from __future__ import annotations

import hashlib
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from agent_service.evidence import (
    AgentServiceR6,
    ArtifactDigestMismatch,
    RuntimeArtifactPayload,
    RuntimeArtifactReader,
    _verification_record_list_for_task,
)
from agent_service.slice1 import CarrierProviderAdapter, ProviderObservation
from agent_service.task_runtime import RuntimeAdapter, RuntimeArtifactDescriptor, RuntimeJobObservation, RuntimeJobRef


class ReadyCarrier(CarrierProviderAdapter):
    def ensure(self, placement_id: str, agent_instance_id: str, revision_id: str) -> None:
        return None

    def retire(self, placement_id: str, agent_instance_id: str) -> None:
        return None

    def observe(self, placement_id: str) -> ProviderObservation:
        return ProviderObservation(placement_id=placement_id, state="READY", evidence_ref="test://ready")


class FakeRuntime(RuntimeAdapter):
    def __init__(self) -> None:
        self.jobs: dict[str, RuntimeJobObservation] = {}
        self.by_request: dict[str, str] = {}

    def submit(self, client_request_id: str, execution: dict) -> RuntimeJobRef:
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


class FakeArtifactReader(RuntimeArtifactReader):
    def __init__(self) -> None:
        self.payloads: dict[tuple[str, str], RuntimeArtifactPayload] = {}
        self.reads: list[tuple[str, str]] = []

    def read(self, job_id: str, artifact_id: str) -> RuntimeArtifactPayload:
        self.reads.append((job_id, artifact_id))
        return self.payloads[(job_id, artifact_id)]


def sha256_text(value: str) -> str:
    return "sha256:" + hashlib.sha256(value.encode("utf-8")).hexdigest()


class AgentServiceEvidenceR6Tests(unittest.TestCase):
    def _open(self, db: Path, runtime: FakeRuntime, artifacts: FakeArtifactReader) -> AgentServiceR6:
        service = AgentServiceR6.open(
            db,
            carrier_adapter=ReadyCarrier(),
            runtime_adapter=runtime,
            artifact_reader=artifacts,
        )
        self.addCleanup(service.close)
        return service

    def _ready_agent(self, service: AgentServiceR6):
        definition = service.definitions.create("worker")
        revision = service.revisions.create(definition.id, {"harness": "test"})
        instance = service.instances.create("request-r6-worker", revision.id)
        service.reconciler.reconcile(instance.id)
        return revision, instance

    def _task(self, service: AgentServiceR6, revision_id: str, acceptance: dict):
        return service.tasks.create(
            description="verify evidence",
            required_revision_id=revision_id,
            execution={
                "workspaceId": "ws-test",
                "executable": "/usr/bin/true",
                "args": [],
                "cwdRelative": ".",
                "env": {},
            },
            acceptance=acceptance,
        )

    def test_activation_and_completion_are_separate_lifecycle_nodes(self) -> None:
        runtime = FakeRuntime()
        artifacts = FakeArtifactReader()
        with tempfile.TemporaryDirectory() as tmp:
            service = self._open(Path(tmp) / "service.db", runtime, artifacts)
            revision, _ = self._ready_agent(service)
            task = self._task(service, revision.id, {"kind": "stdout_contains", "value": "OK"})
            assignment = service.planner.plan(task.id)

            active = service.execution_activator.activate(assignment.id)
            assert active.runtime_job_id is not None
            runtime.jobs[active.runtime_job_id] = RuntimeJobObservation(
                job_id=active.runtime_job_id,
                status="succeeded",
                execution_terminal=True,
                delivery_disposition="committed",
                semantic_completion_evaluated=False,
                stdout_tail="OK\n",
                stderr_tail="",
                artifacts=(),
            )

            service.execution_activator.activate(assignment.id)

            self.assertEqual(service.tasks.get(task.id).state, "RUNNING")
            self.assertEqual(_verification_record_list_for_task(service.events, task.id), [])

            service.completion.reconcile(assignment.id)
            self.assertEqual(service.tasks.get(task.id).state, "SUCCEEDED")

    def test_stdout_resolver_creates_durable_verification_record(self) -> None:
        runtime = FakeRuntime()
        artifacts = FakeArtifactReader()
        with tempfile.TemporaryDirectory() as tmp:
            service = self._open(Path(tmp) / "service.db", runtime, artifacts)
            revision, _ = self._ready_agent(service)
            task = self._task(service, revision.id, {"kind": "stdout_contains", "value": "EXPECTED"})
            assignment = service.planner.plan(task.id)
            active = service.execution_activator.activate(assignment.id)
            assert active.runtime_job_id is not None
            runtime.jobs[active.runtime_job_id] = RuntimeJobObservation(
                job_id=active.runtime_job_id,
                status="succeeded",
                execution_terminal=True,
                delivery_disposition="committed",
                semantic_completion_evaluated=False,
                stdout_tail="prefix EXPECTED suffix\n",
                stderr_tail="",
                artifacts=(),
            )

            service.completion.reconcile(assignment.id)

            records = _verification_record_list_for_task(service.events, task.id)
            self.assertEqual(len(records), 1)
            self.assertTrue(records[0].accepted)
            self.assertEqual(records[0].evidence["resolver"], "stdout_tail")
            self.assertEqual(records[0].runtime_job_id, active.runtime_job_id)

    def test_runtime_artifact_text_resolver_reads_digest_bound_artifact(self) -> None:
        runtime = FakeRuntime()
        artifacts = FakeArtifactReader()
        with tempfile.TemporaryDirectory() as tmp:
            service = self._open(Path(tmp) / "service.db", runtime, artifacts)
            revision, _ = self._ready_agent(service)
            task = self._task(
                service,
                revision.id,
                {
                    "kind": "runtime_artifact_text_contains",
                    "artifactKind": "stdout",
                    "value": "ARTIFACT_OK",
                },
            )
            assignment = service.planner.plan(task.id)
            active = service.execution_activator.activate(assignment.id)
            assert active.runtime_job_id is not None
            artifact_id = "attempt-1.stdout"
            runtime.jobs[active.runtime_job_id] = RuntimeJobObservation(
                job_id=active.runtime_job_id,
                status="succeeded",
                execution_terminal=True,
                delivery_disposition="committed",
                semantic_completion_evaluated=False,
                stdout_tail="truncated tail without marker",
                stderr_tail="",
                artifacts=(artifact_id,),
                artifact_descriptors=(RuntimeArtifactDescriptor(artifact_id=artifact_id, kind="stdout"),),
            )
            content = "large durable output ... ARTIFACT_OK ...\n"
            artifacts.payloads[(active.runtime_job_id, artifact_id)] = RuntimeArtifactPayload(
                job_id=active.runtime_job_id,
                artifact_id=artifact_id,
                digest=sha256_text(content),
                content=content,
            )

            service.completion.reconcile(assignment.id)

            self.assertEqual(service.tasks.get(task.id).state, "SUCCEEDED")
            record = _verification_record_list_for_task(service.events, task.id)[0]
            self.assertEqual(record.evidence["artifactId"], artifact_id)
            self.assertEqual(record.evidence["digest"], sha256_text(content))
            self.assertEqual(artifacts.reads, [(active.runtime_job_id, artifact_id)])

    def test_artifact_digest_mismatch_fails_closed_without_task_terminal_transition(self) -> None:
        runtime = FakeRuntime()
        artifacts = FakeArtifactReader()
        with tempfile.TemporaryDirectory() as tmp:
            service = self._open(Path(tmp) / "service.db", runtime, artifacts)
            revision, _ = self._ready_agent(service)
            task = self._task(
                service,
                revision.id,
                {"kind": "runtime_artifact_text_contains", "artifactKind": "stdout", "value": "OK"},
            )
            assignment = service.planner.plan(task.id)
            active = service.execution_activator.activate(assignment.id)
            assert active.runtime_job_id is not None
            artifact_id = "attempt-1.stdout"
            runtime.jobs[active.runtime_job_id] = RuntimeJobObservation(
                job_id=active.runtime_job_id,
                status="succeeded",
                execution_terminal=True,
                delivery_disposition="committed",
                semantic_completion_evaluated=False,
                stdout_tail="",
                stderr_tail="",
                artifacts=(artifact_id,),
                artifact_descriptors=(RuntimeArtifactDescriptor(artifact_id=artifact_id, kind="stdout"),),
            )
            artifacts.payloads[(active.runtime_job_id, artifact_id)] = RuntimeArtifactPayload(
                job_id=active.runtime_job_id,
                artifact_id=artifact_id,
                digest="sha256:" + "0" * 64,
                content="OK\n",
            )

            with self.assertRaises(ArtifactDigestMismatch):
                service.completion.reconcile(assignment.id)

            self.assertEqual(service.tasks.get(task.id).state, "RUNNING")
            self.assertEqual(_verification_record_list_for_task(service.events, task.id), [])

    def test_completion_replay_does_not_duplicate_verdict_or_terminal_event(self) -> None:
        runtime = FakeRuntime()
        artifacts = FakeArtifactReader()
        with tempfile.TemporaryDirectory() as tmp:
            service = self._open(Path(tmp) / "service.db", runtime, artifacts)
            revision, _ = self._ready_agent(service)
            task = self._task(service, revision.id, {"kind": "stdout_equals", "value": "OK\n"})
            assignment = service.planner.plan(task.id)
            active = service.execution_activator.activate(assignment.id)
            assert active.runtime_job_id is not None
            runtime.jobs[active.runtime_job_id] = RuntimeJobObservation(
                job_id=active.runtime_job_id,
                status="succeeded",
                execution_terminal=True,
                delivery_disposition="committed",
                semantic_completion_evaluated=False,
                stdout_tail="OK\n",
                stderr_tail="",
                artifacts=(),
            )

            service.completion.reconcile(assignment.id)
            service.completion.reconcile(assignment.id)

            self.assertEqual(len(_verification_record_list_for_task(service.events, task.id)), 1)
            event_types = [event.event_type for event in service.events.list_for("Task", task.id)]
            self.assertEqual(event_types.count("TASK_SUCCEEDED"), 1)
            self.assertEqual(event_types.count("TASK_VERIFIED"), 1)

    def test_mechanical_failure_is_recorded_as_verification_evidence(self) -> None:
        runtime = FakeRuntime()
        artifacts = FakeArtifactReader()
        with tempfile.TemporaryDirectory() as tmp:
            service = self._open(Path(tmp) / "service.db", runtime, artifacts)
            revision, _ = self._ready_agent(service)
            task = self._task(service, revision.id, {"kind": "stdout_contains", "value": "OK"})
            assignment = service.planner.plan(task.id)
            active = service.execution_activator.activate(assignment.id)
            assert active.runtime_job_id is not None
            runtime.jobs[active.runtime_job_id] = RuntimeJobObservation(
                job_id=active.runtime_job_id,
                status="failed",
                execution_terminal=True,
                delivery_disposition="committed",
                semantic_completion_evaluated=False,
                stdout_tail="OK\n",
                stderr_tail="boom\n",
                artifacts=(),
            )

            service.completion.reconcile(assignment.id)

            self.assertEqual(service.tasks.get(task.id).state, "FAILED")
            record = _verification_record_list_for_task(service.events, task.id)[0]
            self.assertFalse(record.accepted)
            self.assertEqual(record.reason, "runtime:failed")
            self.assertEqual(record.stage, "mechanical")

    def test_task_terminal_and_verification_record_commit_atomically(self) -> None:
        runtime = FakeRuntime()
        artifacts = FakeArtifactReader()
        with tempfile.TemporaryDirectory() as tmp:
            service = self._open(Path(tmp) / "service.db", runtime, artifacts)
            revision, _ = self._ready_agent(service)
            task = self._task(service, revision.id, {"kind": "stdout_contains", "value": "OK"})
            assignment = service.planner.plan(task.id)
            active = service.execution_activator.activate(assignment.id)
            assert active.runtime_job_id is not None
            runtime.jobs[active.runtime_job_id] = RuntimeJobObservation(
                job_id=active.runtime_job_id,
                status="succeeded",
                execution_terminal=True,
                delivery_disposition="committed",
                semantic_completion_evaluated=False,
                stdout_tail="OK\n",
                stderr_tail="",
                artifacts=(),
            )

            with patch.object(
                service.events,
                "append_once_in_transaction",
                side_effect=RuntimeError("receipt failed"),
            ):
                with self.assertRaises(RuntimeError):
                    service.completion.reconcile(assignment.id)

            self.assertEqual(service.tasks.get(task.id).state, "RUNNING")
            self.assertEqual(service.assignments.get(assignment.id).state, "ACTIVE")
            self.assertEqual(_verification_record_list_for_task(service.events, task.id), [])
            self.assertNotIn(
                "TASK_SUCCEEDED",
                [event.event_type for event in service.events.list_for("Task", task.id)],
            )

    def test_runtime_semantic_authority_violation_fails_closed(self) -> None:
        runtime = FakeRuntime()
        artifacts = FakeArtifactReader()
        with tempfile.TemporaryDirectory() as tmp:
            service = self._open(Path(tmp) / "service.db", runtime, artifacts)
            revision, _ = self._ready_agent(service)
            task = self._task(service, revision.id, {"kind": "stdout_contains", "value": "OK"})
            assignment = service.planner.plan(task.id)
            active = service.execution_activator.activate(assignment.id)
            assert active.runtime_job_id is not None
            runtime.jobs[active.runtime_job_id] = RuntimeJobObservation(
                job_id=active.runtime_job_id,
                status="succeeded",
                execution_terminal=True,
                delivery_disposition="committed",
                semantic_completion_evaluated=True,
                stdout_tail="OK\n",
                stderr_tail="",
                artifacts=(),
            )

            with self.assertRaises(RuntimeError):
                service.completion.reconcile(assignment.id)

            self.assertEqual(service.tasks.get(task.id).state, "RUNNING")
            self.assertEqual(_verification_record_list_for_task(service.events, task.id), [])


if __name__ == "__main__":
    unittest.main()


class VerificationReceiptAuthorityBoundaryTests(unittest.TestCase):
    def test_evidence_receipt_does_not_duplicate_runtime_artifact_content(self) -> None:
        from agent_service.evidence import EvidenceBundle

        bundle = EvidenceBundle(
            resolver="runtime_artifact_text",
            facts={"text": "SECRET_OR_LARGE_RUNTIME_ARTIFACT"},
            provenance={
                "runtimeJobId": "job-1",
                "artifactId": "attempt.stdout",
                "artifactKind": "stdout",
                "digest": sha256_text("SECRET_OR_LARGE_RUNTIME_ARTIFACT"),
                "byteLength": len("SECRET_OR_LARGE_RUNTIME_ARTIFACT"),
            },
        )

        receipt = bundle.receipt()

        self.assertNotIn("SECRET_OR_LARGE_RUNTIME_ARTIFACT", str(receipt))
        self.assertEqual(receipt["digest"], sha256_text("SECRET_OR_LARGE_RUNTIME_ARTIFACT"))
        self.assertEqual(receipt["artifactId"], "attempt.stdout")
