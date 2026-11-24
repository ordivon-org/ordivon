"""Working Set source and transition admission against the existing Run Journal.

Composed only by EventSourcedRunContinuity. Reuses its single Store, lease,
original state and event identity; no separate Writer or authority.
"""
from __future__ import annotations
from anc_canonical import JsonValue
from ..protocol import (
    HarnessProviderCallStatus,
)
from ..working_view import (
    AgentWorkingSetTransitionProposal,
    HarnessWorkingSetSpec,
    HarnessWorkingView,
    HarnessWorkingViewSource,
    compile_working_view,
)
from ..store import (
    HarnessEventAdmission,
    HarnessEventWrite,
    StoredHarnessObject,
)
from .continuity_guards import (
    continuity_event_id,
)
from .run_store_port import (
    HarnessProviderCallRecoveryRequired,
    HarnessProviderCallRequestMismatch,
)


class WorkingSetCommands:
    """Working Set source and transition admission against the existing Run Journal."""

    def store_working_view_source(
        self,
        source: HarnessWorkingViewSource,
    ) -> StoredHarnessObject:
        """Persist one exact Working View source under the Run privacy authority."""
        self._require_working_view_source_authorized(source)
        return self.store.put_object(source.to_dict(), kind="harness-working-view-source")

    def record_working_set(
        self,
        spec: HarnessWorkingSetSpec,
    ) -> HarnessEventAdmission:
        """Admit one exact Agent-owned Working Set revision to Run history.

        The event is a durable selection claim, not a relevance judgment. Pinned
        sources are exact CAS identities. A committed attempt is frozen; a new
        attempt may only replan from the committed head.
        """
        if not self.contract.privacy.allow_model_content:
            raise ValueError(
                "Working Set prototype requires Contract permission to persist model content"
            )
        if self._validate_working_set_transition(spec):
            return HarnessEventAdmission.EXISTING

        spec_object = self.store.put_object(
            spec.to_dict(),
            kind="harness-working-set-spec",
        )
        source_objects: list[StoredHarnessObject] = []
        for pin in spec.pins:
            raw = self.store.get_object(
                pin.resolved_digest,
                expected_kind="harness-working-view-source",
            )
            if not isinstance(raw, dict):
                raise TypeError("Working Set source object is invalid")
            source = HarnessWorkingViewSource.from_dict(raw)
            if (
                source.logical_ref != pin.logical_ref
                or source.logical_generation != pin.logical_generation
            ):
                raise ValueError("Working Set pin differs from its exact source")
            self._require_working_view_source_authorized(source)
            source_objects.append(self.store.inspect_object(pin.resolved_digest))

        now_ms = self.clock_ms()
        lease = self._acquire_lease("working-set", spec.digest, now_ms=now_ms)
        try:
            # The first validation is a fast fail. This second validation is the
            # authority check: another writer may have advanced the head while
            # this caller waited for the Run lease.
            if self._validate_working_set_transition(spec):
                return HarnessEventAdmission.EXISTING
            event_id = continuity_event_id("working-set", spec.digest)
            events = self.store.list_run_events(self.harness_run_id)
            return self.store.append_event(
                event_id=event_id,
                harness_run_id=self.harness_run_id,
                event_kind="harness.working-set-recorded",
                data={
                    "workingSetDigest": spec.digest,
                    "workingSetObjectDigest": spec_object.digest,
                    "attemptId": spec.attempt_id,
                    "workingSetRevision": spec.revision,
                    "committed": spec.committed,
                },
                expected_revision=lease.run_revision,
                recorded_at_ms=self._recorded_time(now_ms),
                lease=lease,
                lease_checked_at_ms=self.clock_ms(),
                caused_by_event_id=None if not events else events[-1].event_id,
                referenced_objects=(spec_object, *source_objects),
            )
        finally:
            self.store.release_run_lease(lease)

    def apply_working_set_transition(
        self,
        proposal: AgentWorkingSetTransitionProposal,
        *,
        source_working_set_digest: str,
        source_model_view_digest: str,
    ) -> HarnessWorkingSetSpec:
        """Atomically admit one Agent-authored successor cognition attempt.

        The Agent supplies the exact successor pins and basis. Harness only
        verifies that those immutable source identities exist under the current
        privacy authority, that the selected WorkingSet is still current, and
        that the exact Provider request which produced the proposal extended that
        WorkingSet's base view. Replan, complete selection and commit are one
        bounded Journal transaction under one Run lease.
        """
        if not self.contract.privacy.allow_model_content:
            raise ValueError(
                "Agent Working Set transition requires permission to retain model content"
            )

        def source_objects_for(
            pins,
        ) -> tuple[StoredHarnessObject, ...]:
            objects: list[StoredHarnessObject] = []
            for pin in pins:
                raw = self.store.get_object(
                    pin.resolved_digest,
                    expected_kind="harness-working-view-source",
                )
                if not isinstance(raw, dict):
                    raise TypeError("Working Set transition source object is invalid")
                source = HarnessWorkingViewSource.from_dict(raw)
                if (
                    source.logical_ref != pin.logical_ref
                    or source.logical_generation != pin.logical_generation
                ):
                    raise ValueError("Working Set transition pin differs from its exact source")
                self._require_working_view_source_authorized(source)
                objects.append(self.store.inspect_object(pin.resolved_digest))
            return tuple(objects)

        def existing_transition() -> HarnessWorkingSetSpec | None:
            current = self._load_current_working_set_or_none()
            if (
                current is None
                or not current.committed
                or current.attempt_id != proposal.next_attempt_id
                or current.pins != proposal.pins
                or current.commit_basis != proposal.basis
            ):
                return None
            history = self.store.list_run_events(self.harness_run_id)
            attempt_events = [
                event
                for event in history
                if event.event_kind == "harness.working-set-recorded"
                and event.data.get("attemptId") == proposal.next_attempt_id
            ]
            if len(attempt_events) != 3:
                return None
            attempt_specs = [self._working_set_from_event(event) for event in attempt_events]
            if [spec.revision for spec in attempt_specs] != [1, 2, 3]:
                return None
            new_evidence = all(
                "sourceWorkingSetDigest" in event.data and "sourceModelViewDigest" in event.data
                for event in attempt_events
            )
            legacy_evidence = all(
                "sourceWorkingViewDigest" in event.data
                and "sourceWorkingSetDigest" not in event.data
                and "sourceModelViewDigest" not in event.data
                for event in attempt_events
            )
            if not (new_evidence or legacy_evidence):
                return None
            if any(
                event.data.get("transitionProposalDigest") != proposal.digest
                for event in attempt_events
            ):
                return None
            if new_evidence and any(
                event.data.get("sourceWorkingSetDigest") != source_working_set_digest
                or event.data.get("sourceModelViewDigest") != source_model_view_digest
                for event in attempt_events
            ):
                return None
            if legacy_evidence and any(
                event.data.get("sourceWorkingViewDigest") != source_model_view_digest
                for event in attempt_events
            ):
                return None
            first = attempt_specs[0]
            if first.previous_digest is None:
                return None
            predecessor = next(
                (
                    self._working_set_from_event(event)
                    for event in history
                    if event.event_kind == "harness.working-set-recorded"
                    and event.data.get("workingSetDigest") == first.previous_digest
                ),
                None,
            )
            if (
                predecessor is None
                or not predecessor.committed
                or predecessor.digest != source_working_set_digest
            ):
                return None
            if (
                legacy_evidence
                and compile_working_view(predecessor, self.store).digest != source_model_view_digest
            ):
                return None
            return current

        replay = existing_transition()
        if replay is not None:
            return replay
        source_objects = source_objects_for(proposal.pins)
        now_ms = self.clock_ms()
        lease = self._acquire_lease("working-set-transition", proposal.digest, now_ms=now_ms)
        try:
            replay = existing_transition()
            if replay is not None:
                return replay
            current = self._load_current_working_set_or_none()
            if current is None or not current.committed:
                raise ValueError("Agent Working Set transition requires a committed predecessor")
            if proposal.next_attempt_id == current.attempt_id:
                raise ValueError("Agent Working Set transition requires a new attempt identity")
            if current.digest != source_working_set_digest:
                raise HarnessProviderCallRequestMismatch(
                    "Agent Working Set transition source WorkingSet is no longer current"
                )
            base_view = compile_working_view(current, self.store)
            provider_evidence_bound = False
            provider = self._load_current_provider_call_or_none()
            if provider is None:
                if source_model_view_digest != base_view.digest:
                    raise HarnessProviderCallRequestMismatch(
                        "overlay-backed Working Set transition requires exact Provider evidence"
                    )
            elif provider.record.status in {
                HarnessProviderCallStatus.CLAIMED,
                HarnessProviderCallStatus.DISPATCHING,
                HarnessProviderCallStatus.UNKNOWN,
            }:
                raise HarnessProviderCallRecoveryRequired(
                    "Working Set cannot change while a Provider Call may still act on the prior view"
                )
            elif provider.record.status is HarnessProviderCallStatus.COMPLETED:
                if provider.request is None or provider.result is None:
                    raise HarnessProviderCallRecoveryRequired(
                        "Agent Working Set transition requires retained exact Provider request/result evidence"
                    )
                effective_view = HarnessWorkingView(
                    attempt_id=current.attempt_id,
                    working_set_digest=current.digest,
                    messages=provider.request.messages,
                )
                if (
                    provider.request.context_digest != source_model_view_digest
                    or effective_view.digest != source_model_view_digest
                    or provider.request.messages[: len(base_view.messages)] != base_view.messages
                ):
                    raise HarnessProviderCallRequestMismatch(
                        "Agent Working Set transition source model view differs from the completed Provider request"
                    )
                if provider.result.working_set_transition != proposal:
                    raise HarnessProviderCallRequestMismatch(
                        "completed Provider result differs from the Agent Working Set transition proposal"
                    )
                provider_evidence_bound = True
            else:
                raise HarnessProviderCallRequestMismatch(
                    "Agent Working Set transition cannot originate from a failed Provider Call"
                )

            replanned = current.replan(proposal.next_attempt_id)
            selected = replanned.select_pins(proposal.pins)
            committed = selected.commit(proposal.basis)
            chain = (replanned, selected, committed)
            self._require_working_set_predecessor(current, replanned)
            self._require_working_set_predecessor(replanned, selected)
            self._require_working_set_predecessor(selected, committed)

            proposal_object = self.store.put_object(
                proposal.to_dict(), kind="agent-working-set-transition-proposal"
            )
            spec_objects = tuple(
                self.store.put_object(spec.to_dict(), kind="harness-working-set-spec")
                for spec in chain
            )
            recorded_at_ms = self._recorded_time(now_ms)
            prior_event_id = self._latest_event_id()
            transition_source_data: dict[str, JsonValue] = (
                {
                    "sourceWorkingSetDigest": source_working_set_digest,
                    "sourceModelViewDigest": source_model_view_digest,
                }
                if provider_evidence_bound
                else {"sourceWorkingViewDigest": source_model_view_digest}
            )
            writes: list[HarnessEventWrite] = []
            caused_by = prior_event_id
            for spec, spec_object in zip(chain, spec_objects, strict=True):
                event_id = continuity_event_id("working-set", spec.digest)
                refs = (spec_object, proposal_object)
                if spec.pins:
                    refs += source_objects
                writes.append(
                    HarnessEventWrite(
                        event_id=event_id,
                        event_kind="harness.working-set-recorded",
                        data={
                            "workingSetDigest": spec.digest,
                            "workingSetObjectDigest": spec_object.digest,
                            "attemptId": spec.attempt_id,
                            "workingSetRevision": spec.revision,
                            "committed": spec.committed,
                            "transitionProposalDigest": proposal.digest,
                            "transitionProposalObjectDigest": proposal_object.digest,
                            **transition_source_data,
                        },
                        recorded_at_ms=recorded_at_ms,
                        caused_by_event_id=caused_by,
                        referenced_objects=refs,
                    )
                )
                caused_by = event_id
            self.store.append_events(
                harness_run_id=self.harness_run_id,
                events=tuple(writes),
                expected_revision=lease.run_revision,
                lease=lease,
                lease_checked_at_ms=self.clock_ms(),
            )
            return committed
        finally:
            self.store.release_run_lease(lease)

    def _validate_working_set_transition(self, spec: HarnessWorkingSetSpec) -> bool:
        current = self._load_current_working_set_or_none()
        if current == spec:
            return True
        provider = self._load_current_provider_call_or_none()
        if provider is not None and provider.record.status in {
            HarnessProviderCallStatus.CLAIMED,
            HarnessProviderCallStatus.DISPATCHING,
            HarnessProviderCallStatus.UNKNOWN,
        }:
            raise HarnessProviderCallRecoveryRequired(
                "Working Set cannot change while a Provider Call may still act on the prior view"
            )
        self._require_working_set_predecessor(current, spec)
        return False
