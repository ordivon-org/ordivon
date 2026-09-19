from __future__ import annotations

import hashlib
import json
import sqlite3
import time
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .delivery import (
    DeliveryObservation,
    TransportBinding,
    TransportBindingStore,
    _delivery_receipt_create,
    _delivery_receipt_get_by_binding,
)
from .evidence import (
    ArtifactDigestMismatch,
    EvidenceBundle,
    _verify_evidence_semantics,
)
from .goals import GoalAssignmentPlanner, TaskReadinessProjector
from .slice1 import ServiceEvent, ServiceEventStore
from .task_runtime import (
    Assignment,
    AssignmentStore,
    SemanticVerdict,
    TaskStore,
)
from .trust import (
    AgentServiceR10,
    RemoteDeliverySnapshot,
    _remote_delivery_observation_latest_for_binding,
)


def _now_ns() -> int:
    return time.time_ns()


def _id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex}"


def _sha256_text(value: str) -> str:
    return "sha256:" + hashlib.sha256(value.encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class TaskExecutionClaim:
    id: str
    task_id: str
    mode: str
    owner_id: str
    created_at_ns: int


class TaskExecutionClaimStore:
    """Exactly one execution owner per Task: local Assignment or one remote Binding."""

    MODES = {"LOCAL_ASSIGNMENT", "REMOTE_BINDING"}

    def __init__(self, connection: sqlite3.Connection) -> None:
        self._connection = connection

    def get(self, task_id: str, required: bool = True) -> TaskExecutionClaim | None:
        row = self._connection.execute(
            "SELECT id, task_id, mode, owner_id, created_at_ns FROM task_execution_claims WHERE task_id = ?",
            (task_id,),
        ).fetchone()
        if row is None:
            if required:
                raise KeyError(task_id)
            return None
        return TaskExecutionClaim(
            id=row["id"],
            task_id=row["task_id"],
            mode=row["mode"],
            owner_id=row["owner_id"],
            created_at_ns=row["created_at_ns"],
        )

    def claim(self, task_id: str, *, mode: str, owner_id: str) -> TaskExecutionClaim:
        with self._connection:
            return self.claim_in_transaction(task_id, mode=mode, owner_id=owner_id)

    def claim_in_transaction(
        self, task_id: str, *, mode: str, owner_id: str
    ) -> TaskExecutionClaim:
        if mode not in self.MODES:
            raise ValueError(f"unsupported Task execution claim mode: {mode}")
        if not isinstance(owner_id, str) or not owner_id.strip():
            raise ValueError("Task execution claim owner_id must be non-empty")
        existing = self.get(task_id, required=False)
        if existing is not None:
            if (existing.mode, existing.owner_id) != (mode, owner_id):
                raise RuntimeError(
                    f"Task {task_id} execution already claimed by {existing.mode}:{existing.owner_id}"
                )
            return existing
        value = TaskExecutionClaim(
            id=_id("execclaim"),
            task_id=task_id,
            mode=mode,
            owner_id=owner_id,
            created_at_ns=_now_ns(),
        )
        self._connection.execute(
            "INSERT INTO task_execution_claims(id, task_id, mode, owner_id, created_at_ns) VALUES (?, ?, ?, ?, ?)",
            (value.id, value.task_id, value.mode, value.owner_id, value.created_at_ns),
        )
        return value


class ClaimAwareAssignmentPlanner:
    """R11 local planner: durable local claim is committed atomically with Assignment."""

    def __init__(
        self,
        connection: sqlite3.Connection,
        tasks: TaskStore,
        assignments: AssignmentStore,
        instances: Any,
        events: ServiceEventStore,
        claims: TaskExecutionClaimStore,
    ) -> None:
        self._connection = connection
        self._tasks = tasks
        self._assignments = assignments
        self._instances = instances
        self._events = events
        self._claims = claims

    def plan(self, task_id: str) -> Assignment:
        task = self._tasks.get(task_id)
        existing_assignment = self._assignments.get_by_task(task_id)
        if existing_assignment is not None:
            with self._connection:
                self._claims.claim_in_transaction(
                    task_id,
                    mode="LOCAL_ASSIGNMENT",
                    owner_id=existing_assignment.id,
                )
            return existing_assignment

        existing_claim = self._claims.get(task_id, required=False)
        if existing_claim is not None:
            raise RuntimeError(
                f"Task {task_id} execution already claimed by {existing_claim.mode}:{existing_claim.owner_id}"
            )
        if task.state != "PENDING":
            raise RuntimeError(f"task is not plannable from state {task.state}")
        candidates = [
            instance
            for instance in self._instances.list_all()
            if instance.state == "READY" and instance.revision_id == task.required_revision_id
        ]
        if not candidates:
            raise LookupError("no READY AgentInstance matches required revision")
        candidates.sort(key=lambda item: (item.created_at_ns, item.id))
        chosen = candidates[0]
        with self._connection:
            assignment = self._assignments.create_in_transaction(task.id, chosen.id)
            self._claims.claim_in_transaction(
                task.id,
                mode="LOCAL_ASSIGNMENT",
                owner_id=assignment.id,
            )
            self._tasks.set_state_in_transaction(task.id, "ASSIGNED")
            self._events.append_in_transaction(
                "Task",
                task.id,
                "TASK_ASSIGNED",
                {"assignmentId": assignment.id, "agentInstanceId": chosen.id},
            )
        return assignment


class ClaimAwareDeliveryCoordinator:
    """Remote delivery claims one exact Binding before any external send effect."""

    def __init__(
        self,
        connection: sqlite3.Connection,
        tasks: TaskStore,
        assignments: AssignmentStore,
        events: ServiceEventStore,
        claims: TaskExecutionClaimStore,
        readiness: TaskReadinessProjector,
        delegations: Any,
        bindings: TransportBindingStore,
        receipts: ServiceEventStore,
        adapters: dict[str],
    ) -> None:
        self._connection = connection
        self._tasks = tasks
        self._assignments = assignments
        self._events = events
        self._claims = claims
        self._readiness = readiness
        self._delegations = delegations
        self._bindings = bindings
        self._receipts = receipts
        self._adapters = dict(adapters)

    def _task_is_goal_managed(self, task_id: str) -> bool:
        row = self._connection.execute(
            "SELECT 1 FROM goal_task_links WHERE task_id = ?", (task_id,)
        ).fetchone()
        return row is not None

    def _claim_remote(
        self,
        binding: TransportBinding,
        envelope: Any,
        *,
        allow_terminal: bool,
    ) -> None:
        task = self._tasks.get(envelope.task_id)
        claim = self._claims.get(task.id, required=False)
        if claim is None:
            historical_assignment = self._assignments.get_by_task(task.id)
            if historical_assignment is not None:
                with self._connection:
                    self._claims.claim_in_transaction(
                        task.id,
                        mode="LOCAL_ASSIGNMENT",
                        owner_id=historical_assignment.id,
                    )
                claim = self._claims.get(task.id)

        if claim is not None:
            if (claim.mode, claim.owner_id) != ("REMOTE_BINDING", binding.id):
                raise RuntimeError(
                    f"Task {task.id} execution already claimed by {claim.mode}:{claim.owner_id}"
                )
            if task.state == "PENDING":
                with self._connection:
                    self._tasks.set_state_in_transaction(task.id, "RUNNING")
                    self._events.append_in_transaction(
                        "Task",
                        task.id,
                        "REMOTE_EXECUTION_CLAIMED",
                        {"bindingId": binding.id, "delegationId": envelope.id},
                    )
                return
            if task.state == "RUNNING":
                return
            if allow_terminal and task.state in {"SUCCEEDED", "FAILED", "CANCELLED"}:
                return
            raise RuntimeError(f"remote delivery cannot execute Task state {task.state}")

        if task.state != "PENDING":
            raise RuntimeError(f"remote delivery cannot claim Task state {task.state}")
        if self._task_is_goal_managed(task.id) and not self._readiness.is_ready(task.id):
            raise LookupError("Task is blocked by dependencies or is not PENDING")
        with self._connection:
            self._claims.claim_in_transaction(
                task.id,
                mode="REMOTE_BINDING",
                owner_id=binding.id,
            )
            self._tasks.set_state_in_transaction(task.id, "RUNNING")
            self._events.append_in_transaction(
                "Task",
                task.id,
                "REMOTE_EXECUTION_CLAIMED",
                {"bindingId": binding.id, "delegationId": envelope.id},
            )

    def deliver(self, binding_id: str):
        binding = self._bindings.get(binding_id)
        envelope = self._delegations.get(binding.delegation_id)
        existing = _delivery_receipt_get_by_binding(self._receipts, binding_id, required=False)
        if existing is not None:
            self._claim_remote(binding, envelope, allow_terminal=True)
            return existing
        adapter = self._adapters.get(binding.transport)
        if adapter is None:
            raise LookupError(f"no delivery provider registered for {binding.transport}")
        self._claim_remote(binding, envelope, allow_terminal=False)
        observation = adapter.send(
            delivery_request_id=binding.delivery_request_id,
            binding=binding,
            envelope=envelope,
        )
        if not isinstance(observation, DeliveryObservation):
            raise TypeError("delivery provider must return DeliveryObservation")
        if observation.admission not in {"committed", "existing"}:
            raise ValueError("DeliveryObservation admission must be committed or existing")
        return _delivery_receipt_create(self._receipts, binding, observation)


@dataclass(frozen=True)
class RemoteArtifactPayload:
    artifact_ref: str
    kind: str
    digest: str
    content: str




class RemoteArtifactEvidenceResolver:
    """Normalize digest-verified remote artifacts into the existing EvidenceBundle contract."""

    def __init__(self, readers: dict[str, Any]) -> None:
        for transport, reader in readers.items():
            if not isinstance(transport, str) or not transport.strip():
                raise TypeError("remote artifact reader transport key must be a non-empty string")
            if not callable(getattr(reader, "read", None)):
                raise TypeError(
                    f"remote artifact reader for {transport!r} must expose callable read()"
                )
        self._readers = dict(readers)

    def resolve(
        self,
        acceptance: dict[str, Any],
        *,
        binding: TransportBinding,
        receipt: Any,
        observation: RemoteDeliverySnapshot,
    ) -> EvidenceBundle:
        if acceptance.get("kind") != "runtime_artifact_text_contains":
            raise ValueError(
                f"unsupported remote acceptance kind: {acceptance.get('kind')}"
            )
        reader = self._readers.get(binding.transport)
        if reader is None:
            raise LookupError(f"no remote artifact reader registered for {binding.transport}")
        artifact_kind = acceptance["artifactKind"]
        matches: list[RemoteArtifactPayload] = []
        for artifact_ref in observation.artifact_refs:
            payload = reader.read(
                binding=binding,
                receipt=receipt,
                observation=observation,
                artifact_ref=artifact_ref,
            )
            if not isinstance(payload, RemoteArtifactPayload):
                raise TypeError("remote artifact reader must return RemoteArtifactPayload")
            if payload.artifact_ref != artifact_ref:
                raise RuntimeError("Remote artifact reader returned mismatched identity")
            if not isinstance(payload.kind, str) or not payload.kind.strip():
                raise ValueError("remote artifact kind must be non-empty")
            if not isinstance(payload.content, str):
                raise TypeError("remote artifact content must be text")
            computed = _sha256_text(payload.content)
            if computed != payload.digest:
                raise ArtifactDigestMismatch(
                    f"Remote artifact digest mismatch: {computed} != {payload.digest}"
                )
            if payload.kind == artifact_kind:
                matches.append(payload)
        if len(matches) != 1:
            raise RuntimeError(
                f"expected exactly one remote artifact of kind {artifact_kind!r}, found {len(matches)}"
            )
        payload = matches[0]
        return EvidenceBundle(
            resolver="remote_artifact_text",
            facts={"text": payload.content},
            provenance={
                "bindingId": binding.id,
                "deliveryRequestId": binding.delivery_request_id,
                "remoteObservationId": observation.id,
                "remoteTaskId": observation.remote_task_id,
                "remoteContextId": observation.remote_context_id,
                "artifactRef": payload.artifact_ref,
                "artifactKind": payload.kind,
                "digest": payload.digest,
                "byteLength": len(payload.content.encode("utf-8")),
                "providerEvidenceRef": observation.evidence_ref,
            },
        )


@dataclass(frozen=True)
class RemoteTaskVerificationRecord:
    id: str
    task_id: str
    binding_id: str
    remote_observation_id: str
    stage: str
    accepted: bool
    reason: str | None
    evidence: dict[str, Any]
    created_at_ns: int


def _remote_task_verification_from_event(event: ServiceEvent) -> RemoteTaskVerificationRecord:
    if (
        event.aggregate_type != "RemoteVerification"
        or event.event_type != "RemoteVerificationRecorded"
    ):
        raise ValueError("event is not a remote Task verification receipt")
    payload = event.payload
    if payload.get("taskId") != event.aggregate_id:
        raise RuntimeError("remote verification Task identity mismatch")
    return RemoteTaskVerificationRecord(
        id=event.id,
        task_id=event.aggregate_id,
        binding_id=payload["bindingId"],
        remote_observation_id=payload["remoteObservationId"],
        stage=payload["stage"],
        accepted=bool(payload["accepted"]),
        reason=payload.get("reason"),
        evidence=payload["evidence"],
        created_at_ns=event.created_at_ns,
    )


def _remote_task_verification_get_by_task(
    events: ServiceEventStore,
    task_id: str,
    required: bool = True,
) -> RemoteTaskVerificationRecord | None:
    history = events.list_for("RemoteVerification", task_id)
    receipts = [item for item in history if item.event_type == "RemoteVerificationRecorded"]
    if not receipts:
        if required:
            raise KeyError(task_id)
        return None
    if len(receipts) != 1:
        raise RuntimeError("remote verification receipt stream contains multiple records")
    return _remote_task_verification_from_event(receipts[0])


def _remote_task_verification_create_in_transaction(
    events: ServiceEventStore,
    *,
    task_id: str,
    binding_id: str,
    remote_observation_id: str,
    stage: str,
    accepted: bool,
    reason: str | None,
    evidence: dict[str, Any],
) -> RemoteTaskVerificationRecord:
    normalized_evidence = json.loads(json.dumps(evidence, sort_keys=True, separators=(",", ":"), ensure_ascii=False))
    event = events.append_once_in_transaction(
        "RemoteVerification",
        task_id,
        "RemoteVerificationRecorded",
        {
            "taskId": task_id,
            "bindingId": binding_id,
            "remoteObservationId": remote_observation_id,
            "stage": stage,
            "accepted": bool(accepted),
            "reason": reason,
            "evidence": normalized_evidence,
        },
    )
    return _remote_task_verification_from_event(event)


class RemoteTaskCompletionReconciler:
    """Remote provider completion becomes local Task truth only after local verification."""

    def __init__(
        self,
        connection: sqlite3.Connection,
        tasks: TaskStore,
        events: ServiceEventStore,
        claims: TaskExecutionClaimStore,
        delegations: Any,
        bindings: TransportBindingStore,
        receipts: ServiceEventStore,
        observations: ServiceEventStore,
        resolver: RemoteArtifactEvidenceResolver,
    ) -> None:
        self._connection = connection
        self._tasks = tasks
        self._events = events
        self._claims = claims
        self._delegations = delegations
        self._bindings = bindings
        self._receipts = receipts
        self._observations = observations
        self._resolver = resolver

    def reconcile(self, binding_id: str) -> RemoteTaskVerificationRecord | None:
        binding = self._bindings.get(binding_id)
        envelope = self._delegations.get(binding.delegation_id)
        task = self._tasks.get(envelope.task_id)
        existing = _remote_task_verification_get_by_task(self._events, task.id, required=False)
        if existing is not None:
            if existing.binding_id != binding.id:
                raise RuntimeError("Task verification belongs to a different remote Binding")
            return existing
        claim = self._claims.get(task.id)
        if (claim.mode, claim.owner_id) != ("REMOTE_BINDING", binding.id):
            raise RuntimeError("remote completion does not own Task execution claim")
        _delivery_receipt_get_by_binding(self._receipts, binding.id)
        observation = _remote_delivery_observation_latest_for_binding(self._observations, binding.id, required=False)
        if observation is None or not observation.terminal:
            return None
        if task.state != "RUNNING":
            raise RuntimeError(f"remote completion cannot verify Task state {task.state}")

        if observation.successful is True:
            receipt = _delivery_receipt_get_by_binding(self._receipts, binding.id)
            evidence = self._resolver.resolve(
                task.acceptance,
                binding=binding,
                receipt=receipt,
                observation=observation,
            )
            verdict = _verify_evidence_semantics(task.acceptance, evidence)
            stage = "semantic"
            evidence_receipt = evidence.receipt()
        else:
            reason = (
                f"remote:{observation.provider_status}"
                if observation.successful is False
                else f"remote:{observation.provider_status}:terminal_without_success"
            )
            verdict = SemanticVerdict(False, reason)
            stage = "mechanical"
            evidence_receipt = {
                "resolver": "remote_mechanical_gate",
                "bindingId": binding.id,
                "deliveryRequestId": binding.delivery_request_id,
                "remoteObservationId": observation.id,
                "providerStatus": observation.provider_status,
                "providerEvidenceRef": observation.evidence_ref,
            }

        task_state = "SUCCEEDED" if verdict.accepted else "FAILED"
        terminal_event = "TASK_SUCCEEDED" if verdict.accepted else "TASK_FAILED"
        with self._connection:
            record = _remote_task_verification_create_in_transaction(
                self._events,
                task_id=task.id,
                binding_id=binding.id,
                remote_observation_id=observation.id,
                stage=stage,
                accepted=verdict.accepted,
                reason=verdict.reason,
                evidence=evidence_receipt,
            )
            self._events.append_in_transaction(
                "Task",
                task.id,
                "TASK_VERIFIED_REMOTE",
                {
                    "remoteVerificationId": record.id,
                    "bindingId": binding.id,
                    "remoteObservationId": observation.id,
                    "stage": stage,
                    "accepted": verdict.accepted,
                    "reason": verdict.reason,
                },
            )
            self._tasks.set_state_in_transaction(
                task.id, task_state, failure_reason=verdict.reason
            )
            self._events.append_in_transaction(
                "Task",
                task.id,
                terminal_event,
                {
                    "remoteVerificationId": record.id,
                    "bindingId": binding.id,
                    "remoteObservationId": observation.id,
                    "reason": verdict.reason,
                },
            )
        return record


class AgentServiceR11:
    """R11: exactly-one execution ownership plus remote evidence -> local verifier bridge."""

    def __init__(
        self,
        r10: AgentServiceR10,
        *,
        delivery_adapters: dict[str],
        remote_artifact_readers: dict[str, Any],
    ) -> None:
        self._r10 = r10
        self._connection = r10._connection
        for name in (
            "definitions", "revisions", "instances", "placements", "events",
            "reconciler", "tasks", "assignments", "execution_activator", "completion",
            "goals", "goal_graph_guard", "goal_task_links", "task_dependencies", "task_readiness",
            "task_graph", "goal_reconciler", "board_projector", "identities",
            "sessions", "session_items", "delegations", "a2a_cards",
            "transport_bindings", "routes",
            "credential_references", "identity_proofs",
            "remote_reconciler", "audit",
        ):
            setattr(self, name, getattr(r10, name))
        self.execution_claims = TaskExecutionClaimStore(self._connection)
        self.planner = ClaimAwareAssignmentPlanner(
            self._connection,
            self.tasks,
            self.assignments,
            self.instances,
            self.events,
            self.execution_claims,
        )
        self.goal_planner = GoalAssignmentPlanner(self.task_readiness, self.planner)
        self.delivery = ClaimAwareDeliveryCoordinator(
            self._connection,
            self.tasks,
            self.assignments,
            self.events,
            self.execution_claims,
            self.task_readiness,
            self.delegations,
            self.transport_bindings,
            self.events,
            delivery_adapters,
        )
        self.remote_artifacts = RemoteArtifactEvidenceResolver(remote_artifact_readers)
        self.remote_completion = RemoteTaskCompletionReconciler(
            self._connection,
            self.tasks,
            self.events,
            self.execution_claims,
            self.delegations,
            self.transport_bindings,
            self.events,
            self.events,
            self.remote_artifacts,
        )

    @classmethod
    def open(
        cls,
        db_path: str | Path,
        *,
        carrier_adapter: Any,
        runtime_adapter: Any,
        artifact_reader: Any,
        policy_adapter: Any | None = None,
        delivery_adapters: dict[str] | None = None,
        identity_proof_adapter: Any | None = None,
        remote_delivery_observers: dict[str, Any] | None = None,
        remote_artifact_readers: dict[str, Any] | None = None,
        board_adapter: Any | None = None,
    ) -> "AgentServiceR11":
        adapters = delivery_adapters or {}
        r10 = AgentServiceR10.open(
            db_path,
            carrier_adapter=carrier_adapter,
            runtime_adapter=runtime_adapter,
            artifact_reader=artifact_reader,
            policy_adapter=policy_adapter,
            delivery_adapters=adapters,
            identity_proof_adapter=identity_proof_adapter,
            remote_delivery_observers=remote_delivery_observers or {},
            board_adapter=board_adapter,
        )
        cls._initialize_schema(r10._connection)
        return cls(
            r10,
            delivery_adapters=adapters,
            remote_artifact_readers=remote_artifact_readers or {},
        )

    @staticmethod
    def _initialize_schema(connection: sqlite3.Connection) -> None:
        legacy_remote_task_verifications = connection.execute(
            "SELECT 1 FROM sqlite_master "
            "WHERE type = 'table' AND name = 'remote_task_verifications'"
        ).fetchone()
        if legacy_remote_task_verifications is not None:
            raise RuntimeError(
                "legacy remote_task_verifications schema is unsupported; "
                "perform explicit destructive migration before opening this revision"
            )
        connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS task_execution_claims (
                id TEXT PRIMARY KEY,
                task_id TEXT NOT NULL UNIQUE REFERENCES service_tasks(id),
                mode TEXT NOT NULL CHECK(mode IN ('LOCAL_ASSIGNMENT', 'REMOTE_BINDING')),
                owner_id TEXT NOT NULL,
                created_at_ns INTEGER NOT NULL
            );
            """
        )
        connection.commit()

    def close(self) -> None:
        self._r10.close()
