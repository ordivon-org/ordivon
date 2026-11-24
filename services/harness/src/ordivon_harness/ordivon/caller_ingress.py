"""Caller-owned cognition ingress and durable promotion, using original Run authority.

Composed only by EventSourcedRunContinuity. Reuses its single Store, lease,
original state and event identity; no separate Writer or authority.
"""
from __future__ import annotations
from anc_canonical import JsonValue, canonical_digest
from ..protocol import (
    HarnessProviderCallStatus,
    HarnessRunPauseReason,
)
from ..working_view import (
    AgentCallerIngressPromotionProposal,
    HarnessWorkingSetPin,
    HarnessWorkingSetSpec,
    HarnessWorkingView,
    HarnessWorkingViewSource,
    compile_working_view,
)
from ..store import (
    HarnessEventWrite,
    HarnessRunEventRecord,
    StoredHarnessObject,
)
from .continuity_guards import (
    continuity_event_id,
    required_event_digest,
)
from .run_store_port import (
    HarnessProviderCallRecoveryRequired,
    HarnessProviderCallRequestMismatch,
)


class CallerIngressContinuity:
    """Caller-owned cognition ingress and durable promotion, using original Run authority."""

    def _caller_ingress_promotion_source(
        self,
        *,
        pause_sequence: int,
        caller_messages: tuple[dict[str, JsonValue], ...],
        message_indexes: tuple[int, ...],
    ) -> HarnessWorkingViewSource:
        try:
            selected_messages = tuple(caller_messages[index] for index in message_indexes)
        except IndexError as error:
            raise ValueError(
                "caller ingress promotion message index is outside current caller cognition"
            ) from error
        source_binding = {
            "schemaVersion": 1,
            "kind": "ordivon.caller-ingress-source-binding",
            "harnessRunId": self.harness_run_id,
            "pauseSequence": pause_sequence,
            "callerMessageIndexes": list(message_indexes),
            "messages": list(selected_messages),
        }
        source_binding_digest = canonical_digest(source_binding)
        return HarnessWorkingViewSource(
            logical_ref=f"caller-ingress:{source_binding_digest}",
            logical_generation=f"caller-ingress-selection:{source_binding_digest}",
            messages=selected_messages,
        )

    def apply_caller_ingress_promotion(
        self,
        proposal: AgentCallerIngressPromotionProposal,
        *,
        source_working_set_digest: str,
        source_model_view_digest: str,
    ) -> HarnessWorkingSetSpec:
        """Atomically materialize exact current caller ingress and select it.

        The Agent names only retained exact pins, one successor slot, and exact
        indexes into the caller ingress it actually saw. Harness derives the
        source bytes and source identity from durable Provider/Snapshot authority.
        """
        if not self.contract.privacy.allow_model_content:
            raise ValueError("caller ingress promotion requires permission to retain model content")

        def existing_promotion() -> HarnessWorkingSetSpec | None:
            current = self._load_current_working_set_or_none()
            if (
                current is None
                or not current.committed
                or current.attempt_id != proposal.next_attempt_id
                or current.commit_basis != proposal.basis
            ):
                return None
            attempt_events = [
                event
                for event in self.store.list_run_events(self.harness_run_id)
                if event.event_kind == "harness.working-set-recorded"
                and event.data.get("attemptId") == proposal.next_attempt_id
            ]
            if len(attempt_events) != 3 or any(
                event.data.get("callerIngressPromotionProposalDigest") != proposal.digest
                for event in attempt_events
            ):
                return None
            promoted = [pin for pin in current.pins if pin.slot == proposal.promotion_slot]
            if len(promoted) != 1:
                return None
            return current

        replay = existing_promotion()
        if replay is not None:
            return replay
        now_ms = self.clock_ms()
        lease = self._acquire_lease("caller-ingress-promotion", proposal.digest, now_ms=now_ms)
        try:
            replay = existing_promotion()
            if replay is not None:
                return replay
            current = self._load_current_working_set_or_none()
            if current is None or not current.committed:
                raise ValueError("caller ingress promotion requires a committed predecessor")
            if proposal.next_attempt_id == current.attempt_id:
                raise ValueError("caller ingress promotion requires a new attempt identity")
            if current.digest != source_working_set_digest:
                raise HarnessProviderCallRequestMismatch(
                    "caller ingress promotion source WorkingSet is no longer current"
                )
            if any(pin.slot == proposal.promotion_slot for pin in current.pins):
                raise ValueError(
                    "caller ingress promotion slot already exists in current cognition"
                )
            base_view = compile_working_view(current, self.store)
            provider = self._load_current_provider_call_or_none()
            if (
                provider is None
                or provider.record.status is not HarnessProviderCallStatus.COMPLETED
            ):
                raise HarnessProviderCallRecoveryRequired(
                    "caller ingress promotion requires a completed Provider proposal"
                )
            if provider.request is None or provider.result is None:
                raise HarnessProviderCallRecoveryRequired(
                    "caller ingress promotion requires retained exact Provider request/result evidence"
                )
            if provider.result.caller_ingress_promotion != proposal:
                raise HarnessProviderCallRequestMismatch(
                    "completed Provider result differs from the caller ingress promotion proposal"
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
                    "caller ingress promotion source model view differs from the completed Provider request"
                )
            self._require_working_view_request_against_state(
                provider.request,
                current,
                provider.state,
            )
            pause_sequence, caller_messages = self._caller_cognition_ingress_for_messages(
                provider.state.messages
            )
            if pause_sequence is None or not caller_messages:
                raise ValueError(
                    "caller ingress promotion requires current needs-input caller cognition"
                )
            promotable_indexes = {
                ref.caller_message_index for ref in provider.request.caller_ingress_refs
            }
            if not set(proposal.caller_message_indexes).issubset(promotable_indexes):
                raise ValueError(
                    "caller ingress promotion indexes were not identified as promotable in the exact Provider request"
                )
            for ref in provider.request.caller_ingress_refs:
                if (
                    provider.request.messages[ref.request_message_index]
                    != caller_messages[ref.caller_message_index]
                ):
                    raise HarnessProviderCallRequestMismatch(
                        "caller ingress request provenance points to different message bytes"
                    )
            already_durable = self._durable_caller_ingress_indexes(
                current,
                pause_sequence=pause_sequence,
                caller_messages=caller_messages,
            )
            overlap = already_durable & set(proposal.caller_message_indexes)
            if overlap:
                raise ValueError(
                    "caller ingress promotion indexes are already durable in current cognition: "
                    + ", ".join(str(index) for index in sorted(overlap))
                )
            source = self._caller_ingress_promotion_source(
                pause_sequence=pause_sequence,
                caller_messages=caller_messages,
                message_indexes=proposal.caller_message_indexes,
            )
            self._require_working_view_source_authorized(source)
            source_object = self.store.put_object(
                source.to_dict(), kind="harness-working-view-source"
            )
            promoted_pin = HarnessWorkingSetPin(
                slot=proposal.promotion_slot,
                logical_ref=source.logical_ref,
                logical_generation=source.logical_generation,
                resolved_digest=source_object.digest,
            )
            successor_pins = tuple(sorted((*current.pins, promoted_pin), key=lambda pin: pin.slot))
            source_objects: list[StoredHarnessObject] = []
            for pin in successor_pins:
                raw_source = self.store.get_object(
                    pin.resolved_digest,
                    expected_kind="harness-working-view-source",
                )
                if not isinstance(raw_source, dict):
                    raise TypeError("caller ingress promotion source object is invalid")
                exact_source = HarnessWorkingViewSource.from_dict(raw_source)
                if (
                    exact_source.logical_ref != pin.logical_ref
                    or exact_source.logical_generation != pin.logical_generation
                ):
                    raise ValueError("caller ingress promotion pin differs from its exact source")
                self._require_working_view_source_authorized(exact_source)
                source_objects.append(self.store.inspect_object(pin.resolved_digest))

            replanned = current.replan(proposal.next_attempt_id)
            selected = replanned.select_pins(successor_pins)
            committed = selected.commit(proposal.basis)
            chain = (replanned, selected, committed)
            self._require_working_set_predecessor(current, replanned)
            self._require_working_set_predecessor(replanned, selected)
            self._require_working_set_predecessor(selected, committed)

            proposal_object = self.store.put_object(
                proposal.to_dict(), kind="agent-caller-ingress-promotion-proposal"
            )
            spec_objects = tuple(
                self.store.put_object(spec.to_dict(), kind="harness-working-set-spec")
                for spec in chain
            )
            recorded_at_ms = self._recorded_time(now_ms)
            caused_by = self._latest_event_id()
            writes: list[HarnessEventWrite] = []
            for spec, spec_object in zip(chain, spec_objects, strict=True):
                event_id = continuity_event_id("working-set", spec.digest)
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
                            "callerIngressPromotionProposalDigest": proposal.digest,
                            "callerIngressPromotionProposalObjectDigest": proposal_object.digest,
                            "sourceWorkingSetDigest": source_working_set_digest,
                            "sourceModelViewDigest": source_model_view_digest,
                            "callerIngressPauseSequence": pause_sequence,
                            "callerIngressMessageIndexes": list(proposal.caller_message_indexes),
                            "promotedSourceObjectDigest": source_object.digest,
                        },
                        recorded_at_ms=recorded_at_ms,
                        caused_by_event_id=caused_by,
                        referenced_objects=(
                            spec_object,
                            proposal_object,
                            *tuple(source_objects),
                        ),
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

    def _caller_cognition_ingress_for_messages(
        self,
        messages: tuple[dict[str, JsonValue], ...],
        *,
        before_event_sequence: int | None = None,
    ) -> tuple[int | None, tuple[dict[str, JsonValue], ...]]:
        """Derive the current caller-owned interaction ingress from Snapshot authority.

        The latest needs-input Snapshot is the interaction boundary. Exact plain
        user messages immediately following that Snapshot state are caller
        cognition until the next non-user Run-history message. They are not
        WorkingSet selection and are consumed by the next needs-input Snapshot.
        """
        pause_event: HarnessRunEventRecord | None = None
        for event in self.store.list_run_events(self.harness_run_id):
            if before_event_sequence is not None and event.sequence >= before_event_sequence:
                break
            if (
                event.event_kind == "harness.run-paused"
                and event.data.get("pauseReason") == HarnessRunPauseReason.NEEDS_INPUT.value
            ):
                pause_event = event
        if pause_event is None:
            return None, ()
        retained = self._load_snapshot_from_event(pause_event)
        if not retained.state.messages_retained:
            raise HarnessProviderCallRecoveryRequired(
                "caller cognition ingress requires retained model content"
            )
        prefix = retained.state.messages
        if messages[: len(prefix)] != prefix:
            raise HarnessProviderCallRequestMismatch(
                "caller cognition ingress state does not extend the latest needs-input Snapshot"
            )
        ingress: list[dict[str, JsonValue]] = []
        for message in messages[len(prefix) :]:
            if message.get("role") != "user":
                break
            if set(message) != {"role", "content"} or not isinstance(message.get("content"), str):
                raise HarnessProviderCallRequestMismatch(
                    "caller cognition ingress must contain plain user messages"
                )
            ingress.append(dict(message))
        return pause_event.sequence, tuple(ingress)

    def _validate_caller_ingress_promotion_attempt(self, attempt_id: str) -> None:
        working_events = [
            event
            for event in self.store.list_run_events(self.harness_run_id)
            if event.event_kind == "harness.working-set-recorded"
        ]
        attempt_events = [
            event
            for event in working_events
            if event.data.get("attemptId") == attempt_id
            and "callerIngressPromotionProposalDigest" in event.data
        ]
        if len(attempt_events) != 3:
            raise ValueError(
                "caller ingress promotion attempt must contain exactly three WorkingSet revisions"
            )
        attempt_events.sort(key=lambda event: event.sequence)
        first_sequence = attempt_events[0].sequence
        predecessor_events = [event for event in working_events if event.sequence < first_sequence]
        if not predecessor_events:
            raise ValueError("caller ingress promotion attempt has no predecessor")
        previous_event = predecessor_events[-1]
        previous_spec = self._working_set_from_event(previous_event)
        for event in attempt_events:
            spec = self._working_set_from_event(event)
            self._require_working_set_predecessor(previous_spec, spec)
            self._validate_caller_ingress_promotion_evidence(
                event,
                spec,
                previous_event=previous_event,
                previous_spec=previous_spec,
            )
            previous_event = event
            previous_spec = spec

    def _durable_caller_ingress_indexes(
        self,
        current: HarnessWorkingSetSpec,
        *,
        pause_sequence: int | None,
        caller_messages: tuple[dict[str, JsonValue], ...],
    ) -> frozenset[int]:
        if pause_sequence is None or not caller_messages:
            return frozenset()
        current_source_digests = {pin.resolved_digest for pin in current.pins}
        suppressed: set[int] = set()
        validated_attempts: set[str] = set()
        for event in self.store.list_run_events(self.harness_run_id):
            if (
                event.event_kind != "harness.working-set-recorded"
                or event.data.get("committed") is not True
                or event.data.get("callerIngressPauseSequence") != pause_sequence
            ):
                continue
            source_digest = event.data.get("promotedSourceObjectDigest")
            if source_digest not in current_source_digests:
                continue
            attempt_id = event.data.get("attemptId")
            if not isinstance(attempt_id, str):
                raise ValueError("caller ingress promotion attempt identity is invalid")
            if attempt_id not in validated_attempts:
                self._validate_caller_ingress_promotion_attempt(attempt_id)
                validated_attempts.add(attempt_id)
            proposal_object_digest = required_event_digest(
                event.data, "callerIngressPromotionProposalObjectDigest"
            )
            raw_proposal = self.store.get_object(
                proposal_object_digest,
                expected_kind="agent-caller-ingress-promotion-proposal",
            )
            if not isinstance(raw_proposal, dict):
                raise TypeError("caller ingress promotion proposal object is invalid")
            proposal = AgentCallerIngressPromotionProposal.from_dict(raw_proposal)
            expected_source = self._caller_ingress_promotion_source(
                pause_sequence=pause_sequence,
                caller_messages=caller_messages,
                message_indexes=proposal.caller_message_indexes,
            )
            raw_source = self.store.get_object(
                source_digest,
                expected_kind="harness-working-view-source",
            )
            if not isinstance(raw_source, dict):
                raise TypeError("promoted caller ingress source object is invalid")
            if HarnessWorkingViewSource.from_dict(raw_source) != expected_source:
                raise HarnessProviderCallRequestMismatch(
                    "promoted caller source differs from its current interaction provenance"
                )
            suppressed.update(proposal.caller_message_indexes)
        return frozenset(suppressed)

    def project_current_caller_ingress(
        self,
        messages: tuple[dict[str, JsonValue], ...],
    ) -> tuple[tuple[int, dict[str, JsonValue]], ...]:
        current = self.load_current_working_set()
        pause_sequence, caller_messages = self._caller_cognition_ingress_for_messages(messages)
        suppressed = self._durable_caller_ingress_indexes(
            current,
            pause_sequence=pause_sequence,
            caller_messages=caller_messages,
        )
        return tuple(
            (index, dict(message))
            for index, message in enumerate(caller_messages)
            if index not in suppressed
        )

    def _validate_caller_ingress_promotion_evidence(
        self,
        event: HarnessRunEventRecord,
        spec: HarnessWorkingSetSpec,
        *,
        previous_event: HarnessRunEventRecord | None,
        previous_spec: HarnessWorkingSetSpec | None,
    ) -> None:
        fields = {
            "callerIngressPromotionProposalDigest",
            "callerIngressPromotionProposalObjectDigest",
            "sourceWorkingSetDigest",
            "sourceModelViewDigest",
            "callerIngressPauseSequence",
            "callerIngressMessageIndexes",
            "promotedSourceObjectDigest",
        }
        if "callerIngressPromotionProposalDigest" not in event.data:
            return
        if not fields.issubset(event.data):
            raise ValueError("caller ingress promotion evidence is incomplete")
        proposal_digest = required_event_digest(event.data, "callerIngressPromotionProposalDigest")
        proposal_object_digest = required_event_digest(
            event.data, "callerIngressPromotionProposalObjectDigest"
        )
        source_working_set_digest = required_event_digest(event.data, "sourceWorkingSetDigest")
        source_model_view_digest = required_event_digest(event.data, "sourceModelViewDigest")
        promoted_source_object_digest = required_event_digest(
            event.data, "promotedSourceObjectDigest"
        )
        pause_sequence = event.data.get("callerIngressPauseSequence")
        raw_indexes = event.data.get("callerIngressMessageIndexes")
        if type(pause_sequence) is not int or pause_sequence < 1:
            raise ValueError("caller ingress promotion pause sequence is invalid")
        if not isinstance(raw_indexes, list):
            raise ValueError("caller ingress promotion message indexes are invalid")
        raw_proposal = self.store.get_object(
            proposal_object_digest,
            expected_kind="agent-caller-ingress-promotion-proposal",
        )
        if not isinstance(raw_proposal, dict):
            raise TypeError("caller ingress promotion proposal object is invalid")
        proposal = AgentCallerIngressPromotionProposal.from_dict(raw_proposal)
        if proposal.digest != proposal_digest:
            raise ValueError("caller ingress promotion proposal digest differs")
        if list(proposal.caller_message_indexes) != raw_indexes:
            raise ValueError("caller ingress promotion indexes differ from proposal")
        if spec.attempt_id != proposal.next_attempt_id:
            raise ValueError("caller ingress promotion attempt differs from proposal")
        raw_source = self.store.get_object(
            promoted_source_object_digest,
            expected_kind="harness-working-view-source",
        )
        if not isinstance(raw_source, dict):
            raise TypeError("promoted caller ingress source object is invalid")
        promoted_source = HarnessWorkingViewSource.from_dict(raw_source)
        self._require_working_view_source_authorized(promoted_source)
        promoted_pin = HarnessWorkingSetPin(
            slot=proposal.promotion_slot,
            logical_ref=promoted_source.logical_ref,
            logical_generation=promoted_source.logical_generation,
            resolved_digest=promoted_source_object_digest,
        )
        expected_pins: tuple[HarnessWorkingSetPin, ...] | None = None

        if spec.revision == 1:
            if previous_spec is None or not previous_spec.committed:
                raise ValueError("caller ingress promotion does not extend a committed predecessor")
            if previous_spec.digest != source_working_set_digest:
                raise ValueError(
                    "caller ingress promotion source WorkingSet differs from predecessor"
                )
            if any(pin.slot == proposal.promotion_slot for pin in previous_spec.pins):
                raise ValueError(
                    "caller ingress promotion slot collides with predecessor cognition"
                )
            base_view = compile_working_view(previous_spec, self.store)
            matched_provider = False
            for provider_event in self.store.list_run_events(self.harness_run_id):
                if provider_event.event_kind != "harness.provider-call-completed":
                    continue
                retained = self._load_provider_from_event(provider_event)
                if retained.request is None or retained.result is None:
                    continue
                if retained.result.caller_ingress_promotion != proposal:
                    continue
                promotable_indexes = {
                    ref.caller_message_index for ref in retained.request.caller_ingress_refs
                }
                if not set(proposal.caller_message_indexes).issubset(promotable_indexes):
                    continue
                effective_view = HarnessWorkingView(
                    attempt_id=previous_spec.attempt_id,
                    working_set_digest=previous_spec.digest,
                    messages=retained.request.messages,
                )
                if (
                    retained.request.context_digest != source_model_view_digest
                    or effective_view.digest != source_model_view_digest
                    or retained.request.messages[: len(base_view.messages)] != base_view.messages
                ):
                    continue
                derived_pause, caller_messages = self._caller_cognition_ingress_for_messages(
                    retained.state.messages,
                    before_event_sequence=provider_event.sequence + 1,
                )
                if derived_pause != pause_sequence:
                    continue
                expected_source = self._caller_ingress_promotion_source(
                    pause_sequence=pause_sequence,
                    caller_messages=caller_messages,
                    message_indexes=proposal.caller_message_indexes,
                )
                if expected_source != promoted_source:
                    continue
                matched_provider = True
                break
            if not matched_provider:
                raise ValueError(
                    "caller ingress promotion lacks matching Provider/caller provenance"
                )
            if spec.pins or spec.committed:
                raise ValueError("caller ingress promotion replan revision is invalid")
            return

        if previous_event is None or previous_spec is None:
            raise ValueError("caller ingress promotion continuation has no predecessor")
        source_predecessor = next(
            (
                self._working_set_from_event(candidate)
                for candidate in self.store.list_run_events(self.harness_run_id)
                if candidate.event_kind == "harness.working-set-recorded"
                and candidate.data.get("workingSetDigest") == source_working_set_digest
            ),
            None,
        )
        if source_predecessor is None or not source_predecessor.committed:
            raise ValueError("caller ingress promotion source predecessor is missing")
        expected_pins = tuple(
            sorted((*source_predecessor.pins, promoted_pin), key=lambda pin: pin.slot)
        )
        for field in fields:
            if previous_event.data.get(field) != event.data.get(field):
                raise ValueError("caller ingress promotion evidence changed within one transaction")
        if previous_spec.attempt_id != spec.attempt_id:
            raise ValueError("caller ingress promotion attempt changed within transaction")
        if spec.revision == 2:
            if previous_spec.revision != 1 or spec.pins != expected_pins or spec.committed:
                raise ValueError("caller ingress promotion selection revision is invalid")
            return
        if spec.revision == 3:
            if (
                previous_spec.revision != 2
                or spec.pins != expected_pins
                or not spec.committed
                or spec.commit_basis != proposal.basis
            ):
                raise ValueError("caller ingress promotion commit revision is invalid")
            return
        raise ValueError("caller ingress promotion has an unsupported revision")
