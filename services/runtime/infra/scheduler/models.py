from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from shared.utils.ids import new_id

VALID_TRIGGER_TYPES = frozenset({"interval", "cron", "manual", "resume"})


@dataclass(frozen=True, slots=True)
class ScheduledTrigger:
    id: str = field(default_factory=lambda: new_id("sched"))
    trigger_type: str = "interval"
    cron_or_interval: str = ""
    target_capability: str = ""
    payload: dict[str, Any] = field(default_factory=dict)
    is_enabled: bool = True
    last_dispatched_at: str | None = None
    dispatch_count: int = 0

    def __post_init__(self) -> None:
        if self.trigger_type not in VALID_TRIGGER_TYPES:
            raise ValueError(
                f"Unsupported scheduler trigger_type: {self.trigger_type}. "
                f"Expected one of {', '.join(sorted(VALID_TRIGGER_TYPES))}."
            )
