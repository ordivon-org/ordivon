"""Typed Host Social ActorRef declaration; not Identity or authorization."""
from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field, field_validator


class ActorKind(StrEnum):
    UNKNOWN = "unknown"
    HUMAN = "human"
    AGENT = "agent"
    SERVICE = "service"
    ORGANIZATION = "organization"


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
