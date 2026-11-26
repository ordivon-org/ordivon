from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
import time

from anc_canonical import JsonValue, canonical_digest

from ..core_contracts import HarnessRunContract
from ..protocol import (
    HarnessRunPauseReason,
    HarnessRunSnapshot,
    HarnessToolStepStatus,
)
from ..run_state import HarnessRunState, state_from_dict
from ..working_view import (
    HarnessWorkingSetSpec,
)
from ..store_errors import (
    HarnessEventConflict,
    HarnessLeaseConflict,
    HarnessRevisionConflict,
)
from ..store import (
    HarnessStore,
    HarnessRunEventRecord,
    HarnessRunLease,
    StoredHarnessObject,
    new_execution_owner_id,
)
from .continuity_guards import (
    _TOOL_EVENT_KINDS,
    continuity_event_id,
    required_event_digest,
    require_active_budget_consistency,
    require_run_snapshot_binding,
    validate_snapshot_state,
)
from .working_set_queries import _WorkingSetReadQueries
from .run_source_inspection import RunSourceInspection
from .working_set_commands import WorkingSetCommands
from .caller_ingress import CallerIngressContinuity
from .working_view_validation import WorkingViewValidation
from .provider_continuity import ProviderContinuityCommands
from .provider_record_io import ProviderRecordIO
from .tool_continuity import ToolContinuity
from .run_store_port import (
    HarnessSuperseded,
    HarnessRunStoreBinding,
    StoredHarnessRunSnapshot,
)

_STORE_LEASE_TTL_MS = 30_000
_PROVIDER_EVENT_KINDS = frozenset(
    {
        "harness.provider-call-claimed",
        "harness.provider-call-superseded",
        "harness.provider-call-dispatching",
        "harness.provider-call-completed",
        "harness.provider-call-failed",
        "harness.provider-call-unknown",
    }
)
_PROVIDER_CLEAR_EVENT_KINDS = frozenset(
    {
        "harness.snapshot-recorded",
        "harness.working-set-recorded",
        "harness.run-paused",
        "harness.tool-step-prepared",
        "harness.run-stopped",
        "harness.run-completed",
        "harness.run-failed",
    }
)


@dataclass(frozen=True, slots=True)
class _Heads:
    provider: HarnessRunEventRecord | None
    tool: HarnessRunEventRecord | None
    snapshot: HarnessRunEventRecord | None
    working_set: HarnessRunEventRecord | None


class EventSourcedRunContinuity(
    _WorkingSetReadQueries, RunSourceInspection,
    WorkingSetCommands, CallerIngressContinuity, WorkingViewValidation,
    ProviderContinuityCommands, ProviderRecordIO, ToolContinuity,
):
    """Independent event-sourced Provider/Tool/Snapshot continuity for one Run."""

    @classmethod
    def open(
        cls,
        store: HarnessStore,
        harness_run_id: str,
        *,
        clock_ms: Callable[[], int] | None = None,
    ) -> EventSourcedRunContinuity:
        projection = store.load_run(harness_run_id)
        raw = store.get_object(
            projection.contract_object_digest,
            expected_kind="harness-run-contract",
        )
        if not isinstance(raw, dict):
            raise TypeError("Harness Run Contract object must be an object")
        return cls(store, HarnessRunContract.from_dict(raw), clock_ms=clock_ms)

    def __init__(
        self,
        store: HarnessStore,
        contract: HarnessRunContract,
        *,
        clock_ms: Callable[[], int] | None = None,
    ) -> None:
        store.validate_run_history(contract.harness_run_id)
        projection = store.load_run(contract.harness_run_id)
        if (
            projection.contract_digest != contract.digest
            or projection.caller_id != contract.caller_id
            or projection.caller_run_ref != contract.caller_run_ref
        ):
            raise ValueError("Harness Run Contract differs from the independent Store")
        self.store = store
        self.contract = contract
        self.harness_run_id = contract.harness_run_id
        self._binding = HarnessRunStoreBinding.for_contract(contract)
        self._clock_ms = clock_ms or (lambda: time.time_ns() // 1_000_000)
        self._execution_owner_id = new_execution_owner_id("continuity")
        self._bound_state: HarnessRunState | None = None
        self._provider_outcome_requires_resume = False
        # A read-only projection of the immutable Journal; never a second
        # persistence authority. A Store revision change invalidates it.
        self._heads_cache: tuple[int, _Heads] | None = None
        self._heads_cache_last_sequence = 0
        self._snapshot_sequence = self._current_snapshot_sequence()

    @property
    def binding(self) -> HarnessRunStoreBinding:
        return self._binding

    @property
    def caller_revision(self) -> int:
        return self.store.load_run(self.harness_run_id).revision

    def clock_ms(self) -> int:
        value = self._clock_ms()
        if type(value) is not int or value < 0:
            raise ValueError("Harness continuity clock must return a non-negative integer")
        return value

    def bind_state(self, state: HarnessRunState) -> None:
        require_active_budget_consistency(state, self.contract)
        self._bound_state = state

    def record_pause(self, pause_reason: HarnessRunPauseReason) -> StoredHarnessRunSnapshot:
        state = self._require_state()
        # A lost physical Tool reply preserves the SAME original Tool Intent.
        # Recovery can only query the real Owner; it must never re-dispatch
        # the action or discard the active cursor. No extra registry/ledger.
        pending_intents: tuple[str, ...] = ()
        if pause_reason is HarnessRunPauseReason.EFFECT_DISPATCH_PENDING:
            current = self.load_current_tool_step()
            if current.receipt is not None and current.receipt.status not in {
                HarnessToolStepStatus.UNKNOWN,
                HarnessToolStepStatus.CANCEL_REQUESTED,
            }:
                raise ValueError(
                    "effect-dispatch-pending requires a prepared or unresolved original Tool"
                )
            # PREPARED without a Receipt is itself a possibly dispatched
            # physical effect: response loss before first observation must
            # preserve its original Intent instead of permitting terminal.
            pending_intents = (current.intent.digest,)
        now_ms = self.clock_ms()
        lease = self._acquire_lease("run-pause", pause_reason.value, now_ms=now_ms)
        try:
            snapshot = self._build_snapshot(
                pause_reason,
                active_intent_digests=pending_intents,
                created_at_ms=self._recorded_time(now_ms),
            )
            retained = self._store_snapshot(snapshot, state)
            self._append_event(
                lease=lease,
                event_kind="harness.run-paused",
                event_id=continuity_event_id("run-paused", snapshot.digest),
                data={
                    "snapshotDigest": snapshot.digest,
                    "snapshotObjectDigest": retained.snapshot_object.digest,
                    "stateObjectDigest": retained.state_object.digest,
                    "pauseReason": pause_reason.value,
                },
                recorded_at_ms=snapshot.created_at_ms,
                referenced_objects=(
                    retained.snapshot_object,
                    retained.state_object,
                ),
                caused_by_event_id=self._latest_event_id(),
            )
            return retained
        finally:
            self.store.release_run_lease(lease)

    def load_current_snapshot(self) -> StoredHarnessRunSnapshot:
        event = self._heads().snapshot
        if event is None:
            raise KeyError("Harness Run has no current Snapshot")
        data = event.data
        snapshot_object_digest = required_event_digest(data, "snapshotObjectDigest")
        state_object_digest = required_event_digest(data, "stateObjectDigest")
        raw_snapshot = self.store.get_object(
            snapshot_object_digest,
            expected_kind="harness-run-snapshot",
        )
        if not isinstance(raw_snapshot, dict):
            raise TypeError("Harness Run Snapshot object is invalid")
        snapshot = HarnessRunSnapshot.from_dict(raw_snapshot)
        if data.get("snapshotDigest") != snapshot.digest:
            raise ValueError("Harness Run Snapshot semantic digest differs")
        require_run_snapshot_binding(snapshot, self.harness_run_id, self.binding, self.contract)
        raw_state = self.store.get_object(
            state_object_digest,
            expected_kind="harness-run-state",
        )
        if not isinstance(raw_state, dict):
            raise TypeError("Harness Run State object is invalid")
        state = state_from_dict(raw_state, harness_run_id=self.harness_run_id)
        validate_snapshot_state(snapshot, state)
        return StoredHarnessRunSnapshot(
            snapshot,
            self.store.inspect_object(snapshot_object_digest),
            state,
            self.store.inspect_object(state_object_digest),
        )

    def doctor(self) -> dict[str, JsonValue]:
        base = self.store.doctor(full=True)
        events = self.store.list_run_events(self.harness_run_id)
        provider_records = 0
        tool_records = 0
        snapshots = 0
        working_sets = 0
        previous_working_set: HarnessWorkingSetSpec | None = None
        previous_working_set_event: HarnessRunEventRecord | None = None
        for event in events:
            if event.event_kind in _PROVIDER_EVENT_KINDS:
                retained_provider = self._load_provider_from_event(event)
                if (
                    previous_working_set is not None
                    and previous_working_set.committed
                    and retained_provider.request is not None
                ):
                    self._require_working_view_request_against_state(
                        retained_provider.request,
                        previous_working_set,
                        retained_provider.state,
                        before_event_sequence=event.sequence,
                    )
                provider_records += 1
            if event.event_kind in _TOOL_EVENT_KINDS:
                self._validate_tool_event(event)
                tool_records += 1
            if "snapshotObjectDigest" in event.data:
                self._load_snapshot_from_event(event)
                snapshots += 1
            if event.event_kind == "harness.working-set-recorded":
                spec = self._working_set_from_event(event)
                self._require_working_set_predecessor(previous_working_set, spec)
                self._validate_caller_ingress_promotion_evidence(
                    event,
                    spec,
                    previous_event=previous_working_set_event,
                    previous_spec=previous_working_set,
                )
                self._validate_working_set_transition_evidence(
                    event,
                    spec,
                    previous_event=previous_working_set_event,
                    previous_spec=previous_working_set,
                )
                previous_working_set = spec
                previous_working_set_event = event
                working_sets += 1
        from ..independent_result_reader import IndependentRunReader

        independent = IndependentRunReader(
            self.store,
            self.contract,
            self.binding,
            clock_ms=self.clock_ms,
        ).doctor()
        return {
            "schemaVersion": 1,
            "kind": "ordivon.harness-continuity-doctor",
            "healthy": True,
            "harnessRunId": self.harness_run_id,
            "runRevision": self.caller_revision,
            "providerRecords": provider_records,
            "toolRecords": tool_records,
            "snapshots": snapshots,
            "workingSets": working_sets,
            "independentResult": independent,
            "store": base,
        }

    def _append_event(
        self,
        *,
        lease: HarnessRunLease,
        event_kind: str,
        event_id: str,
        data: dict[str, JsonValue],
        recorded_at_ms: int,
        referenced_objects: tuple[StoredHarnessObject, ...],
        caused_by_event_id: str | None,
    ) -> None:
        try:
            self.store.append_event(
                event_id=event_id,
                harness_run_id=self.harness_run_id,
                event_kind=event_kind,
                data=data,
                expected_revision=lease.run_revision,
                recorded_at_ms=recorded_at_ms,
                lease=lease,
                lease_checked_at_ms=self.clock_ms(),
                caused_by_event_id=caused_by_event_id,
                referenced_objects=referenced_objects,
            )
        except (
            HarnessEventConflict,
            HarnessLeaseConflict,
            HarnessRevisionConflict,
        ) as error:
            raise HarnessSuperseded(str(error)) from error

    def _acquire_lease(
        self,
        operation: str,
        token: str,
        *,
        now_ms: int,
        expected_run_revision: int | None = None,
    ) -> HarnessRunLease:
        owner_token = canonical_digest(
            {
                "harnessRunId": self.harness_run_id,
                "operation": operation,
                "token": token,
            }
        )[7:31]
        return self.store.acquire_run_lease(
            self.harness_run_id,
            owner_id=f"{self._execution_owner_id}:{operation}:{owner_token}",
            ttl_ms=_STORE_LEASE_TTL_MS,
            now_ms=now_ms,
            expected_run_revision=expected_run_revision,
        )

    def _heads(self) -> _Heads:
        revision = self.store.load_run(self.harness_run_id).revision
        cached = self._heads_cache
        if cached is not None and cached[0] == revision:
            return cached[1]
        # Hot append folds only the immutable tail; cold recovery replays all.
        provider = cached[1].provider if cached is not None else None
        tool = cached[1].tool if cached is not None else None
        snapshot = cached[1].snapshot if cached is not None else None
        working_set = cached[1].working_set if cached is not None else None
        events = self.store.list_run_events(
            self.harness_run_id,
            after_sequence=self._heads_cache_last_sequence if cached is not None else 0,
        )
        for event in events:
            if event.event_kind in _PROVIDER_CLEAR_EVENT_KINDS:
                provider = None
            if event.event_kind in _PROVIDER_EVENT_KINDS:
                provider = event
            if event.event_kind in _TOOL_EVENT_KINDS:
                tool = event
            if "snapshotObjectDigest" in event.data:
                snapshot = event
            if event.event_kind == "harness.working-set-recorded":
                working_set = event
        heads = _Heads(
            provider=provider,
            tool=tool,
            snapshot=snapshot,
            working_set=working_set,
        )
        # If another writer appended between the revision read and the event
        # read, the next call must scan again. The final event revision is
        # authoritative for a complete, ordered Journal read.
        if events and events[-1].run_revision == revision:
            self._heads_cache = (revision, heads)
            self._heads_cache_last_sequence = events[-1].sequence
        return heads

    def _load_snapshot_from_event(self, event: HarnessRunEventRecord) -> StoredHarnessRunSnapshot:
        data = event.data
        snapshot_object_digest = required_event_digest(data, "snapshotObjectDigest")
        state_object_digest = required_event_digest(data, "stateObjectDigest")
        raw_snapshot = self.store.get_object(
            snapshot_object_digest,
            expected_kind="harness-run-snapshot",
        )
        raw_state = self.store.get_object(
            state_object_digest,
            expected_kind="harness-run-state",
        )
        if not isinstance(raw_snapshot, dict) or not isinstance(raw_state, dict):
            raise ValueError("Harness Snapshot event objects are invalid")
        snapshot = HarnessRunSnapshot.from_dict(raw_snapshot)
        state = state_from_dict(raw_state, harness_run_id=self.harness_run_id)
        require_run_snapshot_binding(snapshot, self.harness_run_id, self.binding, self.contract)
        validate_snapshot_state(snapshot, state)
        if data.get("snapshotDigest") != snapshot.digest:
            raise ValueError("Harness Snapshot event digest differs")
        return StoredHarnessRunSnapshot(
            snapshot,
            self.store.inspect_object(snapshot_object_digest),
            state,
            self.store.inspect_object(state_object_digest),
        )

    def _persistent_state(self, state: HarnessRunState) -> HarnessRunState:
        return state.for_persistence(
            allow_model_content=self.contract.privacy.allow_model_content,
            allow_tool_content=self.contract.privacy.allow_tool_content,
        )

    def _put_state(self, state: HarnessRunState) -> StoredHarnessObject:
        persistent = self._persistent_state(state)
        return self.store.put_object(
            persistent.to_dict(self.harness_run_id),
            kind="harness-run-state",
        )

    def _state_for_object(self, stored: StoredHarnessObject) -> HarnessRunState:
        raw = self.store.get_object(stored.digest, expected_kind=stored.kind)
        if not isinstance(raw, dict):
            raise TypeError("Harness Run state object is invalid")
        state = state_from_dict(raw, harness_run_id=self.harness_run_id)
        if self._bound_state is not None and state != self._persistent_state(self._bound_state):
            raise ValueError("Provider Call state object differs from bound state")
        return state

    def _store_snapshot(
        self,
        snapshot: HarnessRunSnapshot,
        state: HarnessRunState,
    ) -> StoredHarnessRunSnapshot:
        persistent = self._persistent_state(state)
        validate_snapshot_state(snapshot, persistent)
        snapshot_object = self.store.put_object(snapshot.to_dict(), kind="harness-run-snapshot")
        state_object = self.store.put_object(
            persistent.to_dict(self.harness_run_id),
            kind="harness-run-state",
        )
        return StoredHarnessRunSnapshot(
            snapshot,
            snapshot_object,
            persistent,
            state_object,
        )

    def _build_snapshot(
        self,
        pause_reason: HarnessRunPauseReason,
        *,
        active_intent_digests: tuple[str, ...],
        created_at_ms: int,
    ) -> HarnessRunSnapshot:
        state = self._require_state()
        self._snapshot_sequence += 1
        return HarnessRunSnapshot(
            snapshot_id=(
                f"harness-run-snapshot:{self.harness_run_id.removeprefix('harness-run:')}:"
                f"s{self._snapshot_sequence}"
            ),
            harness_run_id=self.harness_run_id,
            assignment_id=self.binding.assignment_id,
            assignment_generation=self.binding.assignment_generation,
            assignment_digest=self.binding.assignment_digest,
            sequence=self._snapshot_sequence,
            tool_catalog_digest=self.contract.tool_catalog_digest,
            requested_model_id=state.requested_model_id,
            effective_model_id=state.effective_model_id,
            messages_digest=state.messages_digest,
            observation_digests=state.observation_digests,
            active_tool_step_intent_digests=active_intent_digests,
            remaining_budget=state.remaining_budget,
            pause_reason=pause_reason,
            created_at_ms=created_at_ms,
        )

    def _require_state(self) -> HarnessRunState:
        if self._bound_state is None:
            raise RuntimeError("Harness Run state was not bound before persistence")
        return self._bound_state

    def _latest_event_id(self) -> str | None:
        events = self.store.list_run_events(self.harness_run_id)
        return None if not events else events[-1].event_id

    def _current_snapshot_sequence(self) -> int:
        maximum = 0
        for event in self.store.list_run_events(self.harness_run_id):
            object_digest = event.data.get("snapshotObjectDigest")
            if not isinstance(object_digest, str):
                continue
            raw = self.store.get_object(
                object_digest,
                expected_kind="harness-run-snapshot",
            )
            if not isinstance(raw, dict):
                raise TypeError("current Harness Run Snapshot is not an object")
            maximum = max(maximum, HarnessRunSnapshot.from_dict(raw).sequence)
        return maximum

    def _recorded_time(
        self,
        proposed: int,
        *,
        previous_recorded_at_ms: int | None = None,
    ) -> int:
        projection = self.store.load_run(self.harness_run_id)
        values = [proposed, projection.updated_at_ms]
        if previous_recorded_at_ms is not None:
            values.append(previous_recorded_at_ms + 1)
        return max(values)
