from __future__ import annotations

from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator


class ActorKind(StrEnum):
    UNKNOWN = "unknown"
    HUMAN = "human"
    AGENT = "agent"
    SERVICE = "service"
    ORGANIZATION = "organization"


class WorkState(StrEnum):
    OPEN = "open"
    COMPLETED = "completed"
    ABANDONED = "abandoned"


class WorkRelationKind(StrEnum):
    PARENT_OF = "parent_of"
    DEPENDS_ON = "depends_on"
    BLOCKS = "blocks"
    RELATES_TO = "relates_to"


class ActorRefInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    actor_ref: str = Field(min_length=3, max_length=512)
    actor_kind: ActorKind

    @field_validator("actor_ref")
    @classmethod
    def validate_actor_ref(cls, value: str) -> str:
        if value != value.strip() or any(ord(ch) < 0x20 for ch in value):
            raise ValueError("actor_ref must be trimmed printable text")
        if ":" not in value:
            raise ValueError("actor_ref must be namespaced")
        return value


class WorkSnapshotInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    objective: str = Field(min_length=1, max_length=4096)
    frontier: str = Field(min_length=1, max_length=4096)
    established: list[str] = Field(default_factory=list, max_length=128)
    unresolved: list[str] = Field(default_factory=list, max_length=128)
    rejected: list[str] = Field(default_factory=list, max_length=128)
    constraints: list[str] = Field(default_factory=list, max_length=128)
    next_actions: list[str] = Field(default_factory=list, max_length=128)
    reference_refs: list[str] = Field(default_factory=list, max_length=256)

    @field_validator(
        "established",
        "unresolved",
        "rejected",
        "constraints",
        "next_actions",
        "reference_refs",
    )
    @classmethod
    def validate_string_lists(cls, values: list[str]) -> list[str]:
        for value in values:
            if not value or value != value.strip():
                raise ValueError("snapshot list entries must be non-empty trimmed text")
        return values

    def canonical_payload(self) -> dict[str, Any]:
        return {
            "objective": self.objective,
            "frontier": self.frontier,
            "established": list(self.established),
            "unresolved": list(self.unresolved),
            "rejected": list(self.rejected),
            "constraints": list(self.constraints),
            "nextActions": list(self.next_actions),
            "referenceRefs": list(self.reference_refs),
        }


class WorkCreateInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    work_ref: str = Field(min_length=3, max_length=1024)
    kind: str = Field(min_length=1, max_length=128)
    actor_ref: str = Field(min_length=3, max_length=512)
    initial_snapshot: WorkSnapshotInput

    @field_validator("work_ref", "kind", "actor_ref")
    @classmethod
    def validate_trimmed(cls, value: str) -> str:
        if value != value.strip() or any(ord(ch) < 0x20 for ch in value):
            raise ValueError("identifier fields must be trimmed printable text")
        return value


class WorkRelationInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    source_work_ref: str = Field(min_length=3, max_length=1024)
    relation: WorkRelationKind
    target_work_ref: str = Field(min_length=3, max_length=1024)
    actor_ref: str = Field(min_length=3, max_length=512)

    @field_validator("source_work_ref", "target_work_ref", "actor_ref")
    @classmethod
    def validate_trimmed(cls, value: str) -> str:
        if value != value.strip() or any(ord(ch) < 0x20 for ch in value):
            raise ValueError("relation identifiers must be trimmed printable text")
        return value

    def validate_not_self_relation(self) -> None:
        if self.source_work_ref == self.target_work_ref:
            raise ValueError("work relation cannot target itself")
