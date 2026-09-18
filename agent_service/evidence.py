from __future__ import annotations

import hashlib
import json
import sqlite3
import time
import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .slice1 import CarrierProviderAdapter, ServiceEventStore
from .task_runtime import (
    AgentServiceR5,
    Assignment,
    AssignmentStore,
    RuntimeAdapter,
    RuntimeJobObservation,
    SemanticVerdict,
    TaskStore,
)


def _now_ns() -> int:
    return time.time_ns()


def _id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex}"


def _canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def _sha256_text(value: str) -> str:
    return "sha256:" + hashlib.sha256(value.encode("utf-8")).hexdigest()


class ArtifactDigestMismatch(RuntimeError):
    pass


@dataclass(frozen=True)
class RuntimeArtifactPayload:
    job_id: str
    artifact_id: str
    digest: str
    content: str


class RuntimeArtifactReader(ABC):
    @abstractmethod
    def read(self, job_id: str, artifact_id: str) -> RuntimeArtifactPayload:
        raise NotImplementedError


@dataclass(frozen=True)
class EvidenceBundle:
    resolver: str
    facts: dict[str, Any]
    provenance: dict[str, Any]

    def receipt(self) -> dict[str, Any]:
        # Persist provenance, not Runtime-owned raw evidence bytes. The verifier may
        # consume normalized facts in-memory, while durable replay returns to the
        # original Runtime Artifact by job/artifact identity and digest.
        return {"resolver": self.resolver, **self.provenance}


@dataclass(frozen=True)
class VerificationRecord:
    id: str
    task_id: str
    assignment_id: str
    runtime_job_id: str
    stage: str
    accepted: bool
    reason: str | None
    evidence: dict[str, Any]
    created_at_ns: int


class VerificationRecordStore:
    def __init__(self, connection: sqlite3.Connection) -> None:
        self._connection = connection

    def create_in_transaction(
        self,
        *,
        task_id: str,
        assignment_id: str,
        runtime_job_id: str,
        stage: str,
        accepted: bool,
        reason: str | None,
        evidence: dict[str, Any],
    ) -> VerificationRecord:
        existing = self.get_by_assignment(assignment_id)
        candidate = {
            "taskId": task_id,
            "assignmentId": assignment_id,
            "runtimeJobId": runtime_job_id,
            "stage": stage,
            "accepted": bool(accepted),
            "reason": reason,
            "evidence": evidence,
        }
        if existing is not None:
            historical = {
                "taskId": existing.task_id,
                "assignmentId": existing.assignment_id,
                "runtimeJobId": existing.runtime_job_id,
                "stage": existing.stage,
                "accepted": existing.accepted,
                "reason": existing.reason,
                "evidence": existing.evidence,
            }
            if historical != candidate:
                raise RuntimeError("verification record already exists with different evidence")
            return existing
        value = VerificationRecord(
            id=_id("verify"),
            task_id=task_id,
            assignment_id=assignment_id,
            runtime_job_id=runtime_job_id,
            stage=stage,
            accepted=bool(accepted),
            reason=reason,
            evidence=json.loads(_canonical_json(evidence)),
            created_at_ns=_now_ns(),
        )
        self._connection.execute(
            """
            INSERT INTO task_verifications(
                id, task_id, assignment_id, runtime_job_id, stage, accepted,
                reason, evidence_json, created_at_ns
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                value.id,
                value.task_id,
                value.assignment_id,
                value.runtime_job_id,
                value.stage,
                1 if value.accepted else 0,
                value.reason,
                _canonical_json(value.evidence),
                value.created_at_ns,
            ),
        )
        return value

    def get_by_assignment(self, assignment_id: str) -> VerificationRecord | None:
        row = self._connection.execute(
            """
            SELECT id, task_id, assignment_id, runtime_job_id, stage, accepted,
                   reason, evidence_json, created_at_ns
            FROM task_verifications WHERE assignment_id = ?
            """,
            (assignment_id,),
        ).fetchone()
        return None if row is None else self._from_row(row)

    def list_for_task(self, task_id: str) -> list[VerificationRecord]:
        rows = self._connection.execute(
            """
            SELECT id, task_id, assignment_id, runtime_job_id, stage, accepted,
                   reason, evidence_json, created_at_ns
            FROM task_verifications WHERE task_id = ? ORDER BY created_at_ns, id
            """,
            (task_id,),
        ).fetchall()
        return [self._from_row(row) for row in rows]

    @staticmethod
    def _from_row(row: sqlite3.Row) -> VerificationRecord:
        return VerificationRecord(
            id=row["id"],
            task_id=row["task_id"],
            assignment_id=row["assignment_id"],
            runtime_job_id=row["runtime_job_id"],
            stage=row["stage"],
            accepted=bool(row["accepted"]),
            reason=row["reason"],
            evidence=json.loads(row["evidence_json"]),
            created_at_ns=row["created_at_ns"],
        )


class AssignmentExecutionActivator:
    """N15 narrowed for R6: bind execution only; never decides completion."""

    def __init__(
        self,
        connection: sqlite3.Connection,
        tasks: TaskStore,
        assignments: AssignmentStore,
        events: ServiceEventStore,
        runtime: RuntimeAdapter,
    ) -> None:
        self._connection = connection
        self._tasks = tasks
        self._assignments = assignments
        self._events = events
        self._runtime = runtime

    def activate(self, assignment_id: str) -> Assignment:
        assignment = self._assignments.get(assignment_id)
        task = self._tasks.get(assignment.task_id)
        if assignment.runtime_job_id is not None:
            return assignment
        if task.state != "ASSIGNED":
            raise RuntimeError(f"assignment cannot activate while Task is {task.state}")
        runtime_ref = self._runtime.submit(assignment.client_request_id, task.execution)
        with self._connection:
            self._assignments.bind_runtime_job_in_transaction(assignment.id, runtime_ref.job_id)
            self._tasks.set_state_in_transaction(task.id, "RUNNING")
            self._events.append_in_transaction(
                "Task",
                task.id,
                "RUNTIME_JOB_BOUND",
                {"assignmentId": assignment.id, "runtimeJobId": runtime_ref.job_id},
            )
        return self._assignments.get(assignment.id)


class RuntimeEvidenceGate:
    """Mechanical truth gate before any semantic evidence is interpreted."""

    def evaluate(self, observation: RuntimeJobObservation) -> SemanticVerdict | None:
        if observation.semantic_completion_evaluated is not False:
            raise RuntimeError("Runtime crossed semantic-completion authority boundary")
        if not observation.execution_terminal:
            return None
        if observation.status != "succeeded":
            return SemanticVerdict(False, f"runtime:{observation.status}")
        if observation.delivery_disposition != "committed":
            return SemanticVerdict(False, f"runtime:delivery:{observation.delivery_disposition}")
        return SemanticVerdict(True, None)


class EvidenceResolverRegistry:
    def __init__(self, artifact_reader: RuntimeArtifactReader) -> None:
        self._artifact_reader = artifact_reader

    def resolve(self, acceptance: dict[str, Any], observation: RuntimeJobObservation) -> EvidenceBundle:
        kind = acceptance["kind"]
        if kind in {"stdout_contains", "stdout_equals"}:
            content = observation.stdout_tail
            return EvidenceBundle(
                resolver="stdout_tail",
                facts={"text": content},
                provenance={
                    "runtimeJobId": observation.job_id,
                    "digest": _sha256_text(content),
                    "byteLength": len(content.encode("utf-8")),
                },
            )
        if kind == "runtime_artifact_text_contains":
            artifact_kind = acceptance["artifactKind"]
            matches = [
                descriptor
                for descriptor in observation.artifact_descriptors
                if descriptor.kind == artifact_kind
            ]
            if len(matches) != 1:
                raise RuntimeError(
                    f"expected exactly one Runtime artifact of kind {artifact_kind!r}, found {len(matches)}"
                )
            descriptor = matches[0]
            payload = self._artifact_reader.read(observation.job_id, descriptor.artifact_id)
            if payload.job_id != observation.job_id or payload.artifact_id != descriptor.artifact_id:
                raise RuntimeError("Runtime artifact reader returned mismatched identity")
            computed = _sha256_text(payload.content)
            if computed != payload.digest:
                raise ArtifactDigestMismatch(
                    f"Runtime artifact digest mismatch: {computed} != {payload.digest}"
                )
            return EvidenceBundle(
                resolver="runtime_artifact_text",
                facts={"text": payload.content},
                provenance={
                    "runtimeJobId": observation.job_id,
                    "artifactId": payload.artifact_id,
                    "artifactKind": artifact_kind,
                    "digest": payload.digest,
                    "byteLength": len(payload.content.encode("utf-8")),
                },
            )
        raise ValueError(f"unsupported acceptance kind: {kind}")


class EvidenceSemanticVerifier:
    """Pure semantic verifier over normalized evidence, not Runtime process state."""

    def verify(self, acceptance: dict[str, Any], evidence: EvidenceBundle) -> SemanticVerdict:
        kind = acceptance["kind"]
        text = evidence.facts.get("text")
        if not isinstance(text, str):
            raise RuntimeError("text acceptance requires normalized text evidence")
        expected = acceptance["value"]
        if kind in {"stdout_contains", "runtime_artifact_text_contains"}:
            accepted = expected in text
        elif kind == "stdout_equals":
            accepted = expected == text
        else:
            raise ValueError(f"unsupported acceptance kind: {kind}")
        return SemanticVerdict(
            accepted,
            None if accepted else f"acceptance:{kind}:not_satisfied",
        )


class TaskCompletionReconciler:
    """Reconcile one ACTIVE Assignment from Runtime evidence to one semantic terminal verdict."""

    def __init__(
        self,
        connection: sqlite3.Connection,
        tasks: TaskStore,
        assignments: AssignmentStore,
        events: ServiceEventStore,
        verifications: VerificationRecordStore,
        runtime: RuntimeAdapter,
        mechanical_gate: RuntimeEvidenceGate,
        resolvers: EvidenceResolverRegistry,
        verifier: EvidenceSemanticVerifier,
    ) -> None:
        self._connection = connection
        self._tasks = tasks
        self._assignments = assignments
        self._events = events
        self._verifications = verifications
        self._runtime = runtime
        self._mechanical_gate = mechanical_gate
        self._resolvers = resolvers
        self._verifier = verifier

    def reconcile(self, assignment_id: str) -> Assignment:
        assignment = self._assignments.get(assignment_id)
        task = self._tasks.get(assignment.task_id)
        existing = self._verifications.get_by_assignment(assignment.id)
        if existing is not None:
            return assignment
        if assignment.runtime_job_id is None:
            raise RuntimeError("completion reconciliation requires a Runtime Job binding")
        if task.state != "RUNNING":
            if task.state in {"SUCCEEDED", "FAILED", "CANCELLED"}:
                return assignment
            raise RuntimeError(f"completion cannot reconcile Task state {task.state}")

        observation = self._runtime.observe(assignment.runtime_job_id)
        mechanical = self._mechanical_gate.evaluate(observation)
        if mechanical is None:
            return assignment

        if mechanical.accepted:
            evidence = self._resolvers.resolve(task.acceptance, observation)
            verdict = self._verifier.verify(task.acceptance, evidence)
            stage = "semantic"
            receipt = evidence.receipt()
        else:
            verdict = mechanical
            stage = "mechanical"
            receipt = {
                "resolver": "runtime_mechanical_gate",
                "runtimeJobId": observation.job_id,
                "status": observation.status,
                "deliveryDisposition": observation.delivery_disposition,
                "facts": {},
            }

        task_state = "SUCCEEDED" if verdict.accepted else "FAILED"
        assignment_state = "COMPLETED" if verdict.accepted else "FAILED"
        terminal_event = "TASK_SUCCEEDED" if verdict.accepted else "TASK_FAILED"
        with self._connection:
            record = self._verifications.create_in_transaction(
                task_id=task.id,
                assignment_id=assignment.id,
                runtime_job_id=assignment.runtime_job_id,
                stage=stage,
                accepted=verdict.accepted,
                reason=verdict.reason,
                evidence=receipt,
            )
            self._events.append_in_transaction(
                "Task",
                task.id,
                "TASK_VERIFIED",
                {
                    "verificationId": record.id,
                    "assignmentId": assignment.id,
                    "runtimeJobId": assignment.runtime_job_id,
                    "stage": stage,
                    "accepted": verdict.accepted,
                    "reason": verdict.reason,
                },
            )
            self._tasks.set_state_in_transaction(task.id, task_state, failure_reason=verdict.reason)
            self._assignments.set_state_in_transaction(assignment.id, assignment_state)
            self._events.append_in_transaction(
                "Task",
                task.id,
                terminal_event,
                {
                    "verificationId": record.id,
                    "assignmentId": assignment.id,
                    "runtimeJobId": assignment.runtime_job_id,
                    "reason": verdict.reason,
                },
            )
        return self._assignments.get(assignment.id)


class AgentServiceR6:
    """R6 composition: R5 durable work plus explicit evidence/verification completion."""

    def __init__(
        self,
        r5: AgentServiceR5,
        runtime_adapter: RuntimeAdapter,
        artifact_reader: RuntimeArtifactReader,
    ) -> None:
        self._r5 = r5
        self._connection = r5._connection
        self.definitions = r5.definitions
        self.revisions = r5.revisions
        self.instances = r5.instances
        self.placements = r5.placements
        self.events = r5.events
        self.birth = r5.birth
        self.observer = r5.observer
        self.reconciler = r5.reconciler
        self.tasks = r5.tasks
        self.assignments = r5.assignments
        self.planner = r5.planner
        self.legacy_activator = r5.activator
        self.verifications = VerificationRecordStore(self._connection)
        self.execution_activator = AssignmentExecutionActivator(
            self._connection,
            self.tasks,
            self.assignments,
            self.events,
            runtime_adapter,
        )
        self.mechanical_gate = RuntimeEvidenceGate()
        self.evidence_resolvers = EvidenceResolverRegistry(artifact_reader)
        self.semantic_verifier = EvidenceSemanticVerifier()
        self.completion = TaskCompletionReconciler(
            self._connection,
            self.tasks,
            self.assignments,
            self.events,
            self.verifications,
            runtime_adapter,
            self.mechanical_gate,
            self.evidence_resolvers,
            self.semantic_verifier,
        )

    @classmethod
    def open(
        cls,
        db_path: str | Path,
        *,
        carrier_adapter: CarrierProviderAdapter,
        runtime_adapter: RuntimeAdapter,
        artifact_reader: RuntimeArtifactReader,
    ) -> "AgentServiceR6":
        r5 = AgentServiceR5.open(
            db_path,
            carrier_adapter=carrier_adapter,
            runtime_adapter=runtime_adapter,
        )
        cls._initialize_schema(r5._connection)
        return cls(r5, runtime_adapter, artifact_reader)

    @staticmethod
    def _initialize_schema(connection: sqlite3.Connection) -> None:
        connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS task_verifications (
                id TEXT PRIMARY KEY,
                task_id TEXT NOT NULL REFERENCES service_tasks(id),
                assignment_id TEXT NOT NULL UNIQUE REFERENCES service_assignments(id),
                runtime_job_id TEXT NOT NULL,
                stage TEXT NOT NULL,
                accepted INTEGER NOT NULL CHECK(accepted IN (0, 1)),
                reason TEXT,
                evidence_json TEXT NOT NULL,
                created_at_ns INTEGER NOT NULL
            );
            """
        )
        connection.commit()

    def close(self) -> None:
        self._r5.close()
