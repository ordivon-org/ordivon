from __future__ import annotations

import sqlite3
import time
import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .delivery import DeliveryAdapter, DeliveryReceiptStore, PolicyAdapter, TransportBinding, TransportBindingStore
from .evidence import RuntimeArtifactReader
from .goals import BoardAdapter, GoalAssignmentPlanner
from .remote_evidence import (
    AgentServiceR11,
    ClaimAwareAssignmentPlanner,
    ClaimAwareDeliveryCoordinator,
    RemoteArtifactReader,
    RemoteTaskVerificationStore,
    TaskExecutionClaimStore,
)
from .slice1 import CarrierProviderAdapter, ServiceEventStore
from .task_runtime import RuntimeAdapter, TaskStore
from .trust import (
    IdentityProofAdapter,
    RemoteDeliveryObservationStore,
    RemoteDeliveryObserver,
    RemoteDeliverySnapshot,
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


class ExecutionQuiescenceProofStore:
    """Historical quiescence assessments. Positive proof freezes the source Binding."""

    def __init__(self, connection: sqlite3.Connection) -> None:
        self._connection = connection

    def get(self, proof_id: str) -> ExecutionQuiescenceProofRecord:
        row = self._connection.execute(
            "SELECT * FROM execution_quiescence_proofs WHERE id = ?", (proof_id,)
        ).fetchone()
        if row is None:
            raise KeyError(proof_id)
        return self._from_row(row)

    def get_by_client_request(
        self, client_quiescence_request_id: str, required: bool = True
    ) -> ExecutionQuiescenceProofRecord | None:
        row = self._connection.execute(
            "SELECT * FROM execution_quiescence_proofs WHERE client_quiescence_request_id = ?",
            (client_quiescence_request_id,),
        ).fetchone()
        if row is None:
            if required:
                raise KeyError(client_quiescence_request_id)
            return None
        return self._from_row(row)

    def latest_for_binding(
        self, binding_id: str, *, quiescent_only: bool = False
    ) -> ExecutionQuiescenceProofRecord | None:
        predicate = "AND quiescent = 1" if quiescent_only else ""
        row = self._connection.execute(
            f"""
            SELECT * FROM execution_quiescence_proofs
            WHERE binding_id = ? {predicate}
            ORDER BY created_at_ns DESC, id DESC LIMIT 1
            """,
            (binding_id,),
        ).fetchone()
        return None if row is None else self._from_row(row)

    def create_in_transaction(
        self,
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
        existing = self.get_by_client_request(client_quiescence_request_id, required=False)
        candidate = (
            task_id,
            binding_id,
            bool(quiescent),
            method,
            provider_status,
            remote_task_id,
            remote_context_id,
            basis_remote_observation_id,
            evidence_ref,
        )
        if existing is not None:
            historical = (
                existing.task_id,
                existing.binding_id,
                existing.quiescent,
                existing.method,
                existing.provider_status,
                existing.remote_task_id,
                existing.remote_context_id,
                existing.basis_remote_observation_id,
                existing.evidence_ref,
            )
            if candidate != historical:
                raise RuntimeError("quiescence request already exists with different evidence")
            return existing
        value = ExecutionQuiescenceProofRecord(
            id=_id("quiescence"),
            client_quiescence_request_id=client_quiescence_request_id,
            task_id=task_id,
            binding_id=binding_id,
            quiescent=bool(quiescent),
            method=method,
            provider_status=provider_status,
            remote_task_id=remote_task_id,
            remote_context_id=remote_context_id,
            basis_remote_observation_id=basis_remote_observation_id,
            evidence_ref=evidence_ref,
            created_at_ns=_now_ns(),
        )
        self._connection.execute(
            """
            INSERT INTO execution_quiescence_proofs(
                id, client_quiescence_request_id, task_id, binding_id, quiescent,
                method, provider_status, remote_task_id, remote_context_id,
                basis_remote_observation_id, evidence_ref, created_at_ns
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                value.id,
                value.client_quiescence_request_id,
                value.task_id,
                value.binding_id,
                1 if value.quiescent else 0,
                value.method,
                value.provider_status,
                value.remote_task_id,
                value.remote_context_id,
                value.basis_remote_observation_id,
                value.evidence_ref,
                value.created_at_ns,
            ),
        )
        return value

    @staticmethod
    def _from_row(row: sqlite3.Row) -> ExecutionQuiescenceProofRecord:
        return ExecutionQuiescenceProofRecord(
            id=row["id"],
            client_quiescence_request_id=row["client_quiescence_request_id"],
            task_id=row["task_id"],
            binding_id=row["binding_id"],
            quiescent=bool(row["quiescent"]),
            method=row["method"],
            provider_status=row["provider_status"],
            remote_task_id=row["remote_task_id"],
            remote_context_id=row["remote_context_id"],
            basis_remote_observation_id=row["basis_remote_observation_id"],
            evidence_ref=row["evidence_ref"],
            created_at_ns=row["created_at_ns"],
        )


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
        receipts: DeliveryReceiptStore,
        observations: RemoteDeliveryObservationStore,
        requests: ExecutionQuiescenceRequestStore,
        proofs: ExecutionQuiescenceProofStore,
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
        self._proofs = proofs
        self._adapters = dict(adapters)

    def prove(
        self, *, client_quiescence_request_id: str, binding_id: str
    ) -> ExecutionQuiescenceProofRecord:
        if not isinstance(client_quiescence_request_id, str) or not client_quiescence_request_id.strip():
            raise ValueError("client_quiescence_request_id must be non-empty")
        request_id = client_quiescence_request_id.strip()
        existing = self._proofs.get_by_client_request(request_id, required=False)
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
        receipt = self._receipts.get_by_binding(binding.id, required=False)
        history = self._observations.list_for_binding(binding.id)
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
            proof = self._proofs.get_by_client_request(request_id, required=False)
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
            proof = self._proofs.create_in_transaction(
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


class ReplaySafetyDecisionStore:
    SAFE_CLASSIFICATIONS = {"NO_EFFECTS", "ROLLED_BACK", "COMPENSATED", "IDEMPOTENT_REPLAY"}

    def __init__(self, connection: sqlite3.Connection) -> None:
        self._connection = connection

    def get(self, decision_id: str) -> ReplaySafetyDecision:
        row = self._connection.execute(
            "SELECT * FROM replay_safety_decisions WHERE id = ?", (decision_id,)
        ).fetchone()
        if row is None:
            raise KeyError(decision_id)
        return self._from_row(row)

    def get_by_client_request(
        self, client_replay_safety_request_id: str, required: bool = True
    ) -> ReplaySafetyDecision | None:
        row = self._connection.execute(
            "SELECT * FROM replay_safety_decisions WHERE client_replay_safety_request_id = ?",
            (client_replay_safety_request_id,),
        ).fetchone()
        if row is None:
            if required:
                raise KeyError(client_replay_safety_request_id)
            return None
        return self._from_row(row)

    def create_in_transaction(
        self,
        *,
        client_replay_safety_request_id: str,
        task_id: str,
        source_binding_id: str,
        target_binding_id: str,
        quiescence_proof_id: str,
        observation: ReplaySafetyObservation,
    ) -> ReplaySafetyDecision:
        classification = observation.classification.strip().upper()
        if observation.safe and classification not in self.SAFE_CLASSIFICATIONS:
            raise ValueError("safe replay decision requires a recognized safe classification")
        if not observation.safe and classification in self.SAFE_CLASSIFICATIONS:
            raise ValueError("unsafe replay decision cannot use a safe classification")
        if not classification:
            raise ValueError("replay safety classification must be non-empty")
        if not isinstance(observation.evidence_ref, str) or not observation.evidence_ref.strip():
            raise ValueError("replay safety evidence_ref must be non-empty")
        existing = self.get_by_client_request(client_replay_safety_request_id, required=False)
        candidate = (
            task_id,
            source_binding_id,
            target_binding_id,
            quiescence_proof_id,
            bool(observation.safe),
            classification,
            observation.reason,
            observation.evidence_ref,
        )
        if existing is not None:
            historical = (
                existing.task_id,
                existing.source_binding_id,
                existing.target_binding_id,
                existing.quiescence_proof_id,
                existing.safe,
                existing.classification,
                existing.reason,
                existing.evidence_ref,
            )
            if candidate != historical:
                raise RuntimeError("replay safety request already exists with different evidence")
            return existing
        value = ReplaySafetyDecision(
            id=_id("replaysafety"),
            client_replay_safety_request_id=client_replay_safety_request_id,
            task_id=task_id,
            source_binding_id=source_binding_id,
            target_binding_id=target_binding_id,
            quiescence_proof_id=quiescence_proof_id,
            safe=bool(observation.safe),
            classification=classification,
            reason=observation.reason,
            evidence_ref=observation.evidence_ref,
            created_at_ns=_now_ns(),
        )
        self._connection.execute(
            """
            INSERT INTO replay_safety_decisions(
                id, client_replay_safety_request_id, task_id, source_binding_id,
                target_binding_id, quiescence_proof_id, safe, classification,
                reason, evidence_ref, created_at_ns
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                value.id,
                value.client_replay_safety_request_id,
                value.task_id,
                value.source_binding_id,
                value.target_binding_id,
                value.quiescence_proof_id,
                1 if value.safe else 0,
                value.classification,
                value.reason,
                value.evidence_ref,
                value.created_at_ns,
            ),
        )
        return value

    @staticmethod
    def _from_row(row: sqlite3.Row) -> ReplaySafetyDecision:
        return ReplaySafetyDecision(
            id=row["id"],
            client_replay_safety_request_id=row["client_replay_safety_request_id"],
            task_id=row["task_id"],
            source_binding_id=row["source_binding_id"],
            target_binding_id=row["target_binding_id"],
            quiescence_proof_id=row["quiescence_proof_id"],
            safe=bool(row["safe"]),
            classification=row["classification"],
            reason=row["reason"],
            evidence_ref=row["evidence_ref"],
            created_at_ns=row["created_at_ns"],
        )


class ReplaySafetyCoordinator:
    def __init__(
        self,
        connection: sqlite3.Connection,
        tasks: TaskStore,
        events: ServiceEventStore,
        claims: TaskExecutionClaimStore,
        delegations: Any,
        bindings: TransportBindingStore,
        receipts: DeliveryReceiptStore,
        observations: RemoteDeliveryObservationStore,
        quiescence_proofs: ExecutionQuiescenceProofStore,
        decisions: ReplaySafetyDecisionStore,
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
        self._quiescence_proofs = quiescence_proofs
        self._decisions = decisions
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
        existing = self._decisions.get_by_client_request(request_id, required=False)
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
        proof = self._quiescence_proofs.get(quiescence_proof_id)
        if proof.task_id != task.id or proof.binding_id != source.id:
            raise ValueError("quiescence proof does not belong to source Binding")
        if not proof.quiescent:
            raise RuntimeError("replay safety evaluation requires positive quiescence proof")
        history = tuple(self._observations.list_for_binding(source.id))
        if any(item.terminal and item.successful is True for item in history):
            raise RuntimeError("successful terminal source must be verified, not replayed")
        observation = self._adapter.evaluate_replay_safety(
            replay_safety_request_id=request_id,
            task=task,
            envelope=envelope,
            source_binding=source,
            target_binding=target,
            quiescence_proof=proof,
            source_receipt=self._receipts.get_by_binding(source.id, required=False),
            source_observations=history,
        )
        if not isinstance(observation, ReplaySafetyObservation):
            raise TypeError("ReplaySafetyAdapter must return ReplaySafetyObservation")
        with self._connection:
            decision = self._decisions.create_in_transaction(
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


class ExecutionClaimTransferStore:
    def __init__(self, connection: sqlite3.Connection) -> None:
        self._connection = connection

    def get(self, transfer_id: str) -> ExecutionClaimTransferRecord:
        row = self._connection.execute(
            "SELECT * FROM execution_claim_transfers WHERE id = ?", (transfer_id,)
        ).fetchone()
        if row is None:
            raise KeyError(transfer_id)
        return self._from_row(row)

    def get_by_client_request(
        self, client_transfer_request_id: str, required: bool = True
    ) -> ExecutionClaimTransferRecord | None:
        row = self._connection.execute(
            "SELECT * FROM execution_claim_transfers WHERE client_transfer_request_id = ?",
            (client_transfer_request_id,),
        ).fetchone()
        if row is None:
            if required:
                raise KeyError(client_transfer_request_id)
            return None
        return self._from_row(row)

    def get_by_quiescence_proof(self, proof_id: str) -> ExecutionClaimTransferRecord | None:
        row = self._connection.execute(
            "SELECT * FROM execution_claim_transfers WHERE quiescence_proof_id = ?", (proof_id,)
        ).fetchone()
        return None if row is None else self._from_row(row)

    def has_binding_history(self, binding_id: str) -> bool:
        row = self._connection.execute(
            "SELECT 1 FROM execution_claim_transfers WHERE from_binding_id = ? OR to_binding_id = ? LIMIT 1",
            (binding_id, binding_id),
        ).fetchone()
        return row is not None

    def create_in_transaction(
        self,
        *,
        client_transfer_request_id: str,
        task_id: str,
        from_binding_id: str,
        to_binding_id: str,
        quiescence_proof_id: str,
        replay_safety_decision_id: str,
    ) -> ExecutionClaimTransferRecord:
        existing = self.get_by_client_request(client_transfer_request_id, required=False)
        candidate = (
            task_id,
            from_binding_id,
            to_binding_id,
            quiescence_proof_id,
            replay_safety_decision_id,
        )
        if existing is not None:
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
        sequence_row = self._connection.execute(
            "SELECT COALESCE(MAX(sequence), 0) AS max_sequence FROM execution_claim_transfers WHERE task_id = ?",
            (task_id,),
        ).fetchone()
        value = ExecutionClaimTransferRecord(
            id=_id("claimtransfer"),
            client_transfer_request_id=client_transfer_request_id,
            task_id=task_id,
            from_binding_id=from_binding_id,
            to_binding_id=to_binding_id,
            quiescence_proof_id=quiescence_proof_id,
            replay_safety_decision_id=replay_safety_decision_id,
            sequence=int(sequence_row["max_sequence"]) + 1,
            created_at_ns=_now_ns(),
        )
        self._connection.execute(
            """
            INSERT INTO execution_claim_transfers(
                id, client_transfer_request_id, task_id, from_binding_id, to_binding_id,
                quiescence_proof_id, replay_safety_decision_id, sequence, created_at_ns
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                value.id,
                value.client_transfer_request_id,
                value.task_id,
                value.from_binding_id,
                value.to_binding_id,
                value.quiescence_proof_id,
                value.replay_safety_decision_id,
                value.sequence,
                value.created_at_ns,
            ),
        )
        return value

    @staticmethod
    def _from_row(row: sqlite3.Row) -> ExecutionClaimTransferRecord:
        return ExecutionClaimTransferRecord(
            id=row["id"],
            client_transfer_request_id=row["client_transfer_request_id"],
            task_id=row["task_id"],
            from_binding_id=row["from_binding_id"],
            to_binding_id=row["to_binding_id"],
            quiescence_proof_id=row["quiescence_proof_id"],
            replay_safety_decision_id=row["replay_safety_decision_id"],
            sequence=row["sequence"],
            created_at_ns=row["created_at_ns"],
        )


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
        receipts: DeliveryReceiptStore,
        observations: RemoteDeliveryObservationStore,
        remote_verifications: RemoteTaskVerificationStore,
        quiescence_requests: ExecutionQuiescenceRequestStore,
        quiescence_proofs: ExecutionQuiescenceProofStore,
        replay_safety_decisions: ReplaySafetyDecisionStore,
        transfers: ExecutionClaimTransferStore,
    ) -> None:
        self._connection = connection
        self._tasks = tasks
        self._events = events
        self._claims = claims
        self._delegations = delegations
        self._bindings = bindings
        self._receipts = receipts
        self._observations = observations
        self._remote_verifications = remote_verifications
        self._quiescence_requests = quiescence_requests
        self._quiescence_proofs = quiescence_proofs
        self._replay_safety_decisions = replay_safety_decisions
        self._transfers = transfers

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
        if self._receipts.get_by_binding(target.id, required=False) is not None:
            raise RuntimeError("claim transfer target already has a delivery receipt")
        if self._observations.list_for_binding(target.id):
            raise RuntimeError("claim transfer target already has remote observation history")
        if self._quiescence_requests.latest_for_binding(target.id) is not None:
            raise RuntimeError("claim transfer target has quiescence-attempt history")
        if self._quiescence_proofs.latest_for_binding(target.id, quiescent_only=True) is not None:
            raise RuntimeError("claim transfer target was previously quiesced/frozen")
        if self._transfers.has_binding_history(target.id):
            raise RuntimeError("claim transfer target is not pristine")
        if self._remote_verifications.get_by_task(task.id, required=False) is not None:
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
        existing = self._transfers.get_by_client_request(request_id, required=False)
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
        proof = self._quiescence_proofs.get(quiescence_proof_id)
        if proof.task_id != task.id or proof.binding_id != source.id:
            raise ValueError("quiescence proof does not belong to the current source Binding")
        if not proof.quiescent:
            raise RuntimeError("claim transfer requires positive quiescence proof")
        decision = self._replay_safety_decisions.get(replay_safety_decision_id)
        if (
            decision.task_id != task.id
            or decision.source_binding_id != source.id
            or decision.target_binding_id != target.id
            or decision.quiescence_proof_id != proof.id
        ):
            raise ValueError("replay safety decision does not authorize this exact transfer")
        if not decision.safe:
            raise RuntimeError("claim transfer requires replay-safe decision")
        if self._transfers.get_by_quiescence_proof(proof.id) is not None:
            raise RuntimeError("quiescence proof has already been consumed by another transfer")
        if self._receipts.get_by_binding(target.id, required=False) is not None:
            raise RuntimeError("claim transfer target already has a delivery receipt")
        if self._observations.list_for_binding(target.id):
            raise RuntimeError("claim transfer target already has remote observation history")
        if self._quiescence_proofs.latest_for_binding(target.id, quiescent_only=True) is not None:
            raise RuntimeError("claim transfer target was previously quiesced/frozen")
        if self._transfers.has_binding_history(target.id):
            raise RuntimeError("claim transfer target is not pristine")
        if self._remote_verifications.get_by_task(task.id, required=False) is not None:
            raise RuntimeError("verified Task cannot transfer execution claim")
        source_history = self._observations.list_for_binding(source.id)
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
            transfer = self._transfers.create_in_transaction(
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
        quiescence_records: ExecutionQuiescenceProofStore,
        replay_safety: ReplaySafetyCoordinator,
        replay_safety_records: ReplaySafetyDecisionStore,
        claim_transfers: ExecutionClaimTransferCoordinator,
        transfer_records: ExecutionClaimTransferStore,
    ) -> None:
        self._quiescence = quiescence
        self._quiescence_records = quiescence_records
        self._replay_safety = replay_safety
        self._replay_safety_records = replay_safety_records
        self._claim_transfers = claim_transfers
        self._transfer_records = transfer_records

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
        existing = self._transfer_records.get_by_client_request(failover_id, required=False)
        if existing is not None:
            proof = self._quiescence_records.get(existing.quiescence_proof_id)
            decision = self._replay_safety_records.get(existing.replay_safety_decision_id)
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
            "definitions", "revisions", "instances", "placements", "events", "birth", "observer",
            "reconciler", "tasks", "assignments", "execution_activator", "completion", "verifications",
            "goals", "goal_graph_guard", "goal_task_links", "task_dependencies", "task_readiness",
            "task_graph", "goal_reconciler", "board_receipts", "board_projector", "identities",
            "capabilities", "sessions", "session_items", "delegations", "a2a_cards", "interfaces",
            "policy_decisions", "policy", "transport_bindings", "routes", "delivery_receipts",
            "credential_references", "identity_proof_records", "identity_proofs", "remote_observations",
            "remote_reconciler", "audit", "execution_claims", "remote_verifications",
            "remote_artifacts", "remote_semantic_verifier", "remote_completion",
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
        self.quiescence_proof_records = ExecutionQuiescenceProofStore(self._connection)
        self.quiescence = ExecutionQuiescenceCoordinator(
            self._connection,
            self.tasks,
            self.events,
            self.execution_claims,
            self.delegations,
            self.transport_bindings,
            self.delivery_receipts,
            self.remote_observations,
            self.quiescence_requests,
            self.quiescence_proof_records,
            execution_quiescence_adapters,
        )
        self.replay_safety_decisions = ReplaySafetyDecisionStore(self._connection)
        self.replay_safety = ReplaySafetyCoordinator(
            self._connection,
            self.tasks,
            self.events,
            self.execution_claims,
            self.delegations,
            self.transport_bindings,
            self.delivery_receipts,
            self.remote_observations,
            self.quiescence_proof_records,
            self.replay_safety_decisions,
            replay_safety_adapter,
        )
        self.claim_transfer_records = ExecutionClaimTransferStore(self._connection)
        self.claim_transfers = ExecutionClaimTransferCoordinator(
            self._connection,
            self.tasks,
            self.events,
            self.execution_claims,
            self.delegations,
            self.transport_bindings,
            self.delivery_receipts,
            self.remote_observations,
            self.remote_verifications,
            self.quiescence_requests,
            self.quiescence_proof_records,
            self.replay_safety_decisions,
            self.claim_transfer_records,
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
            self.delivery_receipts,
            delivery_adapters,
            quiescence_requests=self.quiescence_requests,
        )
        self.failover = FailoverCoordinator(
            self.quiescence,
            self.quiescence_proof_records,
            self.replay_safety,
            self.replay_safety_decisions,
            self.claim_transfers,
            self.claim_transfer_records,
        )

    @classmethod
    def open(
        cls,
        db_path: str | Path,
        *,
        carrier_adapter: CarrierProviderAdapter,
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

            CREATE TABLE IF NOT EXISTS execution_quiescence_proofs (
                id TEXT PRIMARY KEY,
                client_quiescence_request_id TEXT NOT NULL UNIQUE,
                task_id TEXT NOT NULL REFERENCES service_tasks(id),
                binding_id TEXT NOT NULL REFERENCES transport_bindings(id),
                quiescent INTEGER NOT NULL CHECK(quiescent IN (0, 1)),
                method TEXT NOT NULL,
                provider_status TEXT NOT NULL,
                remote_task_id TEXT,
                remote_context_id TEXT,
                basis_remote_observation_id TEXT REFERENCES remote_delivery_observations(id),
                evidence_ref TEXT NOT NULL,
                created_at_ns INTEGER NOT NULL
            );

            CREATE TABLE IF NOT EXISTS replay_safety_decisions (
                id TEXT PRIMARY KEY,
                client_replay_safety_request_id TEXT NOT NULL UNIQUE,
                task_id TEXT NOT NULL REFERENCES service_tasks(id),
                source_binding_id TEXT NOT NULL REFERENCES transport_bindings(id),
                target_binding_id TEXT NOT NULL REFERENCES transport_bindings(id),
                quiescence_proof_id TEXT NOT NULL REFERENCES execution_quiescence_proofs(id),
                safe INTEGER NOT NULL CHECK(safe IN (0, 1)),
                classification TEXT NOT NULL,
                reason TEXT,
                evidence_ref TEXT NOT NULL,
                created_at_ns INTEGER NOT NULL
            );

            CREATE TABLE IF NOT EXISTS execution_claim_transfers (
                id TEXT PRIMARY KEY,
                client_transfer_request_id TEXT NOT NULL UNIQUE,
                task_id TEXT NOT NULL REFERENCES service_tasks(id),
                from_binding_id TEXT NOT NULL REFERENCES transport_bindings(id),
                to_binding_id TEXT NOT NULL REFERENCES transport_bindings(id),
                quiescence_proof_id TEXT NOT NULL UNIQUE REFERENCES execution_quiescence_proofs(id),
                replay_safety_decision_id TEXT NOT NULL UNIQUE REFERENCES replay_safety_decisions(id),
                sequence INTEGER NOT NULL,
                created_at_ns INTEGER NOT NULL,
                UNIQUE(task_id, sequence),
                CHECK(from_binding_id <> to_binding_id)
            );
            """
        )
        connection.commit()

    def close(self) -> None:
        self._r11.close()
