from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from agent_service.delivery import (
    DeliveryAdapter,
    DeliveryObservation,
    PolicyAdapter,
    PolicyObservation,
)
from agent_service.evidence import RuntimeArtifactPayload, RuntimeArtifactReader
from agent_service.slice1 import CarrierProviderAdapter, ProviderObservation
from agent_service.task_runtime import RuntimeAdapter, RuntimeJobObservation, RuntimeJobRef
from agent_service.trust import (
    AgentServiceR10,
    IdentityProofAdapter,
    IdentityProofObservation,
    RemoteDeliveryObserver,
    RemoteProviderObservation,
)


class ReadyCarrier(CarrierProviderAdapter):
    def ensure(self, placement_id: str, agent_instance_id: str, revision_id: str) -> None:
        return None

    def retire(self, placement_id: str, agent_instance_id: str) -> None:
        return None

    def observe(self, placement_id: str) -> ProviderObservation:
        return ProviderObservation(placement_id=placement_id, state="READY", evidence_ref="test://ready")


class FakeRuntime(RuntimeAdapter):
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


class NoopArtifactReader(RuntimeArtifactReader):
    def read(self, job_id: str, artifact_id: str) -> RuntimeArtifactPayload:
        raise AssertionError("artifact read not expected")


class AllowPolicy(PolicyAdapter):
    def evaluate(self, request):
        return PolicyObservation(
            allowed=True,
            reason=None,
            policy_revision="policy-r10",
            granted_permissions=("review.invoke",),
        )


class FakeDelivery(DeliveryAdapter):
    def send(self, *, delivery_request_id: str, binding, envelope) -> DeliveryObservation:
        return DeliveryObservation(
            admission="committed",
            status="submitted",
            provider_request_id=f"provider:{delivery_request_id}",
            remote_task_id="remote-task-r10",
            remote_context_id="remote-context-r10",
        )


class FakeProofAdapter(IdentityProofAdapter):
    def __init__(self, observation: IdentityProofObservation) -> None:
        self.observation = observation
        self.calls = 0

    def verify(self, request, credential_reference):
        self.calls += 1
        return self.observation


class FakeRemoteObserver(RemoteDeliveryObserver):
    def __init__(self, observations: list[RemoteProviderObservation]) -> None:
        self.observations = list(observations)
        self.calls = 0

    def observe(self, *, binding, receipt, envelope) -> RemoteProviderObservation:
        self.calls += 1
        if not self.observations:
            raise AssertionError("no remote observation left")
        return self.observations.pop(0)


class AgentServiceTrustRemoteR10Tests(unittest.TestCase):
    def _open(
        self,
        db: Path,
        *,
        proof_adapter: IdentityProofAdapter | None = None,
        remote_observers: dict[str, RemoteDeliveryObserver] | None = None,
        delivery_adapters: dict[str, DeliveryAdapter] | None = None,
    ) -> AgentServiceR10:
        service = AgentServiceR10.open(
            db,
            carrier_adapter=ReadyCarrier(),
            runtime_adapter=FakeRuntime(),
            artifact_reader=NoopArtifactReader(),
            policy_adapter=AllowPolicy(),
            delivery_adapters=delivery_adapters or {"a2a-jsonrpc": FakeDelivery()},
            identity_proof_adapter=proof_adapter,
            remote_delivery_observers=remote_observers or {},
        )
        self.addCleanup(service.close)
        return service

    def _agent(self, service: AgentServiceR10, name: str, *, routes=None):
        definition = service.definitions.create(name)
        revision = service.revisions.create(definition.id, {
            "name": name,
            "harness": "r10",
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
        instance = service.birth.birth(f"birth:{name}:r10", revision.id)
        service.reconciler.reconcile(instance.id)
        return revision, identity, instance

    def _delivery(self, service: AgentServiceR10):
        source_revision, source_identity, source_instance = self._agent(service, "source")
        target_revision, target_identity, _ = self._agent(
            service,
            "target",
            routes=[{
                "transport": "a2a-jsonrpc",
                "protocolVersion": "1.0",
                "url": "https://agents.example.test/target",
                "priority": 10,
                "securityRequirements": {"oauth2": ["review.invoke"]},
            }],
        )
        goal = service.goals.create("r10 goal")
        task = service.tasks.create(
            description="review task",
            required_revision_id=source_revision.id,
            execution={"workspaceId":"ws-test","executable":"/usr/bin/true","args":[],"cwdRelative":".","env":{}},
            acceptance={"kind":"stdout_equals","value":"OK"},
        )
        service.goal_task_links.attach(goal.id, task.id)
        session = service.sessions.open(
            client_session_id="r10:session",
            initiator_identity_id=source_identity.id,
            goal_id=goal.id,
        )
        envelope = service.delegations.create(
            client_delegation_id="r10:delegation",
            session_id=session.id,
            source_identity_id=source_identity.id,
            source_instance_id=source_instance.id,
            target_identity_id=target_identity.id,
            target_revision_id=target_revision.id,
            task_id=task.id,
            capability_key="review",
            payload={"text": "review"},
            evidence_contract={"kind": "text/markdown"},
        )
        binding = service.routes.plan(
            envelope.id,
            client_policy_request_id="r10:policy",
            preferred_transports=["a2a-jsonrpc"],
        )
        receipt = service.delivery.deliver(binding.id)
        return source_identity, session, task, envelope, binding, receipt

    def test_credential_reference_stores_locator_not_secret_material_and_exact_replays(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            service = self._open(Path(tmp) / "service.db")
            first = service.credential_references.register(
                client_reference_id="credref:1",
                provider="vault",
                reference="vault://ordivon/a2a/source-client",
                issuer="https://auth.example.test",
                resource="https://agents.example.test",
                requested_scopes=["review.invoke"],
            )
            replay = service.credential_references.register(
                client_reference_id="credref:1",
                provider="vault",
                reference="vault://ordivon/a2a/source-client",
                issuer="https://auth.example.test",
                resource="https://agents.example.test",
                requested_scopes=["review.invoke"],
            )

            self.assertEqual(first.id, replay.id)
            self.assertFalse(hasattr(first, "access_token"))
            self.assertFalse(hasattr(first, "client_secret"))
            self.assertFalse(hasattr(first, "secret_material"))
            with self.assertRaises(ValueError):
                service.credential_references.register(
                    client_reference_id="credref:1",
                    provider="vault",
                    reference="vault://ordivon/a2a/other",
                    issuer="https://auth.example.test",
                    resource="https://agents.example.test",
                    requested_scopes=["review.invoke"],
                )

    def test_identity_proof_is_evidence_receipt_and_does_not_mutate_agent_identity(self) -> None:
        proof_adapter = FakeProofAdapter(
            IdentityProofObservation(
                authenticated=True,
                principal_id="principal:alice",
                issuer="https://auth.example.test",
                auth_method="oauth2",
                expires_at_ms=9_999_999_999_999,
                evidence_ref="proof://r10/1",
            )
        )
        with tempfile.TemporaryDirectory() as tmp:
            service = self._open(Path(tmp) / "service.db", proof_adapter=proof_adapter)
            _, identity, _ = self._agent(service, "caller")
            credential = service.credential_references.register(
                client_reference_id="credref:proof",
                provider="vault",
                reference="vault://ordivon/caller",
                issuer="https://auth.example.test",
                resource="https://agents.example.test",
                requested_scopes=["review.invoke"],
            )
            proof = service.identity_proofs.verify(
                client_proof_request_id="proof:req:1",
                identity_id=identity.id,
                credential_reference_id=credential.id,
                purpose="outbound-agent-auth",
            )

            self.assertTrue(proof.authenticated)
            self.assertEqual(proof.principal_id, "principal:alice")
            self.assertEqual(service.identities.get(identity.id).stable_name, "caller")
            self.assertFalse(hasattr(service.identities.get(identity.id), "principal_id"))
            self.assertFalse(hasattr(proof, "access_token"))

    def test_identity_proof_exact_replay_is_historical_and_issuer_mismatch_fails_closed(self) -> None:
        adapter = FakeProofAdapter(
            IdentityProofObservation(
                authenticated=True,
                principal_id="principal:alice",
                issuer="https://auth.example.test",
                auth_method="oauth2",
                expires_at_ms=9_999_999_999_999,
                evidence_ref="proof://r10/2",
            )
        )
        with tempfile.TemporaryDirectory() as tmp:
            service = self._open(Path(tmp) / "service.db", proof_adapter=adapter)
            _, identity, _ = self._agent(service, "caller-replay")
            credential = service.credential_references.register(
                client_reference_id="credref:replay",
                provider="vault",
                reference="vault://ordivon/caller-replay",
                issuer="https://auth.example.test",
                resource="https://agents.example.test",
                requested_scopes=[],
            )
            first = service.identity_proofs.verify(
                client_proof_request_id="proof:req:replay",
                identity_id=identity.id,
                credential_reference_id=credential.id,
                purpose="outbound-agent-auth",
            )
            adapter.observation = IdentityProofObservation(
                authenticated=False,
                principal_id=None,
                issuer="https://evil.example.test",
                auth_method="oauth2",
                expires_at_ms=None,
                evidence_ref="proof://changed",
            )
            replay = service.identity_proofs.verify(
                client_proof_request_id="proof:req:replay",
                identity_id=identity.id,
                credential_reference_id=credential.id,
                purpose="outbound-agent-auth",
            )
            self.assertEqual(first.id, replay.id)
            self.assertEqual(adapter.calls, 1)

            mismatch_adapter = FakeProofAdapter(
                IdentityProofObservation(
                    authenticated=True,
                    principal_id="principal:mallory",
                    issuer="https://evil.example.test",
                    auth_method="oauth2",
                    expires_at_ms=None,
                    evidence_ref="proof://mismatch",
                )
            )
            service.identity_proofs.set_adapter(mismatch_adapter)
            with self.assertRaises(ValueError):
                service.identity_proofs.verify(
                    client_proof_request_id="proof:req:mismatch",
                    identity_id=identity.id,
                    credential_reference_id=credential.id,
                    purpose="outbound-agent-auth",
                )

    def test_identity_proof_freshness_is_derived_not_persisted_as_state(self) -> None:
        adapter = FakeProofAdapter(
            IdentityProofObservation(
                authenticated=True,
                principal_id="principal:alice",
                issuer="https://auth.example.test",
                auth_method="oauth2",
                expires_at_ms=2000,
                evidence_ref="proof://freshness",
            )
        )
        with tempfile.TemporaryDirectory() as tmp:
            service = self._open(Path(tmp) / "service.db", proof_adapter=adapter)
            _, identity, _ = self._agent(service, "freshness")
            credential = service.credential_references.register(
                client_reference_id="credref:freshness",
                provider="vault",
                reference="vault://ordivon/freshness",
                issuer="https://auth.example.test",
                resource="https://agents.example.test",
                requested_scopes=[],
            )
            proof = service.identity_proofs.verify(
                client_proof_request_id="proof:req:freshness",
                identity_id=identity.id,
                credential_reference_id=credential.id,
                purpose="test",
                observed_at_ms=1000,
            )

            self.assertTrue(service.identity_proofs.is_current(proof.id, at_ms=1500))
            self.assertFalse(service.identity_proofs.is_current(proof.id, at_ms=2500))
            self.assertFalse(hasattr(proof, "state"))

    def test_remote_terminal_observation_never_directly_completes_local_task(self) -> None:
        observer = FakeRemoteObserver(
            [
                RemoteProviderObservation(
                    provider_status="TASK_STATE_COMPLETED",
                    terminal=True,
                    successful=True,
                    remote_task_id="remote-task-r10",
                    remote_context_id="remote-context-r10",
                    artifact_refs=("remote-artifact:1",),
                    evidence_ref="remote://obs/1",
                )
            ]
        )
        with tempfile.TemporaryDirectory() as tmp:
            service = self._open(
                Path(tmp) / "service.db",
                remote_observers={"a2a-jsonrpc": observer},
            )
            _, _, task, _, binding, _ = self._delivery(service)

            observation = service.remote_reconciler.reconcile(binding.id)

            self.assertTrue(observation.terminal)
            self.assertTrue(observation.successful)
            self.assertEqual(service.tasks.get(task.id).state, "PENDING")
            self.assertNotIn(
                "TASK_SUCCEEDED",
                [event.event_type for event in service.events.list_for("Task", task.id)],
            )

    def test_remote_observation_correlation_mismatch_fails_closed(self) -> None:
        observer = FakeRemoteObserver(
            [
                RemoteProviderObservation(
                    provider_status="TASK_STATE_WORKING",
                    terminal=False,
                    successful=None,
                    remote_task_id="different-remote-task",
                    remote_context_id="remote-context-r10",
                    artifact_refs=(),
                    evidence_ref="remote://bad",
                )
            ]
        )
        with tempfile.TemporaryDirectory() as tmp:
            service = self._open(
                Path(tmp) / "service.db",
                remote_observers={"a2a-jsonrpc": observer},
            )
            _, _, _, _, binding, _ = self._delivery(service)

            with self.assertRaises(ValueError):
                service.remote_reconciler.reconcile(binding.id)

            self.assertEqual(service.remote_observations.list_for_binding(binding.id), [])

    def test_repeated_identical_remote_observation_does_not_duplicate_snapshot(self) -> None:
        value = RemoteProviderObservation(
            provider_status="TASK_STATE_WORKING",
            terminal=False,
            successful=None,
            remote_task_id="remote-task-r10",
            remote_context_id="remote-context-r10",
            artifact_refs=(),
            evidence_ref="remote://working",
        )
        observer = FakeRemoteObserver([value, value])
        with tempfile.TemporaryDirectory() as tmp:
            service = self._open(
                Path(tmp) / "service.db",
                remote_observers={"a2a-jsonrpc": observer},
            )
            _, _, _, _, binding, _ = self._delivery(service)

            first = service.remote_reconciler.reconcile(binding.id)
            second = service.remote_reconciler.reconcile(binding.id)

            self.assertEqual(first.id, second.id)
            self.assertEqual(len(service.remote_observations.list_for_binding(binding.id)), 1)

    def test_remote_observation_history_survives_reconstruction(self) -> None:
        observer = FakeRemoteObserver(
            [
                RemoteProviderObservation(
                    provider_status="TASK_STATE_WORKING",
                    terminal=False,
                    successful=None,
                    remote_task_id="remote-task-r10",
                    remote_context_id="remote-context-r10",
                    artifact_refs=(),
                    evidence_ref="remote://restart",
                )
            ]
        )
        with tempfile.TemporaryDirectory() as tmp:
            db = Path(tmp) / "service.db"
            first = self._open(db, remote_observers={"a2a-jsonrpc": observer})
            _, _, _, _, binding, _ = self._delivery(first)
            recorded = first.remote_reconciler.reconcile(binding.id)
            first.close()

            second = AgentServiceR10.open(
                db,
                carrier_adapter=ReadyCarrier(),
                runtime_adapter=FakeRuntime(),
                artifact_reader=NoopArtifactReader(),
                policy_adapter=AllowPolicy(),
                delivery_adapters={"a2a-jsonrpc": FakeDelivery()},
                remote_delivery_observers={},
            )
            self.addCleanup(second.close)
            restored = second.remote_observations.latest_for_binding(binding.id)
            self.assertEqual(restored.id, recorded.id)
            self.assertEqual(restored.provider_status, "TASK_STATE_WORKING")

    def test_audit_projector_is_pure_and_omits_credential_locator_and_delegation_payload(self) -> None:
        adapter = FakeProofAdapter(
            IdentityProofObservation(
                authenticated=True,
                principal_id="principal:audit",
                issuer="https://auth.example.test",
                auth_method="oauth2",
                expires_at_ms=None,
                evidence_ref="proof://audit",
            )
        )
        observer = FakeRemoteObserver(
            [
                RemoteProviderObservation(
                    provider_status="TASK_STATE_WORKING",
                    terminal=False,
                    successful=None,
                    remote_task_id="remote-task-r10",
                    remote_context_id="remote-context-r10",
                    artifact_refs=(),
                    evidence_ref="remote://audit",
                )
            ]
        )
        with tempfile.TemporaryDirectory() as tmp:
            service = self._open(
                Path(tmp) / "service.db",
                proof_adapter=adapter,
                remote_observers={"a2a-jsonrpc": observer},
            )
            identity, _, _, envelope, binding, _ = self._delivery(service)
            credential = service.credential_references.register(
                client_reference_id="credref:audit",
                provider="vault",
                reference="vault://SECRET-PATH-THAT-MUST-NOT-BE-AUDITED",
                issuer="https://auth.example.test",
                resource="https://agents.example.test",
                requested_scopes=[],
            )
            proof = service.identity_proofs.verify(
                client_proof_request_id="proof:req:audit",
                identity_id=identity.id,
                credential_reference_id=credential.id,
                purpose="audit-test",
            )
            service.remote_reconciler.reconcile(binding.id)

            proof_audit = service.audit.project_identity_proof(proof.id)
            delivery_audit = service.audit.project_remote_delivery(binding.id)
            rendered = repr((proof_audit, delivery_audit))

            self.assertNotIn("SECRET-PATH-THAT-MUST-NOT-BE-AUDITED", rendered)
            self.assertNotIn("review\'", rendered)
            self.assertNotIn(repr(envelope.payload), rendered)
            tables = {
                row["name"]
                for row in service._connection.execute(
                    "SELECT name FROM sqlite_master WHERE type = 'table'"
                ).fetchall()
            }
            self.assertNotIn("audit_records", tables)
            self.assertEqual(proof_audit["credentialReferenceId"], credential.id)
            self.assertEqual(delivery_audit["bindingId"], binding.id)


    def test_remote_correlation_can_be_established_after_delivery_but_cannot_drift(self) -> None:
        class DeliveryWithoutCorrelation(DeliveryAdapter):
            def send(self, *, delivery_request_id: str, binding, envelope) -> DeliveryObservation:
                return DeliveryObservation(
                    admission="committed",
                    status="submitted",
                    provider_request_id=f"provider:{delivery_request_id}",
                    remote_task_id=None,
                    remote_context_id=None,
                )

        observer = FakeRemoteObserver(
            [
                RemoteProviderObservation(
                    provider_status="TASK_STATE_WORKING",
                    terminal=False,
                    successful=None,
                    remote_task_id="remote-task-established",
                    remote_context_id="remote-context-established",
                    artifact_refs=(),
                    evidence_ref="remote://established",
                ),
                RemoteProviderObservation(
                    provider_status="TASK_STATE_WORKING",
                    terminal=False,
                    successful=None,
                    remote_task_id="remote-task-drifted",
                    remote_context_id="remote-context-established",
                    artifact_refs=(),
                    evidence_ref="remote://drifted",
                ),
            ]
        )
        with tempfile.TemporaryDirectory() as tmp:
            service = self._open(
                Path(tmp) / "service.db",
                remote_observers={"a2a-jsonrpc": observer},
                delivery_adapters={"a2a-jsonrpc": DeliveryWithoutCorrelation()},
            )
            _, _, _, _, binding, receipt = self._delivery(service)
            self.assertIsNone(receipt.remote_task_id)
            self.assertIsNone(receipt.remote_context_id)

            first = service.remote_reconciler.reconcile(binding.id)
            self.assertEqual(first.remote_task_id, "remote-task-established")
            self.assertEqual(first.remote_context_id, "remote-context-established")
            audit = service.audit.project_remote_delivery(binding.id)
            self.assertEqual(audit["remoteTaskId"], "remote-task-established")
            self.assertEqual(audit["remoteContextId"], "remote-context-established")

            with self.assertRaises(ValueError):
                service.remote_reconciler.reconcile(binding.id)

            history = service.remote_observations.list_for_binding(binding.id)
            self.assertEqual(len(history), 1)
            self.assertEqual(history[0].remote_task_id, "remote-task-established")


if __name__ == "__main__":
    unittest.main()
