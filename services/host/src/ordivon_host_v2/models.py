from __future__ import annotations

from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator


class TaskState(StrEnum):
    OPEN = "open"
    COMPLETED = "completed"
    ABANDONED = "abandoned"


class Admission(StrEnum):
    COMMITTED = "committed"
    EXISTING = "existing"


class CheckpointInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    payload: dict[str, Any]
    writer_label: str | None = Field(default=None, max_length=256)

    @field_validator("writer_label")
    @classmethod
    def validate_writer_label(cls, value: str | None) -> str | None:
        if value is None:
            return None
        if not value or value != value.strip():
            raise ValueError("writer_label must be non-empty trimmed text")
        return value


class TaskView(BaseModel):
    model_config = ConfigDict(extra="forbid")

    task_id: str
    goal_id: str | None = None
    revision: int = Field(ge=1)
    state: TaskState
    checkpoint_digest: str
    checkpoint: dict[str, Any]
    writer_label: str | None


class MutationResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    admission: Admission
    task: TaskView


class HostStatus(BaseModel):
    model_config = ConfigDict(extra="forbid")

    service: str = "ordivon-host-v2"
    authority: str = "postgresql"
    schema_version: int = 4
