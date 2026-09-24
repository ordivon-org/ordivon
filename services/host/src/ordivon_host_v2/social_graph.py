from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field, field_validator


class ParticipationStanding(StrEnum):
    JOINED = "joined"
    LEFT = "left"
    OBSERVER = "observer"


class TopicState(StrEnum):
    OPEN = "open"
    CLOSED = "closed"


class MessageKind(StrEnum):
    NOTE = "note"
    QUESTION = "question"
    PROPOSAL = "proposal"
    WARNING = "warning"
    FINDING = "finding"
    HANDOFF = "handoff"


class MessageRelationKind(StrEnum):
    REPLY_TO = "reply_to"
    MENTIONS = "mentions"
    REFERENCES = "references"
    ACKNOWLEDGES = "acknowledges"
    SUPERSEDES = "supersedes"
    ABOUT = "about"


class IntentStanding(StrEnum):
    ACTIVE = "active"
    RELEASED = "released"


class SpaceInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    space_ref: str = Field(min_length=3, max_length=1024)
    purpose: str = Field(min_length=1, max_length=4096)
    actor_ref: str = Field(min_length=3, max_length=512)
    subject_refs: list[str] = Field(default_factory=list, max_length=256)

    @field_validator("space_ref", "purpose", "actor_ref")
    @classmethod
    def validate_trimmed(cls, value: str) -> str:
        if value != value.strip() or any(ord(ch) < 0x20 for ch in value):
            raise ValueError("space fields must be trimmed printable text")
        return value

    @field_validator("subject_refs")
    @classmethod
    def validate_subject_refs(cls, values: list[str]) -> list[str]:
        if len(values) != len(set(values)):
            raise ValueError("subject_refs must be unique")
        for value in values:
            if not value or value != value.strip():
                raise ValueError("subject refs must be non-empty trimmed text")
        return values


class TopicInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    topic_ref: str = Field(min_length=3, max_length=1024)
    space_ref: str = Field(min_length=3, max_length=1024)
    title: str = Field(min_length=1, max_length=512)
    actor_ref: str = Field(min_length=3, max_length=512)


class MessageInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    message_ref: str = Field(min_length=3, max_length=1024)
    client_request_id: str = Field(min_length=1, max_length=1024)
    space_ref: str = Field(min_length=3, max_length=1024)
    topic_ref: str = Field(min_length=3, max_length=1024)
    author_actor_ref: str = Field(min_length=3, max_length=512)
    message_kind: MessageKind = MessageKind.NOTE
    body: str = Field(min_length=1, max_length=65536)
    recorded_at_ms: int = Field(ge=0)


class MessageRelationInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    source_message_ref: str = Field(min_length=3, max_length=1024)
    relation: MessageRelationKind
    target_ref: str = Field(min_length=1, max_length=2048)
    actor_ref: str = Field(min_length=3, max_length=512)


class CoordinationIntentInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    intent_ref: str = Field(min_length=3, max_length=1024)
    actor_ref: str = Field(min_length=3, max_length=512)
    subject_ref: str = Field(min_length=1, max_length=2048)
    operation: str = Field(min_length=1, max_length=512)
    standing: IntentStanding = IntentStanding.ACTIVE
    observed_at_ms: int = Field(ge=0)
    expires_at_ms: int | None = Field(default=None, ge=0)
    work_ref: str | None = Field(default=None, max_length=1024)
    space_ref: str | None = Field(default=None, max_length=1024)

    @field_validator("subject_ref", "operation")
    @classmethod
    def validate_trimmed(cls, value: str) -> str:
        if value != value.strip():
            raise ValueError("intent fields must be trimmed")
        return value

    def validate_window(self) -> None:
        if self.expires_at_ms is not None and self.expires_at_ms <= self.observed_at_ms:
            raise ValueError("expires_at_ms must be after observed_at_ms")
