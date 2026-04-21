from dataclasses import dataclass, field
from typing import Any

from shared.utils.ids import new_id
from shared.time.clock import utc_now


@dataclass
class Issue:
    id: str = field(default_factory=lambda: new_id("issue"))
    title: str = ""
    summary: str = ""
    severity: str = "p2"
    category: str = "workflow"
    status: str = "open"
    source_type: str | None = None
    source_id: str | None = None
    detail: dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=lambda: utc_now().isoformat())
    updated_at: str = field(default_factory=lambda: utc_now().isoformat())
    resolved_at: str | None = None
