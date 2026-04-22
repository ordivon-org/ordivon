from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class WakeReason:
    reason: str


@dataclass(frozen=True, slots=True)
class ResumeReason:
    reason: str


@dataclass(frozen=True, slots=True)
class ResumeDirective:
    wake_reason: WakeReason | None = None
    resume_reason: str | None = None
    resume_from_ref: str | None = None
    resume_count: int = 0
