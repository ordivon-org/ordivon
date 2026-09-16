from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path


class TrustState(StrEnum):
    TRUSTED = "TRUSTED"
    APPROVED = "APPROVED"
    QUARANTINED = "QUARANTINED"
    BLOCKED = "BLOCKED"
    UNTRUSTED = "UNTRUSTED"


class EligibilityState(StrEnum):
    READY = "READY"
    BLOCKED = "BLOCKED"
    UNKNOWN = "UNKNOWN"


@dataclass(frozen=True, slots=True)
class SkillSource:
    source_id: str
    root: Path
    scope: str
    priority: int
    trust_state: TrustState
    enabled: bool = True

    def __post_init__(self) -> None:
        if not self.source_id or "/" in self.source_id:
            raise ValueError("source_id must be a non-empty path-segment-safe identifier")
        if not self.scope:
            raise ValueError("scope must be non-empty")


@dataclass(frozen=True, slots=True)
class SkillRecord:
    skill_id: str
    name: str
    description: str
    source_id: str
    scope: str
    source_priority: int
    skill_root: Path
    main_resource: Path
    instruction_digest: str
    trust_state: TrustState
    eligibility_state: EligibilityState = EligibilityState.UNKNOWN

    def __post_init__(self) -> None:
        if self.skill_id != f"{self.source_id}/{self.name}":
            raise ValueError("skill_id must be <source_id>/<name>")
        if not self.name or "/" in self.name:
            raise ValueError("skill name must be a non-empty path-segment-safe identifier")
        if not self.description.strip():
            raise ValueError("skill description must be non-empty")
        if not self.instruction_digest.startswith("sha256:"):
            raise ValueError("instruction_digest must be sha256-prefixed")
