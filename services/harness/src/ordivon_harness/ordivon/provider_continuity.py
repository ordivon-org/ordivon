"""Original Provider claim, dispatch, outcome and retry admission.

Composed by the original Run facade: one Store, one Run lease discipline,
no additional Writer or authority.
"""
from __future__ import annotations
import time
from anc_canonical import canonical_digest
from ..protocol import (
    HarnessProviderCallFailureReceipt,
    HarnessProviderCallStatus,
)
from ..store_errors import (
    HarnessLeaseHeld,
)
from ..store import (
    HarnessRunLease,
)
from .continuity_guards import (
    continuity_event_id,
    inspect_all_unsettled_effect_sources,
)
from .continuity_records import (
    build_provider_call_record_v4,
)
from .model import (
    AgentTurnRequest,
    AgentTurnResult,
)
from .provider_state_guards import (
    _require_provider_request_matches,
    _require_provider_outcome_state,
    _require_provider_safe_retry_state,
    _require_provider_time_monotonic,
    _require_failure_matches,
)
from .run_store_port import (
    HarnessProviderCallClaimHeld,
    HarnessProviderCallRecoveryRequired,
    HarnessProviderCallRequestMismatch,
    HarnessSuperseded,
    HarnessProviderCallSourceRef,
    StoredHarnessProviderCall,
)


_PROVIDER_DISPATCH_LEASE_WAIT_SECONDS = 1.0
_PROVIDER_DISPATCH_LEASE_RETRY_SECONDS = 0.001
_PROVIDER_OUTCOME_LEASE_WAIT_SECONDS = 1.0
_PROVIDER_OUTCOME_LEASE_RETRY_SECONDS = 0.001


class ProviderContinuityCommands:
    """Original Provider claim, dispatch, outcome and retry admission."""

    def claim_provider_call(
        self,
        *,
        source: HarnessProviderCallSourceRef,
        turn_id: str,
        turn_sequence: int,
        request_digest: str,
        provider_request_digest: str,
        adapter_id: str,
        requested_model_id: str,
        holder_id: str,
        ttl_ms: int,
        request: AgentTurnRequest | None = None,
    ) -> StoredHarnessProviderCall:
        if ttl_ms < 1:
            raise ValueError("Provider Call claim TTL must be positive")
        if request is not None and (
            request.harness_run_id != self.harness_run_id
            or request.turn_id != turn_id
            or request.sequence != turn_sequence
            or request.dispatch_digest != request_digest
        ):
            raise HarnessProviderCallRequestMismatch(
                "exact Agent Turn request differs from Provider Call claim identity"
            )
        state = self._require_state()
        state_object = self._put_state(state)
        request_object = (
            None
            if request is None
            else self.store.put_object(request.to_dict(), kind="agent-turn-request")
        )
        now_ms = self.clock_ms()
        provider_call_id = self._provider_call_id(source, turn_sequence)
        active_before_lease = self._load_current_provider_call_or_none()
        if (
            active_before_lease is not None
            and active_before_lease.record.provider_call_id == provider_call_id
        ):
            previous_before_lease = active_before_lease.record
            _require_provider_request_matches(
                previous_before_lease,
                source=source,
                turn_id=turn_id,
                turn_sequence=turn_sequence,
                request_digest=request_digest,
                provider_request_digest=provider_request_digest,
                request_object_digest=(None if request_object is None else request_object.digest),
                adapter_id=adapter_id,
                requested_model_id=requested_model_id,
            )
            if previous_before_lease.status is HarnessProviderCallStatus.DISPATCHING:
                raise HarnessProviderCallRecoveryRequired(
                    "Provider Call may already have been dispatched; explicit reconciliation is required"
                )
            if (
                previous_before_lease.status is HarnessProviderCallStatus.CLAIMED
                and previous_before_lease.holder_id != holder_id
                and now_ms <= previous_before_lease.expires_at_ms
            ):
                raise HarnessProviderCallClaimHeld(
                    "Provider Call is claimed by another Harness execution"
                )
        try:
            lease = self._acquire_lease("provider-claim", provider_call_id, now_ms=now_ms)
        except HarnessLeaseHeld as error:
            raise HarnessProviderCallClaimHeld(
                "Provider Call claim is being admitted by another execution"
            ) from error
        try:
            self._require_provider_source_current(source)
            self._require_current_working_view_request(request)
            active = self._load_current_provider_call_or_none()
            previous = None
            generation = 1
            event_kind = "harness.provider-call-claimed"
            if active is not None:
                previous = active.record
                if previous.provider_call_id == provider_call_id:
                    _require_provider_request_matches(
                        previous,
                        source=source,
                        turn_id=turn_id,
                        turn_sequence=turn_sequence,
                        request_digest=request_digest,
                        provider_request_digest=provider_request_digest,
                        request_object_digest=(
                            None if request_object is None else request_object.digest
                        ),
                        adapter_id=adapter_id,
                        requested_model_id=requested_model_id,
                    )
                    if previous.status in {
                        HarnessProviderCallStatus.COMPLETED,
                        HarnessProviderCallStatus.FAILED,
                        HarnessProviderCallStatus.UNKNOWN,
                    }:
                        return active
                    if previous.status is HarnessProviderCallStatus.CLAIMED:
                        if previous.holder_id == holder_id:
                            if active.state_object.digest != state_object.digest:
                                raise HarnessProviderCallRequestMismatch(
                                    "Provider Call claimant state differs from its durable claim"
                                )
                            return active
                        if now_ms <= previous.expires_at_ms:
                            raise HarnessProviderCallClaimHeld(
                                "Provider Call is claimed by another Harness execution"
                            )
                        _require_provider_outcome_state(
                            active.state,
                            state,
                            label="expired Provider Call claim",
                        )
                        generation = previous.claim_generation + 1
                        event_kind = "harness.provider-call-superseded"
                    elif previous.status is HarnessProviderCallStatus.DISPATCHING:
                        raise HarnessProviderCallRecoveryRequired(
                            "Provider Call may already have been dispatched; explicit reconciliation is required"
                        )
                    else:
                        raise HarnessProviderCallRecoveryRequired(
                            "Provider Call has a terminal attempt that was not consumed"
                        )
                elif (
                    previous.status is HarnessProviderCallStatus.COMPLETED
                    and previous.source_kind is source.kind
                    and previous.source_digest == source.digest
                    and previous.source_object_digest == source.object_digest
                    and turn_sequence == previous.turn_sequence + 1
                ):
                    _require_provider_time_monotonic(
                        active.state,
                        state,
                        label="next-turn Provider Call",
                    )
                else:
                    raise HarnessProviderCallRecoveryRequired(
                        "another Provider Call record is still active"
                    )
            # Exact same-Provider replay can return the already committed
            # record above without new dispatch authority. Guard only NEW
            # Claim/Supersede Journal Events against every other unresolved
            # Provider and Tool in the original PG history. This is inside
            # the original PG Lease, so the admission read and append cannot
            # race another Writer on this Run.
            verified_projection, verified_events = self._read_verified_source_cut()
            if verified_projection.revision != lease.run_revision:
                raise HarnessProviderCallRecoveryRequired(
                    "Run changed during new Provider admission"
                )
            unsettled_providers, unsettled_tools = inspect_all_unsettled_effect_sources(
                verified_events,
                store=self.store,
                harness_run_id=self.harness_run_id,
                binding=self.binding,
                allow_tool_content=self.contract.privacy.allow_tool_content,
                provider_record_reader=self._load_provider_from_event,
            )
            if unsettled_tools:
                raise HarnessProviderCallRecoveryRequired(
                    "unresolved Tool Step remains in original PG history; "
                    "new Provider Call needs exact Owner reconciliation"
                )
            if any(identity != provider_call_id for identity in unsettled_providers):
                raise HarnessProviderCallRecoveryRequired(
                    "unresolved previous Provider Call remains in original PG history; "
                    "new Provider Call needs exact Owner reconciliation"
                )
            recorded_at_ms = self._recorded_time(
                now_ms,
                previous_recorded_at_ms=(None if previous is None else previous.recorded_at_ms),
            )
            record = build_provider_call_record_v4(
                provider_call_id=provider_call_id,
                harness_run_id=self.harness_run_id,
                binding_digest=self.binding.digest,
                source_kind=source.kind,
                source_digest=source.digest,
                source_object_digest=source.object_digest,
                state_object_digest=state_object.digest,
                turn_id=turn_id,
                turn_sequence=turn_sequence,
                request_digest=request_digest,
                request_object_digest=(None if request_object is None else request_object.digest),
                provider_request_digest=provider_request_digest,
                adapter_id=adapter_id,
                requested_model_id=requested_model_id,
                holder_id=holder_id,
                generation=generation,
                status=HarnessProviderCallStatus.CLAIMED,
                result_digest=None,
                result_object_digest=None,
                failure_digest=None,
                failure_object_digest=None,
                previous_record_digest=(None if previous is None else previous.digest),
                issued_at_ms=now_ms,
                expires_at_ms=now_ms + ttl_ms,
                recorded_at_ms=recorded_at_ms,
            )
            stored = self._store_provider_call(
                record,
                state_object=state_object,
                request=request,
                request_object=request_object,
            )
            self._append_provider_event(
                lease=lease,
                event_kind=event_kind,
                stored=stored,
                caused_by_event_id=(
                    None
                    if previous is None
                    else self._provider_event_id_for_digest(previous.digest)
                ),
            )
            return stored
        finally:
            self.store.release_run_lease(lease)

    def mark_provider_call_dispatching(
        self,
        retained: StoredHarnessProviderCall,
    ) -> StoredHarnessProviderCall:
        lease = self._acquire_provider_dispatch_lease(retained)
        now_ms = self.clock_ms()
        try:
            current = self._require_current_provider_call(retained.record)
            if current.record.status is not HarnessProviderCallStatus.CLAIMED:
                if current.record.status is HarnessProviderCallStatus.COMPLETED:
                    return current
                raise HarnessProviderCallRecoveryRequired(
                    "Provider Call cannot dispatch from its current state"
                )
            if now_ms > current.record.expires_at_ms:
                raise HarnessProviderCallClaimHeld(
                    "Provider Call claim expired before physical dispatch"
                )
            state = self._require_state()
            _require_provider_outcome_state(
                current.state,
                state,
                label="Provider Call dispatch admission",
            )
            state_object = self._put_state(state)
            record = self._transition_provider_call(
                current.record,
                status=HarnessProviderCallStatus.DISPATCHING,
                state_object_digest=state_object.digest,
                recorded_at_ms=self._recorded_time(
                    now_ms,
                    previous_recorded_at_ms=current.record.recorded_at_ms,
                ),
            )
            stored = self._store_provider_call(
                record,
                state_object=state_object,
                request=current.request,
                request_object=current.request_object,
            )
            self._append_provider_event(
                lease=lease,
                event_kind="harness.provider-call-dispatching",
                stored=stored,
                caused_by_event_id=self._provider_event_id_for_digest(current.record.digest),
            )
            return stored
        finally:
            self.store.release_run_lease(lease)

    def complete_provider_call(
        self,
        retained: StoredHarnessProviderCall,
        result: AgentTurnResult,
    ) -> StoredHarnessProviderCall:
        self._provider_outcome_requires_resume = False

        def matches(existing: StoredHarnessProviderCall) -> bool:
            return existing.record.result_digest == result.digest and (
                existing.record == retained.record
                or existing.record.previous_record_digest == retained.record.digest
            )

        existing = self.load_current_provider_call()
        if existing.record.status is HarnessProviderCallStatus.COMPLETED:
            if matches(existing):
                return existing
            raise HarnessProviderCallRequestMismatch(
                "another Provider result already completed this call"
            )
        preflight = self._require_current_provider_call(retained.record)
        if preflight.record.status is not HarnessProviderCallStatus.DISPATCHING:
            raise HarnessProviderCallRecoveryRequired(
                "Provider result arrived without a current dispatch record"
            )
        lease = self._acquire_provider_outcome_lease("provider-complete", retained)
        now_ms = self.clock_ms()
        try:
            current = self.load_current_provider_call()
            if current.record.status is HarnessProviderCallStatus.COMPLETED:
                if matches(current):
                    return current
                raise HarnessProviderCallRequestMismatch(
                    "another Provider result already completed this call"
                )
            if current.record != retained.record:
                raise HarnessSuperseded("Harness Provider Call is no longer current")
            if current.record.status is not HarnessProviderCallStatus.DISPATCHING:
                raise HarnessProviderCallRecoveryRequired(
                    "Provider result arrived without a current dispatch record"
                )
            state = self._require_state()
            _require_provider_outcome_state(current.state, state)
            state_object = self._put_state(state)
            retain_result = self.contract.privacy.allow_model_content and (
                self.contract.privacy.allow_tool_content or not result.tool_calls
            )
            result_object = (
                self.store.put_object(result.to_dict(), kind="agent-turn-result")
                if retain_result
                else None
            )
            record = self._transition_provider_call(
                current.record,
                status=HarnessProviderCallStatus.COMPLETED,
                state_object_digest=state_object.digest,
                result_digest=result.digest,
                result_object_digest=(None if result_object is None else result_object.digest),
                recorded_at_ms=self._recorded_time(
                    now_ms,
                    previous_recorded_at_ms=current.record.recorded_at_ms,
                ),
            )
            stored = self._store_provider_call(
                record,
                state_object=state_object,
                request=current.request,
                request_object=current.request_object,
                result=(result if result_object is not None else None),
                result_object=result_object,
            )
            self._append_provider_event(
                lease=lease,
                event_kind="harness.provider-call-completed",
                stored=stored,
                caused_by_event_id=self._provider_event_id_for_digest(current.record.digest),
            )
            return stored
        finally:
            self.store.release_run_lease(lease)

    def fail_provider_call(
        self,
        retained: StoredHarnessProviderCall,
        *,
        failure: HarnessProviderCallFailureReceipt,
    ) -> StoredHarnessProviderCall:
        self._provider_outcome_requires_resume = False
        lease = self._acquire_provider_outcome_lease("provider-fail", retained)
        now_ms = self.clock_ms()
        try:
            current = self.load_current_provider_call()
            if current.record.status in {
                HarnessProviderCallStatus.FAILED,
                HarnessProviderCallStatus.UNKNOWN,
            }:
                if (
                    current.record.previous_record_digest == retained.record.digest
                    and current.failure == failure
                ):
                    return current
                raise HarnessProviderCallRecoveryRequired(
                    "another Provider failure already completed this call"
                )
            if current.record != retained.record:
                raise HarnessSuperseded("Harness Provider Call is no longer current")
            if current.record.status is not HarnessProviderCallStatus.DISPATCHING:
                raise HarnessProviderCallRecoveryRequired(
                    "Provider failure arrived without a current dispatch record"
                )
            _require_failure_matches(current.record, failure)
            state = self._require_state()
            _require_provider_outcome_state(current.state, state)
            state_object = self._put_state(state)
            failure_object = self.store.put_object(
                failure.to_dict(), kind="harness-provider-call-failure"
            )
            status = (
                HarnessProviderCallStatus.UNKNOWN
                if failure.dispatch_safety == "dispatch_ambiguous"
                else HarnessProviderCallStatus.FAILED
            )
            record = self._transition_provider_call(
                current.record,
                status=status,
                state_object_digest=state_object.digest,
                failure_digest=failure.digest,
                failure_object_digest=failure_object.digest,
                recorded_at_ms=self._recorded_time(
                    now_ms,
                    previous_recorded_at_ms=current.record.recorded_at_ms,
                ),
            )
            stored = self._store_provider_call(
                record,
                state_object=state_object,
                request=current.request,
                request_object=current.request_object,
                failure=failure,
                failure_object=failure_object,
            )
            self._append_provider_event(
                lease=lease,
                event_kind=(
                    "harness.provider-call-unknown"
                    if status is HarnessProviderCallStatus.UNKNOWN
                    else "harness.provider-call-failed"
                ),
                stored=stored,
                caused_by_event_id=self._provider_event_id_for_digest(current.record.digest),
            )
            return stored
        finally:
            self.store.release_run_lease(lease)

    def fail_claimed_provider_call(
        self,
        retained: StoredHarnessProviderCall,
        *,
        failure: HarnessProviderCallFailureReceipt,
    ) -> StoredHarnessProviderCall:
        now_ms = self.clock_ms()
        lease = self._acquire_lease(
            "provider-pre-dispatch-fail",
            retained.record.provider_call_id,
            now_ms=now_ms,
        )
        try:
            current = self._require_current_provider_call(retained.record)
            if current.record.status is not HarnessProviderCallStatus.CLAIMED:
                raise HarnessProviderCallRecoveryRequired(
                    "pre-dispatch Provider failure requires a current claim"
                )
            _require_failure_matches(current.record, failure)
            if failure.dispatch_safety != "pre_dispatch_safe":
                raise HarnessProviderCallRequestMismatch(
                    "pre-dispatch Provider failure is not proven safe"
                )
            state = self._require_state()
            _require_provider_outcome_state(current.state, state)
            state_object = self._put_state(state)
            failure_object = self.store.put_object(
                failure.to_dict(), kind="harness-provider-call-failure"
            )
            record = self._transition_provider_call(
                current.record,
                status=HarnessProviderCallStatus.FAILED,
                state_object_digest=state_object.digest,
                failure_digest=failure.digest,
                failure_object_digest=failure_object.digest,
                recorded_at_ms=self._recorded_time(
                    now_ms,
                    previous_recorded_at_ms=current.record.recorded_at_ms,
                ),
            )
            stored = self._store_provider_call(
                record,
                state_object=state_object,
                request=current.request,
                request_object=current.request_object,
                failure=failure,
                failure_object=failure_object,
            )
            self._append_provider_event(
                lease=lease,
                event_kind="harness.provider-call-failed",
                stored=stored,
                caused_by_event_id=self._provider_event_id_for_digest(current.record.digest),
            )
            return stored
        finally:
            self.store.release_run_lease(lease)

    def retry_failed_provider_call(
        self,
        retained: StoredHarnessProviderCall,
        *,
        holder_id: str,
        ttl_ms: int,
    ) -> StoredHarnessProviderCall:
        if not holder_id or holder_id != holder_id.strip():
            raise ValueError("Provider Call retry holder must be non-empty and trimmed")
        if ttl_ms < 1:
            raise ValueError("Provider Call retry TTL must be positive")
        now_ms = self.clock_ms()
        lease = self._acquire_lease(
            "provider-retry", retained.record.provider_call_id, now_ms=now_ms
        )
        try:
            current = self._require_current_provider_call(retained.record)
            if current.record.status is not HarnessProviderCallStatus.FAILED:
                raise HarnessProviderCallRecoveryRequired(
                    "only an explicitly safe failed Provider attempt can retry"
                )
            if current.failure is None or current.failure.dispatch_safety != "pre_dispatch_safe":
                raise HarnessProviderCallRecoveryRequired(
                    "Provider failure does not prove that redispatch is safe"
                )
            state = self._require_state()
            _require_provider_safe_retry_state(current.state, state)
            state_object = self._put_state(state)
            previous = current.record
            record = build_provider_call_record_v4(
                provider_call_id=previous.provider_call_id,
                harness_run_id=self.harness_run_id,
                binding_digest=self.binding.digest,
                source_kind=previous.source_kind,
                source_digest=previous.source_digest,
                source_object_digest=previous.source_object_digest,
                state_object_digest=state_object.digest,
                turn_id=previous.turn_id,
                turn_sequence=previous.turn_sequence,
                request_digest=previous.request_digest,
                request_object_digest=getattr(previous, "request_object_digest", None),
                provider_request_digest=previous.provider_request_digest,
                adapter_id=previous.adapter_id,
                requested_model_id=previous.requested_model_id,
                holder_id=holder_id,
                generation=previous.claim_generation + 1,
                status=HarnessProviderCallStatus.CLAIMED,
                result_digest=None,
                result_object_digest=None,
                failure_digest=None,
                failure_object_digest=None,
                previous_record_digest=previous.digest,
                issued_at_ms=now_ms,
                expires_at_ms=now_ms + ttl_ms,
                recorded_at_ms=self._recorded_time(
                    now_ms,
                    previous_recorded_at_ms=previous.recorded_at_ms,
                ),
            )
            stored = self._store_provider_call(
                record,
                state_object=state_object,
                request=current.request,
                request_object=current.request_object,
            )
            self._append_provider_event(
                lease=lease,
                event_kind="harness.provider-call-superseded",
                stored=stored,
                caused_by_event_id=self._provider_event_id_for_digest(previous.digest),
            )
            return stored
        finally:
            self.store.release_run_lease(lease)

    def _append_provider_event(
        self,
        *,
        lease: HarnessRunLease,
        event_kind: str,
        stored: StoredHarnessProviderCall,
        caused_by_event_id: str | None,
    ) -> None:
        references = [stored.record_object, stored.state_object]
        if stored.request_object is not None:
            references.append(stored.request_object)
        if stored.result_object is not None:
            references.append(stored.result_object)
        if stored.failure_object is not None:
            references.append(stored.failure_object)
        self._append_event(
            lease=lease,
            event_kind=event_kind,
            event_id=continuity_event_id("provider", stored.record.digest),
            data={
                "providerCallRecordDigest": stored.record.digest,
                "providerCallRecordObjectDigest": stored.record_object.digest,
                "stateObjectDigest": stored.state_object.digest,
                "requestObjectDigest": (
                    None if stored.request_object is None else stored.request_object.digest
                ),
                "resultObjectDigest": (
                    None if stored.result_object is None else stored.result_object.digest
                ),
                "failureObjectDigest": (
                    None if stored.failure_object is None else stored.failure_object.digest
                ),
            },
            recorded_at_ms=stored.record.recorded_at_ms,
            referenced_objects=tuple(references),
            caused_by_event_id=caused_by_event_id,
        )

    def _acquire_provider_dispatch_lease(
        self,
        retained: StoredHarnessProviderCall,
    ) -> HarnessRunLease:
        """Wait through short Run-lease contention after exact Provider claim.

        The durable CLAIMED record is the semantic authority for the holder's
        next dispatch-admission transition. A competing execution may briefly
        hold the generic Run lease while discovering that it does not own this
        Provider claim. That mechanical lease must not strand the exact claim
        owner before physical dispatch.
        """
        deadline = time.monotonic() + _PROVIDER_DISPATCH_LEASE_WAIT_SECONDS
        while True:
            try:
                return self._acquire_lease(
                    "provider-dispatch",
                    retained.record.provider_call_id,
                    now_ms=self.clock_ms(),
                )
            except HarnessLeaseHeld:
                current = self.load_current_provider_call()
                if current.record != retained.record:
                    raise HarnessSuperseded(
                        "Harness Provider Call changed while waiting for dispatch admission"
                    )
                if time.monotonic() >= deadline:
                    raise HarnessProviderCallRecoveryRequired(
                        "Provider claim owner could not reacquire the Run lease before dispatch"
                    )
                time.sleep(_PROVIDER_DISPATCH_LEASE_RETRY_SECONDS)

    def _acquire_provider_outcome_lease(
        self,
        operation: str,
        retained: StoredHarnessProviderCall,
    ) -> HarnessRunLease:
        """Wait through short Run-lease contention after physical Provider dispatch.

        The durable DISPATCHING record is the semantic authority for the known
        Provider outcome. A competing execution may briefly hold the Run lease
        while discovering that it must not redispatch. That short mechanical
        lease must not make the physical dispatch owner lose its ability to
        commit the already-known result.
        """
        deadline = time.monotonic() + _PROVIDER_OUTCOME_LEASE_WAIT_SECONDS
        while True:
            try:
                return self._acquire_lease(
                    operation,
                    retained.record.provider_call_id,
                    now_ms=self.clock_ms(),
                )
            except HarnessLeaseHeld:
                current = self.load_current_provider_call()
                if current.record != retained.record:
                    raise HarnessSuperseded(
                        "Harness Provider Call changed while waiting to commit its physical outcome"
                    )
                if time.monotonic() >= deadline:
                    raise HarnessProviderCallRecoveryRequired(
                        "Provider outcome could not reacquire the Run lease after physical dispatch"
                    )
                time.sleep(_PROVIDER_OUTCOME_LEASE_RETRY_SECONDS)

    def _provider_call_id(
        self,
        source: HarnessProviderCallSourceRef,
        turn_sequence: int,
    ) -> str:
        token = canonical_digest(
            {
                "harnessRunId": self.harness_run_id,
                "sourceKind": source.kind.value,
                "sourceObjectDigest": source.object_digest,
                "turnSequence": turn_sequence,
            }
        )[7:39]
        return f"provider-call:{token}"

    def _provider_event_id_for_digest(self, digest: str) -> str | None:
        for event in reversed(self.store.list_run_events(self.harness_run_id)):
            if event.data.get("providerCallRecordDigest") == digest:
                return event.event_id
        return None
