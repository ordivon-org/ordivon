from __future__ import annotations

import hashlib
import json
import sqlite3
import time
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .slice1 import ServiceEvent, ServiceEventStore
from .task_runtime import (
    Assignment,
    AssignmentStore,
    RuntimeJobObservation,
    SemanticVerdict,
    TaskStore,
)


def _now_ns() -> int:
    return time.time_ns()


def _id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex}"


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


def _require_artifact_reader(reader: Any) -> Any:
    if not callable(getattr(reader, "read", None)):
        raise TypeError("artifact reader must expose callable read()")
    return reader


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


def _verification_record_from_event(event: ServiceEvent) -> VerificationRecord:
    if event.aggregate_type != "Verification" or event.event_type != "VerificationRecorded":
        raise ValueError("event is not a VerificationRecord receipt")
    payload = event.payload
    if payload.get("assignmentId") != event.aggregate_id:
        raise RuntimeError("verification assignment identity mismatch")
    return VerificationRecord(
        id=event.id,
        task_id=payload["taskId"],
        assignment_id=event.aggregate_id,
        runtime_job_id=payload["runtimeJobId"],
        stage=payload["stage"],
        accepted=bool(payload["accepted"]),
        reason=payload.get("reason"),
        evidence=payload["evidence"],
        created_at_ns=event.created_at_ns,
    )


def _verification_record_get_by_assignment(
    events: ServiceEventStore,
    assignment_id: str,
) -> VerificationRecord | None:
    history = events.list_for("Verification", assignment_id)
    receipts = [item for item in history if item.event_type == "VerificationRecorded"]
    if not receipts:
        return None
    if len(receipts) != 1:
        raise RuntimeError("verification receipt stream contains multiple records")
    return _verification_record_from_event(receipts[0])


def _verification_record_list_for_task(
    events: ServiceEventStore,
    task_id: str,
) -> list[VerificationRecord]:
    records: list[VerificationRecord] = []
    for event in events.list_for("Task", task_id):
        if event.event_type != "TASK_VERIFIED":
            continue
        verification_id = event.payload.get("verificationId")
        if not isinstance(verification_id, str) or not verification_id:
            raise RuntimeError("TASK_VERIFIED event lacks verification identity")
        records.append(_verification_record_from_event(events.get(verification_id)))
    return records


def _verification_record_create_in_transaction(
    events: ServiceEventStore,
    *,
    task_id: str,
    assignment_id: str,
    runtime_job_id: str,
    stage: str,
    accepted: bool,
    reason: str | None,
    evidence: dict[str, Any],
) -> VerificationRecord:
    canonical_evidence = json.loads(json.dumps(evidence, sort_keys=True, separators=(",", ":"), ensure_ascii=False))
    event = events.append_once_in_transaction(
        "Verification",
        assignment_id,
        "VerificationRecorded",
        {
            "taskId": task_id,
            "assignmentId": assignment_id,
            "runtimeJobId": runtime_job_id,
            "stage": stage,
            "accepted": bool(accepted),
            "reason": reason,
            "evidence": canonical_evidence,
        },
    )
    return _verification_record_from_event(event)


class AssignmentExecutionActivator:
    """N15 narrowed for R6: bind execution only; never decides completion."""

    def __init__(
        self,
        connection: sqlite3.Connection,
        tasks: TaskStore,
        assignments: AssignmentStore,
        events: ServiceEventStore,
        runtime: Any,
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


def _evaluate_runtime_evidence_gate(
    observation: RuntimeJobObservation,
) -> SemanticVerdict | None:
    """Mechanical truth gate before any semantic evidence is interpreted."""
    if observation.semantic_completion_evaluated is not False:
        raise RuntimeError("Runtime crossed semantic-completion authority boundary")
    if not observation.execution_terminal:
        return None
    if observation.status != "succeeded":
        return SemanticVerdict(False, f"runtime:{observation.status}")
    if observation.delivery_disposition != "committed":
        return SemanticVerdict(False, f"runtime:delivery:{observation.delivery_disposition}")
    return SemanticVerdict(True, None)


def _resolve_evidence(
    artifact_reader: Any,
    acceptance: dict[str, Any],
    observation: RuntimeJobObservation,
) -> EvidenceBundle:
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
        payload = artifact_reader.read(observation.job_id, descriptor.artifact_id)
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

def _verify_evidence_semantics(
    acceptance: dict[str, Any],
    evidence: EvidenceBundle,
) -> SemanticVerdict:
    """Pure semantic verifier over normalized evidence, not Runtime process state."""
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
        runtime: Any,
        artifact_reader: Any,
    ) -> None:
        artifact_reader = _require_artifact_reader(artifact_reader)
        self._connection = connection
        self._tasks = tasks
        self._assignments = assignments
        self._events = events
        self._runtime = runtime
        self._artifact_reader = artifact_reader

    def reconcile(self, assignment_id: str) -> Assignment:
        assignment = self._assignments.get(assignment_id)
        task = self._tasks.get(assignment.task_id)
        existing = _verification_record_get_by_assignment(self._events, assignment.id)
        if existing is not None:
            return assignment
        if assignment.runtime_job_id is None:
            raise RuntimeError("completion reconciliation requires a Runtime Job binding")
        if task.state != "RUNNING":
            if task.state in {"SUCCEEDED", "FAILED", "CANCELLED"}:
                return assignment
            raise RuntimeError(f"completion cannot reconcile Task state {task.state}")

        observation = self._runtime.observe(assignment.runtime_job_id)
        mechanical = _evaluate_runtime_evidence_gate(observation)
        if mechanical is None:
            return assignment

        if mechanical.accepted:
            evidence = _resolve_evidence(self._artifact_reader, task.acceptance, observation)
            verdict = _verify_evidence_semantics(task.acceptance, evidence)
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
            record = _verification_record_create_in_transaction(
                self._events,
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
