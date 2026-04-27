from __future__ import annotations

from dataclasses import dataclass, field

from shared.time.clock import utc_now
from shared.utils.ids import new_id


VALID_CANDIDATE_RULE_STATES = {"draft", "under_review", "rejected", "accepted_candidate"}


@dataclass
class CandidateRule:
    id: str = field(default_factory=lambda: new_id("crule"))
    issue_key: str = ""
    summary: str = ""
    status: str = "draft"
    recommendation_ids: tuple[str, ...] = field(default_factory=tuple)
    review_ids: tuple[str, ...] = field(default_factory=tuple)
    lesson_ids: tuple[str, ...] = field(default_factory=tuple)
    knowledge_entry_ids: tuple[str, ...] = field(default_factory=tuple)
    source_refs: tuple[str, ...] = field(default_factory=tuple)
    created_at: str = field(default_factory=lambda: utc_now().isoformat())

    def __post_init__(self) -> None:
        if not self.issue_key:
            raise ValueError("CandidateRule requires issue_key.")
        if not self.summary:
            raise ValueError("CandidateRule requires summary.")
        if self.status not in VALID_CANDIDATE_RULE_STATES:
            raise ValueError(f"Unsupported candidate rule status: {self.status}")
