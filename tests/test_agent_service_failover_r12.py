from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from agent_service.delivery import DeliveryAdapter, DeliveryObservation, PolicyAdapter, PolicyObservation
from agent_service.evidence import RuntimeArtifactPayload, RuntimeArtifactReader
from agent_service.failover import (
    AgentServiceR12,
    ExecutionQuiescenceAdapter,
    ExecutionQuiescenceObservation,
    ReplaySafetyAdapter,
    ReplaySafetyObservation,
)
from agent_service.slice1 import CarrierProviderAdapter, ProviderObservation
from agent_service.task_runtime import RuntimeAdapter, RuntimeJobObservation, RuntimeJobRef
from agent_service.trust import RemoteProviderObservation


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


class NoopRuntimeArtifactReader(RuntimeArtifactReader):
    def read(self, job_id: str, artifact_id: str) -> RuntimeArtifactPayload:
        raise AssertionError("runtime artifact read not expected")


class AllowPolicy(PolicyAdapter):
    def evaluate(self, request):
        return PolicyObservation(
            allowed=True,
            reason=None,
            policy_revision="policy-r12",
            granted_permissions=("review.invoke",),
        )


class RecordingDelivery(DeliveryAdapter):
    def __init__(self) -> None:
        self.calls: list[tuple[str, str]] = []
        self.committed: dict[str, DeliveryObservation] = {}

    def send(self, *, delivery_request_id: str, binding, envelope) -> DeliveryObservation:
        self.calls.append((binding.id, delivery_request_id))
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
            remote_task_id=f"remote-task:{binding.id}",
            remote_context_id=f"remote-context:{envelope.id}",
        )
        self.committed[delivery_request_id] = value
        return value


class RecordingQuiescenceAdapter(ExecutionQuiescenceAdapter):
    def __init__(self, *, quiescent: bool = True) -> None:
        self.quiescent = quiescent
        self.calls: list[str] = []
        self.observations: dict[str, ExecutionQuiescenceObservation] = {}
        self.fail_after_commit_once = False
        self.override_remote_task_id: str | None = None

    def prove_quiescence(self, *, quiescence_request_id: str, binding, receipt, envelope, latest_observation):
        self.calls.append(quiescence_request_id)
        existing = self.observations.get(quiescence_request_id)
        if existing is not None:
            return existing
        remote_task_id = self.override_remote_task_id
        if remote_task_id is None:
            remote_task_id = (
                receipt.remote_task_id
                if receipt is not None
                else None if latest_observation is None else latest_observation.remote_task_id
            )
        remote_context_id = (
            receipt.remote_context_id
            if receipt is not None
            else None if latest_observation is None else latest_observation.remote_context_id
        )
        value = ExecutionQuiescenceObservation(
            quiescent=self.quiescent,
            provider_status="TASK_STATE_CANCELED" if self.quiescent else "TASK_STATE_WORKING",
            remote_task_id=remote_task_id,
            remote_context_id=remote_context_id,
            evidence_ref=f"quiescence://{quiescence_request_id}",
        )
        self.observations[quiescence_request_id] = value
        if self.fail_after_commit_once:
            self.fail_after_commit_once = False
            raise RuntimeError("quiescence response lost after provider commit")
        return value


class RecordingReplaySafetyAdapter(ReplaySafetyAdapter):
    def __init__(
        self,
        *,
        safe: bool = True,
        classification: str = "IDEMPOTENT_REPLAY",
        reason: str | None = None,
    ) -> None:
        self.safe = safe
        self.classification = classification
        self.reason = reason
        self.calls: list[str] = []
        self.observations: dict[str, ReplaySafetyObservation] = {}
        self.fail_after_commit_once = False

    def evaluate_replay_safety(
        self,
        *,
        replay_safety_request_id: str,
        task,
        envelope,
        source_binding,
        target_binding,
        quiescence_proof,
        source_receipt,
        source_observations,
    ) -> ReplaySafetyObservation:
        self.calls.append(replay_safety_request_id)
        existing = self.observations.get(replay_safety_request_id)
        if existing is not None:
            return existing
        value = ReplaySafetyObservation(
            safe=self.safe,
            classification=self.classification,
            reason=self.reason,
            evidence_ref=f"replay://{replay_safety_request_id}",
        )
        self.observations[replay_safety_request_id] = value
        if self.fail_after_commit_once:
            self.fail_after_commit_once = False
            raise RuntimeError("replay-safety response lost after provider commit")
        return value


class AgentServiceFailoverR12Tests(unittest.TestCase):
    def _open(
        self,
        db: Path,
        *,
        delivery: RecordingDelivery | None = None,
        quiescence_adapter: ExecutionQuiescenceAdapter | None = None,
        replay_safety_adapter: ReplaySafetyAdapter | None = None,
    ) -> AgentServiceR12:
        delivery = delivery or RecordingDelivery()
        quiescence_adapters = {}
        if quiescence_adapter is not None:
            quiescence_adapters = {
                "a2a-jsonrpc": quiescence_adapter,
                "mcp": quiescence_adapter,
            }
        service = AgentServiceR12.open(
            db,
            carrier_adapter=ReadyCarrier(),
            runtime_adapter=FakeRuntime(),
            artifact_reader=NoopRuntimeArtifactReader(),
            policy_adapter=AllowPolicy(),
            delivery_adapters={"a2a-jsonrpc": delivery, "mcp": delivery},
            remote_delivery_observers={},
            remote_artifact_readers={},
            execution_quiescence_adapters=quiescence_adapters,
            replay_safety_adapter=replay_safety_adapter,
        )
        self.addCleanup(service.close)
        return service

    def _agent(self, service: AgentServiceR12, name: str, *, routes=None):
        definition = service.definitions.create(name)
        revision = service.revisions.create(definition.id, {
            "name": name,
            "harness": "r12",
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
        instance = service.birth.birth(f"birth:{name}:r12", revision.id)
        service.reconciler.reconcile(instance.id)
        return revision, identity, instance

    def _setup(self, service: AgentServiceR12, suffix: str = "main"):
        source_revision, source_identity, source_instance = self._agent(service, f"source-{suffix}")
        target_revision, target_identity, _ = self._agent(
            service,
            f"target-{suffix}",
            routes=[
                {
                    "transport": "a2a-jsonrpc",
                    "protocolVersion": "1.0",
                    "url": f"https://agents.example.test/{suffix}",
                    "priority": 10,
                    "securityRequirements": {},
                },
                {
                    "transport": "mcp",
                    "protocolVersion": "2026-07-28",
                    "url": f"https://mcp.example.test/{suffix}",
                    "priority": 20,
                    "securityRequirements": {},
                },
            ],
        )
        task = service.tasks.create(
            description=f"review-{suffix}",
            required_revision_id=source_revision.id,
            execution={"workspaceId":"ws-test","executable":"/usr/bin/true","args":[],"cwdRelative":".","env":{}},
            acceptance={"kind":"runtime_artifact_text_contains","artifactKind":"review-markdown","value":"ACCEPTED"},
        )
        session = service.sessions.open(
            client_session_id=f"r12:session:{suffix}",
            initiator_identity_id=source_identity.id,
        )
        envelope = service.delegations.create(
            client_delegation_id=f"r12:delegation:{suffix}",
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
        policy_request_id = f"r12:policy:{suffix}"
        primary = service.routes.plan(
            envelope.id,
            client_policy_request_id=policy_request_id,
            preferred_transports=["a2a-jsonrpc"],
        )
        fallback = service.routes.plan(
            envelope.id,
            client_policy_request_id=policy_request_id,
            preferred_transports=["mcp"],
        )
        return task, envelope, primary, fallback

    def _deliver_primary(self, service: AgentServiceR12, primary):
        receipt = service.delivery.deliver(primary.id)
        task_id = service.delegations.get(primary.delegation_id).task_id
        self.assertEqual(service.execution_claims.get(task_id).owner_id, primary.id)
        return receipt

    def _failover(self, service: AgentServiceR12, primary, fallback, suffix: str = "ok"):
        return service.failover.failover(
            client_failover_request_id=f"r12:failover:{suffix}",
            client_quiescence_request_id=f"r12:quiescence:{suffix}",
            client_replay_safety_request_id=f"r12:replay:{suffix}",
            from_binding_id=primary.id,
            to_binding_id=fallback.id,
        )

    def test_cancel_ack_or_working_status_is_not_quiescence(self) -> None:
        quiescence = RecordingQuiescenceAdapter(quiescent=False)
        replay = RecordingReplaySafetyAdapter()
        with tempfile.TemporaryDirectory() as tmp:
            service = self._open(Path(tmp) / "service.db", quiescence_adapter=quiescence, replay_safety_adapter=replay)
            task, _, primary, fallback = self._setup(service)
            self._deliver_primary(service, primary)

            proof = service.quiescence.prove(
                client_quiescence_request_id="r12:q:not-stopped", binding_id=primary.id
            )
            self.assertFalse(proof.quiescent)
            self.assertEqual(
                service.quiescence_requests.get_by_client_request("r12:q:not-stopped").state,
                "NOT_PROVED",
            )
            with self.assertRaises(RuntimeError):
                service.delivery.deliver(primary.id)
            with self.assertRaises(RuntimeError):
                service.replay_safety.evaluate(
                    client_replay_safety_request_id="r12:r:not-stopped",
                    from_binding_id=primary.id,
                    to_binding_id=fallback.id,
                    quiescence_proof_id=proof.id,
                )
            self.assertEqual(service.execution_claims.get(task.id).owner_id, primary.id)
            self.assertEqual(replay.calls, [])

    def test_quiescence_exact_replay_does_not_reinvoke_adapter(self) -> None:
        adapter = RecordingQuiescenceAdapter(quiescent=True)
        with tempfile.TemporaryDirectory() as tmp:
            service = self._open(Path(tmp) / "service.db", quiescence_adapter=adapter)
            _, _, primary, _ = self._setup(service)
            self._deliver_primary(service, primary)
            first = service.quiescence.prove(
                client_quiescence_request_id="r12:q:replay", binding_id=primary.id
            )
            adapter.quiescent = False
            replay = service.quiescence.prove(
                client_quiescence_request_id="r12:q:replay", binding_id=primary.id
            )
            self.assertEqual(first.id, replay.id)
            self.assertTrue(replay.quiescent)
            self.assertEqual(len(adapter.calls), 1)

    def test_quiescence_response_loss_keeps_source_claim_until_exact_retry(self) -> None:
        adapter = RecordingQuiescenceAdapter(quiescent=True)
        adapter.fail_after_commit_once = True
        replay = RecordingReplaySafetyAdapter()
        with tempfile.TemporaryDirectory() as tmp:
            service = self._open(Path(tmp) / "service.db", quiescence_adapter=adapter, replay_safety_adapter=replay)
            task, _, primary, fallback = self._setup(service)
            self._deliver_primary(service, primary)
            with self.assertRaises(RuntimeError):
                self._failover(service, primary, fallback, "lost-q")
            self.assertEqual(service.execution_claims.get(task.id).owner_id, primary.id)
            pending = service.quiescence_requests.get_by_client_request("r12:quiescence:lost-q")
            self.assertEqual(pending.state, "REQUESTED")
            with self.assertRaises(RuntimeError):
                service.delivery.deliver(primary.id)
            transfer = self._failover(service, primary, fallback, "lost-q")
            self.assertEqual(service.execution_claims.get(task.id).owner_id, fallback.id)
            self.assertEqual(transfer.to_binding_id, fallback.id)
            self.assertEqual(adapter.calls[0], adapter.calls[1])
            self.assertEqual(
                service.quiescence_requests.get_by_client_request("r12:quiescence:lost-q").state,
                "PROVED",
            )

    def test_positive_quiescence_freezes_old_binding_before_transfer(self) -> None:
        adapter = RecordingQuiescenceAdapter(quiescent=True)
        delivery = RecordingDelivery()
        with tempfile.TemporaryDirectory() as tmp:
            service = self._open(Path(tmp) / "service.db", delivery=delivery, quiescence_adapter=adapter)
            _, _, primary, _ = self._setup(service)
            original = self._deliver_primary(service, primary)
            proof = service.quiescence.prove(
                client_quiescence_request_id="r12:q:freeze", binding_id=primary.id
            )
            self.assertTrue(proof.quiescent)
            with self.assertRaises(RuntimeError):
                service.delivery.deliver(primary.id)
            self.assertEqual(service.delivery_receipts.get_by_binding(primary.id).id, original.id)
            self.assertEqual(len([x for x in delivery.calls if x[0] == primary.id]), 1)

    def test_terminal_unsuccessful_observation_proves_quiescence_without_adapter(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            service = self._open(Path(tmp) / "service.db")
            _, _, primary, _ = self._setup(service)
            receipt = self._deliver_primary(service, primary)
            service.remote_observations.record(
                binding_id=primary.id,
                observation=RemoteProviderObservation(
                    provider_status="TASK_STATE_FAILED",
                    terminal=True,
                    successful=False,
                    remote_task_id=receipt.remote_task_id,
                    remote_context_id=receipt.remote_context_id,
                    artifact_refs=(),
                    evidence_ref="remote://r12/failed",
                ),
            )
            proof = service.quiescence.prove(
                client_quiescence_request_id="r12:q:terminal-failed", binding_id=primary.id
            )
            self.assertTrue(proof.quiescent)
            self.assertEqual(proof.method, "terminal_unsuccessful_observation")

    def test_terminal_unknown_requires_adapter_proof(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            service = self._open(Path(tmp) / "service.db")
            _, _, primary, _ = self._setup(service)
            receipt = self._deliver_primary(service, primary)
            service.remote_observations.record(
                binding_id=primary.id,
                observation=RemoteProviderObservation(
                    provider_status="TASK_STATE_CANCELED",
                    terminal=True,
                    successful=None,
                    remote_task_id=receipt.remote_task_id,
                    remote_context_id=receipt.remote_context_id,
                    artifact_refs=(),
                    evidence_ref="remote://r12/canceled-unknown",
                ),
            )
            with self.assertRaises(LookupError):
                service.quiescence.prove(
                    client_quiescence_request_id="r12:q:unknown", binding_id=primary.id
                )

    def test_any_historical_terminal_success_blocks_failover_even_after_later_failure(self) -> None:
        adapter = RecordingQuiescenceAdapter(quiescent=True)
        replay = RecordingReplaySafetyAdapter()
        with tempfile.TemporaryDirectory() as tmp:
            service = self._open(Path(tmp) / "service.db", quiescence_adapter=adapter, replay_safety_adapter=replay)
            task, _, primary, fallback = self._setup(service)
            receipt = self._deliver_primary(service, primary)
            service.remote_observations.record(
                binding_id=primary.id,
                observation=RemoteProviderObservation(
                    provider_status="TASK_STATE_COMPLETED",
                    terminal=True,
                    successful=True,
                    remote_task_id=receipt.remote_task_id,
                    remote_context_id=receipt.remote_context_id,
                    artifact_refs=("artifact:done",),
                    evidence_ref="remote://r12/completed",
                ),
            )
            service.remote_observations.record(
                binding_id=primary.id,
                observation=RemoteProviderObservation(
                    provider_status="TASK_STATE_FAILED",
                    terminal=True,
                    successful=False,
                    remote_task_id=receipt.remote_task_id,
                    remote_context_id=receipt.remote_context_id,
                    artifact_refs=(),
                    evidence_ref="remote://r12/regressed-failed",
                ),
            )
            with self.assertRaises(RuntimeError):
                self._failover(service, primary, fallback, "history-success")
            self.assertEqual(service.execution_claims.get(task.id).owner_id, primary.id)
            self.assertEqual(adapter.calls, [])
            self.assertEqual(replay.calls, [])

    def test_quiescence_correlation_mismatch_fails_closed_without_proof(self) -> None:
        adapter = RecordingQuiescenceAdapter(quiescent=True)
        adapter.override_remote_task_id = "remote-task:wrong"
        with tempfile.TemporaryDirectory() as tmp:
            service = self._open(Path(tmp) / "service.db", quiescence_adapter=adapter)
            _, _, primary, _ = self._setup(service)
            self._deliver_primary(service, primary)
            with self.assertRaises(ValueError):
                service.quiescence.prove(
                    client_quiescence_request_id="r12:q:mismatch", binding_id=primary.id
                )
            self.assertIsNone(
                service.quiescence_proof_records.get_by_client_request("r12:q:mismatch", required=False)
            )

    def test_quiescent_but_partial_effects_blocks_transfer(self) -> None:
        quiescence = RecordingQuiescenceAdapter(quiescent=True)
        replay = RecordingReplaySafetyAdapter(
            safe=False, classification="PARTIAL_EFFECTS", reason="irreversible write observed"
        )
        with tempfile.TemporaryDirectory() as tmp:
            service = self._open(Path(tmp) / "service.db", quiescence_adapter=quiescence, replay_safety_adapter=replay)
            task, _, primary, fallback = self._setup(service)
            self._deliver_primary(service, primary)
            with self.assertRaises(RuntimeError):
                self._failover(service, primary, fallback, "partial-effects")
            decision = service.replay_safety_decisions.get_by_client_request("r12:replay:partial-effects")
            self.assertFalse(decision.safe)
            self.assertEqual(decision.classification, "PARTIAL_EFFECTS")
            self.assertEqual(service.execution_claims.get(task.id).owner_id, primary.id)
            with self.assertRaises(RuntimeError):
                service.delivery.deliver(primary.id)

    def test_replay_safety_exact_replay_does_not_reinvoke_adapter(self) -> None:
        quiescence = RecordingQuiescenceAdapter(quiescent=True)
        replay = RecordingReplaySafetyAdapter(safe=True, classification="COMPENSATED")
        with tempfile.TemporaryDirectory() as tmp:
            service = self._open(Path(tmp) / "service.db", quiescence_adapter=quiescence, replay_safety_adapter=replay)
            _, _, primary, fallback = self._setup(service)
            self._deliver_primary(service, primary)
            proof = service.quiescence.prove(
                client_quiescence_request_id="r12:q:replay-safe", binding_id=primary.id
            )
            first = service.replay_safety.evaluate(
                client_replay_safety_request_id="r12:r:replay-safe",
                from_binding_id=primary.id,
                to_binding_id=fallback.id,
                quiescence_proof_id=proof.id,
            )
            replay.safe = False
            replay.classification = "UNKNOWN"
            second = service.replay_safety.evaluate(
                client_replay_safety_request_id="r12:r:replay-safe",
                from_binding_id=primary.id,
                to_binding_id=fallback.id,
                quiescence_proof_id=proof.id,
            )
            self.assertEqual(first.id, second.id)
            self.assertTrue(second.safe)
            self.assertEqual(second.classification, "COMPENSATED")
            self.assertEqual(len(replay.calls), 1)

    def test_replay_safety_response_loss_does_not_transfer_until_exact_retry(self) -> None:
        quiescence = RecordingQuiescenceAdapter(quiescent=True)
        replay = RecordingReplaySafetyAdapter(safe=True, classification="ROLLED_BACK")
        replay.fail_after_commit_once = True
        with tempfile.TemporaryDirectory() as tmp:
            service = self._open(Path(tmp) / "service.db", quiescence_adapter=quiescence, replay_safety_adapter=replay)
            task, _, primary, fallback = self._setup(service)
            self._deliver_primary(service, primary)
            with self.assertRaises(RuntimeError):
                self._failover(service, primary, fallback, "lost-replay")
            self.assertEqual(service.execution_claims.get(task.id).owner_id, primary.id)
            transfer = self._failover(service, primary, fallback, "lost-replay")
            self.assertEqual(transfer.to_binding_id, fallback.id)
            self.assertEqual(replay.calls[0], replay.calls[1])

    def test_quiescence_and_replay_safety_allow_atomic_transfer_then_fallback_delivery(self) -> None:
        quiescence = RecordingQuiescenceAdapter(quiescent=True)
        replay = RecordingReplaySafetyAdapter(safe=True, classification="IDEMPOTENT_REPLAY")
        delivery = RecordingDelivery()
        with tempfile.TemporaryDirectory() as tmp:
            service = self._open(
                Path(tmp) / "service.db",
                delivery=delivery,
                quiescence_adapter=quiescence,
                replay_safety_adapter=replay,
            )
            task, _, primary, fallback = self._setup(service)
            self._deliver_primary(service, primary)
            transfer = self._failover(service, primary, fallback, "ok")
            self.assertEqual(service.execution_claims.get(task.id).owner_id, fallback.id)
            self.assertEqual(service.tasks.get(task.id).state, "RUNNING")
            self.assertEqual(transfer.from_binding_id, primary.id)
            self.assertEqual(transfer.to_binding_id, fallback.id)
            with self.assertRaises(RuntimeError):
                service.delivery.deliver(primary.id)
            receipt = service.delivery.deliver(fallback.id)
            self.assertEqual(receipt.binding_id, fallback.id)
            self.assertEqual(service.tasks.get(task.id).state, "RUNNING")

    def test_target_with_historical_delivery_or_observation_is_not_pristine(self) -> None:
        quiescence = RecordingQuiescenceAdapter(quiescent=True)
        replay = RecordingReplaySafetyAdapter()
        with tempfile.TemporaryDirectory() as tmp:
            service = self._open(Path(tmp) / "service.db", quiescence_adapter=quiescence, replay_safety_adapter=replay)
            task, envelope, primary, fallback = self._setup(service)
            self._deliver_primary(service, primary)
            service.delivery_receipts.create(
                fallback,
                DeliveryObservation(
                    admission="committed",
                    status="submitted",
                    provider_request_id="legacy:fallback",
                    remote_task_id="legacy:task",
                    remote_context_id=f"legacy:{envelope.id}",
                ),
            )
            with self.assertRaises(RuntimeError):
                self._failover(service, primary, fallback, "dirty-target")
            self.assertEqual(service.execution_claims.get(task.id).owner_id, primary.id)
            self.assertEqual(quiescence.calls, [])
            self.assertEqual(replay.calls, [])

    def test_cross_delegation_target_is_rejected_before_replay_safety_effect(self) -> None:
        quiescence = RecordingQuiescenceAdapter(quiescent=True)
        replay = RecordingReplaySafetyAdapter()
        with tempfile.TemporaryDirectory() as tmp:
            service = self._open(Path(tmp) / "service.db", quiescence_adapter=quiescence, replay_safety_adapter=replay)
            task, _, primary, _ = self._setup(service, "one")
            _, _, _, other_fallback = self._setup(service, "two")
            self._deliver_primary(service, primary)
            with self.assertRaises(ValueError):
                service.failover.failover(
                    client_failover_request_id="r12:failover:cross",
                    client_quiescence_request_id="r12:q:cross",
                    client_replay_safety_request_id="r12:r:cross",
                    from_binding_id=primary.id,
                    to_binding_id=other_fallback.id,
                )
            self.assertEqual(service.execution_claims.get(task.id).owner_id, primary.id)
            self.assertEqual(quiescence.calls, [])
            self.assertEqual(replay.calls, [])

    def test_empty_failover_identity_fails_before_any_external_effect(self) -> None:
        quiescence = RecordingQuiescenceAdapter(quiescent=True)
        replay = RecordingReplaySafetyAdapter()
        with tempfile.TemporaryDirectory() as tmp:
            service = self._open(Path(tmp) / "service.db", quiescence_adapter=quiescence, replay_safety_adapter=replay)
            _, _, primary, fallback = self._setup(service)
            self._deliver_primary(service, primary)
            with self.assertRaises(ValueError):
                service.failover.failover(
                    client_failover_request_id=" ",
                    client_quiescence_request_id="r12:q:should-not-run",
                    client_replay_safety_request_id="r12:r:should-not-run",
                    from_binding_id=primary.id,
                    to_binding_id=fallback.id,
                )
            self.assertEqual(quiescence.calls, [])
            self.assertEqual(replay.calls, [])

    def test_late_old_owner_success_cannot_steal_task_after_transfer_and_failover_replay_is_exact(self) -> None:
        quiescence = RecordingQuiescenceAdapter(quiescent=True)
        replay = RecordingReplaySafetyAdapter(safe=True, classification="NO_EFFECTS")
        with tempfile.TemporaryDirectory() as tmp:
            service = self._open(Path(tmp) / "service.db", quiescence_adapter=quiescence, replay_safety_adapter=replay)
            task, _, primary, fallback = self._setup(service)
            receipt = self._deliver_primary(service, primary)
            transfer = self._failover(service, primary, fallback, "replay-final")
            again = self._failover(service, primary, fallback, "replay-final")
            self.assertEqual(transfer.id, again.id)
            self.assertEqual(len(quiescence.calls), 1)
            self.assertEqual(len(replay.calls), 1)

            service.remote_observations.record(
                binding_id=primary.id,
                observation=RemoteProviderObservation(
                    provider_status="TASK_STATE_COMPLETED",
                    terminal=True,
                    successful=True,
                    remote_task_id=receipt.remote_task_id,
                    remote_context_id=receipt.remote_context_id,
                    artifact_refs=("artifact:late",),
                    evidence_ref="remote://r12/late-success",
                ),
            )
            with self.assertRaises(RuntimeError):
                service.remote_completion.reconcile(primary.id)
            self.assertEqual(service.tasks.get(task.id).state, "RUNNING")
            self.assertEqual(service.execution_claims.get(task.id).owner_id, fallback.id)


if __name__ == "__main__":
    unittest.main()
