"""Unambiguous JSON metadata admission for Data's two native readers.

Use the standard decoder's object-pairs hook before duplicate keys can be
collapsed. This is a narrow interoperability profile, not full I-JSON or
JSON-LD validation, nor canonicalization of the source bytes.
"""

from __future__ import annotations

import json
import math
from typing import Any


def _unique_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate JSON member in metadata")
        result[key] = value
    return result


def _reject_constant(value: str) -> Any:
    raise ValueError("non-finite JSON number in metadata")


def _finite_float(value: str) -> float:
    number = float(value)
    if not math.isfinite(number):
        raise ValueError("non-finite JSON number in metadata")
    return number


def contains_surrogate(value: str) -> bool:
    """Lone UTF-16 surrogate code points cannot denote UTF-8 metadata paths."""
    return any(0xD800 <= ord(ch) <= 0xDFFF for ch in value)


def read_metadata(raw: bytes | str) -> Any:
    """Decode without silently choosing one of multiple declared members."""
    return json.loads(
        raw,
        object_pairs_hook=_unique_object,
        parse_constant=_reject_constant,
        parse_float=_finite_float,
    )
