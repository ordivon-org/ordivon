"""Shared, deterministic contract vocabulary for grounded task and receipt modules."""

from __future__ import annotations

import hashlib
import json
from typing import Any

RELATION_LABELS = (
    "CAUSES",
    "ENABLES",
    "CONDITION",
    "SUPPORTS",
    "CONTRASTS",
    "DUPLICATES",
    "EXTENDS",
    "CONTRADICTS",
    "SEQUENCE",
    "IRRELEVANT",
    "NONE",
)


def canonical_digest(value: Any) -> str:
    encoded = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode(
        "utf-8"
    )
    return "sha256:" + hashlib.sha256(encoded).hexdigest()
