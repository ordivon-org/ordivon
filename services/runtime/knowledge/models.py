from __future__ import annotations

from dataclasses import dataclass, field

from shared.time.clock import utc_now
from shared.utils.ids import new_id


STATE_TRUTH_OBJECT_TYPES = frozenset(
    {
        "analysis",
        "recommendation",
        "review",
        "workflow_run",
        "intelligence_run",
        "agent_action",
        "execution_request",
        "execution_receipt",
        "audit_event",
        "outcome",
    }
)


@dataclass(frozen=True, slots=True)
class KnowledgeRef:
    object_type: str
    object_id: str
    relation: str = "evidence"
    path: str | None = None

    def __post_init__(self) -> None:
        if not self.object_type.strip():
            raise ValueError("KnowledgeRef.object_type is required")
        if not self.object_id.strip():
            raise ValueError("KnowledgeRef.object_id is required")
        if not self.relation.strip():
            raise ValueError("KnowledgeRef.relation is required")


@dataclass(frozen=True, slots=True)
class KnowledgeEntry:
    title: str
    narrative: str
    knowledge_type: str = "lesson"
    derived_from: KnowledgeRef | None = None
    evidence_refs: tuple[KnowledgeRef, ...] = field(default_factory=tuple)
    feedback_targets: tuple[str, ...] = field(default_factory=tuple)
    confidence: float = 0.0
    created_at: str = field(default_factory=lambda: utc_now().isoformat())
    id: str = field(default_factory=lambda: new_id("know"))

    def __post_init__(self) -> None:
        if not self.title.strip():
            raise ValueError("KnowledgeEntry.title is required")
        if not self.narrative.strip():
            raise ValueError("KnowledgeEntry.narrative is required")
        if self.knowledge_type in STATE_TRUTH_OBJECT_TYPES:
            raise ValueError(
                f"KnowledgeEntry.knowledge_type cannot masquerade as state truth: {self.knowledge_type}"
            )
        if not self.evidence_refs:
            raise ValueError("KnowledgeEntry.evidence_refs must not be empty")
        if self.derived_from is None:
            raise ValueError("KnowledgeEntry.derived_from is required")
        if self.derived_from.relation != "derived_from":
            raise ValueError("KnowledgeEntry.derived_from must use relation='derived_from'")
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError("KnowledgeEntry.confidence must be between 0.0 and 1.0")

