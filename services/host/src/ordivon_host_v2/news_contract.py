from __future__ import annotations

import re
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator

_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


class NewsItem(BaseModel):
    model_config = ConfigDict(extra="forbid")

    itemId: str = Field(min_length=1, max_length=512)
    section: str = Field(min_length=1, max_length=128)
    category: str = Field(min_length=1, max_length=128)
    threadKey: str = Field(min_length=1, max_length=512)
    status: str = Field(min_length=1, max_length=128)
    headline: str = Field(min_length=1, max_length=4096)
    summary: str = Field(min_length=1, max_length=16384)
    confidence: str = Field(min_length=1, max_length=64)
    importance: int = Field(ge=0, le=10)
    novelty: str | None = Field(default=None, max_length=16384)
    continuationOf: str | None = Field(default=None, max_length=512)
    eventAtMs: int | None = Field(default=None, ge=0)
    observedAtMs: int | None = Field(default=None, ge=0)
    publishedAtMs: int | None = Field(default=None, ge=0)
    evidence: list[dict[str, Any]] = Field(max_length=64)


class NewsEditionInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    schemaVersion: int = Field(ge=1)
    kind: str = Field(min_length=1, max_length=256)
    truthRole: str = Field(min_length=1, max_length=256)
    editionId: str = Field(min_length=6, max_length=512, pattern=r"^news:")
    editionDate: str
    timezone: str = Field(min_length=1, max_length=128)
    generatedAtMs: int = Field(ge=0)
    coverageStartMs: int | None = Field(default=None, ge=0)
    coverageEndMs: int | None = Field(default=None, ge=0)
    marketCutoffMs: int | None = Field(default=None, ge=0)
    producerLabel: str = Field(min_length=1, max_length=256)
    renderedBrief: str = Field(max_length=262144)
    items: list[NewsItem] = Field(max_length=4096)

    @field_validator("editionDate")
    @classmethod
    def validate_edition_date(cls, value: str) -> str:
        if _DATE_RE.fullmatch(value) is None:
            raise ValueError("editionDate must use YYYY-MM-DD")
        return value
