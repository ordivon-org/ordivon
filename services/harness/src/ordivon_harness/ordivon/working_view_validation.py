"""Original Working View provenance, evidence and Provider request validation.

Composed only by EventSourcedRunContinuity. Reuses its single Store, lease,
original state and event identity; no separate Writer or authority.
"""
from __future__ import annotations
from anc_canonical import JsonValue
from ..agent_tool_observation import HarnessToolObservation
from ..run_state import HarnessRunState
from ..working_view import (
    AgentWorkingSetTransitionProposal,
    HarnessWorkingSetSpec,
    HarnessWorkingView,
    HarnessWorkingViewSource,
    compile_working_view,
    compile_working_view_with_refs,
)
from ..store import (
    HarnessRunEventRecord,
)
from .continuity_guards import (
    required_event_digest,
)
from .model import (
    AgentCallerIngressRef,
    AgentTurnRequest,
)
from .run_store_port import (
    HarnessProviderCallRequestMismatch,
)


class WorkingViewValidation:
    """Original Working View provenance, evidence and Provider request validation."""

    def _require_working_view_source_authorized(
        self,
        source: HarnessWorkingViewSource,
    ) -> None:
        if not self.contract.privacy.allow_model_content:
            raise ValueError(
                "Working View source requires Contract permission to persist model content"
            )
        if not self.contract.privacy.allow_tool_content and any(
            message.get("role") == "tool" or "toolCalls" in message for message in source.messages
        ):
            raise ValueError(
                "Working View source contains Tool content without Contract permission"
            )

    @staticmethod
    def _require_working_set_predecessor(
        current: HarnessWorkingSetSpec | None,
        spec: HarnessWorkingSetSpec,
    ) -> None:
        if current is None:
            if (
                spec.revision != 1
                or spec.previous_digest is not None
                or spec.parent_attempt_id is not None
            ):
                raise ValueError("initial Working Set revision or predecessor is invalid")
            return
        if spec.attempt_id == current.attempt_id:
            if current.committed:
                raise ValueError("committed Working Set is frozen for this attempt")
            if spec.revision != current.revision + 1 or spec.previous_digest != current.digest:
                raise ValueError("Working Set revision does not extend the current attempt")
            if spec.parent_attempt_id != current.parent_attempt_id:
                raise ValueError("Working Set parent attempt changed within one attempt")
            return
        if not current.committed:
            raise ValueError("Working Set replan requires a committed predecessor")
        if (
            spec.revision != 1
            or spec.parent_attempt_id != current.attempt_id
            or spec.previous_digest != current.digest
        ):
            raise ValueError("Working Set replan does not identify its committed predecessor")

    def _working_set_from_event(self, event: HarnessRunEventRecord) -> HarnessWorkingSetSpec:
        object_digest = required_event_digest(event.data, "workingSetObjectDigest")
        raw = self.store.get_object(
            object_digest,
            expected_kind="harness-working-set-spec",
        )
        if not isinstance(raw, dict):
            raise TypeError("Harness Working Set object is invalid")
        spec = HarnessWorkingSetSpec.from_dict(raw)
        if (
            event.data.get("workingSetDigest") != spec.digest
            or event.data.get("attemptId") != spec.attempt_id
            or event.data.get("workingSetRevision") != spec.revision
            or event.data.get("committed") is not spec.committed
        ):
            raise ValueError("Harness Working Set event differs from its object")
        for pin in spec.pins:
            raw_source = self.store.get_object(
                pin.resolved_digest,
                expected_kind="harness-working-view-source",
            )
            if not isinstance(raw_source, dict):
                raise TypeError("Harness Working Set source object is invalid")
            source = HarnessWorkingViewSource.from_dict(raw_source)
            if (
                source.logical_ref != pin.logical_ref
                or source.logical_generation != pin.logical_generation
            ):
                raise ValueError("Harness Working Set source identity differs")
            self._require_working_view_source_authorized(source)
        return spec

    def _validate_working_set_transition_evidence(
        self,
        event: HarnessRunEventRecord,
        spec: HarnessWorkingSetSpec,
        *,
        previous_event: HarnessRunEventRecord | None,
        previous_spec: HarnessWorkingSetSpec | None,
    ) -> None:
        if "callerIngressPromotionProposalDigest" in event.data:
            return
        legacy_fields = {
            "transitionProposalDigest",
            "transitionProposalObjectDigest",
            "sourceWorkingViewDigest",
        }
        current_fields = {
            "transitionProposalDigest",
            "transitionProposalObjectDigest",
            "sourceWorkingSetDigest",
            "sourceModelViewDigest",
        }
        transition_keys = legacy_fields | current_fields
        present = transition_keys & set(event.data)
        if not present:
            return
        if current_fields.issubset(event.data) and "sourceWorkingViewDigest" not in event.data:
            fields = current_fields
            source_working_set_digest = required_event_digest(event.data, "sourceWorkingSetDigest")
            source_model_view_digest = required_event_digest(event.data, "sourceModelViewDigest")
            legacy = False
        elif legacy_fields.issubset(event.data) and not {
            "sourceWorkingSetDigest",
            "sourceModelViewDigest",
        } & set(event.data):
            fields = legacy_fields
            source_working_set_digest = None
            source_model_view_digest = required_event_digest(event.data, "sourceWorkingViewDigest")
            legacy = True
        else:
            raise ValueError("Working Set transition evidence is incomplete")
        proposal_digest = required_event_digest(event.data, "transitionProposalDigest")
        proposal_object_digest = required_event_digest(event.data, "transitionProposalObjectDigest")
        raw = self.store.get_object(
            proposal_object_digest,
            expected_kind="agent-working-set-transition-proposal",
        )
        if not isinstance(raw, dict):
            raise TypeError("Agent Working Set transition proposal object is invalid")
        proposal = AgentWorkingSetTransitionProposal.from_dict(raw)
        if proposal.digest != proposal_digest:
            raise ValueError("Working Set transition proposal digest differs")
        if spec.attempt_id != proposal.next_attempt_id:
            raise ValueError("Working Set transition attempt differs from its proposal")

        if spec.revision == 1:
            if previous_spec is None or not previous_spec.committed:
                raise ValueError("Working Set transition does not extend a committed predecessor")
            base_view = compile_working_view(previous_spec, self.store)
            if legacy:
                if base_view.digest != source_model_view_digest:
                    raise ValueError(
                        "Working Set transition source view differs from its predecessor"
                    )
            else:
                if previous_spec.digest != source_working_set_digest:
                    raise ValueError(
                        "Working Set transition source WorkingSet differs from its predecessor"
                    )
                matched_provider = False
                for provider_event in self.store.list_run_events(self.harness_run_id):
                    if provider_event.event_kind != "harness.provider-call-completed":
                        continue
                    retained = self._load_provider_from_event(provider_event)
                    if retained.request is None or retained.result is None:
                        continue
                    if retained.result.working_set_transition != proposal:
                        continue
                    effective_view = HarnessWorkingView(
                        attempt_id=previous_spec.attempt_id,
                        working_set_digest=previous_spec.digest,
                        messages=retained.request.messages,
                    )
                    if (
                        retained.request.context_digest == source_model_view_digest
                        and effective_view.digest == source_model_view_digest
                        and retained.request.messages[: len(base_view.messages)]
                        == base_view.messages
                    ):
                        matched_provider = True
                        break
                if not matched_provider:
                    raise ValueError(
                        "Working Set transition source model view lacks matching Provider evidence"
                    )
            if spec.pins or spec.committed:
                raise ValueError("Working Set transition replan revision is invalid")
            return

        if previous_event is None or previous_spec is None:
            raise ValueError("Working Set transition continuation has no predecessor")
        for field in fields:
            if previous_event.data.get(field) != event.data.get(field):
                raise ValueError("Working Set transition evidence changed within one transaction")
        if previous_spec.attempt_id != spec.attempt_id:
            raise ValueError("Working Set transition attempt changed within transaction")
        if spec.revision == 2:
            if previous_spec.revision != 1 or spec.pins != proposal.pins or spec.committed:
                raise ValueError("Working Set transition selection revision is invalid")
            return
        if spec.revision == 3:
            if (
                previous_spec.revision != 2
                or spec.pins != proposal.pins
                or not spec.committed
                or spec.commit_basis != proposal.basis
            ):
                raise ValueError("Working Set transition commit revision is invalid")
            return
        raise ValueError("Working Set transition has an unsupported revision")

    def _require_working_view_request_against_state(
        self,
        request: AgentTurnRequest,
        spec: HarnessWorkingSetSpec,
        state: HarnessRunState,
        *,
        before_event_sequence: int | None = None,
    ) -> None:
        base_view, expected_working_set_refs = compile_working_view_with_refs(spec, self.store)
        if request.messages[: len(base_view.messages)] != base_view.messages:
            raise HarnessProviderCallRequestMismatch(
                "Provider Call request does not preserve the current committed Working View prefix"
            )
        overlay_messages = request.messages[len(base_view.messages) :]
        pause_sequence, raw_caller_messages = self._caller_cognition_ingress_for_messages(
            state.messages,
            before_event_sequence=before_event_sequence,
        )
        suppressed_caller_indexes = self._durable_caller_ingress_indexes(
            spec,
            pause_sequence=pause_sequence,
            caller_messages=raw_caller_messages,
        )
        caller_entries = tuple(
            (index, message)
            for index, message in enumerate(raw_caller_messages)
            if index not in suppressed_caller_indexes
        )
        caller_messages = tuple(message for _index, message in caller_entries)
        retained_observations = (
            tuple(HarnessToolObservation.from_dict(raw) for raw in state.observations)
            if state.observations_retained
            else ()
        )
        segments = (
            self._current_attempt_tool_exchange_segments(
                retained_observations,
                current=spec,
                before_event_sequence=before_event_sequence,
            )
            if retained_observations
            else ()
        )
        expected_overlay: list[dict[str, JsonValue]] = []
        expected_caller_refs: list[AgentCallerIngressRef] = []
        caller_inserted = False

        def insert_caller_messages() -> None:
            start = len(base_view.messages) + len(expected_overlay)
            expected_overlay.extend(dict(message) for message in caller_messages)
            expected_caller_refs.extend(
                AgentCallerIngressRef(
                    caller_message_index=caller_index,
                    request_message_index=start + position,
                )
                for position, (caller_index, _message) in enumerate(caller_entries)
            )

        for sequence, segment in segments:
            if (
                caller_messages
                and not caller_inserted
                and pause_sequence is not None
                and sequence > pause_sequence
            ):
                insert_caller_messages()
                caller_inserted = True
            expected_overlay.extend(dict(message) for message in segment)
        if caller_messages and not caller_inserted:
            insert_caller_messages()
        if overlay_messages != tuple(expected_overlay):
            raise HarnessProviderCallRequestMismatch(
                (
                    "Provider Working View overlay differs from durable Tool/caller cognition authority"
                    if caller_messages
                    else "Provider Working View overlay is not a completed Provider-authored Tool exchange"
                )
            )
        if request.caller_ingress_refs and request.caller_ingress_refs != tuple(
            expected_caller_refs
        ):
            raise HarnessProviderCallRequestMismatch(
                "Provider caller ingress provenance differs from durable cognition authority"
            )
        if request.working_set_refs and request.working_set_refs != expected_working_set_refs:
            raise HarnessProviderCallRequestMismatch(
                "Provider current WorkingSet provenance differs from durable cognition authority"
            )
        effective_view = HarnessWorkingView(
            attempt_id=spec.attempt_id,
            working_set_digest=spec.digest,
            messages=request.messages,
        )
        if request.context_digest != effective_view.digest:
            raise HarnessProviderCallRequestMismatch(
                "Provider Call request digest differs from its current Working View plus transient cognition"
            )

    def _require_current_working_view_request(
        self,
        request: AgentTurnRequest | None,
    ) -> None:
        spec = self._load_current_working_set_or_none()
        if spec is None:
            return
        if not spec.committed:
            raise HarnessProviderCallRequestMismatch(
                "Provider Call cannot bind an uncommitted Working Set"
            )
        if request is None:
            raise HarnessProviderCallRequestMismatch(
                "Provider Call for a Working Set requires its exact Agent Turn request"
            )
        self._require_working_view_request_against_state(
            request,
            spec,
            self._require_state(),
        )
