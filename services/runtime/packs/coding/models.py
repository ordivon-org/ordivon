"""Coding Pack domain models.

CodingDecisionPayload represents an AI coding agent's proposed action:
what task, which files, estimated impact, reasoning, and test plan.
"""
from __future__ import annotations

from dataclasses import dataclass, field

VALID_IMPACT_LEVELS = frozenset({"low", "medium", "high"})


@dataclass(slots=True)
class CodingDecisionPayload:
    """An AI coding agent's proposed code change intent."""

    task_description: str = ""
    file_paths: tuple[str, ...] = field(default_factory=tuple)
    estimated_impact: str = "low"
    reasoning: str = ""
    test_plan: str | None = None

    def __post_init__(self) -> None:
        if self.estimated_impact not in VALID_IMPACT_LEVELS:
            raise ValueError(
                f"estimated_impact must be one of {sorted(VALID_IMPACT_LEVELS)}, "
                f"got {self.estimated_impact!r}"
            )
