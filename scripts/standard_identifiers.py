#!/usr/bin/env python3
"""Small validators for external identifier standards; owns no Ordivon identity ontology."""

from __future__ import annotations
import re
import uuid

UUID7_PATTERN = r"^[0-9a-f]{8}-[0-9a-f]{4}-7[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$"
_UUID7_RE = re.compile(UUID7_PATTERN)


def require_uuid7(value: str, label: str = "identifier") -> str:
    if not isinstance(value, str) or not _UUID7_RE.fullmatch(value):
        raise ValueError(f"{label} must be one canonical lowercase RFC 9562 UUIDv7")
    try:
        parsed = uuid.UUID(value)
    except ValueError as error:
        raise ValueError(f"{label} must be one canonical lowercase RFC 9562 UUIDv7") from error
    if parsed.version != 7 or str(parsed) != value:
        raise ValueError(f"{label} must be one canonical lowercase RFC 9562 UUIDv7")
    return value
