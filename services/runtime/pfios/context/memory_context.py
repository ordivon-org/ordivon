from dataclasses import dataclass, field


@dataclass
class MemoryContext:
    lessons: list[str] = field(default_factory=list)
    related_reviews: list[str] = field(default_factory=list)
