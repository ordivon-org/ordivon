from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from agent_service.delivery import DeliveryAdapter, DeliveryObservation, PolicyAdapter, PolicyObservation
from agent_service.effect_authority import AgentServiceR15
from agent_service.evidence import RuntimeArtifactPayload, RuntimeArtifactReader
from agent_service.slice1 import CarrierProviderAdapter, ProviderObservation
from agent_service.task_runtime import RuntimeAdapter, RuntimeJobObservation, RuntimeJobRef


class ReadyCarrier(CarrierProviderAdapter):
    def ensure(self, placement_id: str, agent_instance_id: str, revision_id: str) -> None:
        return None

    def retire(self, placement_id: str, agent_instance_id: str) -> None:
        return None

    def observe(self, placement_id: str) -> ProviderObservation:
        return ProviderObservation(
            placement_id=placement_id,
            state="READY",
            evidence_ref="test://ready",
        )


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


class MutablePolicy(PolicyAdapter):
    def __init__(self, allowed: bool = True) -> None:
        self.allowed = allowed
        self.revision = 1
        self.calls = 0

    def evaluate(self, request):
        self.calls += 1
        return PolicyObservation(
            allowed=self.allowed,
            reason=None if self.allowed else "revoked-by-test-policy",
            policy_revision=f"policy-r{self.revision}",
            granted_permissions=("review.invoke",),
        )


class CountingDelivery(DeliveryAdapter):
    def __init__(self) -> None:
        self.calls = 0
        self.fail_once = False

    def send(self, *, delivery_request_id: str, binding, envelope) -> DeliveryObservation:
        self.calls += 1
        if self.fail_once:
            self.fail_once = False
            raise RuntimeError("simulated response loss")
        return DeliveryObservation(
            admission="committed",
            status="submitted",
            provider_request_id=f"provider:{delivery_request_id}",
            remote_task_id=f"remote:{delivery_request_id}",
            remote_context_id="context:r15",
        )


class AgentServiceEffectAuthorityR15Tests(unittest.TestCase):
    def _open(self, db: Path, policy: PolicyAdapter | None, delivery: CountingDelivery) -> AgentServiceR15:
        service = AgentServiceR15.open(
            db,
            carrier_adapter=ReadyCarrier(),
            runtime_adapter=FakeRuntime(),
            artifact_reader=NoopArtifactReader(),
            policy_adapter=policy,
            delivery_adapters={"a2a-jsonrpc": delivery},
        )
        self.addCleanup(service.close)
        return service

    def _agent(self, service, name: str, *, routes=None):
        definition = service.definitions.create(name)
        revision = service.revisions.create(definition.id, {
            "name": name,
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
        identity = service.identities.create(
            definition.id,
            stable_name=name,
            description=name,
        )
        instance = service.birth.birth(f"birth:{name}:r15", revision.id)
        service.reconciler.reconcile(instance.id)
        return revision, identity, instance

    def _setup(self, service):
        source_revision, source_identity, source_instance = self._agent(service, "source-r15")
        target_revision, target_identity, _ = self._agent(
            service,
            "target-r15",
            routes=[{
                "transport": "a2a-jsonrpc",
                "protocolVersion": "1.0",
                "url": "https://agents.example.test/rpc",
                "priority": 10,
                "securityRequirements": {},
            }],
        )
        task = service.tasks.create(
            description="r15",
            required_revision_id=source_revision.id,
            execution={
                "workspaceId": "x",
                "executable": "/usr/bin/true",
                "args": [],
                "cwdRelative": ".",
                "env": {},
            },
            acceptance={
                "kind": "runtime_artifact_text_contains",
                "artifactKind": "review-markdown",
                "value": "ACCEPTED",
            },
        )
        session = service.sessions.open(
            client_session_id="r15:session",
            initiator_identity_id=source_identity.id,
        )
        envelope = service.delegations.create(
            client_delegation_id="r15:delegation",
            session_id=session.id,
            source_identity_id=source_identity.id,
            source_instance_id=source_instance.id,
            target_identity_id=target_identity.id,
            target_revision_id=target_revision.id,
            task_id=task.id,
            capability_key="review",
            payload={"text": "review"},
            evidence_contract={"kind": "review-markdown"},
        )
        binding = service.routes.plan(
            envelope.id,
            client_policy_request_id="r15:route-policy",
            preferred_transports=["a2a-jsonrpc"],
        )
        route_receipt = service.events.get(binding.policy_receipt_id)
        return session, envelope, route_receipt, binding

    def test_missing_effect_policy_fails_closed_before_external_send(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            route_policy = MutablePolicy(allowed=True)
            delivery = CountingDelivery()
            service = self._open(Path(tmp) / "s.db", route_policy, delivery)
            _, _, _, binding = self._setup(service)

            service.effect_authorizations._policy_adapter = None
            with self.assertRaisesRegex(RuntimeError, "no PolicyAdapter configured"):
                service.delivery.deliver(binding.id)

            self.assertEqual(delivery.calls, 0)

    def test_current_policy_is_rechecked_before_first_external_effect(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            policy = MutablePolicy(allowed=True)
            delivery = CountingDelivery()
            service = self._open(Path(tmp) / "s.db", policy, delivery)
            _, _, route_receipt, binding = self._setup(service)
            self.assertTrue(route_receipt.payload["allowed"])
            self.assertEqual(policy.calls, 1)

            policy.allowed = False
            policy.revision = 2

            with self.assertRaises(PermissionError):
                service.delivery.deliver(binding.id)

            self.assertEqual(delivery.calls, 0)
            self.assertEqual(policy.calls, 2)
            effect = service.effect_authorization_records.get_by_binding(binding.id)
            self.assertFalse(effect.allowed)
            self.assertEqual(effect.policy_revision, "policy-r2")

    def test_denied_effect_identity_stays_denied_when_policy_later_changes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            policy = MutablePolicy(allowed=True)
            delivery = CountingDelivery()
            service = self._open(Path(tmp) / "s.db", policy, delivery)
            _, _, _, binding = self._setup(service)

            policy.allowed = False
            policy.revision = 2
            with self.assertRaises(PermissionError):
                service.delivery.deliver(binding.id)
            self.assertEqual(policy.calls, 2)
            self.assertEqual(delivery.calls, 0)

            policy.allowed = True
            policy.revision = 3
            with self.assertRaises(PermissionError):
                service.delivery.deliver(binding.id)

            self.assertEqual(
                policy.calls,
                2,
                "same denied effect identity must not be silently re-authorized",
            )
            self.assertEqual(delivery.calls, 0)
            frozen = service.effect_authorization_records.get_by_binding(binding.id)
            self.assertFalse(frozen.allowed)
            self.assertEqual(frozen.policy_revision, "policy-r2")

    def test_session_close_is_continuity_close_not_implicit_revocation(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            policy = MutablePolicy(allowed=True)
            delivery = CountingDelivery()
            service = self._open(Path(tmp) / "s.db", policy, delivery)
            session, _, _, binding = self._setup(service)
            service.sessions.close(session.id)

            receipt = service.delivery.deliver(binding.id)

            self.assertEqual(receipt.binding_id, binding.id)
            self.assertEqual(delivery.calls, 1)
            self.assertEqual(policy.calls, 2)
            effect = service.effect_authorization_records.get_by_binding(binding.id)
            self.assertTrue(effect.allowed)

    def test_effect_authorization_is_frozen_to_exact_binding_effect_identity(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            policy = MutablePolicy(allowed=True)
            delivery = CountingDelivery()
            delivery.fail_once = True
            service = self._open(Path(tmp) / "s.db", policy, delivery)
            _, _, _, binding = self._setup(service)

            with self.assertRaisesRegex(RuntimeError, "simulated response loss"):
                service.delivery.deliver(binding.id)

            effect = service.effect_authorization_records.get_by_binding(binding.id)
            self.assertTrue(effect.allowed)
            self.assertEqual(policy.calls, 2)

            policy.allowed = False
            policy.revision = 2
            receipt = service.delivery.deliver(binding.id)

            self.assertEqual(receipt.binding_id, binding.id)
            self.assertEqual(delivery.calls, 2)
            self.assertEqual(
                policy.calls,
                2,
                "same exact delivery effect must replay its frozen effect authorization",
            )

    def test_existing_receipt_replay_does_not_require_new_authorization(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            policy = MutablePolicy(allowed=True)
            delivery = CountingDelivery()
            service = self._open(Path(tmp) / "s.db", policy, delivery)
            _, _, _, binding = self._setup(service)

            first = service.delivery.deliver(binding.id)
            self.assertEqual(policy.calls, 2)
            policy.allowed = False
            policy.revision = 2

            replay = service.delivery.deliver(binding.id)

            self.assertEqual(replay.id, first.id)
            self.assertEqual(delivery.calls, 1)
            self.assertEqual(policy.calls, 2)


if __name__ == "__main__":
    unittest.main()
