"""Validate JSON representation without rewriting the qualified bytes."""

from __future__ import annotations

import json
import math


def _unique_object(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate JSON key")
        result[key] = value
    return result


def _reject_constant(_value: str) -> object:
    raise ValueError("non-JSON numeric constant")


def _finite_float(value: str) -> float:
    # Retain the existing input profile's rejection of numeric overflow.
    # This approximation is for validation only; never send it to OPA.
    number = float(value)
    if not math.isfinite(number):
        raise ValueError("unrepresentable JSON number")
    return number


class InvalidJsonObject(ValueError):
    pass


def qualify_json_object(raw: bytes) -> None:
    """Require unique UTF-8 JSON object and Unicode scalar names/strings.

    The caller retains and transports the exact original bytes. This is
    representation qualification, not domain schema or authority validation.
    """
    parsed = json.loads(
        raw.decode("utf-8"),
        object_pairs_hook=_unique_object,
        parse_constant=_reject_constant,
        parse_float=_finite_float,
    )
    if not isinstance(parsed, dict):
        raise InvalidJsonObject("evaluation must be an object")
    # Iterative traversal avoids adding a second recursive serialization.
    pending = [parsed]
    while pending:
        value = pending.pop()
        if isinstance(value, dict):
            for key, member in value.items():
                key.encode("utf-8")
                pending.append(member)
        elif isinstance(value, list):
            pending.extend(value)
        elif isinstance(value, str):
            value.encode("utf-8")
