from __future__ import annotations

from dataclasses import dataclass, field

from knowledge.feedback import KnowledgeHint


@dataclass
class KnowledgeFeedbackPacketRecord:
    id: str
    recommendation_id: str
    review_id: str | None
    knowledge_entry_ids: tuple[str, ...] = field(default_factory=tuple)
    governance_hints: tuple[KnowledgeHint, ...] = field(default_factory=tuple)
    intelligence_hints: tuple[KnowledgeHint, ...] = field(default_factory=tuple)
    created_at: str = ""
