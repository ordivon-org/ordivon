from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from agent_service.delivery import (
    AgentServiceR9,
    DeliveryAdapter,
    DeliveryObservation,
    PolicyAdapter,
    PolicyObservation,
)
from agent_service.evidence import RuntimeArtifactPayload, RuntimeArtifactReader
from agent_service.slice1 import CarrierProviderAdapter, ProviderObservation
from agent_service.task_runtime import RuntimeAdapter, RuntimeJobObservation, RuntimeJobRef


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


class FakePolicy(PolicyAdapter):
    def __init__(self, *, allowed: bool, revision: str = "policy-r1", permissions: tuple[str, ...] = ()) -> None:
        self.allowed = allowed
        self.revision = revision
        self.permissions = permissions
        self.calls = 0

    def evaluate(self, request):
        self.calls += 1
        return PolicyObservation(
            allowed=self.allowed,
            reason=None if self.allowed else "denied-by-test-policy",
            policy_revision=self.revision,
            granted_permissions=self.permissions,
        )


class FakeDelivery(DeliveryAdapter):
    def __init__(self, transport: str = "a2a-jsonrpc") -> None:
        self.transport = transport
        self.committed: dict[str, DeliveryObservation] = {}
        self.calls: list[str] = []
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
            remote_task_id=f"remote-task:{len(self.committed)+1}" if self.transport.startswith("a2a") else None,
            remote_context_id=f"remote-context:{len(self.committed)+1}" if self.transport.startswith("a2a") else None,
        )
        self.committed[delivery_request_id] = value
        if self.fail_after_commit_once:
            self.fail_after_commit_once = False
            raise RuntimeError("simulated response loss after remote commit")
        return value


class AgentServiceDeliveryR9Tests(unittest.TestCase):
    def _open(
        self,
        db: Path,
        *,
        policy: PolicyAdapter | None = None,
        deliveries: dict[str, DeliveryAdapter] | None = None,
    ) -> AgentServiceR9:
        service = AgentServiceR9.open(
            db,
            carrier_adapter=ReadyCarrier(),
            runtime_adapter=FakeRuntime(),
            artifact_reader=NoopArtifactReader(),
            policy_adapter=policy,
            delivery_adapters=deliveries or {},
        )
        self.addCleanup(service.close)
        return service

    def _agent(self, service: AgentServiceR9, name: str, *, routes=None):
        definition = service.definitions.create(name)
        revision = service.revisions.create(definition.id, {
            "name": name,
            "harness": "r9",
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
        instance = service.birth.birth(f"birth:{name}:r9", revision.id)
        service.reconciler.reconcile(instance.id)
        return revision, identity, instance

    def _setup_delegation(self, service: AgentServiceR9):
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
                    "securityRequirements": {"oauth2": ["tools.call"]},
                },
            ],
        )
        goal = service.goals.create("r9 goal")
        task = service.tasks.create(
            description="review task",
            required_revision_id=source_revision.id,
            execution={"workspaceId":"ws-test","executable":"/usr/bin/true","args":[],"cwdRelative":".","env":{}},
            acceptance={"kind":"stdout_equals","value":"OK"},
        )
        service.goal_task_links.attach(goal.id, task.id)
        session = service.sessions.open(
            client_session_id="r9:session",
            initiator_identity_id=source_identity.id,
            goal_id=goal.id,
        )
        envelope = service.delegations.create(
            client_delegation_id="r9:delegation",
            session_id=session.id,
            source_identity_id=source_identity.id,
            source_instance_id=source_instance.id,
            target_identity_id=target_identity.id,
            target_revision_id=target_revision.id,
            task_id=task.id,
            capability_key="review",
            payload={"text":"review"},
            evidence_contract={"kind":"text/markdown"},
        )
        return envelope, session, task, target_revision

    def test_route_profiles_are_revision_native_without_second_interface_store(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            service = self._open(Path(tmp) / "service.db")
            _, _, _, target_revision = self._setup_delegation(service)
            persisted = service.revisions.get(target_revision.id).spec["routes"]

            self.assertEqual(len(persisted), 2)
            self.assertEqual(persisted[0]["transport"], "a2a-jsonrpc")
            self.assertEqual(persisted[0]["protocolVersion"], "1.0")
            self.assertFalse(hasattr(service, "interfaces"))
            table = service._connection.execute(
                "SELECT 1 FROM sqlite_master "
                "WHERE type='table' AND name='agent_interface_advertisements'"
            ).fetchone()
            self.assertIsNone(table)

    def test_denied_policy_decision_blocks_route_even_when_capability_is_advertised(self) -> None:
        policy = FakePolicy(allowed=False)
        with tempfile.TemporaryDirectory() as tmp:
            service = self._open(Path(tmp) / "service.db", policy=policy)
            envelope, _, _, target_revision = self._setup_delegation(service)
            decision = service.policy.evaluate(
                client_policy_request_id="policy:deny",
                delegation_id=envelope.id,
            )

            self.assertFalse(decision.payload["allowed"])
            with self.assertRaises(PermissionError):
                service.routes.plan(envelope.id, decision.id, preferred_transports=["a2a-jsonrpc"])

    def test_policy_exact_replay_uses_historical_decision_without_re_evaluation(self) -> None:
        policy = FakePolicy(allowed=True, revision="policy-r1", permissions=("review.invoke",))
        with tempfile.TemporaryDirectory() as tmp:
            service = self._open(Path(tmp) / "service.db", policy=policy)
            envelope, _, _, _ = self._setup_delegation(service)
            first = service.policy.evaluate(
                client_policy_request_id="policy:replay",
                delegation_id=envelope.id,
            )
            policy.allowed = False
            replay = service.policy.evaluate(
                client_policy_request_id="policy:replay",
                delegation_id=envelope.id,
            )

            self.assertEqual(first.id, replay.id)
            self.assertTrue(replay.payload["allowed"])
            self.assertEqual(replay.payload["grantedPermissions"], ["review.invoke"])
            self.assertEqual(policy.calls, 1)

    def test_route_planner_selects_only_advertised_interface_after_allowed_policy(self) -> None:
        policy = FakePolicy(allowed=True)
        with tempfile.TemporaryDirectory() as tmp:
            service = self._open(Path(tmp) / "service.db", policy=policy)
            envelope, _, _, target_revision = self._setup_delegation(service)
            decision = service.policy.evaluate(
                client_policy_request_id="policy:allow-route",
                delegation_id=envelope.id,
            )
            binding = service.routes.plan(
                envelope.id,
                decision.id,
                preferred_transports=["a2a-jsonrpc", "mcp"],
            )

            self.assertEqual(binding.transport, "a2a-jsonrpc")
            self.assertEqual(binding.endpoint, "https://agents.example.test/target")
            self.assertFalse(hasattr(binding, "remote_task_id"))
            self.assertFalse(hasattr(binding, "remote_context_id"))


    def test_same_delegation_can_have_distinct_immutable_route_bindings_for_fallback(self) -> None:
        policy = FakePolicy(allowed=True)
        with tempfile.TemporaryDirectory() as tmp:
            service = self._open(Path(tmp) / "service.db", policy=policy)
            envelope, _, _, target_revision = self._setup_delegation(service)
            decision = service.policy.evaluate(
                client_policy_request_id="policy:fallback",
                delegation_id=envelope.id,
            )

            primary = service.routes.plan(
                envelope.id, decision.id, preferred_transports=["a2a-jsonrpc"]
            )
            fallback = service.routes.plan(
                envelope.id, decision.id, preferred_transports=["mcp"]
            )

            self.assertNotEqual(primary.id, fallback.id)
            self.assertEqual(primary.delegation_id, fallback.delegation_id)
            self.assertEqual(primary.transport, "a2a-jsonrpc")
            self.assertEqual(fallback.transport, "mcp")
            self.assertEqual(len(service.transport_bindings.list_for_delegation(envelope.id)), 2)

    def test_route_rejects_policy_decision_for_different_delegation(self) -> None:
        policy = FakePolicy(allowed=True)
        with tempfile.TemporaryDirectory() as tmp:
            service = self._open(Path(tmp) / "service.db", policy=policy)
            envelope, _, _, target_revision = self._setup_delegation(service)
            other = service.delegations.get_by_client_id("r9:delegation")
            decision = service.policy.evaluate(
                client_policy_request_id="policy:bound",
                delegation_id=other.id,
            )
            # manufacture a second delegation with a different exact identity
            second = service.delegations.create(
                client_delegation_id="r9:delegation:2",
                session_id=other.session_id,
                source_identity_id=other.source_identity_id,
                source_instance_id=other.source_instance_id,
                target_identity_id=other.target_identity_id,
                target_revision_id=other.target_revision_id,
                task_id=other.task_id,
                capability_key=other.capability_key,
                payload={"text":"different intent"},
                evidence_contract=other.evidence_contract,
            )

            with self.assertRaises(ValueError):
                service.routes.plan(second.id, decision.id, preferred_transports=["a2a-jsonrpc"])

    def test_delivery_response_loss_replays_same_request_and_remote_correlation(self) -> None:
        policy = FakePolicy(allowed=True)
        delivery = FakeDelivery("a2a-jsonrpc")
        delivery.fail_after_commit_once = True
        with tempfile.TemporaryDirectory() as tmp:
            service = self._open(
                Path(tmp) / "service.db",
                policy=policy,
                deliveries={"a2a-jsonrpc": delivery},
            )
            envelope, session, task, target_revision = self._setup_delegation(service)
            decision = service.policy.evaluate(
                client_policy_request_id="policy:deliver",
                delegation_id=envelope.id,
            )
            binding = service.routes.plan(
                envelope.id,
                decision.id,
                preferred_transports=["a2a-jsonrpc"],
            )

            with self.assertRaises(RuntimeError):
                service.delivery.deliver(binding.id)
            self.assertEqual(service.delivery_receipts.list_for_binding(binding.id), [])

            receipt = service.delivery.deliver(binding.id)

            self.assertEqual(delivery.calls[0], delivery.calls[1])
            self.assertEqual(len(delivery.committed), 1)
            self.assertEqual(receipt.admission, "existing")
            self.assertTrue(receipt.remote_task_id.startswith("remote-task:"))
            self.assertTrue(receipt.remote_context_id.startswith("remote-context:"))
            self.assertNotEqual(receipt.remote_task_id, task.id)
            self.assertNotEqual(receipt.remote_context_id, session.id)
            self.assertFalse(hasattr(service.sessions.get(session.id), "remote_context_id"))
            self.assertFalse(hasattr(service.tasks.get(task.id), "remote_task_id"))

    def test_mcp_delivery_receipt_may_have_no_remote_task_or_context(self) -> None:
        policy = FakePolicy(allowed=True)
        delivery = FakeDelivery("mcp")
        with tempfile.TemporaryDirectory() as tmp:
            service = self._open(
                Path(tmp) / "service.db",
                policy=policy,
                deliveries={"mcp": delivery},
            )
            envelope, _, _, target_revision = self._setup_delegation(service)
            decision = service.policy.evaluate(
                client_policy_request_id="policy:mcp",
                delegation_id=envelope.id,
            )
            binding = service.routes.plan(envelope.id, decision.id, preferred_transports=["mcp"])
            receipt = service.delivery.deliver(binding.id)

            self.assertIsNone(receipt.remote_task_id)
            self.assertIsNone(receipt.remote_context_id)

    def test_delivery_state_survives_service_reconstruction(self) -> None:
        policy = FakePolicy(allowed=True)
        delivery = FakeDelivery("a2a-jsonrpc")
        with tempfile.TemporaryDirectory() as tmp:
            db = Path(tmp) / "service.db"
            first = self._open(db, policy=policy, deliveries={"a2a-jsonrpc": delivery})
            envelope, _, _, target_revision = self._setup_delegation(first)
            decision = first.policy.evaluate(
                client_policy_request_id="policy:restart",
                delegation_id=envelope.id,
            )
            binding = first.routes.plan(envelope.id, decision.id, preferred_transports=["a2a-jsonrpc"])
            receipt = first.delivery.deliver(binding.id)
            first.close()

            second = AgentServiceR9.open(
                db,
                carrier_adapter=ReadyCarrier(),
                runtime_adapter=FakeRuntime(),
                artifact_reader=NoopArtifactReader(),
                policy_adapter=FakePolicy(allowed=False),
                delivery_adapters={"a2a-jsonrpc": delivery},
            )
            self.addCleanup(second.close)

            self.assertTrue(second.events.get(decision.id).payload["allowed"])
            self.assertFalse(hasattr(second, "policy_decisions"))
            self.assertEqual(second.transport_bindings.get(binding.id).endpoint, binding.endpoint)
            self.assertEqual(second.delivery_receipts.get(receipt.id).remote_task_id, receipt.remote_task_id)
            replay = second.delivery.deliver(binding.id)
            self.assertEqual(replay.id, receipt.id)


if __name__ == "__main__":
    unittest.main()
