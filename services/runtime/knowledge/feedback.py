from __future__ import annotations

from dataclasses import dataclass, field

from knowledge.models import KnowledgeEntry
from shared.time.clock import utc_now
from shared.utils.ids import new_id


@dataclass(frozen=True, slots=True)
class KnowledgeHint:
    target: str
    hint_type: str
    summary: str
    evidence_object_ids: tuple[str, ...] = field(default_factory=tuple)


@dataclass(frozen=True, slots=True)
class KnowledgeFeedbackPacket:
    recommendation_id: str
    knowledge_entry_ids: tuple[str, ...]
    review_id: str | None = None
    governance_hints: tuple[KnowledgeHint, ...] = field(default_factory=tuple)
    intelligence_hints: tuple[KnowledgeHint, ...] = field(default_factory=tuple)
    id: str = field(default_factory=lambda: new_id("kfpkt"))
    created_at: str = field(default_factory=lambda: utc_now().isoformat())


class KnowledgeFeedbackService:
    """Derives lightweight feedback packets from structured knowledge entries."""

    def build_packet(
        self,
        recommendation_id: str,
        entries: list[KnowledgeEntry],
        review_id: str | None = None,
    ) -> KnowledgeFeedbackPacket:
        governance_hints: list[KnowledgeHint] = []
        intelligence_hints: list[KnowledgeHint] = []

        for entry in entries:
            evidence_ids = tuple(ref.object_id for ref in entry.evidence_refs)
            if "governance" in entry.feedback_targets:
                governance_hints.append(
                    KnowledgeHint(
                        target="governance",
                        hint_type="lesson_caution",
                        summary=entry.narrative,
                        evidence_object_ids=evidence_ids,
                    )
                )
            if "intelligence" in entry.feedback_targets:
                intelligence_hints.append(
                    KnowledgeHint(
                        target="intelligence",
                        hint_type="memory_lesson",
                        summary=entry.narrative,
                        evidence_object_ids=evidence_ids,
                    )
                )

        return KnowledgeFeedbackPacket(
            recommendation_id=recommendation_id,
            review_id=review_id,
            knowledge_entry_ids=tuple(entry.id for entry in entries),
            governance_hints=tuple(governance_hints),
            intelligence_hints=tuple(intelligence_hints),
        )
