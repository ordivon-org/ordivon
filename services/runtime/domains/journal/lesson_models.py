from dataclasses import dataclass, field

from shared.utils.ids import new_id
from shared.time.clock import utc_now


@dataclass
class Lesson:
    id: str = field(default_factory=lambda: new_id("lesson"))
    review_id: str | None = None
    recommendation_id: str | None = None
    title: str = ""
    body: str = ""
    lesson_type: str = "review_learning"
    tags: list[str] = field(default_factory=list)
    confidence: float = 0.0
    source_refs: list[str] = field(default_factory=list)
    wiki_path: str | None = None
    created_at: str = field(default_factory=lambda: utc_now().isoformat())
