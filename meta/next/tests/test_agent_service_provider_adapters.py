from __future__ import annotations

from tests.agent_service_test_support import open_current

import tempfile
import unittest

from agent_service import open_agent_service
from pathlib import Path

from agent_service.delivery import DeliveryObservation, PolicyObservation
from agent_service.evidence import RuntimeArtifactPayload
from agent_service.failover import _replay_safety_decision_get
from agent_service.provider_adapters import A2AQuiescenceAdapter, EffectLedgerEffect, EffectLedgerReplaySafetyAdapter, EffectLedgerSnapshot, MCPTaskQuiescenceAdapter, ProviderProtocolError, ProviderRemoteError, QuiescencePending, RemoteExecutionCompleted
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


class NoopArtifactReader:
    def read(self, job_id: str, artifact_id: str) -> RuntimeArtifactPayload:
        raise AssertionError("not used")


class AllowPolicy:
    def evaluate(self, request):
        return PolicyObservation(
            allowed=True,
            reason=None,
            policy_revision="r13",
            granted_permissions=("review.invoke",),
        )


class Delivery:
    def send(self, *, delivery_request_id, binding, envelope):
        return DeliveryObservation(
            admission="committed",
            status="submitted",
            provider_request_id=f"provider:{delivery_request_id}",
            remote_task_id="remote-task-1",
            remote_context_id="remote-context-1",
        )


class SequenceCaller:
    def __init__(self, responses):
        self.responses = list(responses)
        self.calls = []

    def __call__(self, *, binding, method, params, request_identity):
        self.calls.append((binding.transport, binding.endpoint, method, params, request_identity))
        if not self.responses:
            raise AssertionError("unexpected provider call")
        value = self.responses.pop(0)
        if isinstance(value, BaseException):
            raise value
        return value


class LedgerReader:
    def __init__(self, snapshot: EffectLedgerSnapshot):
        self.snapshot = snapshot
        self.calls = []

    def read_replay_snapshot(
        self,
        *,
        task,
        envelope,
        source_binding,
        target_binding,
        quiescence_proof,
        source_receipt,
        source_observations,
    ):
        self.calls.append((task.id, source_binding.id, target_binding.id, quiescence_proof.id))
        return self.snapshot




class FakeHttpResponse:
    def __init__(self, payload, status=200):
        import json
        self.status = status
        self._body = json.dumps(payload).encode("utf-8")
        self.headers = {"Content-Type": "application/json"}

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def read(self):
        return self._body


class DynamicNoEffectsReader:
    def __init__(self):
        self.calls = []

    def read_replay_snapshot(
        self,
        *,
        task,
        envelope,
        source_binding,
        target_binding,
        quiescence_proof,
        source_receipt,
        source_observations,
    ):
        self.calls.append((task.id, source_binding.id, target_binding.id))
        return EffectLedgerSnapshot(
            task_id=task.id,
            source_binding_id=source_binding.id,
            target_binding_id=target_binding.id,
            complete=True,
            effects=(),
            evidence_ref=f"ledger://{task.id}/complete",
        )


class AgentServiceProviderAdaptersTests(unittest.TestCase):
    def _service(self, db: Path, *, q_adapter=None, replay_adapter=None):
        service = open_current(
            db,
            carrier_adapter=ReadyCarrier(),
            runtime_adapter=FakeRuntime(),
            artifact_reader=NoopArtifactReader(),
            policy_adapter=AllowPolicy(),
            delivery_adapters={"a2a-jsonrpc": Delivery(), "mcp": Delivery()},
            remote_delivery_observers={},
            remote_artifact_readers={},
            execution_quiescence_adapters={} if q_adapter is None else q_adapter,
            replay_safety_adapter=replay_adapter,
        )
        self.addCleanup(service.close)
        return service

    def _agent(self, service, name, *, routes=None):
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
        identity = service.identities.create(definition.id, stable_name=name, description=name)
        instance = service.instances.create(f"request:{name}:r13", revision.id)
        service.reconciler.reconcile(instance.id)
        return revision, identity, instance

    def _bindings(self, service):
        sr, si, inst = self._agent(service, "source")
        tr, ti, _ = self._agent(
            service,
            "target",
            routes=[
                {
                    "transport": "a2a-jsonrpc",
                    "protocolVersion": "1.0",
                    "url": "https://a2a.example.test/rpc",
                    "priority": 10,
                    "securityRequirements": {},
                },
                {
                    "transport": "mcp",
                    "protocolVersion": "2026-07-28",
                    "url": "https://mcp.example.test/mcp",
                    "priority": 20,
                    "securityRequirements": {},
                },
            ],
        )
        task = service.tasks.create(
            description="r13",
            required_revision_id=sr.id,
            execution={"workspaceId":"x","executable":"/usr/bin/true","args":[],"cwdRelative":".","env":{}},
            acceptance={"kind":"runtime_artifact_text_contains","artifactKind":"review-markdown","value":"ACCEPTED"},
        )
        session = service.sessions.open(client_session_id="r13:session", initiator_identity_id=si.id)
        envelope = service.delegations.create(
            client_delegation_id="r13:delegation",
            session_id=session.id,
            source_identity_id=si.id,
            source_instance_id=inst.id,
            target_identity_id=ti.id,
            target_revision_id=tr.id,
            task_id=task.id,
            capability_key="review",
            payload={"text":"review"},
            evidence_contract={"kind":"review-markdown"},
        )
        a2a = service.routes.plan(
            envelope.id,
            client_policy_request_id="r13:policy",
            preferred_transports=["a2a-jsonrpc"],
        )
        mcp = service.routes.plan(
            envelope.id,
            client_policy_request_id="r13:policy",
            preferred_transports=["mcp"],
        )
        return task, envelope, a2a, mcp

    def _receipt_and_context(self, service, binding):
        receipt = service.delivery.deliver(binding.id)
        envelope = service.delegations.get(binding.delegation_id)
        return receipt, envelope

    def test_a2a_cancelled_is_quiescent_and_uses_pascalcase_methods(self):
        caller = SequenceCaller([
            {"id":"remote-task-1","contextId":"remote-context-1","status":{"state":"TASK_STATE_CANCELED"}}
        ])
        adapter = A2AQuiescenceAdapter(caller)
        with tempfile.TemporaryDirectory() as tmp:
            service = self._service(Path(tmp)/"s.db")
            _, _, a2a, _ = self._bindings(service)
            receipt, envelope = self._receipt_and_context(service, a2a)
            obs = adapter.prove_quiescence(
                quiescence_request_id="q-a2a-cancelled",
                binding=a2a,
                receipt=receipt,
                envelope=envelope,
                latest_observation=None,
            )
        self.assertTrue(obs.quiescent)
        self.assertEqual(obs.provider_status, "TASK_STATE_CANCELED")
        self.assertEqual(caller.calls[0][2], "CancelTask")
        self.assertEqual(caller.calls[0][3], {"id":"remote-task-1"})

    def test_a2a_nonterminal_cancel_result_polls_gettask_then_pending(self):
        caller = SequenceCaller([
            {"id":"remote-task-1","contextId":"remote-context-1","status":{"state":"TASK_STATE_WORKING"}},
            {"id":"remote-task-1","contextId":"remote-context-1","status":{"state":"TASK_STATE_WORKING"}},
        ])
        adapter = A2AQuiescenceAdapter(caller)
        with tempfile.TemporaryDirectory() as tmp:
            service = self._service(Path(tmp)/"s.db")
            _, _, a2a, _ = self._bindings(service)
            receipt, envelope = self._receipt_and_context(service, a2a)
            with self.assertRaises(QuiescencePending):
                adapter.prove_quiescence(
                    quiescence_request_id="q-a2a-pending",
                    binding=a2a,
                    receipt=receipt,
                    envelope=envelope,
                    latest_observation=None,
                )
        self.assertEqual([x[2] for x in caller.calls], ["CancelTask", "GetTask"])

    def test_a2a_task_not_cancelable_reconciles_with_gettask(self):
        caller = SequenceCaller([
            ProviderRemoteError("CancelTask", {"code":-32002,"message":"not cancelable"}),
            {"id":"remote-task-1","contextId":"remote-context-1","status":{"state":"TASK_STATE_FAILED"}},
        ])
        adapter = A2AQuiescenceAdapter(caller)
        with tempfile.TemporaryDirectory() as tmp:
            service = self._service(Path(tmp)/"s.db")
            _, _, a2a, _ = self._bindings(service)
            receipt, envelope = self._receipt_and_context(service, a2a)
            obs = adapter.prove_quiescence(
                quiescence_request_id="q-a2a-not-cancelable",
                binding=a2a,
                receipt=receipt,
                envelope=envelope,
                latest_observation=None,
            )
        self.assertTrue(obs.quiescent)
        self.assertEqual(obs.provider_status, "TASK_STATE_FAILED")
        self.assertEqual([x[2] for x in caller.calls], ["CancelTask", "GetTask"])

    def test_a2a_completed_routes_to_verification_not_failover(self):
        caller = SequenceCaller([
            {"id":"remote-task-1","contextId":"remote-context-1","status":{"state":"TASK_STATE_COMPLETED"}}
        ])
        adapter = A2AQuiescenceAdapter(caller)
        with tempfile.TemporaryDirectory() as tmp:
            service = self._service(Path(tmp)/"s.db")
            _, _, a2a, _ = self._bindings(service)
            receipt, envelope = self._receipt_and_context(service, a2a)
            with self.assertRaises(RemoteExecutionCompleted):
                adapter.prove_quiescence(
                    quiescence_request_id="q-a2a-done",
                    binding=a2a,
                    receipt=receipt,
                    envelope=envelope,
                    latest_observation=None,
                )

    def test_a2a_task_or_context_mismatch_fails_closed(self):
        caller = SequenceCaller([
            {"id":"wrong","contextId":"remote-context-1","status":{"state":"TASK_STATE_CANCELED"}}
        ])
        adapter = A2AQuiescenceAdapter(caller)
        with tempfile.TemporaryDirectory() as tmp:
            service = self._service(Path(tmp)/"s.db")
            _, _, a2a, _ = self._bindings(service)
            receipt, envelope = self._receipt_and_context(service, a2a)
            with self.assertRaises(ProviderProtocolError):
                adapter.prove_quiescence(
                    quiescence_request_id="q-a2a-mismatch",
                    binding=a2a,
                    receipt=receipt,
                    envelope=envelope,
                    latest_observation=None,
                )

    def test_mcp_cancel_ack_is_not_proof_and_cancelled_get_is_quiescent(self):
        caller = SequenceCaller([
            {"resultType":"complete"},
            {"resultType":"complete","taskId":"remote-task-1","status":"cancelled","ttlMs":1000},
        ])
        adapter = MCPTaskQuiescenceAdapter(caller)
        with tempfile.TemporaryDirectory() as tmp:
            service = self._service(Path(tmp)/"s.db")
            _, _, _, mcp = self._bindings(service)
            receipt, envelope = self._receipt_and_context(service, mcp)
            obs = adapter.prove_quiescence(
                quiescence_request_id="q-mcp-cancelled",
                binding=mcp,
                receipt=receipt,
                envelope=envelope,
                latest_observation=None,
            )
        self.assertTrue(obs.quiescent)
        self.assertEqual(obs.provider_status, "cancelled")
        self.assertEqual([x[2] for x in caller.calls], ["tasks/cancel", "tasks/get"])

    def test_mcp_working_after_cancel_ack_is_pending(self):
        caller = SequenceCaller([
            {"resultType":"complete"},
            {"resultType":"complete","taskId":"remote-task-1","status":"working","ttlMs":1000},
        ])
        adapter = MCPTaskQuiescenceAdapter(caller)
        with tempfile.TemporaryDirectory() as tmp:
            service = self._service(Path(tmp)/"s.db")
            _, _, _, mcp = self._bindings(service)
            receipt, envelope = self._receipt_and_context(service, mcp)
            with self.assertRaises(QuiescencePending):
                adapter.prove_quiescence(
                    quiescence_request_id="q-mcp-working",
                    binding=mcp,
                    receipt=receipt,
                    envelope=envelope,
                    latest_observation=None,
                )

    def test_mcp_completed_routes_to_verification(self):
        caller = SequenceCaller([
            {"resultType":"complete"},
            {"resultType":"complete","taskId":"remote-task-1","status":"completed","ttlMs":1000,"result":{}},
        ])
        adapter = MCPTaskQuiescenceAdapter(caller)
        with tempfile.TemporaryDirectory() as tmp:
            service = self._service(Path(tmp)/"s.db")
            _, _, _, mcp = self._bindings(service)
            receipt, envelope = self._receipt_and_context(service, mcp)
            with self.assertRaises(RemoteExecutionCompleted):
                adapter.prove_quiescence(
                    quiescence_request_id="q-mcp-completed",
                    binding=mcp,
                    receipt=receipt,
                    envelope=envelope,
                    latest_observation=None,
                )

    def test_mcp_failed_is_quiescent_but_not_semantic_success(self):
        caller = SequenceCaller([
            {"resultType":"complete"},
            {"resultType":"complete","taskId":"remote-task-1","status":"failed","ttlMs":1000,"error":{"code":-32603}},
        ])
        adapter = MCPTaskQuiescenceAdapter(caller)
        with tempfile.TemporaryDirectory() as tmp:
            service = self._service(Path(tmp)/"s.db")
            _, _, _, mcp = self._bindings(service)
            receipt, envelope = self._receipt_and_context(service, mcp)
            obs = adapter.prove_quiescence(
                quiescence_request_id="q-mcp-failed",
                binding=mcp,
                receipt=receipt,
                envelope=envelope,
                latest_observation=None,
            )
        self.assertTrue(obs.quiescent)
        self.assertEqual(obs.provider_status, "failed")

    def test_mcp_task_identity_mismatch_fails_closed(self):
        caller = SequenceCaller([
            {"resultType":"complete"},
            {"resultType":"complete","taskId":"wrong","status":"cancelled","ttlMs":1000},
        ])
        adapter = MCPTaskQuiescenceAdapter(caller)
        with tempfile.TemporaryDirectory() as tmp:
            service = self._service(Path(tmp)/"s.db")
            _, _, _, mcp = self._bindings(service)
            receipt, envelope = self._receipt_and_context(service, mcp)
            with self.assertRaises(ProviderProtocolError):
                adapter.prove_quiescence(
                    quiescence_request_id="q-mcp-mismatch",
                    binding=mcp,
                    receipt=receipt,
                    envelope=envelope,
                    latest_observation=None,
                )

    def test_effect_ledger_complete_empty_snapshot_is_no_effects(self):
        snapshot = EffectLedgerSnapshot(
            task_id="task-x",
            source_binding_id="source-x",
            target_binding_id="target-x",
            complete=True,
            effects=(),
            evidence_ref="ledger://empty",
        )
        adapter = EffectLedgerReplaySafetyAdapter(LedgerReader(snapshot))
        obs = adapter._evaluate_snapshot(snapshot, expected_task_id="task-x", expected_source_binding_id="source-x", expected_target_binding_id="target-x")
        self.assertTrue(obs.safe)
        self.assertEqual(obs.classification, "NO_EFFECTS")

    def test_effect_ledger_incomplete_snapshot_is_unknown(self):
        snapshot = EffectLedgerSnapshot(
            task_id="task-x",
            source_binding_id="source-x",
            target_binding_id="target-x",
            complete=False,
            effects=(),
            evidence_ref="ledger://incomplete",
        )
        obs = EffectLedgerReplaySafetyAdapter(LedgerReader(snapshot))._evaluate_snapshot(
            snapshot,
            expected_task_id="task-x",
            expected_source_binding_id="source-x",
            expected_target_binding_id="target-x",
        )
        self.assertFalse(obs.safe)
        self.assertEqual(obs.classification, "UNKNOWN")

    def test_effect_ledger_all_rolled_back_is_replay_safe(self):
        snapshot = EffectLedgerSnapshot(
            task_id="task-x",
            source_binding_id="source-x",
            target_binding_id="target-x",
            complete=True,
            effects=(
                EffectLedgerEffect("e1","ROLLED_BACK",None,None,"effect://e1"),
                EffectLedgerEffect("e2","ROLLED_BACK",None,None,"effect://e2"),
            ),
            evidence_ref="ledger://rolled-back",
        )
        obs = EffectLedgerReplaySafetyAdapter(LedgerReader(snapshot))._evaluate_snapshot(
            snapshot,
            expected_task_id="task-x",
            expected_source_binding_id="source-x",
            expected_target_binding_id="target-x",
        )
        self.assertTrue(obs.safe)
        self.assertEqual(obs.classification, "ROLLED_BACK")

    def test_effect_ledger_compensated_effects_are_replay_safe(self):
        snapshot = EffectLedgerSnapshot(
            task_id="task-x",
            source_binding_id="source-x",
            target_binding_id="target-x",
            complete=True,
            effects=(
                EffectLedgerEffect("e1","COMPENSATED",None,None,"effect://e1"),
                EffectLedgerEffect("e2","ROLLED_BACK",None,None,"effect://e2"),
            ),
            evidence_ref="ledger://compensated",
        )
        obs = EffectLedgerReplaySafetyAdapter(LedgerReader(snapshot))._evaluate_snapshot(
            snapshot,
            expected_task_id="task-x",
            expected_source_binding_id="source-x",
            expected_target_binding_id="target-x",
        )
        self.assertTrue(obs.safe)
        self.assertEqual(obs.classification, "COMPENSATED")

    def test_effect_ledger_committed_effect_requires_target_bound_idempotency(self):
        safe = EffectLedgerSnapshot(
            task_id="task-x",
            source_binding_id="source-x",
            target_binding_id="target-x",
            complete=True,
            effects=(EffectLedgerEffect("e1","COMMITTED","idem-1","target-x","effect://e1"),),
            evidence_ref="ledger://idem",
        )
        unsafe = EffectLedgerSnapshot(
            task_id="task-x",
            source_binding_id="source-x",
            target_binding_id="target-x",
            complete=True,
            effects=(EffectLedgerEffect("e1","COMMITTED","idem-1","other-target","effect://e1"),),
            evidence_ref="ledger://wrong-target",
        )
        adapter = EffectLedgerReplaySafetyAdapter(LedgerReader(safe))
        yes = adapter._evaluate_snapshot(safe, expected_task_id="task-x", expected_source_binding_id="source-x", expected_target_binding_id="target-x")
        no = adapter._evaluate_snapshot(unsafe, expected_task_id="task-x", expected_source_binding_id="source-x", expected_target_binding_id="target-x")
        self.assertTrue(yes.safe)
        self.assertEqual(yes.classification, "IDEMPOTENT_REPLAY")
        self.assertFalse(no.safe)
        self.assertEqual(no.classification, "PARTIAL_EFFECTS")

    def test_effect_ledger_identity_mismatch_fails_closed(self):
        snapshot = EffectLedgerSnapshot(
            task_id="wrong",
            source_binding_id="source-x",
            target_binding_id="target-x",
            complete=True,
            effects=(),
            evidence_ref="ledger://wrong",
        )
        with self.assertRaises(ProviderProtocolError):
            EffectLedgerReplaySafetyAdapter(LedgerReader(snapshot))._evaluate_snapshot(
                snapshot,
                expected_task_id="task-x",
                expected_source_binding_id="source-x",
                expected_target_binding_id="target-x",
            )


    def test_agent_service_r13_wires_a2a_quiescence_and_effect_ledger_into_r12_failover(self):
        a2a_caller = SequenceCaller([
            {"id":"remote-task-1","contextId":"remote-context-1","status":{"state":"TASK_STATE_CANCELED"}},
        ])
        mcp_caller = SequenceCaller([])
        ledger = DynamicNoEffectsReader()
        with tempfile.TemporaryDirectory() as tmp:
            service = open_agent_service(
                Path(tmp)/"s.db",
                carrier_adapter=ReadyCarrier(),
                runtime_adapter=FakeRuntime(),
                artifact_reader=NoopArtifactReader(),
                policy_adapter=AllowPolicy(),
                delivery_adapters={"a2a-jsonrpc":Delivery(),"mcp":Delivery()},
                a2a_caller=a2a_caller,
                mcp_tasks_caller=mcp_caller,
                effect_ledger_reader=ledger,
            )
            self.addCleanup(service.close)
            task, _, a2a, mcp = self._bindings(service)
            service.delivery.deliver(a2a.id)
            transfer = service.failover.failover(
                client_failover_request_id="r13:failover",
                client_quiescence_request_id="r13:q",
                client_replay_safety_request_id="r13:replay",
                from_binding_id=a2a.id,
                to_binding_id=mcp.id,
            )
            self.assertEqual(service.execution_claims.get(task.id).owner_id, mcp.id)
            self.assertEqual(_replay_safety_decision_get(service.events, transfer.replay_safety_decision_id).classification, "NO_EFFECTS")
            receipt = service.delivery.deliver(mcp.id)
            self.assertEqual(receipt.binding_id, mcp.id)
            self.assertEqual(service.tasks.get(task.id).state, "RUNNING")
        self.assertEqual(a2a_caller.calls[0][2], "CancelTask")
        self.assertEqual(len(ledger.calls), 1)


if __name__ == "__main__":
    unittest.main()
