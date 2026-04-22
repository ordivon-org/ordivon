from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from shared.time.clock import utc_now
from shared.utils.ids import new_id


@dataclass(frozen=True, slots=True)
class HandoffArtifact:
    task_run_id: str
    root_object_ref: dict[str, str | None]
    partial_results: dict[str, Any] = field(default_factory=dict)
    blocked_reason: str = ""
    next_action: str = ""
    evidence_refs: tuple[dict[str, str | None], ...] = field(default_factory=tuple)
    created_at: str = field(default_factory=lambda: utc_now().isoformat())
    id: str = field(default_factory=lambda: new_id("handoff"))

    def to_payload(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "task_run_id": self.task_run_id,
            "root_object_ref": dict(self.root_object_ref),
            "partial_results": dict(self.partial_results),
            "blocked_reason": self.blocked_reason,
            "next_action": self.next_action,
            "evidence_refs": [dict(ref) for ref in self.evidence_refs],
            "created_at": self.created_at,
        }
