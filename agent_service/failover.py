from __future__ import annotations

import sqlite3
import time
import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .delivery import DeliveryAdapter, PolicyAdapter, TransportBinding, TransportBindingStore, _delivery_receipt_get_by_binding
from .evidence import RuntimeArtifactReader
from .goals import BoardAdapter, GoalAssignmentPlanner
from .remote_evidence import (
    AgentServiceR11,
    ClaimAwareAssignmentPlanner,
    ClaimAwareDeliveryCoordinator,
    RemoteArtifactReader,
    TaskExecutionClaimStore,
    _remote_task_verification_get_by_task,
)
from .slice1 import ServiceEvent, ServiceEventStore
from .task_runtime import RuntimeAdapter, TaskStore
from .trust import (
    IdentityProofAdapter,
    RemoteDeliveryObserver,
    RemoteDeliverySnapshot,
    _remote_delivery_observation_list_for_binding,
    _remote_delivery_observation_latest_for_binding,
)


def _now_ns() -> int:
    return time.time_ns()


def _id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex}"


@dataclass(frozen=True)
class ExecutionQuiescenceObservation:
    quiescent: bool
    provider_status: str
    remote_task_id: str | None
    remote_context_id: str | None
    evidence_ref: str


class ExecutionQuiescenceAdapter(ABC):
    """Provider seam that proves whether a remote owner can no longer execute."""

    @abstractmethod
    def prove_quiescence(
        self,
        *,
        quiescence_request_id: str,
        binding: TransportBinding,
        receipt: Any | None,
        envelope: Any,
        latest_observation: RemoteDeliverySnapshot | None,
    ) -> ExecutionQuiescenceObservation:
        raise NotImplementedError


@dataclass(frozen=True)
class ExecutionQuiescenceRequestRecord:
    id: str
    client_quiescence_request_id: str
    task_id: str
    binding_id: str
    state: str
    created_at_ns: int
    updated_at_ns: int


class ExecutionQuiescenceRequestStore:
    STATES = {"REQUESTED", "PROVED", "NOT_PROVED"}

    def __init__(self, connection: sqlite3.Connection) -> None:
        self._connection = connection

    def get(self, request_id: str) -> ExecutionQuiescenceRequestRecord:
        row = self._connection.execute(
            "SELECT * FROM execution_quiescence_requests WHERE id = ?", (request_id,)
        ).fetchone()
        if row is None:
            raise KeyError(request_id)
        return self._from_row(row)

    def get_by_client_request(
        self, client_quiescence_request_id: str, required: bool = True
    ) -> ExecutionQuiescenceRequestRecord | None:
        row = self._connection.execute(
            "SELECT * FROM execution_quiescence_requests WHERE client_quiescence_request_id = ?",
            (client_quiescence_request_id,),
        ).fetchone()
        if row is None:
            if required:
                raise KeyError(client_quiescence_request_id)
            return None
        return self._from_row(row)

    def latest_for_binding(self, binding_id: str) -> ExecutionQuiescenceRequestRecord | None:
        row = self._connection.execute(
            """
            SELECT * FROM execution_quiescence_requests
            WHERE binding_id = ? ORDER BY created_at_ns DESC, id DESC LIMIT 1
            """,
            (binding_id,),
        ).fetchone()
        return None if row is None else self._from_row(row)

    def create_requested_in_transaction(
        self, *, client_quiescence_request_id: str, task_id: str, binding_id: str
    ) -> ExecutionQuiescenceRequestRecord:
        existing = self.get_by_client_request(client_quiescence_request_id, required=False)
        if existing is not None:
            if (existing.task_id, existing.binding_id) != (task_id, binding_id):
                raise ValueError("quiescence request identity already bound to different Task/Binding")
            return existing
        now = _now_ns()
        value = ExecutionQuiescenceRequestRecord(
            id=_id("quiescencereq"),
            client_quiescence_request_id=client_quiescence_request_id,
            task_id=task_id,
            binding_id=binding_id,
            state="REQUESTED",
            created_at_ns=now,
            updated_at_ns=now,
        )
        self._connection.execute(
            """
            INSERT INTO execution_quiescence_requests(
                id, client_quiescence_request_id, task_id, binding_id, state,
                created_at_ns, updated_at_ns
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                value.id,
                value.client_quiescence_request_id,
                value.task_id,
                value.binding_id,
                value.state,
                value.created_at_ns,
                value.updated_at_ns,
            ),
        )
        return value

    def set_state_in_transaction(
        self, request_id: str, state: str
    ) -> ExecutionQuiescenceRequestRecord:
        if state not in self.STATES:
            raise ValueError(f"unsupported quiescence request state: {state}")
        current = self.get(request_id)
        if current.state == state:
            return current
        if current.state != "REQUESTED":
            raise RuntimeError(f"quiescence request is already terminal: {current.state}")
        now = _now_ns()
        self._connection.execute(
            "UPDATE execution_quiescence_requests SET state = ?, updated_at_ns = ? WHERE id = ?",
            (state, now, request_id),
        )
        return ExecutionQuiescenceRequestRecord(
            id=current.id,
            client_quiescence_request_id=current.client_quiescence_request_id,
            task_id=current.task_id,
            binding_id=current.binding_id,
            state=state,
            created_at_ns=current.created_at_ns,
            updated_at_ns=now,
        )

    @staticmethod
    def _from_row(row: sqlite3.Row) -> ExecutionQuiescenceRequestRecord:
        return ExecutionQuiescenceRequestRecord(
            id=row["id"],
            client_quiescence_request_id=row["client_quiescence_request_id"],
            task_id=row["task_id"],
            binding_id=row["binding_id"],
            state=row["state"],
            created_at_ns=row["created_at_ns"],
            updated_at_ns=row["updated_at_ns"],
        )


@dataclass(frozen=True)
class ExecutionQuiescenceProofRecord:
    id: str
    client_quiescence_request_id: str
    task_id: str
    binding_id: str
    quiescent: bool
    method: str
    provider_status: str
    remote_task_id: str | None
    remote_context_id: str | None
    basis_remote_observation_id: str | None
    evidence_ref: str
    created_at_ns: int


def _execution_quiescence_proof_from_event(
    event: ServiceEvent,
) -> ExecutionQuiescenceProofRecord:
    if (
        event.aggregate_type != "ExecutionQuiescenceProof"
        or event.event_type != "ExecutionQuiescenceProofRecorded"
    ):
        raise ValueError("event is not an execution-quiescence proof receipt")
    payload = event.payload
    if payload.get("clientQuiescenceRequestId") != event.aggregate_id:
        raise RuntimeError("quiescence proof request identity mismatch")
    return ExecutionQuiescenceProofRecord(
        id=event.id,
        client_quiescence_request_id=event.aggregate_id,
        task_id=payload["taskId"],
        binding_id=payload["bindingId"],
        quiescent=bool(payload["quiescent"]),
        method=payload["method"],
        provider_status=payload["providerStatus"],
        remote_task_id=payload.get("remoteTaskId"),
        remote_context_id=payload.get("remoteContextId"),
        basis_remote_observation_id=payload.get("basisRemoteObservationId"),
        evidence_ref=payload["evidenceRef"],
        created_at_ns=event.created_at_ns,
    )


def _execution_quiescence_proof_get(
    events: ServiceEventStore,
    proof_id: str,
) -> ExecutionQuiescenceProofRecord:
    return _execution_quiescence_proof_from_event(events.get(proof_id))


def _execution_quiescence_proof_get_by_client_request(
    events: ServiceEventStore,
    client_quiescence_request_id: str,
    required: bool = True,
) -> ExecutionQuiescenceProofRecord | None:
    history = events.list_for(
        "ExecutionQuiescenceProof", client_quiescence_request_id
    )
    proofs = [
        item for item in history
        if item.event_type == "ExecutionQuiescenceProofRecorded"
    ]
    if not proofs:
        if required:
            raise KeyError(client_quiescence_request_id)
        return None
    if len(proofs) != 1:
        raise RuntimeError("quiescence proof stream contains multiple records")
    return _execution_quiescence_proof_from_event(proofs[0])


def _execution_quiescence_proof_latest_for_binding(
    events: ServiceEventStore,
    task_id: str,
    binding_id: str,
    *,
    quiescent_only: bool = False,
) -> ExecutionQuiescenceProofRecord | None:
    latest: ExecutionQuiescenceProofRecord | None = None
    for task_event in events.list_for("Task", task_id):
        if task_event.event_type not in {
            "REMOTE_EXECUTION_QUIESCENCE_PROVED",
            "REMOTE_EXECUTION_QUIESCENCE_NOT_PROVED",
        }:
            continue
        proof_id = task_event.payload.get("quiescenceProofId")
        if not isinstance(proof_id, str) or not proof_id:
            raise RuntimeError("quiescence Task event lacks proof identity")
        proof = _execution_quiescence_proof_get(events, proof_id)
        if proof.task_id != task_id:
            raise RuntimeError("quiescence proof Task identity mismatch")
        if proof.binding_id != binding_id:
            continue
        if quiescent_only and not proof.quiescent:
            continue
        latest = proof
    return latest


def _execution_quiescence_proof_create_in_transaction(
    events: ServiceEventStore,
    *,
    client_quiescence_request_id: str,
    task_id: str,
    binding_id: str,
    quiescent: bool,
    method: str,
    provider_status: str,
    remote_task_id: str | None,
    remote_context_id: str | None,
    basis_remote_observation_id: str | None,
    evidence_ref: str,
) -> ExecutionQuiescenceProofRecord:
    event = events.append_once_in_transaction(
        "ExecutionQuiescenceProof",
        client_quiescence_request_id,
        "ExecutionQuiescenceProofRecorded",
        {
            "clientQuiescenceRequestId": client_quiescence_request_id,
            "taskId": task_id,
            "bindingId": binding_id,
            "quiescent": bool(quiescent),
            "method": method,
            "providerStatus": provider_status,
            "remoteTaskId": remote_task_id,
            "remoteContextId": remote_context_id,
            "basisRemoteObservationId": basis_remote_observation_id,
            "evidenceRef": evidence_ref,
        },
    )
    return _execution_quiescence_proof_from_event(event)


class ExecutionQuiescenceCoordinator:
    """Prove execution quiescence without conflating cancel ACK with a stopped owner."""

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
        requests: ExecutionQuiescenceRequestStore,
        adapters: dict[str, ExecutionQuiescenceAdapter],
    ) -> None:
        self._connection = connection
        self._tasks = tasks
        self._events = events
        self._claims = claims
        self._delegations = delegations
        self._bindings = bindings
        self._receipts = receipts
        self._observations = observations
        self._requests = requests
        self._adapters = dict(adapters)

    def prove(
        self, *, client_quiescence_request_id: str, binding_id: str
    ) -> ExecutionQuiescenceProofRecord:
        if not isinstance(client_quiescence_request_id, str) or not client_quiescence_request_id.strip():
            raise ValueError("client_quiescence_request_id must be non-empty")
        request_id = client_quiescence_request_id.strip()
        existing = _execution_quiescence_proof_get_by_client_request(self._events, request_id, required=False)
        if existing is not None:
            if existing.binding_id != binding_id:
                raise ValueError("quiescence request replay targets a different Binding")
            return existing
        request = self._requests.get_by_client_request(request_id, required=False)
        if request is not None and request.binding_id != binding_id:
            raise ValueError("quiescence request replay targets a different Binding")

        binding = self._bindings.get(binding_id)
        envelope = self._delegations.get(binding.delegation_id)
        task = self._tasks.get(envelope.task_id)
        if task.state != "RUNNING":
            raise RuntimeError(f"quiescence proof requires RUNNING Task, got {task.state}")
        claim = self._claims.get(task.id)
        if (claim.mode, claim.owner_id) != ("REMOTE_BINDING", binding.id):
            raise RuntimeError("quiescence proof requires Binding to own the Task execution claim")
        receipt = _delivery_receipt_get_by_binding(self._receipts, binding.id, required=False)
        history = _remote_delivery_observation_list_for_binding(self._observations, binding.id)
        latest = None if not history else history[-1]

        if any(item.terminal and item.successful is True for item in history):
            raise RuntimeError("successful terminal remote execution must be verified, not failed over")

        use_terminal_observation = latest is not None and latest.terminal and latest.successful is False
        if not use_terminal_observation and self._adapters.get(binding.transport) is None:
            raise LookupError(f"no ExecutionQuiescenceAdapter registered for {binding.transport}")
        if request is None:
            with self._connection:
                request = self._requests.create_requested_in_transaction(
                    client_quiescence_request_id=request_id,
                    task_id=task.id,
                    binding_id=binding.id,
                )
                self._events.append_in_transaction(
                    "Task",
                    task.id,
                    "REMOTE_EXECUTION_QUIESCENCE_REQUESTED",
                    {"quiescenceRequestId": request.id, "bindingId": binding.id},
                )
        elif request.state != "REQUESTED":
            proof = _execution_quiescence_proof_get_by_client_request(self._events, request_id, required=False)
            if proof is None:
                raise RuntimeError("terminal quiescence request has no proof receipt")
            return proof

        if use_terminal_observation:
            observation = ExecutionQuiescenceObservation(
                quiescent=True,
                provider_status=latest.provider_status,
                remote_task_id=latest.remote_task_id,
                remote_context_id=latest.remote_context_id,
                evidence_ref=latest.evidence_ref,
            )
            method = "terminal_unsuccessful_observation"
        else:
            adapter = self._adapters[binding.transport]
            observation = adapter.prove_quiescence(
                quiescence_request_id=request_id,
                binding=binding,
                receipt=receipt,
                envelope=envelope,
                latest_observation=latest,
            )
            if not isinstance(observation, ExecutionQuiescenceObservation):
                raise TypeError("ExecutionQuiescenceAdapter must return ExecutionQuiescenceObservation")
            method = "adapter"

        self._validate_observation(observation, receipt=receipt, latest=latest)
        with self._connection:
            proof = _execution_quiescence_proof_create_in_transaction(
                self._events,
                client_quiescence_request_id=request_id,
                task_id=task.id,
                binding_id=binding.id,
                quiescent=observation.quiescent,
                method=method,
                provider_status=observation.provider_status,
                remote_task_id=observation.remote_task_id,
                remote_context_id=observation.remote_context_id,
                basis_remote_observation_id=None if latest is None else latest.id,
                evidence_ref=observation.evidence_ref,
            )
            self._requests.set_state_in_transaction(
                request.id, "PROVED" if proof.quiescent else "NOT_PROVED"
            )
            self._events.append_in_transaction(
                "Task",
                task.id,
                "REMOTE_EXECUTION_QUIESCENCE_PROVED" if proof.quiescent else "REMOTE_EXECUTION_QUIESCENCE_NOT_PROVED",
                {
                    "quiescenceProofId": proof.id,
                    "bindingId": binding.id,
                    "quiescent": proof.quiescent,
                    "method": proof.method,
                    "providerStatus": proof.provider_status,
                },
            )
        return proof

    @staticmethod
    def _validate_observation(
        observation: ExecutionQuiescenceObservation,
        *,
        receipt: Any | None,
        latest: RemoteDeliverySnapshot | None,
    ) -> None:
        if not isinstance(observation.provider_status, str) or not observation.provider_status.strip():
            raise ValueError("quiescence provider_status must be non-empty")
        if not isinstance(observation.evidence_ref, str) or not observation.evidence_ref.strip():
            raise ValueError("quiescence evidence_ref must be non-empty")
        expected_task = None if receipt is None else receipt.remote_task_id
        expected_context = None if receipt is None else receipt.remote_context_id
        if expected_task is None and latest is not None:
            expected_task = latest.remote_task_id
        if expected_context is None and latest is not None:
            expected_context = latest.remote_context_id
        if expected_task is not None and observation.remote_task_id != expected_task:
            raise ValueError("quiescence remote task correlation mismatch")
        if expected_context is not None and observation.remote_context_id != expected_context:
            raise ValueError("quiescence remote context correlation mismatch")


@dataclass(frozen=True)
class ReplaySafetyObservation:
    safe: bool
    classification: str
    reason: str | None
    evidence_ref: str


class ReplaySafetyAdapter(ABC):
    """Domain/effect seam that decides whether executing the Task again is safe."""

    @abstractmethod
    def evaluate_replay_safety(
        self,
        *,
        replay_safety_request_id: str,
        task: Any,
        envelope: Any,
        source_binding: TransportBinding,
        target_binding: TransportBinding,
        quiescence_proof: ExecutionQuiescenceProofRecord,
        source_receipt: Any | None,
        source_observations: tuple[RemoteDeliverySnapshot, ...],
    ) -> ReplaySafetyObservation:
        raise NotImplementedError


@dataclass(frozen=True)
class ReplaySafetyDecision:
    id: str
    client_replay_safety_request_id: str
    task_id: str
    source_binding_id: str
    target_binding_id: str
    quiescence_proof_id: str
    safe: bool
    classification: str
    reason: str | None
    evidence_ref: str
    created_at_ns: int


_REPLAY_SAFE_CLASSIFICATIONS = {
    "NO_EFFECTS",
    "ROLLED_BACK",
    "COMPENSATED",
    "IDEMPOTENT_REPLAY",
}


def _replay_safety_decision_from_event(event: ServiceEvent) -> ReplaySafetyDecision:
    if (
        event.aggregate_type != "ReplaySafetyDecision"
        or event.event_type != "ReplaySafetyDecisionRecorded"
    ):
        raise ValueError("event is not a replay-safety decision receipt")
    payload = event.payload
    if payload.get("clientReplaySafetyRequestId") != event.aggregate_id:
        raise RuntimeError("replay-safety request identity mismatch")
    return ReplaySafetyDecision(
        id=event.id,
        client_replay_safety_request_id=event.aggregate_id,
        task_id=payload["taskId"],
        source_binding_id=payload["sourceBindingId"],
        target_binding_id=payload["targetBindingId"],
        quiescence_proof_id=payload["quiescenceProofId"],
        safe=bool(payload["safe"]),
        classification=payload["classification"],
        reason=payload.get("reason"),
        evidence_ref=payload["evidenceRef"],
        created_at_ns=event.created_at_ns,
    )


def _replay_safety_decision_get(
    events: ServiceEventStore,
    decision_id: str,
) -> ReplaySafetyDecision:
    return _replay_safety_decision_from_event(events.get(decision_id))


def _replay_safety_decision_get_by_client_request(
    events: ServiceEventStore,
    client_replay_safety_request_id: str,
    required: bool = True,
) -> ReplaySafetyDecision | None:
    history = events.list_for(
        "ReplaySafetyDecision", client_replay_safety_request_id
    )
    receipts = [
        item for item in history
        if item.event_type == "ReplaySafetyDecisionRecorded"
    ]
    if not receipts:
        if required:
            raise KeyError(client_replay_safety_request_id)
        return None
    if len(receipts) != 1:
        raise RuntimeError("replay-safety decision stream contains multiple records")
    return _replay_safety_decision_from_event(receipts[0])


def _replay_safety_decision_create_in_transaction(
    events: ServiceEventStore,
    *,
    client_replay_safety_request_id: str,
    task_id: str,
    source_binding_id: str,
    target_binding_id: str,
    quiescence_proof_id: str,
    observation: ReplaySafetyObservation,
) -> ReplaySafetyDecision:
    classification = observation.classification.strip().upper()
    if observation.safe and classification not in _REPLAY_SAFE_CLASSIFICATIONS:
        raise ValueError(
            "safe replay decision requires a recognized safe classification"
        )
    if not observation.safe and classification in _REPLAY_SAFE_CLASSIFICATIONS:
        raise ValueError(
            "unsafe replay decision cannot use a safe classification"
        )
    if not classification:
        raise ValueError("replay safety classification must be non-empty")
    if (
        not isinstance(observation.evidence_ref, str)
        or not observation.evidence_ref.strip()
    ):
        raise ValueError("replay safety evidence_ref must be non-empty")

    event = events.append_once_in_transaction(
        "ReplaySafetyDecision",
        client_replay_safety_request_id,
        "ReplaySafetyDecisionRecorded",
        {
            "clientReplaySafetyRequestId": client_replay_safety_request_id,
            "taskId": task_id,
            "sourceBindingId": source_binding_id,
            "targetBindingId": target_binding_id,
            "quiescenceProofId": quiescence_proof_id,
            "safe": bool(observation.safe),
            "classification": classification,
            "reason": observation.reason,
            "evidenceRef": observation.evidence_ref.strip(),
        },
    )
    return _replay_safety_decision_from_event(event)


class ReplaySafetyCoordinator:
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
        adapter: ReplaySafetyAdapter | None,
    ) -> None:
        self._connection = connection
        self._tasks = tasks
        self._events = events
        self._claims = claims
        self._delegations = delegations
        self._bindings = bindings
        self._receipts = receipts
        self._observations = observations
        self._adapter = adapter

    def evaluate(
        self,
        *,
        client_replay_safety_request_id: str,
        from_binding_id: str,
        to_binding_id: str,
        quiescence_proof_id: str,
    ) -> ReplaySafetyDecision:
        if not isinstance(client_replay_safety_request_id, str) or not client_replay_safety_request_id.strip():
            raise ValueError("client_replay_safety_request_id must be non-empty")
        request_id = client_replay_safety_request_id.strip()
        existing = _replay_safety_decision_get_by_client_request(self._events, request_id, required=False)
        if existing is not None:
            candidate = (from_binding_id, to_binding_id, quiescence_proof_id)
            historical = (
                existing.source_binding_id,
                existing.target_binding_id,
                existing.quiescence_proof_id,
            )
            if candidate != historical:
                raise ValueError("replay safety request replay conflicts with committed decision")
            return existing
        if self._adapter is None:
            raise RuntimeError("no ReplaySafetyAdapter configured")
        if from_binding_id == to_binding_id:
            raise ValueError("replay safety requires distinct source and target Bindings")
        source = self._bindings.get(from_binding_id)
        target = self._bindings.get(to_binding_id)
        if source.delegation_id != target.delegation_id:
            raise ValueError("replay safety target must belong to the same DelegationEnvelope")
        envelope = self._delegations.get(source.delegation_id)
        task = self._tasks.get(envelope.task_id)
        if task.state != "RUNNING":
            raise RuntimeError(f"replay safety requires RUNNING Task, got {task.state}")
        claim = self._claims.get(task.id)
        if (claim.mode, claim.owner_id) != ("REMOTE_BINDING", source.id):
            raise RuntimeError("replay safety source is not the current remote execution owner")
        proof = _execution_quiescence_proof_get(self._events, quiescence_proof_id)
        if proof.task_id != task.id or proof.binding_id != source.id:
            raise ValueError("quiescence proof does not belong to source Binding")
        if not proof.quiescent:
            raise RuntimeError("replay safety evaluation requires positive quiescence proof")
        history = tuple(_remote_delivery_observation_list_for_binding(self._observations, source.id))
        if any(item.terminal and item.successful is True for item in history):
            raise RuntimeError("successful terminal source must be verified, not replayed")
        observation = self._adapter.evaluate_replay_safety(
            replay_safety_request_id=request_id,
            task=task,
            envelope=envelope,
            source_binding=source,
            target_binding=target,
            quiescence_proof=proof,
            source_receipt=_delivery_receipt_get_by_binding(self._receipts, source.id, required=False),
            source_observations=history,
        )
        if not isinstance(observation, ReplaySafetyObservation):
            raise TypeError("ReplaySafetyAdapter must return ReplaySafetyObservation")
        with self._connection:
            decision = _replay_safety_decision_create_in_transaction(
                self._events,
                client_replay_safety_request_id=request_id,
                task_id=task.id,
                source_binding_id=source.id,
                target_binding_id=target.id,
                quiescence_proof_id=proof.id,
                observation=observation,
            )
            self._events.append_in_transaction(
                "Task",
                task.id,
                "REMOTE_REPLAY_SAFETY_EVALUATED",
                {
                    "replaySafetyDecisionId": decision.id,
                    "fromBindingId": source.id,
                    "toBindingId": target.id,
                    "safe": decision.safe,
                    "classification": decision.classification,
                },
            )
        return decision


@dataclass(frozen=True)
class ExecutionClaimTransferRecord:
    id: str
    client_transfer_request_id: str
    task_id: str
    from_binding_id: str
    to_binding_id: str
    quiescence_proof_id: str
    replay_safety_decision_id: str
    sequence: int
    created_at_ns: int


def _execution_claim_transfer_from_event(
    event: ServiceEvent,
) -> ExecutionClaimTransferRecord:
    if (
        event.aggregate_type != "ExecutionClaimTransfer"
        or event.event_type != "ExecutionClaimTransferred"
    ):
        raise ValueError("event is not an execution claim transfer receipt")
    payload = event.payload
    if payload.get("clientTransferRequestId") != event.aggregate_id:
        raise RuntimeError("claim transfer request identity mismatch")
    return ExecutionClaimTransferRecord(
        id=event.id,
        client_transfer_request_id=event.aggregate_id,
        task_id=payload["taskId"],
        from_binding_id=payload["fromBindingId"],
        to_binding_id=payload["toBindingId"],
        quiescence_proof_id=payload["quiescenceProofId"],
        replay_safety_decision_id=payload["replaySafetyDecisionId"],
        sequence=int(payload["sequence"]),
        created_at_ns=event.created_at_ns,
    )


def _execution_claim_transfer_get_by_client_request(
    events: ServiceEventStore,
    client_transfer_request_id: str,
    required: bool = True,
) -> ExecutionClaimTransferRecord | None:
    history = events.list_for("ExecutionClaimTransfer", client_transfer_request_id)
    receipts = [item for item in history if item.event_type == "ExecutionClaimTransferred"]
    if not receipts:
        if required:
            raise KeyError(client_transfer_request_id)
        return None
    if len(receipts) != 1:
        raise RuntimeError("claim transfer receipt stream contains multiple records")
    return _execution_claim_transfer_from_event(receipts[0])


def _execution_claim_transfer_task_history(
    events: ServiceEventStore,
    task_id: str,
) -> list[ExecutionClaimTransferRecord]:
    records: list[ExecutionClaimTransferRecord] = []
    for task_event in events.list_for("Task", task_id):
        if task_event.event_type != "REMOTE_EXECUTION_CLAIM_TRANSFERRED":
            continue
        transfer_id = task_event.payload.get("claimTransferId")
        if not isinstance(transfer_id, str) or not transfer_id:
            raise RuntimeError("claim transfer Task event lacks transfer identity")
        record = _execution_claim_transfer_from_event(events.get(transfer_id))
        if record.task_id != task_id:
            raise RuntimeError("claim transfer receipt Task identity mismatch")
        records.append(record)
    return records


def _execution_claim_transfer_get_by_quiescence_proof(
    events: ServiceEventStore,
    task_id: str,
    proof_id: str,
) -> ExecutionClaimTransferRecord | None:
    for record in _execution_claim_transfer_task_history(events, task_id):
        if record.quiescence_proof_id == proof_id:
            return record
    return None


def _execution_claim_transfer_has_binding_history(
    events: ServiceEventStore,
    task_id: str,
    binding_id: str,
) -> bool:
    return any(
        binding_id in {record.from_binding_id, record.to_binding_id}
        for record in _execution_claim_transfer_task_history(events, task_id)
    )


def _execution_claim_transfer_create_in_transaction(
    events: ServiceEventStore,
    *,
    client_transfer_request_id: str,
    task_id: str,
    from_binding_id: str,
    to_binding_id: str,
    quiescence_proof_id: str,
    replay_safety_decision_id: str,
) -> ExecutionClaimTransferRecord:
    existing = _execution_claim_transfer_get_by_client_request(
        events, client_transfer_request_id, required=False
    )
    if existing is not None:
        candidate = (
            task_id,
            from_binding_id,
            to_binding_id,
            quiescence_proof_id,
            replay_safety_decision_id,
        )
        historical = (
            existing.task_id,
            existing.from_binding_id,
            existing.to_binding_id,
            existing.quiescence_proof_id,
            existing.replay_safety_decision_id,
        )
        if candidate != historical:
            raise RuntimeError("claim transfer replay conflicts with committed transfer")
        return existing

    history = _execution_claim_transfer_task_history(events, task_id)
    sequence = max((record.sequence for record in history), default=0) + 1
    event = events.append_once_in_transaction(
        "ExecutionClaimTransfer",
        client_transfer_request_id,
        "ExecutionClaimTransferred",
        {
            "clientTransferRequestId": client_transfer_request_id,
            "taskId": task_id,
            "fromBindingId": from_binding_id,
            "toBindingId": to_binding_id,
            "quiescenceProofId": quiescence_proof_id,
            "replaySafetyDecisionId": replay_safety_decision_id,
            "sequence": sequence,
        },
    )
    record = _execution_claim_transfer_from_event(event)

    events.append_once_in_transaction(
        "ExecutionClaimTransferProof",
        quiescence_proof_id,
        "ExecutionClaimTransferProofConsumed",
        {
            "claimTransferId": record.id,
            "clientTransferRequestId": client_transfer_request_id,
            "taskId": task_id,
        },
    )
    events.append_once_in_transaction(
        "ExecutionClaimTransferDecision",
        replay_safety_decision_id,
        "ExecutionClaimTransferDecisionConsumed",
        {
            "claimTransferId": record.id,
            "clientTransferRequestId": client_transfer_request_id,
            "taskId": task_id,
        },
    )
    return record


class ExecutionClaimTransferCoordinator:
    """CAS transfer requires both positive quiescence and positive replay-safety proof."""

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
        quiescence_requests: ExecutionQuiescenceRequestStore,
    ) -> None:
        self._connection = connection
        self._tasks = tasks
        self._events = events
        self._claims = claims
        self._delegations = delegations
        self._bindings = bindings
        self._receipts = receipts
        self._observations = observations
        self._quiescence_requests = quiescence_requests

    def preflight(self, *, from_binding_id: str, to_binding_id: str) -> tuple[Any, TransportBinding, TransportBinding]:
        if from_binding_id == to_binding_id:
            raise ValueError("claim transfer requires distinct source and target Bindings")
        source = self._bindings.get(from_binding_id)
        target = self._bindings.get(to_binding_id)
        if source.delegation_id != target.delegation_id:
            raise ValueError("claim transfer target must belong to the same DelegationEnvelope")
        envelope = self._delegations.get(source.delegation_id)
        task = self._tasks.get(envelope.task_id)
        if task.state != "RUNNING":
            raise RuntimeError(f"claim transfer requires RUNNING Task, got {task.state}")
        claim = self._claims.get(task.id)
        if (claim.mode, claim.owner_id) != ("REMOTE_BINDING", source.id):
            raise RuntimeError("claim transfer source is not the current remote execution owner")
        if _delivery_receipt_get_by_binding(self._receipts, target.id, required=False) is not None:
            raise RuntimeError("claim transfer target already has a delivery receipt")
        if _remote_delivery_observation_list_for_binding(self._observations, target.id):
            raise RuntimeError("claim transfer target already has remote observation history")
        if self._quiescence_requests.latest_for_binding(target.id) is not None:
            raise RuntimeError("claim transfer target has quiescence-attempt history")
        if _execution_quiescence_proof_latest_for_binding(self._events, task.id, target.id, quiescent_only=True) is not None:
            raise RuntimeError("claim transfer target was previously quiesced/frozen")
        if _execution_claim_transfer_has_binding_history(self._events, task.id, target.id):
            raise RuntimeError("claim transfer target is not pristine")
        if _remote_task_verification_get_by_task(self._events, task.id, required=False) is not None:
            raise RuntimeError("verified Task cannot transfer execution claim")
        return task, source, target

    def transfer(
        self,
        *,
        client_transfer_request_id: str,
        from_binding_id: str,
        to_binding_id: str,
        quiescence_proof_id: str,
        replay_safety_decision_id: str,
    ) -> ExecutionClaimTransferRecord:
        if not isinstance(client_transfer_request_id, str) or not client_transfer_request_id.strip():
            raise ValueError("client_transfer_request_id must be non-empty")
        request_id = client_transfer_request_id.strip()
        existing = _execution_claim_transfer_get_by_client_request(self._events, request_id, required=False)
        if existing is not None:
            candidate = (
                from_binding_id,
                to_binding_id,
                quiescence_proof_id,
                replay_safety_decision_id,
            )
            historical = (
                existing.from_binding_id,
                existing.to_binding_id,
                existing.quiescence_proof_id,
                existing.replay_safety_decision_id,
            )
            if candidate != historical:
                raise ValueError("claim transfer replay conflicts with committed transfer")
            return existing
        if from_binding_id == to_binding_id:
            raise ValueError("claim transfer requires distinct source and target Bindings")
        source = self._bindings.get(from_binding_id)
        target = self._bindings.get(to_binding_id)
        if source.delegation_id != target.delegation_id:
            raise ValueError("claim transfer target must belong to the same DelegationEnvelope")
        envelope = self._delegations.get(source.delegation_id)
        task = self._tasks.get(envelope.task_id)
        if task.state != "RUNNING":
            raise RuntimeError(f"claim transfer requires RUNNING Task, got {task.state}")
        claim = self._claims.get(task.id)
        if (claim.mode, claim.owner_id) != ("REMOTE_BINDING", source.id):
            raise RuntimeError("claim transfer source is not the current remote execution owner")
        proof = _execution_quiescence_proof_get(self._events, quiescence_proof_id)
        if proof.task_id != task.id or proof.binding_id != source.id:
            raise ValueError("quiescence proof does not belong to the current source Binding")
        if not proof.quiescent:
            raise RuntimeError("claim transfer requires positive quiescence proof")
        decision = _replay_safety_decision_get(self._events, replay_safety_decision_id)
        if (
            decision.task_id != task.id
            or decision.source_binding_id != source.id
            or decision.target_binding_id != target.id
            or decision.quiescence_proof_id != proof.id
        ):
            raise ValueError("replay safety decision does not authorize this exact transfer")
        if not decision.safe:
            raise RuntimeError("claim transfer requires replay-safe decision")
        if _execution_claim_transfer_get_by_quiescence_proof(self._events, task.id, proof.id) is not None:
            raise RuntimeError("quiescence proof has already been consumed by another transfer")
        if _delivery_receipt_get_by_binding(self._receipts, target.id, required=False) is not None:
            raise RuntimeError("claim transfer target already has a delivery receipt")
        if _remote_delivery_observation_list_for_binding(self._observations, target.id):
            raise RuntimeError("claim transfer target already has remote observation history")
        if _execution_quiescence_proof_latest_for_binding(self._events, task.id, target.id, quiescent_only=True) is not None:
            raise RuntimeError("claim transfer target was previously quiesced/frozen")
        if _execution_claim_transfer_has_binding_history(self._events, task.id, target.id):
            raise RuntimeError("claim transfer target is not pristine")
        if _remote_task_verification_get_by_task(self._events, task.id, required=False) is not None:
            raise RuntimeError("verified Task cannot transfer execution claim")
        source_history = _remote_delivery_observation_list_for_binding(self._observations, source.id)
        if any(item.terminal and item.successful is True for item in source_history):
            raise RuntimeError("successful terminal source must be verified, not failed over")
        later = [item for item in source_history if item.created_at_ns > proof.created_at_ns]
        if any(not (item.terminal and item.successful is False) for item in later):
            raise RuntimeError("quiescence proof was contradicted by a later source observation")
        with self._connection:
            cursor = self._connection.execute(
                """
                UPDATE task_execution_claims
                SET owner_id = ?
                WHERE task_id = ? AND mode = 'REMOTE_BINDING' AND owner_id = ?
                """,
                (target.id, task.id, source.id),
            )
            if cursor.rowcount != 1:
                raise RuntimeError("execution claim changed before transfer commit")
            transfer = _execution_claim_transfer_create_in_transaction(
                self._events,
                client_transfer_request_id=request_id,
                task_id=task.id,
                from_binding_id=source.id,
                to_binding_id=target.id,
                quiescence_proof_id=proof.id,
                replay_safety_decision_id=decision.id,
            )
            self._events.append_in_transaction(
                "Task",
                task.id,
                "REMOTE_EXECUTION_CLAIM_TRANSFERRED",
                {
                    "claimTransferId": transfer.id,
                    "quiescenceProofId": proof.id,
                    "replaySafetyDecisionId": decision.id,
                    "fromBindingId": source.id,
                    "toBindingId": target.id,
                    "sequence": transfer.sequence,
                },
            )
        return transfer


class TransferAwareDeliveryCoordinator(ClaimAwareDeliveryCoordinator):
    """Any durable quiescence attempt freezes that old Binding from new delivery."""

    def __init__(
        self,
        *args: Any,
        quiescence_requests: ExecutionQuiescenceRequestStore,
        **kwargs: Any,
    ) -> None:
        super().__init__(*args, **kwargs)
        self._quiescence_requests_r12 = quiescence_requests

    def deliver(self, binding_id: str):
        if self._quiescence_requests_r12.latest_for_binding(binding_id) is not None:
            raise RuntimeError("remote Binding is frozen by a quiescence attempt")
        return super().deliver(binding_id)


class FailoverCoordinator:
    """Prove quiescence, prove replay safety, then atomically transfer execution ownership."""

    def __init__(
        self,
        quiescence: ExecutionQuiescenceCoordinator,
        replay_safety: ReplaySafetyCoordinator,
        claim_transfers: ExecutionClaimTransferCoordinator,
        events: ServiceEventStore,
    ) -> None:
        self._quiescence = quiescence
        self._replay_safety = replay_safety
        self._claim_transfers = claim_transfers
        self._events = events

    def failover(
        self,
        *,
        client_failover_request_id: str,
        client_quiescence_request_id: str,
        client_replay_safety_request_id: str,
        from_binding_id: str,
        to_binding_id: str,
    ) -> ExecutionClaimTransferRecord:
        if not isinstance(client_failover_request_id, str) or not client_failover_request_id.strip():
            raise ValueError("client_failover_request_id must be non-empty")
        if not isinstance(client_quiescence_request_id, str) or not client_quiescence_request_id.strip():
            raise ValueError("client_quiescence_request_id must be non-empty")
        if not isinstance(client_replay_safety_request_id, str) or not client_replay_safety_request_id.strip():
            raise ValueError("client_replay_safety_request_id must be non-empty")
        failover_id = client_failover_request_id.strip()
        quiescence_id = client_quiescence_request_id.strip()
        replay_id = client_replay_safety_request_id.strip()
        existing = _execution_claim_transfer_get_by_client_request(self._events, failover_id, required=False)
        if existing is not None:
            proof = _execution_quiescence_proof_get(self._events, existing.quiescence_proof_id)
            decision = _replay_safety_decision_get(self._events, existing.replay_safety_decision_id)
            if (
                existing.from_binding_id != from_binding_id
                or existing.to_binding_id != to_binding_id
                or proof.client_quiescence_request_id != quiescence_id
                or decision.client_replay_safety_request_id != replay_id
            ):
                raise ValueError("failover replay conflicts with committed transfer")
            return existing
        self._claim_transfers.preflight(
            from_binding_id=from_binding_id,
            to_binding_id=to_binding_id,
        )
        proof = self._quiescence.prove(
            client_quiescence_request_id=quiescence_id,
            binding_id=from_binding_id,
        )
        decision = self._replay_safety.evaluate(
            client_replay_safety_request_id=client_replay_safety_request_id,
            from_binding_id=from_binding_id,
            to_binding_id=to_binding_id,
            quiescence_proof_id=proof.id,
        )
        return self._claim_transfers.transfer(
            client_transfer_request_id=failover_id,
            from_binding_id=from_binding_id,
            to_binding_id=to_binding_id,
            quiescence_proof_id=proof.id,
            replay_safety_decision_id=decision.id,
        )


class AgentServiceR12:
    """R12: quiescence + replay safety + CAS execution-claim failover."""

    def __init__(
        self,
        r11: AgentServiceR11,
        *,
        delivery_adapters: dict[str, DeliveryAdapter],
        execution_quiescence_adapters: dict[str, ExecutionQuiescenceAdapter],
        replay_safety_adapter: ReplaySafetyAdapter | None,
    ) -> None:
        self._r11 = r11
        self._connection = r11._connection
        for name in (
            "definitions", "revisions", "instances", "placements", "events",
            "reconciler", "tasks", "assignments", "execution_activator", "completion",
            "goals", "goal_graph_guard", "goal_task_links", "task_dependencies", "task_readiness",
            "task_graph", "goal_reconciler", "board_projector", "identities",
            "sessions", "session_items", "delegations", "a2a_cards",
            "transport_bindings", "routes",
            "credential_references", "identity_proofs",
            "remote_reconciler", "audit", "execution_claims",
            "remote_artifacts", "remote_completion",
        ):
            setattr(self, name, getattr(r11, name))
        self.planner = ClaimAwareAssignmentPlanner(
            self._connection,
            self.tasks,
            self.assignments,
            self.instances,
            self.events,
            self.execution_claims,
        )
        self.goal_planner = GoalAssignmentPlanner(self.task_readiness, self.planner)
        self.quiescence_requests = ExecutionQuiescenceRequestStore(self._connection)
        self.quiescence = ExecutionQuiescenceCoordinator(
            self._connection,
            self.tasks,
            self.events,
            self.execution_claims,
            self.delegations,
            self.transport_bindings,
            self.events,
            self.events,
            self.quiescence_requests,
            execution_quiescence_adapters,
        )
        self.replay_safety = ReplaySafetyCoordinator(
            self._connection,
            self.tasks,
            self.events,
            self.execution_claims,
            self.delegations,
            self.transport_bindings,
            self.events,
            self.events,
            replay_safety_adapter,
        )
        self.claim_transfers = ExecutionClaimTransferCoordinator(
            self._connection,
            self.tasks,
            self.events,
            self.execution_claims,
            self.delegations,
            self.transport_bindings,
            self.events,
            self.events,
            self.quiescence_requests,
        )
        self.delivery = TransferAwareDeliveryCoordinator(
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
            quiescence_requests=self.quiescence_requests,
        )
        self.failover = FailoverCoordinator(
            self.quiescence,
            self.replay_safety,
            self.claim_transfers,
            self.events,
        )

    @classmethod
    def open(
        cls,
        db_path: str | Path,
        *,
        carrier_adapter: Any,
        runtime_adapter: RuntimeAdapter,
        artifact_reader: RuntimeArtifactReader,
        policy_adapter: PolicyAdapter | None = None,
        delivery_adapters: dict[str, DeliveryAdapter] | None = None,
        identity_proof_adapter: IdentityProofAdapter | None = None,
        remote_delivery_observers: dict[str, RemoteDeliveryObserver] | None = None,
        remote_artifact_readers: dict[str, RemoteArtifactReader] | None = None,
        execution_quiescence_adapters: dict[str, ExecutionQuiescenceAdapter] | None = None,
        replay_safety_adapter: ReplaySafetyAdapter | None = None,
        board_adapter: BoardAdapter | None = None,
    ) -> "AgentServiceR12":
        adapters = delivery_adapters or {}
        r11 = AgentServiceR11.open(
            db_path,
            carrier_adapter=carrier_adapter,
            runtime_adapter=runtime_adapter,
            artifact_reader=artifact_reader,
            policy_adapter=policy_adapter,
            delivery_adapters=adapters,
            identity_proof_adapter=identity_proof_adapter,
            remote_delivery_observers=remote_delivery_observers or {},
            remote_artifact_readers=remote_artifact_readers or {},
            board_adapter=board_adapter,
        )
        cls._initialize_schema(r11._connection)
        return cls(
            r11,
            delivery_adapters=adapters,
            execution_quiescence_adapters=execution_quiescence_adapters or {},
            replay_safety_adapter=replay_safety_adapter,
        )

    @staticmethod
    def _initialize_schema(connection: sqlite3.Connection) -> None:
        legacy_execution_claim_transfers = connection.execute(
            "SELECT 1 FROM sqlite_master "
            "WHERE type = 'table' AND name = 'execution_claim_transfers'"
        ).fetchone()
        if legacy_execution_claim_transfers is not None:
            raise RuntimeError(
                "legacy execution_claim_transfers schema is unsupported; "
                "perform explicit destructive migration before opening this revision"
            )
        legacy_replay_safety_decisions = connection.execute(
            "SELECT 1 FROM sqlite_master "
            "WHERE type = 'table' AND name = 'replay_safety_decisions'"
        ).fetchone()
        if legacy_replay_safety_decisions is not None:
            raise RuntimeError(
                "legacy replay_safety_decisions schema is unsupported; "
                "perform explicit destructive migration before opening this revision"
            )
        legacy_execution_quiescence_proofs = connection.execute(
            "SELECT 1 FROM sqlite_master "
            "WHERE type = 'table' AND name = 'execution_quiescence_proofs'"
        ).fetchone()
        if legacy_execution_quiescence_proofs is not None:
            raise RuntimeError(
                "legacy execution_quiescence_proofs schema is unsupported; "
                "perform explicit destructive migration before opening this revision"
            )
        connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS execution_quiescence_requests (
                id TEXT PRIMARY KEY,
                client_quiescence_request_id TEXT NOT NULL UNIQUE,
                task_id TEXT NOT NULL REFERENCES service_tasks(id),
                binding_id TEXT NOT NULL REFERENCES transport_bindings(id),
                state TEXT NOT NULL CHECK(state IN ('REQUESTED', 'PROVED', 'NOT_PROVED')),
                created_at_ns INTEGER NOT NULL,
                updated_at_ns INTEGER NOT NULL
            );

            """
        )
        connection.commit()

    def close(self) -> None:
        self._r11.close()
