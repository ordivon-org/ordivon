from __future__ import annotations

import hashlib
import tempfile
import unittest
from pathlib import Path

from agent_service.delivery import (
    DeliveryAdapter,
    DeliveryObservation,
    PolicyAdapter,
    PolicyObservation,
)
from agent_service.evidence import ArtifactDigestMismatch, RuntimeArtifactPayload
from agent_service.remote_evidence import (
    AgentServiceR11,
    RemoteArtifactPayload,
    RemoteArtifactReader,
    _remote_task_verification_get_by_task,
)
from agent_service.slice1 import ProviderObservation
from agent_service.task_runtime import RuntimeJobObservation, RuntimeJobRef
from agent_service.trust import AgentServiceR10, RemoteDeliveryObserver, RemoteProviderObservation


def digest(text: str) -> str:
    return "sha256:" + hashlib.sha256(text.encode("utf-8")).hexdigest()


class ReadyCarrier:
    def ensure(self, placement_id: str, agent_instance_id: str, revision_id: str) -> None:
        return None

    def retire(self, placement_id: str, agent_instance_id: str) -> None:
        return None

    def observe(self, placement_id: str) -> ProviderObservation:
        return ProviderObservation(placement_id=placement_id, state="READY", evidence_ref="test://ready")


class FakeRuntime:
    def submit(self, client_request_id: str, execution: dict) -> RuntimeJobRef:
        return RuntimeJobRef(job_id=f"job:{client_request_id}")

    def observe(self, job_id: str) -> RuntimeJobObservation:
        return RuntimeJobObservation(
            job_id=job_id,
            status="working",
            execution_terminal=False,
            delivery_disposition="committed",
            semantic_completion_evaluated=False,
            stdout_tail="",
            stderr_tail="",
            artifacts=(),
        )


class NoopRuntimeArtifactReader:
    def read(self, job_id: str, artifact_id: str) -> RuntimeArtifactPayload:
        raise AssertionError("runtime artifact read not expected")


class AllowPolicy(PolicyAdapter):
    def evaluate(self, request):
        return PolicyObservation(
            allowed=True,
            reason=None,
            policy_revision="policy-r11",
            granted_permissions=("review.invoke",),
        )


class RecordingDelivery(DeliveryAdapter):
    def __init__(self) -> None:
        self.calls: list[str] = []
        self.committed: dict[str, DeliveryObservation] = {}
        self.fail_after_commit_once = False

    def send(self, *, delivery_request_id: str, binding, envelope) -> DeliveryObservation:
        self.calls.append(delivery_request_id)
        existing = self.committed.get(delivery_request_id)
        if existing is not None:
            return DeliveryObservation(
                admission="existing",
                status=existing.status,
                provider_request_id=existing.provider_request_id,
                remote_task_id=existing.remote_task_id,
                remote_context_id=existing.remote_context_id,
            )
        value = DeliveryObservation(
            admission="committed",
            status="submitted",
            provider_request_id=f"provider:{delivery_request_id}",
            remote_task_id=f"remote-task:{len(self.committed) + 1}",
            remote_context_id=f"remote-context:{len(self.committed) + 1}",
        )
        self.committed[delivery_request_id] = value
        if self.fail_after_commit_once:
            self.fail_after_commit_once = False
            raise RuntimeError("response lost after remote commit")
        return value


class TerminalRemoteObserver(RemoteDeliveryObserver):
    def __init__(self, *, successful: bool, artifact_refs: tuple[str, ...] = ("artifact:review",)) -> None:
        self.successful = successful
        self.artifact_refs = artifact_refs

    def observe(self, *, binding, receipt, envelope) -> RemoteProviderObservation:
        return RemoteProviderObservation(
            provider_status="TASK_STATE_COMPLETED" if self.successful else "TASK_STATE_FAILED",
            terminal=True,
            successful=self.successful,
            remote_task_id=receipt.remote_task_id,
            remote_context_id=receipt.remote_context_id,
            artifact_refs=self.artifact_refs,
            evidence_ref=f"remote://terminal/{'success' if self.successful else 'failure'}",
        )


class MappingRemoteArtifactReader(RemoteArtifactReader):
    def __init__(self, payloads: dict[str, RemoteArtifactPayload]) -> None:
        self.payloads = payloads
        self.calls: list[str] = []

    def read(self, *, binding, receipt, observation, artifact_ref: str) -> RemoteArtifactPayload:
        self.calls.append(artifact_ref)
        return self.payloads[artifact_ref]


class AgentServiceRemoteEvidenceR11Tests(unittest.TestCase):
    def _open(
        self,
        db: Path,
        *,
        delivery: RecordingDelivery | None = None,
        remote_observer: RemoteDeliveryObserver | None = None,
        artifact_reader: RemoteArtifactReader | None = None,
    ) -> AgentServiceR11:
        delivery = delivery or RecordingDelivery()
        service = AgentServiceR11.open(
            db,
            carrier_adapter=ReadyCarrier(),
            runtime_adapter=FakeRuntime(),
            artifact_reader=NoopRuntimeArtifactReader(),
            policy_adapter=AllowPolicy(),
            delivery_adapters={"a2a-jsonrpc": delivery, "mcp": delivery},
            remote_delivery_observers=(
                {"a2a-jsonrpc": remote_observer, "mcp": remote_observer}
                if remote_observer is not None
                else {}
            ),
            remote_artifact_readers=(
                {"a2a-jsonrpc": artifact_reader, "mcp": artifact_reader}
                if artifact_reader is not None
                else {}
            ),
        )
        self.addCleanup(service.close)
        return service

    def _agent(self, service: AgentServiceR11, name: str, *, routes=None):
        definition = service.definitions.create(name)
        revision = service.revisions.create(definition.id, {
            "name": name,
            "harness": "r11",
            "skills": [{
                "id": "review",
                "name": "Review",
                "description": "review",
                "tags": ["review"],
                "inputModes": ["text/plain"],
                "outputModes": ["text/markdown"],
            }],
            "routes": routes or [],
        })
        identity = service.identities.create(definition.id, stable_name=name, description=name)
        instance = service.instances.create(f"request:{name}:r11", revision.id)
        service.reconciler.reconcile(instance.id)
        return revision, identity, instance

    def _task(self, service: AgentServiceR11, revision_id: str, label: str = "review"):
        return service.tasks.create(
            description=label,
            required_revision_id=revision_id,
            execution={"workspaceId":"ws-test","executable":"/usr/bin/true","args":[],"cwdRelative":".","env":{}},
            acceptance={"kind":"runtime_artifact_text_contains","artifactKind":"review-markdown","value":"ACCEPTED"},
        )

    def _remote_setup(self, service: AgentServiceR11, *, with_goal: bool = False):
        source_revision, source_identity, source_instance = self._agent(service, "source")
        target_revision, target_identity, _ = self._agent(
            service,
            "target",
            routes=[
                {
                    "transport": "a2a-jsonrpc",
                    "protocolVersion": "1.0",
                    "url": "https://agents.example.test/target",
                    "priority": 10,
                    "securityRequirements": {},
                },
                {
                    "transport": "mcp",
                    "protocolVersion": "2026-07-28",
                    "url": "https://mcp.example.test/target",
                    "priority": 20,
                    "securityRequirements": {},
                },
            ],
        )
        task = self._task(service, source_revision.id)
        goal = None
        if with_goal:
            goal = service.goals.create("r11 goal")
            service.goal_task_links.attach(goal.id, task.id)
        session = service.sessions.open(
            client_session_id=f"r11:session:{task.id}",
            initiator_identity_id=source_identity.id,
            goal_id=None if goal is None else goal.id,
        )
        envelope = service.delegations.create(
            client_delegation_id=f"r11:delegation:{task.id}",
            session_id=session.id,
            source_identity_id=source_identity.id,
            source_instance_id=source_instance.id,
            target_identity_id=target_identity.id,
            target_revision_id=target_revision.id,
            task_id=task.id,
            capability_key="review",
            payload={"text":"review"},
            evidence_contract={"kind":"review-markdown"},
        )
        policy_request_id = f"r11:policy:{task.id}"
        a2a = service.routes.plan(
            envelope.id,
            client_policy_request_id=policy_request_id,
            preferred_transports=["a2a-jsonrpc"],
        )
        mcp = service.routes.plan(
            envelope.id,
            client_policy_request_id=policy_request_id,
            preferred_transports=["mcp"],
        )
        return source_revision, task, goal, envelope, a2a, mcp

    def test_local_assignment_claim_blocks_remote_delivery_for_same_task(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            service = self._open(Path(tmp) / "service.db")
            _, task, _, _, a2a, _ = self._remote_setup(service)
            assignment = service.planner.plan(task.id)

            claim = service.execution_claims.get(task.id)
            self.assertEqual(claim.mode, "LOCAL_ASSIGNMENT")
            self.assertEqual(claim.owner_id, assignment.id)
            with self.assertRaises(RuntimeError):
                service.delivery.deliver(a2a.id)

    def test_remote_delivery_claims_task_sets_running_and_blocks_local_assignment(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            service = self._open(Path(tmp) / "service.db")
            _, task, _, _, a2a, _ = self._remote_setup(service)
            receipt = service.delivery.deliver(a2a.id)

            claim = service.execution_claims.get(task.id)
            self.assertEqual(claim.mode, "REMOTE_BINDING")
            self.assertEqual(claim.owner_id, a2a.id)
            self.assertEqual(service.tasks.get(task.id).state, "RUNNING")
            self.assertIsNotNone(receipt.id)
            with self.assertRaises(RuntimeError):
                service.planner.plan(task.id)

    def test_second_fallback_binding_cannot_execute_after_primary_binding_claims_task(self) -> None:
        delivery = RecordingDelivery()
        with tempfile.TemporaryDirectory() as tmp:
            service = self._open(Path(tmp) / "service.db", delivery=delivery)
            _, task, _, _, a2a, mcp = self._remote_setup(service)
            service.delivery.deliver(a2a.id)

            with self.assertRaises(RuntimeError):
                service.delivery.deliver(mcp.id)
            self.assertEqual(len(delivery.committed), 1)
            self.assertEqual(service.execution_claims.get(task.id).owner_id, a2a.id)

    def test_remote_delivery_cannot_bypass_goal_dependency_readiness(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            service = self._open(Path(tmp) / "service.db")
            revision, task, goal, _, a2a, _ = self._remote_setup(service, with_goal=True)
            dependency = self._task(service, revision.id, "dependency")
            service.goal_task_links.attach(goal.id, dependency.id)
            service.task_dependencies.add(task.id, dependency.id)

            with self.assertRaises(LookupError):
                service.delivery.deliver(a2a.id)
            self.assertIsNone(service.execution_claims.get(task.id, required=False))
            self.assertEqual(service.tasks.get(task.id).state, "PENDING")

    def test_delivery_response_loss_keeps_remote_claim_and_retry_reuses_same_remote_effect(self) -> None:
        delivery = RecordingDelivery()
        delivery.fail_after_commit_once = True
        with tempfile.TemporaryDirectory() as tmp:
            service = self._open(Path(tmp) / "service.db", delivery=delivery)
            _, task, _, _, a2a, _ = self._remote_setup(service)

            with self.assertRaises(RuntimeError):
                service.delivery.deliver(a2a.id)
            self.assertEqual(service.tasks.get(task.id).state, "RUNNING")
            self.assertEqual(service.execution_claims.get(task.id).owner_id, a2a.id)

            receipt = service.delivery.deliver(a2a.id)
            self.assertEqual(delivery.calls[0], delivery.calls[1])
            self.assertEqual(len(delivery.committed), 1)
            self.assertEqual(receipt.admission, "existing")

    def test_remote_success_only_completes_task_after_artifact_acceptance_passes(self) -> None:
        text = "review result: ACCEPTED"
        reader = MappingRemoteArtifactReader(
            {
                "artifact:review": RemoteArtifactPayload(
                    artifact_ref="artifact:review",
                    kind="review-markdown",
                    digest=digest(text),
                    content=text,
                )
            }
        )
        observer = TerminalRemoteObserver(successful=True)
        with tempfile.TemporaryDirectory() as tmp:
            service = self._open(
                Path(tmp) / "service.db",
                remote_observer=observer,
                artifact_reader=reader,
            )
            _, task, _, _, a2a, _ = self._remote_setup(service)
            service.delivery.deliver(a2a.id)
            service.remote_reconciler.reconcile(a2a.id)
            self.assertEqual(service.tasks.get(task.id).state, "RUNNING")

            record = service.remote_completion.reconcile(a2a.id)

            self.assertTrue(record.accepted)
            self.assertEqual(record.stage, "semantic")
            self.assertEqual(service.tasks.get(task.id).state, "SUCCEEDED")
            self.assertEqual(record.evidence["resolver"], "remote_artifact_text")
            self.assertEqual(record.evidence["artifactRef"], "artifact:review")

    def test_remote_success_with_rejected_artifact_fails_semantic_acceptance(self) -> None:
        text = "review result: REJECTED"
        reader = MappingRemoteArtifactReader(
            {
                "artifact:review": RemoteArtifactPayload(
                    artifact_ref="artifact:review",
                    kind="review-markdown",
                    digest=digest(text),
                    content=text,
                )
            }
        )
        with tempfile.TemporaryDirectory() as tmp:
            service = self._open(
                Path(tmp) / "service.db",
                remote_observer=TerminalRemoteObserver(successful=True),
                artifact_reader=reader,
            )
            _, task, _, _, a2a, _ = self._remote_setup(service)
            service.delivery.deliver(a2a.id)
            service.remote_reconciler.reconcile(a2a.id)

            record = service.remote_completion.reconcile(a2a.id)

            self.assertFalse(record.accepted)
            self.assertEqual(record.stage, "semantic")
            self.assertEqual(service.tasks.get(task.id).state, "FAILED")
            self.assertIn("not_satisfied", record.reason)

    def test_remote_mechanical_failure_fails_task_without_reading_artifact(self) -> None:
        reader = MappingRemoteArtifactReader({})
        with tempfile.TemporaryDirectory() as tmp:
            service = self._open(
                Path(tmp) / "service.db",
                remote_observer=TerminalRemoteObserver(successful=False, artifact_refs=()),
                artifact_reader=reader,
            )
            _, task, _, _, a2a, _ = self._remote_setup(service)
            service.delivery.deliver(a2a.id)
            service.remote_reconciler.reconcile(a2a.id)

            record = service.remote_completion.reconcile(a2a.id)

            self.assertFalse(record.accepted)
            self.assertEqual(record.stage, "mechanical")
            self.assertEqual(service.tasks.get(task.id).state, "FAILED")
            self.assertEqual(reader.calls, [])

    def test_remote_artifact_digest_mismatch_fails_closed_without_task_verdict(self) -> None:
        text = "review result: ACCEPTED"
        reader = MappingRemoteArtifactReader(
            {
                "artifact:review": RemoteArtifactPayload(
                    artifact_ref="artifact:review",
                    kind="review-markdown",
                    digest="sha256:" + "0" * 64,
                    content=text,
                )
            }
        )
        with tempfile.TemporaryDirectory() as tmp:
            service = self._open(
                Path(tmp) / "service.db",
                remote_observer=TerminalRemoteObserver(successful=True),
                artifact_reader=reader,
            )
            _, task, _, _, a2a, _ = self._remote_setup(service)
            service.delivery.deliver(a2a.id)
            service.remote_reconciler.reconcile(a2a.id)

            with self.assertRaises(ArtifactDigestMismatch):
                service.remote_completion.reconcile(a2a.id)

            self.assertEqual(service.tasks.get(task.id).state, "RUNNING")
            self.assertIsNone(_remote_task_verification_get_by_task(service.events, task.id, required=False))

    def test_remote_verification_is_durable_and_exact_replay_safe(self) -> None:
        text = "ACCEPTED"
        reader = MappingRemoteArtifactReader(
            {
                "artifact:review": RemoteArtifactPayload(
                    artifact_ref="artifact:review",
                    kind="review-markdown",
                    digest=digest(text),
                    content=text,
                )
            }
        )
        with tempfile.TemporaryDirectory() as tmp:
            db = Path(tmp) / "service.db"
            first = self._open(
                db,
                remote_observer=TerminalRemoteObserver(successful=True),
                artifact_reader=reader,
            )
            _, task, _, _, a2a, _ = self._remote_setup(first)
            first.delivery.deliver(a2a.id)
            first.remote_reconciler.reconcile(a2a.id)
            record = first.remote_completion.reconcile(a2a.id)
            replay = first.remote_completion.reconcile(a2a.id)
            self.assertEqual(record.id, replay.id)
            first.close()

            second = AgentServiceR11.open(
                db,
                carrier_adapter=ReadyCarrier(),
                runtime_adapter=FakeRuntime(),
                artifact_reader=NoopRuntimeArtifactReader(),
                policy_adapter=AllowPolicy(),
                delivery_adapters={},
                remote_delivery_observers={},
                remote_artifact_readers={},
            )
            self.addCleanup(second.close)
            restored = _remote_task_verification_get_by_task(second.events, task.id)
            self.assertEqual(restored.id, record.id)
            self.assertEqual(second.tasks.get(task.id).state, "SUCCEEDED")


    def test_r10_existing_delivery_receipt_is_adopted_without_remote_resend(self) -> None:
        delivery = RecordingDelivery()
        with tempfile.TemporaryDirectory() as tmp:
            db = Path(tmp) / "service.db"
            first = AgentServiceR10.open(
                db,
                carrier_adapter=ReadyCarrier(),
                runtime_adapter=FakeRuntime(),
                artifact_reader=NoopRuntimeArtifactReader(),
                policy_adapter=AllowPolicy(),
                delivery_adapters={"a2a-jsonrpc": delivery, "mcp": delivery},
                remote_delivery_observers={},
            )
            _, task, _, _, a2a, _ = self._remote_setup(first)
            old_receipt = first.delivery.deliver(a2a.id)
            self.assertEqual(first.tasks.get(task.id).state, "PENDING")
            calls_before_upgrade = len(delivery.calls)
            first.close()

            second = AgentServiceR11.open(
                db,
                carrier_adapter=ReadyCarrier(),
                runtime_adapter=FakeRuntime(),
                artifact_reader=NoopRuntimeArtifactReader(),
                policy_adapter=AllowPolicy(),
                delivery_adapters={},
                remote_delivery_observers={},
                remote_artifact_readers={},
            )
            self.addCleanup(second.close)
            replay = second.delivery.deliver(a2a.id)

            self.assertEqual(replay.id, old_receipt.id)
            self.assertEqual(len(delivery.calls), calls_before_upgrade)
            self.assertEqual(second.tasks.get(task.id).state, "RUNNING")
            claim = second.execution_claims.get(task.id)
            self.assertEqual(claim.mode, "REMOTE_BINDING")
            self.assertEqual(claim.owner_id, a2a.id)


if __name__ == "__main__":
    unittest.main()
