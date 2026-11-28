"""Shared, deterministic contract vocabulary for grounded task and receipt modules."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Sequence
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


def qa_result_schema(question_ids: Sequence[str], option_ids: Sequence[str]) -> dict[str, Any]:
    """Build the shared grounded-observer answer wire contract."""
    return {
        "type": "object",
        "additionalProperties": False,
        "properties": {
            "answers": {
                "type": "array",
                "minItems": len(question_ids),
                "maxItems": len(question_ids),
                "items": {
                    "type": "object",
                    "additionalProperties": False,
                    "properties": {
                        "questionId": {"type": "string", "enum": list(question_ids)},
                        "optionId": {"type": "string", "enum": list(option_ids)},
                        "evidenceIds": {
                            "type": "array",
                            "maxItems": 6,
                            "items": {"type": "string"},
                        },
                    },
                    "required": ["questionId", "optionId", "evidenceIds"],
                },
            }
        },
        "required": ["answers"],
    }
