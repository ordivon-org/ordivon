from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from shared.utils.ids import new_id


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
