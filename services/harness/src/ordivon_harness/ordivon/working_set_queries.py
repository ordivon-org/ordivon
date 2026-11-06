from __future__ import annotations

from anc_canonical import JsonValue

from ..agent_tool_observation import HarnessToolObservation
from ..protocol import HarnessToolStepIntent, HarnessToolStepReceipt
from .continuity_guards import _TOOL_EVENT_KINDS, required_event_digest
from ..working_view import (
    WORKING_SET_HISTORY_CONTROL_NAME,
    HarnessWorkingSetSpec,
    parse_working_set_history_query,
)
from .model import AgentToolCall
from .run_store_port import (
    HarnessProviderCallRecoveryRequired,
    HarnessProviderCallRequestMismatch,
)


class _WorkingSetReadQueries:
    """Journal-backed Working Set history projections; no mutation authority."""

    def load_current_working_set(self) -> HarnessWorkingSetSpec:
        value = self._load_current_working_set_or_none()
        if value is None:
            raise KeyError("Harness Run has no Working Set")
        return value

    def inspect_working_set_history(
        self,
        *,
        limit: int,
        before_sequence: int | None = None,
    ) -> dict[str, JsonValue]:
        """List exact identities from earlier committed Working Sets only."""
        limit, before_sequence = parse_working_set_history_query(
            {
                "limit": limit,
                **(
                    {}
                    if before_sequence is None
                    else {"before_sequence": before_sequence}
                ),
            }
        )
        if not self.contract.privacy.allow_model_content:
            raise ValueError(
                "Working Set history inspection requires model-content authority"
            )
        if not self.contract.privacy.allow_tool_content:
            raise ValueError(
                "Working Set history inspection requires Tool-content authority because its Provider-faithful response uses a Tool channel"
            )
        current = self.load_current_working_set()
        return self._working_set_history_for(
            current,
            limit=limit,
            before_sequence=before_sequence,
        )

    def _working_set_history_for(
        self,
        current: HarnessWorkingSetSpec,
        *,
        limit: int,
        before_sequence: int | None,
    ) -> dict[str, JsonValue]:
        """Project a mechanical history catalog relative to one exact cognition head."""
        if not current.committed:
            raise ValueError(
                "Working Set history inspection requires a committed cognition head"
            )
        current_sequence = self._working_set_event_sequence(current)
        cutoff = (
            current_sequence
            if before_sequence is None
            else min(current_sequence, before_sequence)
        )
        candidates = [
            event
            for event in self.store.list_run_events(self.harness_run_id)
            if event.event_kind == "harness.working-set-recorded"
            and event.sequence < cutoff
            and event.data.get("committed") is True
        ]
        candidates.reverse()
        selected_events = candidates[:limit]
        selections: list[JsonValue] = []
        for event in selected_events:
            spec = self._working_set_from_event(event)
            if not spec.committed:
                raise ValueError(
                    "Working Set history committed event decoded as mutable state"
                )
            selections.append(
                {
                    "eventSequence": event.sequence,
                    "attemptId": spec.attempt_id,
                    "workingSetDigest": spec.digest,
                    "pins": [pin.to_dict() for pin in spec.pins],
                }
            )
        return {
            "schemaVersion": 1,
            "kind": "ordivon.harness-working-set-history",
            "currentAttemptId": current.attempt_id,
            "currentWorkingSetDigest": current.digest,
            "currentWorkingSetEventSequence": current_sequence,
            "selections": selections,
            "nextBeforeSequence": (
                selected_events[-1].sequence
                if len(candidates) > len(selected_events) and selected_events
                else None
            ),
        }

    def _expected_working_set_history_observation(
        self,
        call: AgentToolCall,
        *,
        current: HarnessWorkingSetSpec,
    ) -> HarnessToolObservation:
        if call.name != WORKING_SET_HISTORY_CONTROL_NAME:
            raise ValueError("Working Set history observation requires its reserved control")
        limit, before_sequence = parse_working_set_history_query(call.arguments)
        return HarnessToolObservation(
            tool_call_id=call.tool_call_id,
            tool_name=call.name,
            status="observed",
            structured_content=self._working_set_history_for(
                current,
                limit=limit,
                before_sequence=before_sequence,
            ),
        )

    def _load_current_working_set_or_none(self) -> HarnessWorkingSetSpec | None:
        event = self._heads().working_set
        return None if event is None else self._working_set_from_event(event)

    def _working_set_event_sequence(self, spec: HarnessWorkingSetSpec) -> int:
        matches = [
            event.sequence
            for event in self.store.list_run_events(self.harness_run_id)
            if event.event_kind == "harness.working-set-recorded"
            and event.data.get("workingSetDigest") == spec.digest
        ]
        if len(matches) != 1:
            raise ValueError(
                "Harness Working Set must have exactly one durable Journal event"
            )
        return matches[0]

    def _current_attempt_tool_exchange_segments(
        self,
        observations: tuple[HarnessToolObservation, ...],
        *,
        current: HarnessWorkingSetSpec,
        before_event_sequence: int | None = None,
    ) -> tuple[tuple[int, tuple[dict[str, JsonValue], ...]], ...]:
        if not self.contract.privacy.allow_model_content:
            raise HarnessProviderCallRecoveryRequired(
                "transient Tool exchange recovery requires retained model content"
            )
        if not self.contract.privacy.allow_tool_content:
            raise HarnessProviderCallRecoveryRequired(
                "transient Tool exchange recovery requires retained Tool content"
            )
        if not current.committed:
            raise HarnessProviderCallRequestMismatch(
                "transient Tool exchange recovery requires a committed Working Set"
            )
        boundary_sequence = self._working_set_event_sequence(current)
        events = self.store.list_run_events(self.harness_run_id)
        observations_by_call: dict[str, HarnessToolObservation] = {}
        for observation in observations:
            if observation.tool_call_id in observations_by_call:
                raise HarnessProviderCallRequestMismatch(
                    "recovered Tool Observation identities must remain unique"
                )
            observations_by_call[observation.tool_call_id] = observation

        terminal_tool_evidence: dict[
            tuple[str, str], tuple[HarnessToolStepIntent, HarnessToolObservation]
        ] = {}
        for event in events:
            if event.sequence <= boundary_sequence:
                continue
            if (
                before_event_sequence is not None
                and event.sequence >= before_event_sequence
            ):
                break
            if event.event_kind not in _TOOL_EVENT_KINDS:
                continue
            receipt_object_digest = event.data.get("receiptObjectDigest")
            observation_object_digest = event.data.get("observationObjectDigest")
            if receipt_object_digest is None or observation_object_digest is None:
                continue
            self._validate_tool_event(event)
            if not isinstance(receipt_object_digest, str) or not isinstance(
                observation_object_digest, str
            ):
                raise ValueError("Tool recovery event object references are invalid")
            raw_receipt = self.store.get_object(
                receipt_object_digest,
                expected_kind="harness-tool-step-receipt",
            )
            raw_intent = self.store.get_object(
                required_event_digest(event.data, "toolStepIntentObjectDigest"),
                expected_kind="harness-tool-step-intent",
            )
            raw_observation = self.store.get_object(
                observation_object_digest,
                expected_kind="harness-tool-observation",
            )
            if not isinstance(raw_receipt, dict) or not isinstance(raw_intent, dict):
                raise TypeError("Tool recovery receipt or intent object is invalid")
            if not isinstance(raw_observation, dict):
                raise TypeError("Tool recovery Observation object is invalid")
            receipt = HarnessToolStepReceipt.from_dict(raw_receipt)
            if not receipt.terminal:
                continue
            intent = HarnessToolStepIntent.from_dict(raw_intent)
            observation = HarnessToolObservation.from_dict(raw_observation)
            if (
                observation.tool_call_id != intent.tool_call_id
                or observation.tool_name != intent.tool_name
                or observation.digest != receipt.observation_digest
            ):
                raise HarnessProviderCallRequestMismatch(
                    "durable Tool recovery evidence differs from its intent/receipt"
                )
            terminal_tool_evidence[(intent.turn_id, intent.tool_call_id)] = (
                intent,
                observation,
            )

        segments: list[tuple[int, tuple[dict[str, JsonValue], ...]]] = []
        for event in events:
            if event.sequence <= boundary_sequence:
                continue
            if (
                before_event_sequence is not None
                and event.sequence >= before_event_sequence
            ):
                break
            if event.event_kind != "harness.provider-call-completed":
                continue
            retained = self._load_provider_from_event(event)
            result = retained.result
            if result is None:
                raise HarnessProviderCallRecoveryRequired(
                    "current-attempt Tool exchange recovery requires exact Provider result content"
                )
            if not result.tool_calls:
                continue
            assistant_message: dict[str, JsonValue] = {
                "role": "assistant",
                "content": result.content,
                "toolCalls": [call.to_dict() for call in result.tool_calls],
            }
            turn_messages: list[dict[str, JsonValue]] = [assistant_message]
            for call in result.tool_calls:
                observation = observations_by_call.get(call.tool_call_id)
                if observation is None or observation.tool_name != call.name:
                    raise HarnessProviderCallRecoveryRequired(
                        "current-attempt Provider Tool call lacks its recovered exact Observation"
                    )
                if call.argument_error is None:
                    if call.name == WORKING_SET_HISTORY_CONTROL_NAME:
                        expected_history = self._expected_working_set_history_observation(
                            call,
                            current=current,
                        )
                        if observation != expected_history:
                            raise HarnessProviderCallRequestMismatch(
                                "recovered Working Set history Observation differs from deterministic Journal projection"
                            )
                    else:
                        evidence = terminal_tool_evidence.get(
                            (retained.record.turn_id, call.tool_call_id)
                        )
                        if evidence is None:
                            raise HarnessProviderCallRecoveryRequired(
                                "current-attempt Provider Tool call lacks terminal durable Tool evidence"
                            )
                        intent, durable_observation = evidence
                        if (
                            intent.tool_call_digest != call.digest
                            or durable_observation != observation
                        ):
                            raise HarnessProviderCallRequestMismatch(
                                "recovered Tool exchange differs from durable Provider/Tool evidence"
                            )
                else:
                    error = observation.structured_content.get("error")
                    if (
                        observation.status != "rejected"
                        or not isinstance(error, dict)
                        or error.get("safeToCorrect") is not True
                        or error.get("physicalDispatch") is not False
                    ):
                        raise HarnessProviderCallRequestMismatch(
                            "local Tool correction recovery lacks exact no-dispatch evidence"
                        )
                turn_messages.append(observation.to_model_message())
            segments.append((event.sequence, tuple(turn_messages)))
        return tuple(segments)

    def load_current_attempt_tool_exchange_messages(
        self,
        observations: tuple[HarnessToolObservation, ...],
    ) -> tuple[dict[str, JsonValue], ...]:
        """Rebuild exact transient Tool exchanges for the current committed attempt."""
        if not observations:
            return ()
        current = self.load_current_working_set()
        return tuple(
            message
            for _sequence, segment in self._current_attempt_tool_exchange_segments(
                observations,
                current=current,
            )
            for message in segment
        )

    def load_current_attempt_cognition_overlay_messages(
        self,
        messages: tuple[dict[str, JsonValue], ...],
        observations: tuple[HarnessToolObservation, ...],
    ) -> dict[str, JsonValue]:
        """Rebuild ordered non-WorkingSet cognition for the current interaction."""
        current = self.load_current_working_set()
        pause_sequence, caller_messages = self._caller_cognition_ingress_for_messages(
            messages
        )
        segments = (
            self._current_attempt_tool_exchange_segments(
                observations,
                current=current,
            )
            if observations
            else ()
        )
        pre_caller: list[dict[str, JsonValue]] = []
        post_caller: list[dict[str, JsonValue]] = []
        for sequence, segment in segments:
            target = (
                pre_caller
                if pause_sequence is not None and sequence < pause_sequence
                else post_caller
            )
            target.extend(dict(message) for message in segment)
        suppressed = self._durable_caller_ingress_indexes(
            current,
            pause_sequence=pause_sequence,
            caller_messages=caller_messages,
        )
        return {
            "preCallerToolMessages": pre_caller,
            "callerMessages": [
                dict(message)
                for index, message in enumerate(caller_messages)
                if index not in suppressed
            ],
            "postCallerToolMessages": post_caller,
        }
