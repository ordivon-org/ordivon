"""Read-only original PG terminal result, Trace and Doctor capability.

A Journal reader never writes Run/Tool events or imports EventSourcedRunContinuity.
The independent Writer may recover a terminal conflict through its natural
Journal command owner; source inspection consumes only this Reader.
"""

from __future__ import annotations

from typing import Any

from anc_canonical import JsonValue, canonical_digest

from .agent_tool_observation import HarnessToolObservation
from .core_contracts import HarnessRunContract
from .independent_result_contracts import (
    IndependentCompletionProposal,
    IndependentHarnessRunReceipt,
    StoredIndependentRunResult,
    _digest,
)
from .ordivon.events import HarnessRunEvent, HarnessTrace
from .ordivon.model import AgentRunConclusion
from .ordivon.run_contract import RunStopCode
from .ordivon.run_store_port import HarnessRunStoreBinding
from .store import HarnessStore

_TRACE_EVENT_KIND = "harness.trace-recorded"
_TERMINAL_EVENT_KINDS = frozenset(
    {"harness.run-completed", "harness.run-stopped", "harness.run-failed"}
)
_FAILED_CODES = frozenset(
    {
        RunStopCode.PROVIDER_FAILED,
        RunStopCode.PROVIDER_TIMEOUT,
        RunStopCode.PROVIDER_TRANSPORT_FAILED,
        RunStopCode.PROVIDER_REJECTED,
        RunStopCode.PROVIDER_UNAVAILABLE,
        RunStopCode.INVALID_TOOL_CALL,
        RunStopCode.INVALID_MODEL_OUTPUT,
        RunStopCode.HARNESS_FAILED,
    }
)

class IndependentRunReader:
    """One original Run's immutable terminal and trace evidence."""

    def __init__(
        self,
        store: HarnessStore,
        contract: HarnessRunContract,
        binding: HarnessRunStoreBinding,
        *,
        clock_ms,
    ) -> None:
        projection = store.load_run(contract.harness_run_id)
        if (
            projection.contract_digest != contract.digest
            or binding.harness_run_id != contract.harness_run_id
        ):
            raise ValueError("independent Run Reader identities differ")
        self.store = store
        self.contract = contract
        self.binding = binding
        self.clock_ms = clock_ms

    def load_terminal_result(self) -> StoredIndependentRunResult:
        terminal = next(
            (
                event
                for event in reversed(self.store.list_run_events(self.contract.harness_run_id))
                if event.event_kind in _TERMINAL_EVENT_KINDS
            ),
            None,
        )
        if terminal is None:
            raise KeyError("Harness Run has no independent terminal result")
        data = terminal.data
        receipt_object_digest = self._required_digest(data, "runReceiptObjectDigest")
        trace_object_digest = self._required_digest(data, "traceObjectDigest")
        observations_object_digest = self._required_digest(data, "observationsObjectDigest")
        raw_receipt = self.store.get_object(
            receipt_object_digest, expected_kind="independent-harness-run-receipt"
        )
        raw_trace = self.store.get_object(trace_object_digest, expected_kind="harness-trace")
        raw_observations = self.store.get_object(
            observations_object_digest, expected_kind="harness-tool-observations"
        )
        if (
            not isinstance(raw_receipt, dict)
            or not isinstance(raw_trace, dict)
            or not isinstance(raw_observations, list)
            or any(not isinstance(item, dict) for item in raw_observations)
        ):
            raise ValueError("independent terminal objects are invalid")
        receipt = IndependentHarnessRunReceipt.from_dict(raw_receipt)
        trace = HarnessTrace.from_dict(raw_trace)
        if trace.harness_run_id != self.contract.harness_run_id:
            raise ValueError("Harness Trace belongs to another Run")
        observations = tuple(HarnessToolObservation.from_dict(item) for item in raw_observations)
        conclusion = None
        conclusion_object = None
        conclusion_object_digest = data.get("conclusionObjectDigest")
        if conclusion_object_digest is not None:
            if not isinstance(conclusion_object_digest, str):
                raise ValueError("Harness conclusion object reference is invalid")
            raw_conclusion = self.store.get_object(
                conclusion_object_digest, expected_kind="harness-run-conclusion"
            )
            if not isinstance(raw_conclusion, dict):
                raise ValueError("Harness conclusion object is invalid")
            conclusion = AgentRunConclusion.from_dict(raw_conclusion)
            conclusion_object = self.store.inspect_object(conclusion_object_digest)
        proposal = None
        proposal_object = None
        raw_proposal: dict[str, Any] | None = None
        proposal_object_digest = data.get("completionProposalObjectDigest")
        if proposal_object_digest is not None:
            if not isinstance(proposal_object_digest, str):
                raise ValueError("Completion Proposal object reference is invalid")
            raw_proposal = self.store.get_object(
                proposal_object_digest, expected_kind="independent-completion-proposal"
            )
            if not isinstance(raw_proposal, dict):
                raise ValueError("Completion Proposal object is invalid")
            proposal = IndependentCompletionProposal.from_dict(raw_proposal)
            proposal_object = self.store.inspect_object(proposal_object_digest)
        conclusion_digest = data.get("conclusionDigest")
        if conclusion_digest is not None:
            if not isinstance(conclusion_digest, str):
                raise ValueError("Harness conclusion digest is invalid")
            _digest(conclusion_digest, "Harness conclusion digest")
        proposal_digest = data.get("completionProposalDigest")
        if proposal_digest is not None:
            if not isinstance(proposal_digest, str):
                raise ValueError("Completion Proposal digest is invalid")
            _digest(proposal_digest, "Completion Proposal digest")
        if (
            receipt.digest != data.get("runReceiptDigest")
            or trace.digest != data.get("traceDigest")
            or receipt.trace_digest != trace.digest
            or receipt.contract_digest != self.contract.digest
            or receipt.harness_run_id != self.contract.harness_run_id
            or receipt.conclusion_digest != conclusion_digest
            or (proposal_digest is not None) != (receipt.stop_reason == "completed")
        ):
            raise ValueError("independent terminal evidence bindings differ")
        if conclusion is not None and canonical_digest(conclusion.to_dict()) != conclusion_digest:
            raise ValueError("Harness conclusion differs from its digest")
        if (
            conclusion is None
            and conclusion_digest is not None
            and self.contract.privacy.allow_model_content
        ):
            raise ValueError("authorized Harness conclusion content is missing")
        if proposal is not None and (
            # A v1 proposal has no unresolvedUnknowns. Its persisted digest
            # binds the original v1 wire object, not the upgraded v2 view.
            canonical_digest(raw_proposal) != proposal_digest
            or proposal.run_receipt_digest != receipt.digest
            or proposal.trace_digest != trace.digest
            or proposal.contract_digest != self.contract.digest
        ):
            raise ValueError("Completion Proposal bindings differ")
        if proposal is not None and (
            proposal.harness_run_id != receipt.harness_run_id
            or proposal.caller_id != receipt.caller_id
            or proposal.caller_run_ref != receipt.caller_run_ref
        ):
            raise ValueError("Completion Proposal identity differs from Run Receipt")
        if (
            proposal is not None
            and conclusion is not None
            and (
                conclusion.status != "candidate_completed"
                or proposal.summary != conclusion.summary
                or proposal.evidence_refs != conclusion.evidence_refs
                or proposal.artifact_refs != conclusion.artifact_refs
                or proposal.usage != receipt.usage
                or (
                    raw_proposal is not None
                    and (raw_proposal["schemaVersion"] == 2 or bool(conclusion.unresolved_unknowns))
                    and proposal.unresolved_unknowns != conclusion.unresolved_unknowns
                )
            )
        ):
            raise ValueError("Completion Proposal claims differ from source conclusion")
        if (
            proposal is None
            and proposal_digest is not None
            and self.contract.privacy.allow_model_content
        ):
            raise ValueError("authorized Completion Proposal content is missing")
        if not self.contract.privacy.allow_tool_content and observations:
            raise ValueError("metadata-only terminal evidence retained Tool content")
        if terminal.event_kind != self._terminal_event_kind(RunStopCode(receipt.termination_code)):
            raise ValueError("terminal Event kind differs from Run Receipt")
        return StoredIndependentRunResult(
            receipt=receipt,
            receipt_object=self.store.inspect_object(receipt_object_digest),
            trace=trace,
            trace_object=self.store.inspect_object(trace_object_digest),
            observations=observations,
            observations_object=self.store.inspect_object(observations_object_digest),
            conclusion=conclusion,
            conclusion_object=conclusion_object,
            completion_proposal=proposal,
            completion_proposal_object=proposal_object,
        )

    def doctor(self) -> dict[str, JsonValue]:
        trace_segments = 0
        terminal_results = 0
        for event in self.store.list_run_events(self.contract.harness_run_id):
            if event.event_kind == _TRACE_EVENT_KIND:
                raw = self.store.get_object(
                    self._required_digest(event.data, "traceObjectDigest"),
                    expected_kind="harness-trace",
                )
                if not isinstance(raw, dict):
                    raise ValueError("Harness Trace object is invalid")
                trace = HarnessTrace.from_dict(raw)
                if trace.harness_run_id != self.contract.harness_run_id:
                    raise ValueError("Harness Trace belongs to another Run")
                if trace.digest != event.data.get("traceDigest"):
                    raise ValueError("Harness Trace Event digest differs")
                trace_segments += 1
            elif event.event_kind in _TERMINAL_EVENT_KINDS:
                self.load_terminal_result()
                terminal_results += 1
        return {
            "schemaVersion": 1,
            "kind": "ordivon.independent-run-doctor",
            "healthy": True,
            "harnessRunId": self.contract.harness_run_id,
            "traceSegments": trace_segments,
            "terminalResults": terminal_results,
        }

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

    @staticmethod
    def _terminal_event_kind(code: RunStopCode) -> str:
        if code is RunStopCode.CANDIDATE_COMPLETED:
            return "harness.run-completed"
        if code in _FAILED_CODES:
            return "harness.run-failed"
        return "harness.run-stopped"

    @staticmethod
    def _required_digest(data: dict[str, JsonValue], field: str) -> str:
        value = data.get(field)
        if not isinstance(value, str):
            raise ValueError(f"Harness Event {field} is missing")
        return _digest(value, f"Harness Event {field}")
