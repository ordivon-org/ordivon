from __future__ import annotations

from dataclasses import dataclass, field

from shared.time.clock import utc_now
from shared.utils.ids import new_id


VALID_FEEDBACK_CONSUMER_TYPES = {"governance", "intelligence"}


@dataclass
class FeedbackRecord:
    id: str = field(default_factory=lambda: new_id("fdbk"))
    packet_id: str = ""
    recommendation_id: str = ""
    review_id: str | None = None
    consumer_type: str = ""
    subject_key: str = ""
    knowledge_entry_ids: tuple[str, ...] = field(default_factory=tuple)
    consumed_hint_count: int = 0
    created_at: str = field(default_factory=lambda: utc_now().isoformat())

    def __post_init__(self) -> None:
        if not self.packet_id:
            raise ValueError("FeedbackRecord requires packet_id.")
        if not self.recommendation_id:
            raise ValueError("FeedbackRecord requires recommendation_id.")
        if self.consumer_type not in VALID_FEEDBACK_CONSUMER_TYPES:
            raise ValueError(f"Unsupported feedback consumer_type: {self.consumer_type}")
        if not self.subject_key:
            raise ValueError("FeedbackRecord requires subject_key.")
