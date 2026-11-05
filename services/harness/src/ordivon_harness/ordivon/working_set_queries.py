from __future__ import annotations

from anc_canonical import JsonValue

from ..agent_tool_observation import HarnessToolObservation
from ..working_view import (
    WORKING_SET_HISTORY_CONTROL_NAME,
    HarnessWorkingSetSpec,
    parse_working_set_history_query,
)
from .model import AgentToolCall


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
