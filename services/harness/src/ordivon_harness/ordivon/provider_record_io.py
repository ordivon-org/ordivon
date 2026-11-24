"""Original Provider source, record and replay-state binding.

Composed by the original Run facade: one Store, one Run lease discipline,
no additional Writer or authority.
"""
from __future__ import annotations
from anc_canonical import JsonValue
from ..protocol import (
    HarnessProviderCallFailureReceipt,
    HarnessProviderCallSource,
    HarnessProviderCallStatus,
)
from ..run_state import HarnessRunState
from ..store import (
    HarnessRunEventRecord,
    StoredHarnessObject,
)
from .continuity_records import (
    HarnessProviderCallRecordV3,
    HarnessProviderCallRecordV4,
    build_provider_call_record_v4,
)
from .model import (
    AgentTurnRequest,
    AgentTurnResult,
)
from .provider_record_reader import read_provider_record
from .provider_state_guards import (
    require_provider_continuation_state,
)
from .run_store_port import (
    HarnessProviderCallRequestMismatch,
    HarnessSuperseded,
    HarnessProviderCallSourceRef,
    StoredHarnessProviderCall,
    StoredHarnessRunSnapshot,
)




class ProviderRecordIO:
    """Original Provider source, record and replay-state binding."""

    @property
    def provider_outcome_requires_resume(self) -> bool:
        if self._provider_outcome_requires_resume:
            return True
        current = self._load_current_provider_call_or_none()
        return bool(
            current is not None and current.record.status is HarnessProviderCallStatus.UNKNOWN
        )

    def assignment_provider_source(self) -> HarnessProviderCallSourceRef:
        projection = self.store.load_run(self.harness_run_id)
        return HarnessProviderCallSourceRef(
            HarnessProviderCallSource.ASSIGNMENT,
            self.contract.digest,
            projection.contract_object_digest,
        )

    @staticmethod
    def snapshot_provider_source(
        retained: StoredHarnessRunSnapshot,
    ) -> HarnessProviderCallSourceRef:
        return HarnessProviderCallSourceRef(
            HarnessProviderCallSource.SNAPSHOT,
            retained.snapshot.digest,
            retained.snapshot_object.digest,
        )

    def load_current_provider_call(self) -> StoredHarnessProviderCall:
        retained = self._load_current_provider_call_or_none()
        if retained is None:
            raise KeyError("Harness Run has no active Provider Call")
        return retained

    def load_provider_replay_state(
        self,
        *,
        source: HarnessProviderCallSourceRef,
        snapshot: StoredHarnessRunSnapshot,
        additional_messages: tuple[dict[str, JsonValue], ...],
        adapter_id: str,
        requested_model_id: str,
    ) -> HarnessRunState | None:
        if source != self.snapshot_provider_source(snapshot):
            raise HarnessProviderCallRequestMismatch(
                "Provider Call resume source differs from the retained Snapshot"
            )
        self._require_provider_source_current(source)
        active = self._load_current_provider_call_or_none()
        if active is None or active.record.status not in {
            HarnessProviderCallStatus.CLAIMED,
            HarnessProviderCallStatus.COMPLETED,
            HarnessProviderCallStatus.FAILED,
            HarnessProviderCallStatus.UNKNOWN,
        }:
            return None
        record = active.record
        if (
            record.source_kind is not source.kind
            or record.source_digest != source.digest
            or record.source_object_digest != source.object_digest
            or record.adapter_id != adapter_id
            or record.requested_model_id != requested_model_id
        ):
            raise HarnessProviderCallRequestMismatch(
                "Provider Call differs from the requested resume identity"
            )
        require_provider_continuation_state(
            record,
            snapshot_state=snapshot.state,
            provider_state=active.state,
            additional_messages=additional_messages,
            max_model_calls=self.contract.budget.get("maxModelCalls"),
        )
        return active.state

    def _load_current_provider_call_or_none(
        self,
    ) -> StoredHarnessProviderCall | None:
        event = self._heads().provider
        return None if event is None else self._load_provider_from_event(event)

    def _load_provider_from_event(self, event: HarnessRunEventRecord) -> StoredHarnessProviderCall:
        return read_provider_record(self.store, self.binding, event)

    def _transition_provider_call(
        self,
        previous,
        *,
        status: HarnessProviderCallStatus,
        state_object_digest: str,
        recorded_at_ms: int,
        result_digest: str | None = None,
        result_object_digest: str | None = None,
        failure_digest: str | None = None,
        failure_object_digest: str | None = None,
    ) -> HarnessProviderCallRecordV4:
        return build_provider_call_record_v4(
            provider_call_id=previous.provider_call_id,
            harness_run_id=self.harness_run_id,
            binding_digest=self.binding.digest,
            source_kind=previous.source_kind,
            source_digest=previous.source_digest,
            source_object_digest=previous.source_object_digest,
            state_object_digest=state_object_digest,
            turn_id=previous.turn_id,
            turn_sequence=previous.turn_sequence,
            request_digest=previous.request_digest,
            request_object_digest=getattr(previous, "request_object_digest", None),
            provider_request_digest=previous.provider_request_digest,
            adapter_id=previous.adapter_id,
            requested_model_id=previous.requested_model_id,
            holder_id=previous.holder_id,
            generation=previous.claim_generation,
            status=status,
            result_digest=result_digest,
            result_object_digest=result_object_digest,
            failure_digest=failure_digest,
            failure_object_digest=failure_object_digest,
            previous_record_digest=previous.digest,
            issued_at_ms=previous.issued_at_ms,
            expires_at_ms=previous.expires_at_ms,
            recorded_at_ms=recorded_at_ms,
        )

    def _store_provider_call(
        self,
        record: HarnessProviderCallRecordV3 | HarnessProviderCallRecordV4,
        *,
        state_object: StoredHarnessObject,
        request: AgentTurnRequest | None = None,
        request_object: StoredHarnessObject | None = None,
        result: AgentTurnResult | None = None,
        result_object: StoredHarnessObject | None = None,
        failure: HarnessProviderCallFailureReceipt | None = None,
        failure_object: StoredHarnessObject | None = None,
    ) -> StoredHarnessProviderCall:
        if record.state_object_digest != state_object.digest:
            raise ValueError("Provider Call state object differs from its record")
        request_digest = getattr(record, "request_object_digest", None)
        if request_digest is None:
            if request is not None or request_object is not None:
                raise ValueError(
                    "Provider Call record without request-object binding cannot carry one"
                )
        else:
            if request is None or request_object is None:
                raise ValueError("Provider Call v3 exact request object is incomplete")
            if (
                request_object.digest != request_digest
                or request.dispatch_digest != record.request_digest
            ):
                raise ValueError("Provider Call exact request differs from its record")
        if (result is None) != (result_object is None):
            raise ValueError("Provider Call result object is incomplete")
        if result is not None and (
            record.result_digest != result.digest
            or record.result_object_digest != result_object.digest
        ):
            raise ValueError("Provider Call result differs from its record")
        if (
            result is None
            and record.result_digest is not None
            and not isinstance(record, HarnessProviderCallRecordV4)
        ):
            raise ValueError("Provider Call result content is missing from a non-redacted record")
        if (failure is None) != (failure_object is None):
            raise ValueError("Provider Call failure object is incomplete")
        if failure is not None and (
            record.failure_digest != failure.digest
            or record.failure_object_digest != failure_object.digest
        ):
            raise ValueError("Provider Call failure differs from its record")
        record_object = self.store.put_object(record.to_dict(), kind="harness-provider-call-record")
        return StoredHarnessProviderCall(
            record,
            record_object,
            self._state_for_object(state_object),
            state_object,
            result,
            result_object,
            failure,
            failure_object,
            request=request,
            request_object=request_object,
        )

    def _require_provider_source_current(self, source: HarnessProviderCallSourceRef) -> None:
        snapshot_event = self._heads().snapshot
        if source.kind is HarnessProviderCallSource.ASSIGNMENT:
            if snapshot_event is not None:
                raise HarnessSuperseded(
                    "initial Provider Call source was replaced by a Run Snapshot"
                )
            if source != self.assignment_provider_source():
                raise HarnessSuperseded("Provider Call Contract source is no longer current")
            return
        if snapshot_event is None:
            raise HarnessSuperseded("Provider Call Snapshot source is absent")
        if (
            snapshot_event.data.get("snapshotDigest") != source.digest
            or snapshot_event.data.get("snapshotObjectDigest") != source.object_digest
        ):
            raise HarnessSuperseded("Provider Call Snapshot source is no longer current")

    def _require_current_provider_call(self, expected) -> StoredHarnessProviderCall:
        current = self.load_current_provider_call()
        if current.record != expected:
            raise HarnessSuperseded("Harness Provider Call is no longer current")
        return current
