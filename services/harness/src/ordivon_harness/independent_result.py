from __future__ import annotations

from typing import Callable

from anc_canonical import JsonValue, canonical_digest

from .agent_tool_observation import HarnessArtifactReference, HarnessToolObservation
from .core_contracts import HarnessRunContract
from .independent_result_projection import (
    TRACE_EVENT_KIND as _TRACE_EVENT_KIND,
    IndependentCompletionProposal,
    IndependentHarnessRunReceipt,
    StoredIndependentRunResult,
    doctor_independent_result,
    load_independent_terminal_result,
    require_sha256_digest,
    stop_reason_for_stop_code,
    terminal_event_kind_for_stop_code,
)
from .store_errors import HarnessTerminalConflict
from .ordivon.events import HarnessRunEvent, HarnessTrace
from .ordivon.loop import AgentLoopResult, RunStopCode
from .ordivon.run_store_port import HarnessRunStoreBinding
from .store import (
    HarnessEventAdmission,
    HarnessStore,
    HarnessRunStatus,
    StoredHarnessObject,
    new_execution_owner_id,
)

_STORE_LEASE_TTL_MS = 30_000
_PAUSED_CODES = frozenset({RunStopCode.NEEDS_INPUT})


class IndependentRunRecorder:
    """Admit owner-native terminal and recovery evidence to one Harness Journal."""

    def __init__(
        self,
        store: HarnessStore,
        contract: HarnessRunContract,
        binding: HarnessRunStoreBinding,
        *,
        clock_ms: Callable[[], int],
    ) -> None:
        projection = store.load_run(contract.harness_run_id)
        if (
            projection.contract_digest != contract.digest
            or binding.harness_run_id != contract.harness_run_id
        ):
            raise ValueError("independent Run Recorder identities differ")
        self.store = store
        self.contract = contract
        self.binding = binding
        self.clock_ms = clock_ms
        self._execution_owner_id = new_execution_owner_id("independent-result")

    def _persistent_trace(self, trace: HarnessTrace) -> HarnessTrace:
        if self.contract.privacy.allow_model_content and self.contract.privacy.allow_tool_content:
            return trace
        events: list[HarnessRunEvent] = []
        for event in trace.events:
            payload = dict(event.payload)
            normalized_result = payload.get("normalizedResult")
            normalized_has_tool_calls = (
                isinstance(normalized_result, dict)
                and isinstance(normalized_result.get("toolCalls"), list)
                and bool(normalized_result["toolCalls"])
            )
            if (
                not self.contract.privacy.allow_model_content
                or not self.contract.privacy.allow_tool_content
                and normalized_has_tool_calls
            ):
                payload.pop("normalizedResult", None)
            if not self.contract.privacy.allow_tool_content:
                payload.pop("toolCall", None)
            if "detail" in payload and (
                not self.contract.privacy.allow_model_content
                or not self.contract.privacy.allow_tool_content
            ):
                detail = payload.pop("detail")
                payload["detailDigest"] = canonical_digest(detail)
            events.append(
                HarnessRunEvent(
                    sequence=event.sequence,
                    kind=event.kind,
                    occurred_at_ms=event.occurred_at_ms,
                    payload=payload,
                )
            )
        return HarnessTrace(trace.harness_run_id, tuple(events))

    def record_trace_segment(self, trace: HarnessTrace) -> HarnessEventAdmission:
        if trace.harness_run_id != self.contract.harness_run_id:
            raise ValueError("Harness Trace belongs to another Run")
        persistent_trace = self._persistent_trace(trace)
        events = self.store.list_run_events(self.contract.harness_run_id)
        existing = next(
            (
                event
                for event in events
                if event.event_kind == _TRACE_EVENT_KIND
                and event.data.get("traceDigest") == persistent_trace.digest
            ),
            None,
        )
        if existing is not None:
            raw = self.store.get_object(
                self._required_digest(existing.data, "traceObjectDigest"),
                expected_kind="harness-trace",
            )
            if not isinstance(raw, dict) or HarnessTrace.from_dict(raw) != persistent_trace:
                raise ValueError("existing Harness Trace segment differs")
            return HarnessEventAdmission.EXISTING
        now_ms = self._recorded_time(self.clock_ms())
        lease = self._acquire_lease("trace", persistent_trace.digest, now_ms=now_ms)
        try:
            stored = self.store.put_object(persistent_trace.to_dict(), kind="harness-trace")
            return self.store.append_event(
                event_id=self._event_id("trace", persistent_trace.digest),
                harness_run_id=self.contract.harness_run_id,
                event_kind=_TRACE_EVENT_KIND,
                data={
                    "traceDigest": persistent_trace.digest,
                    "traceObjectDigest": stored.digest,
                    "segmentIndex": 1
                    + sum(event.event_kind == _TRACE_EVENT_KIND for event in events),
                },
                expected_revision=lease.run_revision,
                recorded_at_ms=now_ms,
                lease=lease,
                lease_checked_at_ms=self.clock_ms(),
                caused_by_event_id=None if not events else events[-1].event_id,
                referenced_objects=(stored,),
            )
        finally:
            self.store.release_run_lease(lease)

    def record_result(
        self,
        result: AgentLoopResult,
        *,
        started_at_ms: int,
        finished_at_ms: int | None = None,
    ) -> StoredIndependentRunResult | None:
        if result.harness_run_id != self.contract.harness_run_id:
            raise ValueError("Agent Loop result belongs to another Harness Run")
        self.record_trace_segment(result.trace)
        if result.stop_code in _PAUSED_CODES:
            return None
        # Tool UNKNOWN is recoverable only when the ORIGINAL Run's own
        # durable Effect-Dispatch-Pending pause exists. Other runtime
        # unknowns keep their existing stop/terminal semantics.
        if result.stop_code in {RunStopCode.RUNTIME_UNKNOWN, RunStopCode.CANCEL_UNKNOWN}:
            original = self.store.load_run(self.contract.harness_run_id)
            if original.status is HarnessRunStatus.PAUSED:
                pauses = (
                    event
                    for event in reversed(self.store.list_run_events(self.contract.harness_run_id))
                    if event.event_kind == "harness.run-paused"
                )
                latest_pause = next(pauses, None)
                if (
                    latest_pause is not None
                    and latest_pause.data.get("pauseReason") == "effect-dispatch-pending"
                ):
                    return None
        finished = self.clock_ms() if finished_at_ms is None else finished_at_ms
        if started_at_ms < 0 or finished < started_at_ms:
            raise ValueError("independent Run recording times are invalid")
        projection = self.store.load_run(self.contract.harness_run_id)
        if projection.status.terminal:
            existing = self.load_terminal_result()
            candidate = self._build_receipt(result, started_at_ms, finished, trace=existing.trace)
            if existing.receipt.digest != candidate.digest:
                raise ValueError("terminal Harness Run differs from replayed result")
            return existing

        trace = self._combined_trace()
        conclusion = result.conclusion
        conclusion_digest = None if conclusion is None else canonical_digest(conclusion.to_dict())
        receipt = self._build_receipt(
            result,
            started_at_ms,
            finished,
            trace=trace,
            conclusion_digest=conclusion_digest,
        )
        observations = tuple(
            HarnessToolObservation.from_dict(item.to_dict()) for item in result.observations
        )
        now_ms = self._recorded_time(finished)
        lease = self._acquire_lease("terminal", receipt.digest, now_ms=now_ms)
        terminal_blocker: HarnessTerminalConflict | None = None
        try:
            trace_object = self.store.put_object(trace.to_dict(), kind="harness-trace")
            persistent_observations = (
                observations if self.contract.privacy.allow_tool_content else ()
            )
            observations_object = self.store.put_object(
                [item.to_dict() for item in persistent_observations],
                kind="harness-tool-observations",
            )
            conclusion_object = (
                None
                if conclusion is None or not self.contract.privacy.allow_model_content
                else self.store.put_object(conclusion.to_dict(), kind="harness-run-conclusion")
            )
            receipt_object = self.store.put_object(
                receipt.to_dict(), kind="independent-harness-run-receipt"
            )
            proposal = self._build_completion_proposal(receipt, result, now_ms)
            proposal_object = (
                None
                if proposal is None or not self.contract.privacy.allow_model_content
                else self.store.put_object(
                    proposal.to_dict(), kind="independent-completion-proposal"
                )
            )
            references = [trace_object, observations_object, receipt_object]
            if conclusion_object is not None:
                references.append(conclusion_object)
            if proposal_object is not None:
                references.append(proposal_object)
            events = self.store.list_run_events(self.contract.harness_run_id)
            try:
                self.store.append_event(
                    event_id=self._event_id("terminal", receipt.digest),
                    harness_run_id=self.contract.harness_run_id,
                    event_kind=terminal_event_kind_for_stop_code(result.stop_code),
                    data=self._terminal_data(
                        result,
                        receipt,
                        receipt_object,
                        trace,
                        trace_object,
                        observations_object,
                        conclusion_digest,
                        conclusion_object,
                        proposal,
                        proposal_object,
                    ),
                    expected_revision=lease.run_revision,
                    recorded_at_ms=now_ms,
                    lease=lease,
                    lease_checked_at_ms=self.clock_ms(),
                    caused_by_event_id=None if not events else events[-1].event_id,
                    referenced_objects=tuple(references),
                )
            except HarnessTerminalConflict as error:
                # The original PG transaction rejected terminal admission.
                # Release its Lease *before* acquiring a second one for a
                # durable hold. Never bypass the original Journal guard.
                terminal_blocker = error
        finally:
            self.store.release_run_lease(lease)
        if terminal_blocker is not None:
            # A candidate claiming completion is not a recoverable pause
            # receipt. Surface the authoritative rejection rather than
            # returning a misleading candidate_completed loop conclusion.
            if result.stop_code is RunStopCode.CANDIDATE_COMPLETED:
                raise terminal_blocker
            from .ordivon.run_continuity import EventSourcedRunContinuity
            from .protocol import HarnessRunPauseReason, HarnessToolStepStatus

            continuity = EventSourcedRunContinuity.open(
                self.store, self.contract.harness_run_id, clock_ms=self.clock_ms
            )
            try:
                current_tool = continuity.load_current_tool_step()
            except KeyError:
                raise terminal_blocker from None
            if current_tool.receipt is not None and current_tool.receipt.status not in {
                HarnessToolStepStatus.UNKNOWN,
                HarnessToolStepStatus.CANCEL_REQUESTED,
            }:
                raise terminal_blocker
            # The original Prepared/UNKNOWN/CANCEL_REQUESTED Tool keeps its
            # exact Intent identity and retained State. The new PAUSED
            # snapshot is not a new physical effect or Runtime certificate.
            current_snapshot = continuity.load_current_snapshot()
            continuity.bind_state(current_snapshot.state)
            continuity.record_pause(HarnessRunPauseReason.EFFECT_DISPATCH_PENDING)
            return None
        return self.load_terminal_result()

    def load_terminal_result(self) -> StoredIndependentRunResult:
        return load_independent_terminal_result(self.store, self.contract)

    def doctor(self) -> dict[str, JsonValue]:
        return doctor_independent_result(self.store, self.contract)

    def _combined_trace(self) -> HarnessTrace:
        combined: list[HarnessRunEvent] = []
        for event in self.store.list_run_events(self.contract.harness_run_id):
            if event.event_kind != _TRACE_EVENT_KIND:
                continue
            raw = self.store.get_object(
                self._required_digest(event.data, "traceObjectDigest"),
                expected_kind="harness-trace",
            )
            if not isinstance(raw, dict):
                raise ValueError("Harness Trace segment object is invalid")
            segment = HarnessTrace.from_dict(raw)
            if segment.harness_run_id != self.contract.harness_run_id:
                raise ValueError("Harness Trace belongs to another Run")
            if segment.digest != event.data.get("traceDigest"):
                raise ValueError("Harness Trace segment digest differs")
            for item in segment.events:
                combined.append(
                    HarnessRunEvent(
                        sequence=len(combined) + 1,
                        kind=item.kind,
                        occurred_at_ms=item.occurred_at_ms,
                        payload=item.payload,
                    )
                )
        if not combined:
            raise ValueError("independent terminal Run has no retained Trace segment")
        return HarnessTrace(self.contract.harness_run_id, tuple(combined))

    def _build_receipt(
        self,
        result: AgentLoopResult,
        started_at_ms: int,
        finished_at_ms: int,
        *,
        trace: HarnessTrace | None = None,
        conclusion_digest: str | None = None,
    ) -> IndependentHarnessRunReceipt:
        retained_trace = result.trace if trace is None else trace
        artifacts: dict[str, HarnessArtifactReference] = {}
        jobs: set[str] = set()
        for observation in result.observations:
            if observation.runtime_job_ref is not None:
                jobs.add(observation.runtime_job_ref)
            for item in observation.artifact_refs:
                converted = HarnessArtifactReference(item.ref, item.kind, item.digest)
                existing = artifacts.get(converted.ref)
                if existing is not None and existing != converted:
                    raise ValueError("one Artifact reference resolves to conflicting evidence")
                artifacts[converted.ref] = converted
        return IndependentHarnessRunReceipt(
            harness_run_id=self.contract.harness_run_id,
            caller_id=self.contract.caller_id,
            caller_run_ref=self.contract.caller_run_ref,
            contract_digest=self.contract.digest,
            harness_implementation_id=self.contract.harness_implementation_id,
            system_manifest_digest=self.contract.system_manifest_ref.digest,
            started_at_ms=started_at_ms,
            finished_at_ms=finished_at_ms,
            stop_reason=stop_reason_for_stop_code(result.stop_code),
            termination_code=result.stop_code.value,
            trace_digest=retained_trace.digest,
            context_digests=tuple(item.digest for item in self.contract.context_refs),
            tool_catalog_digest=self.contract.tool_catalog_digest,
            tool_grant_digest=self.contract.tool_grant_digest,
            runtime_job_refs=tuple(sorted(jobs)),
            artifact_refs=tuple(artifacts[key] for key in sorted(artifacts)),
            usage=result.usage,
            conclusion_digest=(
                conclusion_digest
                if conclusion_digest is not None
                else None
                if result.conclusion is None
                else canonical_digest(result.conclusion.to_dict())
            ),
        )

    def _build_completion_proposal(
        self,
        receipt: IndependentHarnessRunReceipt,
        result: AgentLoopResult,
        created_at_ms: int,
    ) -> IndependentCompletionProposal | None:
        if result.stop_code is not RunStopCode.CANDIDATE_COMPLETED:
            return None
        conclusion = result.conclusion
        if conclusion is None or conclusion.status != "candidate_completed":
            raise ValueError("candidate-completed Run omitted its candidate conclusion")
        token = canonical_digest(
            {
                "harnessRunId": self.contract.harness_run_id,
                "contractDigest": self.contract.digest,
                "runReceiptDigest": receipt.digest,
                "traceDigest": receipt.trace_digest,
            }
        )[7:31]
        return IndependentCompletionProposal(
            completion_proposal_id=f"completion-proposal:{token}",
            harness_run_id=self.contract.harness_run_id,
            caller_id=self.contract.caller_id,
            caller_run_ref=self.contract.caller_run_ref,
            contract_digest=self.contract.digest,
            run_receipt_digest=receipt.digest,
            trace_digest=receipt.trace_digest,
            summary=conclusion.summary,
            evidence_refs=conclusion.evidence_refs,
            artifact_refs=conclusion.artifact_refs,
            unresolved_unknowns=conclusion.unresolved_unknowns,
            usage=result.usage,
            created_at_ms=created_at_ms,
        )

    @staticmethod
    def _terminal_data(
        result: AgentLoopResult,
        receipt: IndependentHarnessRunReceipt,
        receipt_object: StoredHarnessObject,
        trace: HarnessTrace,
        trace_object: StoredHarnessObject,
        observations_object: StoredHarnessObject,
        conclusion_digest: str | None,
        conclusion_object: StoredHarnessObject | None,
        proposal: IndependentCompletionProposal | None,
        proposal_object: StoredHarnessObject | None,
    ) -> dict[str, JsonValue]:
        return {
            "stopCode": result.stop_code.value,
            "runReceiptDigest": receipt.digest,
            "runReceiptObjectDigest": receipt_object.digest,
            "traceDigest": trace.digest,
            "traceObjectDigest": trace_object.digest,
            "observationsObjectDigest": observations_object.digest,
            "conclusionDigest": conclusion_digest,
            "conclusionObjectDigest": None
            if conclusion_object is None
            else conclusion_object.digest,
            "completionProposalDigest": None if proposal is None else proposal.digest,
            "completionProposalObjectDigest": (
                None if proposal_object is None else proposal_object.digest
            ),
        }

    def _acquire_lease(self, operation: str, token: str, *, now_ms: int):
        owner = canonical_digest(
            {
                "harnessRunId": self.contract.harness_run_id,
                "operation": operation,
                "token": token,
            }
        )[7:31]
        return self.store.acquire_run_lease(
            self.contract.harness_run_id,
            owner_id=f"{self._execution_owner_id}:{operation}:{owner}",
            ttl_ms=_STORE_LEASE_TTL_MS,
            now_ms=now_ms,
        )

    def _recorded_time(self, proposed: int) -> int:
        events = self.store.list_run_events(self.contract.harness_run_id)
        return max(proposed, events[-1].recorded_at_ms if events else proposed)

    @staticmethod
    def _event_id(label: str, digest: str) -> str:
        return f"event:independent-{label}:{digest[7:31]}"

    @staticmethod
    def _required_digest(data: dict[str, JsonValue], field: str) -> str:
        value = data.get(field)
        if not isinstance(value, str):
            raise ValueError(f"Harness Event {field} is missing")
        return require_sha256_digest(value, f"Harness Event {field}")


__all__ = [
    "IndependentCompletionProposal",
    "IndependentHarnessRunReceipt",
    "IndependentRunRecorder",
    "StoredIndependentRunResult",
]
