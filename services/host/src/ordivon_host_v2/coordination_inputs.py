from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field, StrictInt, field_validator

# PostgreSQL signed bigint is an independent wire/DB boundary in this domain.
POSTGRES_BIGINT_MAX = (1 << 63) - 1


class IntentStanding(StrEnum):
    ACTIVE = "active"
    RELEASED = "released"


class CoordinationIntentInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    intent_ref: str = Field(min_length=3, max_length=1024)
    actor_ref: str = Field(min_length=3, max_length=512)
    subject_ref: str = Field(min_length=1, max_length=2048)
    operation: str = Field(min_length=1, max_length=512)
    standing: IntentStanding = IntentStanding.ACTIVE
    observed_at_ms: StrictInt = Field(ge=0, le=POSTGRES_BIGINT_MAX)
    expires_at_ms: StrictInt | None = Field(default=None, ge=0, le=POSTGRES_BIGINT_MAX)
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
