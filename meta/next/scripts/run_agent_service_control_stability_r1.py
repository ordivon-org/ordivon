#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
import tempfile
import urllib.parse
from pathlib import Path
from typing import Any
from unittest.mock import patch

_REPO_ROOT = Path(__file__).resolve().parents[1]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from agent_service.failover import AgentServiceR12
from agent_service.provider_adapters import EffectLedgerReader
from agent_service.slice1 import AgentServiceSlice1, CarrierProviderAdapter, ProviderObservation
from agent_service.task_runtime import RuntimeAdapter, RuntimeJobObservation, RuntimeJobRef
from agent_service.transport_credentials import AgentServiceR14
from agent_service.trust import RemoteProviderObservation, _remote_delivery_observation_list_for_binding, _remote_delivery_observation_record

from tests.test_agent_service_failover_r12 import (
    AllowPolicy,
    NoopRuntimeArtifactReader,
    RecordingDelivery,
    RecordingQuiescenceAdapter,
    RecordingReplaySafetyAdapter,
)
from tests.test_agent_service_interface_credentials_r14 import MaterialProvider, ProofAdapter
from tests.test_agent_service_provider_adapters_r13 import DynamicNoEffectsReader


class ReadyCarrier(CarrierProviderAdapter):
    def ensure(self, placement_id: str, agent_instance_id: str, revision_id: str) -> None:
        return None

    def retire(self, placement_id: str, agent_instance_id: str) -> None:
        return None

    def observe(self, placement_id: str) -> ProviderObservation:
        return ProviderObservation(
            placement_id=placement_id,
            state="READY",
            evidence_ref="stability://ready",
        )


class SequenceCarrier(CarrierProviderAdapter):
    def __init__(self, observations: list[tuple[str, str]]) -> None:
        self._observations = list(observations)
        self.ensure_calls = 0
        self.retire_calls = 0
        self.observe_calls = 0

    def ensure(self, placement_id: str, agent_instance_id: str, revision_id: str) -> None:
        self.ensure_calls += 1

    def retire(self, placement_id: str, agent_instance_id: str) -> None:
        self.retire_calls += 1

    def observe(self, placement_id: str) -> ProviderObservation:
        self.observe_calls += 1
        if not self._observations:
            raise AssertionError("SequenceCarrier exhausted")
        state, evidence_ref = self._observations.pop(0)
        return ProviderObservation(
            placement_id=placement_id,
            state=state,
            evidence_ref=evidence_ref,
        )


class WorkingRuntime(RuntimeAdapter):
    def __init__(self) -> None:
        self.submit_calls: list[str] = []
        self.external_jobs: list[str] = []

    def submit(self, client_request_id: str, execution: dict[str, Any]) -> RuntimeJobRef:
        self.submit_calls.append(client_request_id)
        job_id = f"job:{client_request_id}"
        if job_id not in self.external_jobs:
            self.external_jobs.append(job_id)
        return RuntimeJobRef(job_id=job_id)

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


class ResponseLossRuntime(WorkingRuntime):
    def __init__(self, *, idempotent: bool) -> None:
        super().__init__()
        self.idempotent = idempotent
        self._failed_once = False
        self._committed_by_request: dict[str, str] = {}
        self._counter = 0

    def submit(self, client_request_id: str, execution: dict[str, Any]) -> RuntimeJobRef:
        self.submit_calls.append(client_request_id)
        if self.idempotent and client_request_id in self._committed_by_request:
            return RuntimeJobRef(job_id=self._committed_by_request[client_request_id])

        self._counter += 1
        job_id = f"job-loss-{self._counter}:{client_request_id}"
        self.external_jobs.append(job_id)
        if self.idempotent:
            self._committed_by_request[client_request_id] = job_id

        if not self._failed_once:
            self._failed_once = True
            raise TimeoutError("simulated response loss after external Runtime admission")
        return RuntimeJobRef(job_id=job_id)


def _open_r14(
    db: Path,
    *,
    runtime: RuntimeAdapter | None = None,
    carrier: CarrierProviderAdapter | None = None,
    delivery: RecordingDelivery | None = None,
    proof_adapter: ProofAdapter | None = None,
    material_provider: MaterialProvider | None = None,
) -> AgentServiceR14:
    delivery = delivery or RecordingDelivery()
    return AgentServiceR14.open(
        db,
        carrier_adapter=carrier or ReadyCarrier(),
        runtime_adapter=runtime or WorkingRuntime(),
        artifact_reader=NoopRuntimeArtifactReader(),
        delivery_adapters={"a2a-jsonrpc": delivery, "mcp": delivery},
        effect_ledger_reader=DynamicNoEffectsReader(),
        policy_adapter=AllowPolicy(),
        identity_proof_adapter=proof_adapter,
        credential_material_provider=material_provider,
    )


def _open_r12(
    db: Path,
    *,
    delivery: RecordingDelivery,
    quiescence: RecordingQuiescenceAdapter,
    replay: RecordingReplaySafetyAdapter,
) -> AgentServiceR12:
    return AgentServiceR12.open(
        db,
        carrier_adapter=ReadyCarrier(),
        runtime_adapter=WorkingRuntime(),
        artifact_reader=NoopRuntimeArtifactReader(),
        policy_adapter=AllowPolicy(),
        delivery_adapters={"a2a-jsonrpc": delivery, "mcp": delivery},
        remote_delivery_observers={},
        remote_artifact_readers={},
        execution_quiescence_adapters={
            "a2a-jsonrpc": quiescence,
            "mcp": quiescence,
        },
        replay_safety_adapter=replay,
    )


def _agent(
    service: Any,
    name: str,
    *,
    routes: list[dict[str, Any]] | None = None,
) -> tuple[Any, Any, Any]:
    definition = service.definitions.create(name)
    revision = service.revisions.create(
        definition.id,
        {
            "name": name,
            "stability": "r1",
            "skills": [
                {
                    "id": "review",
                    "name": "Review",
                    "description": "review",
                    "tags": ["review"],
                    "inputModes": ["text/plain"],
                    "outputModes": ["text/markdown"],
                }
            ],
            "routes": routes or [],
        },
    )
    identity = service.identities.create(
        definition.id,
        stable_name=name,
        description=name,
    )
    instance = service.birth.birth(f"birth:{name}:stability-r1", revision.id)
    service.reconciler.reconcile(instance.id)
    return revision, identity, instance


def _local_task(service: Any, revision_id: str, suffix: str) -> Any:
    return service.tasks.create(
        description=f"local-stability-{suffix}",
        required_revision_id=revision_id,
        execution={
            "workspaceId": "ws-stability",
            "executable": "/usr/bin/true",
            "args": [],
            "cwdRelative": ".",
            "env": {},
        },
        acceptance={"kind": "stdout_contains", "value": "OK"},
    )


def _remote_setup(
    service: Any,
    *,
    suffix: str,
    same_hostname: bool = False,
    security: dict[str, list[str]] | None = None,
) -> dict[str, Any]:
    source_revision, source_identity, source_instance = _agent(
        service, f"source-{suffix}"
    )
    if same_hostname:
        a2a_url = f"https://shared-provider.example.test/{suffix}/a2a"
        mcp_url = f"https://shared-provider.example.test/{suffix}/mcp"
    else:
        a2a_url = f"https://a2a.example.test/{suffix}"
        mcp_url = f"https://mcp.example.test/{suffix}"
    target_revision, target_identity, _ = _agent(
        service,
        f"target-{suffix}",
        routes=[
            {
                "transport": "a2a-jsonrpc",
                "protocolVersion": "1.0",
                "url": a2a_url,
                "priority": 10,
                "securityRequirements": security or {},
            },
            {
                "transport": "mcp",
                "protocolVersion": "2026-07-28",
                "url": mcp_url,
                "priority": 20,
                "securityRequirements": security or {},
            },
        ],
    )
    task = service.tasks.create(
        description=f"remote-stability-{suffix}",
        required_revision_id=source_revision.id,
        execution={
            "workspaceId": "ws-stability",
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
        client_session_id=f"stability:session:{suffix}",
        initiator_identity_id=source_identity.id,
    )
    envelope = service.delegations.create(
        client_delegation_id=f"stability:delegation:{suffix}",
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
    policy_request_id = f"stability:policy:{suffix}"
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
    policy_receipt = service.events.get(primary.policy_receipt_id)
    return {
        "sourceRevision": source_revision,
        "sourceIdentity": source_identity,
        "sourceInstance": source_instance,
        "targetRevision": target_revision,
        "targetIdentity": target_identity,
        "task": task,
        "envelope": envelope,
        "decision": policy_receipt,
        "primary": primary,
        "fallback": fallback,
    }


def _credential_bind(service: AgentServiceR14, source_identity: Any, binding: Any) -> tuple[Any, Any]:
    credential = service.credential_references.register(
        client_reference_id=f"stability:cred:{binding.id}",
        provider="vault",
        reference=f"vault://stability/{binding.id}",
        issuer="https://auth.example.test",
        resource="https://a2a.example.test",
        requested_scopes=["review.invoke"],
    )
    proof = service.identity_proofs.verify(
        client_proof_request_id=f"stability:proof:{binding.id}",
        identity_id=source_identity.id,
        credential_reference_id=credential.id,
        purpose="outbound-transport-auth",
    )
    service.transport_credentials.bind(
        client_binding_request_id=f"stability:tcred:{binding.id}",
        binding_id=binding.id,
        security_scheme="oauth2",
        identity_proof_id=proof.id,
    )
    return credential, proof


def _scenario_placement_flap() -> dict[str, Any]:
    carrier = SequenceCarrier(
        [
            ("READY", "obs://1-ready"),
            ("UNKNOWN", "obs://2-unknown"),
            ("READY", "obs://3-ready"),
            ("UNKNOWN", "obs://4-unknown"),
            ("READY", "obs://5-ready"),
        ]
    )
    with tempfile.TemporaryDirectory() as tmp:
        service = AgentServiceSlice1.open(
            Path(tmp) / "service.db",
            carrier_adapter=carrier,
        )
        try:
            definition = service.definitions.create("flap-agent")
            revision = service.revisions.create(definition.id, {"name": "flap-agent"})
            instance = service.birth.birth("birth:flap:r1", revision.id)
            states: list[str] = []
            for _ in range(5):
                states.append(service.reconciler.reconcile(instance.id).state)
            events = [
                event.event_type
                for event in service.events.list_for("AgentInstance", instance.id)
            ]
            return {
                "classification": "OSCILLATION_EXPOSED",
                "instanceStates": states,
                "ensureCalls": carrier.ensure_calls,
                "events": events,
                "hysteresisPresent": False,
                "interpretation": (
                    "Every observed READY/UNKNOWN edge is propagated immediately into AgentInstance readiness; "
                    "there is no dwell/hysteresis layer in the placement loop."
                ),
            }
        finally:
            service.close()


def _scenario_stale_placement_observation() -> dict[str, Any]:
    carrier = SequenceCarrier(
        [
            ("READY", "fresh://ready-t1"),
            ("UNKNOWN", "fresh://unknown-t2"),
            ("READY", "stale://ready-t0-arrived-late"),
        ]
    )
    with tempfile.TemporaryDirectory() as tmp:
        service = AgentServiceSlice1.open(
            Path(tmp) / "service.db",
            carrier_adapter=carrier,
        )
        try:
            definition = service.definitions.create("stale-agent")
            revision = service.revisions.create(definition.id, {"name": "stale-agent"})
            instance = service.birth.birth("birth:stale:r1", revision.id)
            service.reconciler.reconcile(instance.id)
            after_unknown = service.reconciler.reconcile(instance.id).state
            after_stale = service.reconciler.reconcile(instance.id).state
            observation_fields = set(ProviderObservation.__dataclass_fields__)
            return {
                "classification": "STALE_OBSERVATION_EXPOSED",
                "stateAfterFreshUnknown": after_unknown,
                "stateAfterLateStaleReady": after_stale,
                "observationCarriesFreshness": bool(
                    {"observed_at_ms", "sequence", "generation"} & observation_fields
                ),
                "interpretation": (
                    "ProviderObservation contains no freshness/order coordinate, so a late stale READY fact "
                    "is observationally indistinguishable from a fresh recovery."
                ),
            }
        finally:
            service.close()


def _scenario_runtime_response_loss(*, idempotent: bool) -> dict[str, Any]:
    runtime = ResponseLossRuntime(idempotent=idempotent)
    with tempfile.TemporaryDirectory() as tmp:
        service = _open_r14(Path(tmp) / "service.db", runtime=runtime)
        try:
            revision, _, _ = _agent(service, f"runtime-{idempotent}")
            task = _local_task(service, revision.id, f"runtime-{idempotent}")
            assignment = service.planner.plan(task.id)
            first_failed = False
            try:
                service.execution_activator.activate(assignment.id)
            except TimeoutError:
                first_failed = True
            activated = service.execution_activator.activate(assignment.id)
            if not first_failed:
                raise AssertionError("response-loss perturbation did not fire")
            result = {
                "submitCalls": len(runtime.submit_calls),
                "sameClientRequestIdentity": len(set(runtime.submit_calls)) == 1,
                "externalJobCount": len(runtime.external_jobs),
                "boundMatchesFirstExternalJob": (
                    bool(runtime.external_jobs)
                    and activated.runtime_job_id == runtime.external_jobs[0]
                ),
                "taskState": service.tasks.get(task.id).state,
            }
            if idempotent:
                result["classification"] = "CONVERGES"
            else:
                result["classification"] = "CONTRACT_DEPENDENCY_EXPOSED"
                result["orphanExternalJobPresent"] = (
                    len(runtime.external_jobs) == 2
                    and activated.runtime_job_id == runtime.external_jobs[1]
                    and runtime.external_jobs[0] != runtime.external_jobs[1]
                )
                result["interpretation"] = (
                    "Agent Service reuses the exact Runtime clientRequestId, but if the Runtime adapter violates "
                    "that replay contract after response loss, the first external Job is not locally observable."
                )
            return result
        finally:
            service.close()


def _scenario_credential_expiry() -> dict[str, Any]:
    proof_adapter = ProofAdapter()
    material_provider = MaterialProvider(secret="stability-secret")
    with tempfile.TemporaryDirectory() as tmp:
        service = _open_r14(
            Path(tmp) / "service.db",
            proof_adapter=proof_adapter,
            material_provider=material_provider,
        )
        try:
            setup = _remote_setup(
                service,
                suffix="credential-expiry",
                security={"oauth2": ["review.invoke"]},
            )
            binding = setup["primary"]
            _, proof = _credential_bind(
                service,
                setup["sourceIdentity"],
                binding,
            )
            first = service.credential_headers(binding)
            blocked = False
            after_expiry_ms = (
                proof.expires_at_ms + 1
                if proof.expires_at_ms is not None
                else 10_000_000_000_000
            )
            with patch("agent_service.trust._now_ms", return_value=after_expiry_ms):
                try:
                    service.credential_headers(binding)
                except PermissionError:
                    blocked = True
            return {
                "classification": "FAIL_CLOSED",
                "firstHeaderResolved": first.get("Authorization") == "Bearer stability-secret",
                "secondCallBlocked": blocked,
                "materialProviderCalls": material_provider.calls,
                "interpretation": (
                    "Credential material is re-admitted per call; once the durable proof is no longer current, "
                    "the external secret provider is not invoked again."
                ),
            }
        finally:
            service.close()


def _scenario_single_owner_blocks_remote_overlap() -> dict[str, Any]:
    delivery = RecordingDelivery()
    with tempfile.TemporaryDirectory() as tmp:
        service = _open_r14(
            Path(tmp) / "service.db",
            delivery=delivery,
        )
        try:
            setup = _remote_setup(service, suffix="owner-overlap")
            task = setup["task"]
            assignment = service.planner.plan(task.id)
            claim = service.execution_claims.get(task.id)
            blocked = False
            try:
                service.delivery.deliver(setup["primary"].id)
            except RuntimeError:
                blocked = True
            return {
                "classification": "FAIL_CLOSED",
                "claimMode": claim.mode,
                "claimOwnerMatchesAssignment": claim.owner_id == assignment.id,
                "remoteDeliveryBlocked": blocked,
                "deliveryCalls": len(delivery.calls),
                "interpretation": (
                    "A local Assignment and remote Binding cannot concurrently own the same Task; "
                    "the remote provider effect is blocked before DeliveryAdapter.send."
                ),
            }
        finally:
            service.close()


def _scenario_failover_exact_replay(*, same_hostname: bool = False) -> dict[str, Any]:
    delivery = RecordingDelivery()
    quiescence = RecordingQuiescenceAdapter(quiescent=True)
    replay = RecordingReplaySafetyAdapter(
        safe=True,
        classification="NO_EFFECTS",
    )
    with tempfile.TemporaryDirectory() as tmp:
        service = _open_r12(
            Path(tmp) / "service.db",
            delivery=delivery,
            quiescence=quiescence,
            replay=replay,
        )
        try:
            setup = _remote_setup(
                service,
                suffix="shared-domain" if same_hostname else "exact-replay",
                same_hostname=same_hostname,
            )
            task = setup["task"]
            primary = setup["primary"]
            fallback = setup["fallback"]
            service.delivery.deliver(primary.id)
            first = service.failover.failover(
                client_failover_request_id="stability:failover:shared" if same_hostname else "stability:failover:replay",
                client_quiescence_request_id="stability:q:shared" if same_hostname else "stability:q:replay",
                client_replay_safety_request_id="stability:r:shared" if same_hostname else "stability:r:replay",
                from_binding_id=primary.id,
                to_binding_id=fallback.id,
            )
            second = service.failover.failover(
                client_failover_request_id="stability:failover:shared" if same_hostname else "stability:failover:replay",
                client_quiescence_request_id="stability:q:shared" if same_hostname else "stability:q:replay",
                client_replay_safety_request_id="stability:r:shared" if same_hostname else "stability:r:replay",
                from_binding_id=primary.id,
                to_binding_id=fallback.id,
            )
            if same_hostname:
                source_host = urllib.parse.urlparse(primary.endpoint).hostname
                target_host = urllib.parse.urlparse(fallback.endpoint).hostname
                fields = set(primary.__dataclass_fields__)
                return {
                    "classification": "FAILURE_DOMAIN_UNMODELED_EXPOSED",
                    "sameHostname": source_host == target_host,
                    "sourceHostname": source_host,
                    "targetHostname": target_host,
                    "transferAdmitted": first.to_binding_id == fallback.id,
                    "failureDomainModeled": any(
                        name in fields
                        for name in ("failure_domain_id", "failure_domain", "failure_domains")
                    ),
                    "claimTransferredToFallback": (
                        service.execution_claims.get(task.id).owner_id == fallback.id
                    ),
                    "interpretation": (
                        "R12 proves source quiescence and replay safety, but current Binding identity carries no "
                        "failure-domain coordinate; two transports on the same provider hostname are accepted as fallback."
                    ),
                }
            return {
                "classification": "CONVERGES",
                "sameTransferId": first.id == second.id,
                "quiescenceCalls": len(quiescence.calls),
                "replaySafetyCalls": len(replay.calls),
                "claimTransferredToFallback": (
                    service.execution_claims.get(task.id).owner_id == fallback.id
                ),
                "interpretation": (
                    "Exact failover replay returns the durable transfer and does not re-invoke quiescence or replay-safety effects."
                ),
            }
        finally:
            service.close()


def _scenario_remote_success_then_failure() -> dict[str, Any]:
    delivery = RecordingDelivery()
    quiescence = RecordingQuiescenceAdapter(quiescent=True)
    replay = RecordingReplaySafetyAdapter(safe=True, classification="NO_EFFECTS")
    with tempfile.TemporaryDirectory() as tmp:
        service = _open_r12(
            Path(tmp) / "service.db",
            delivery=delivery,
            quiescence=quiescence,
            replay=replay,
        )
        try:
            setup = _remote_setup(service, suffix="regression")
            primary = setup["primary"]
            fallback = setup["fallback"]
            receipt = service.delivery.deliver(primary.id)
            _remote_delivery_observation_record(
                service.events,
                binding_id=primary.id,
                observation=RemoteProviderObservation(
                    provider_status="TASK_STATE_COMPLETED",
                    terminal=True,
                    successful=True,
                    remote_task_id=receipt.remote_task_id,
                    remote_context_id=receipt.remote_context_id,
                    artifact_refs=("artifact:completed",),
                    evidence_ref="stability://completed",
                ),
            )
            _remote_delivery_observation_record(
                service.events,
                binding_id=primary.id,
                observation=RemoteProviderObservation(
                    provider_status="TASK_STATE_FAILED",
                    terminal=True,
                    successful=False,
                    remote_task_id=receipt.remote_task_id,
                    remote_context_id=receipt.remote_context_id,
                    artifact_refs=(),
                    evidence_ref="stability://regressed-failed",
                ),
            )
            blocked = False
            try:
                service.failover.failover(
                    client_failover_request_id="stability:failover:regression",
                    client_quiescence_request_id="stability:q:regression",
                    client_replay_safety_request_id="stability:r:regression",
                    from_binding_id=primary.id,
                    to_binding_id=fallback.id,
                )
            except RuntimeError:
                blocked = True
            history = _remote_delivery_observation_list_for_binding(service.events, primary.id)
            return {
                "classification": "FAIL_CLOSED",
                "historicalSuccessPresent": any(x.terminal and x.successful is True for x in history),
                "failoverBlocked": blocked,
                "quiescenceCalls": len(quiescence.calls),
                "replaySafetyCalls": len(replay.calls),
                "interpretation": (
                    "A later provider regression cannot erase historical terminal success; "
                    "failover is rejected before cancel/replay-safety actuation."
                ),
            }
        finally:
            service.close()


def run_experiments() -> dict[str, Any]:
    scenarios = {
        "S1_PLACEMENT_FLAP": _scenario_placement_flap(),
        "S2_STALE_PLACEMENT_OBSERVATION": _scenario_stale_placement_observation(),
        "S3_RUNTIME_RESPONSE_LOSS_IDEMPOTENT": _scenario_runtime_response_loss(idempotent=True),
        "S4_RUNTIME_RESPONSE_LOSS_NONIDEMPOTENT": _scenario_runtime_response_loss(idempotent=False),
        "S5_CREDENTIAL_EXPIRES_BETWEEN_CALLS": _scenario_credential_expiry(),
        "S6_SINGLE_OWNER_BLOCKS_REMOTE_OVERLAP": _scenario_single_owner_blocks_remote_overlap(),
        "S7_FAILOVER_EXACT_REPLAY": _scenario_failover_exact_replay(same_hostname=False),
        "S8_SHARED_FAILURE_DOMAIN_FALLBACK": _scenario_failover_exact_replay(same_hostname=True),
        "S9_REMOTE_SUCCESS_THEN_FAILURE": _scenario_remote_success_then_failure(),
    }
    counts: dict[str, int] = {}
    for value in scenarios.values():
        classification = value["classification"]
        counts[classification] = counts.get(classification, 0) + 1
    return {
        "schemaVersion": 1,
        "kind": "ordivon.agent-service-control-stability-r1-experiment",
        "analyzedImplementationCommit": "0721009237365ea61cd975bd187be5171f1dcd52",
        "scenarioCount": len(scenarios),
        "classificationCounts": dict(sorted(counts.items())),
        "scenarios": scenarios,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--write", type=Path)
    args = parser.parse_args()
    payload = json.dumps(
        run_experiments(),
        indent=2,
        sort_keys=True,
        ensure_ascii=False,
    ) + "\n"
    if args.write is not None:
        args.write.parent.mkdir(parents=True, exist_ok=True)
        args.write.write_text(payload)
    else:
        print(payload, end="")


if __name__ == "__main__":
    main()
