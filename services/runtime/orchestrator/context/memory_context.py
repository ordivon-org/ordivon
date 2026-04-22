from dataclasses import dataclass, field

from intelligence.runtime.policy import MemoryPolicy


@dataclass
class MemoryContext:
    lessons: list[str] = field(default_factory=list)
    related_reviews: list[str] = field(default_factory=list)
    policy: MemoryPolicy = field(default_factory=MemoryPolicy)
