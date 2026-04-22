from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class MemoryPolicy:
    allow_transient_context: bool = True
    allow_persisted_memory: bool = False
    allow_feedback_hints: bool = True
    forbid_state_truth_write: bool = True

    def allow_channel(self, channel: str) -> bool:
        if channel == "transient_context":
            return self.allow_transient_context
        if channel == "persisted_memory":
            return self.allow_persisted_memory
        if channel == "feedback_hints":
            return self.allow_feedback_hints
        return False
