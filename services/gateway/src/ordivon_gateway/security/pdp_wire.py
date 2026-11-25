"""Shared bounded PDP wire representation; no decisions or authority here."""

from __future__ import annotations

import json
import math
import time
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    import requests

MAX_RESPONSE_BYTES = 65536


def _unique_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate JSON member")
        result[key] = value
    return result


def _finite(value: str) -> float:
    result = float(value)
    if not math.isfinite(result):
        raise ValueError("nonfinite JSON number")
    return result


def decode_object(raw: bytes) -> dict[str, Any]:
    """Strict UTF-8 object, unique names, finite numbers, Unicode scalars."""
    if len(raw) > MAX_RESPONSE_BYTES:
        raise ValueError("PDP JSON exceeds bounded size")
    try:
        value = json.loads(
            raw.decode("utf-8"),
            object_pairs_hook=_unique_object,
            parse_float=_finite,
            parse_constant=_finite,
        )
        # JSON escaping can otherwise introduce isolated UTF-16 surrogates
        # even when the original transport bytes are valid UTF-8.
        json.dumps(value, ensure_ascii=False, allow_nan=False).encode("utf-8")
    except (ValueError, RecursionError) as exc:
        raise ValueError("invalid PDP JSON") from exc
    if not isinstance(value, dict):
        raise ValueError("PDP JSON must be an object")
    return value


def read_response(response: requests.Response, *, deadline: float) -> bytes:
    """Limit decoded response bytes, including compressed responses.

    The caller owns HTTP status, correlation, response lifetime and the
    socket timeouts. The monotonic check is not a hard socket deadline.
    """
    if (
        response.headers.get("Content-Type", "").partition(";")[0].strip().lower()
        != "application/json"
    ):
        raise ValueError("PDP response media type invalid")
    body = bytearray()
    for chunk in response.iter_content(chunk_size=8192):
        if time.monotonic() > deadline:
            raise ValueError("PDP response observation deadline exceeded")
        if len(body) + len(chunk) > MAX_RESPONSE_BYTES:
            raise ValueError("PDP response exceeds bounded size")
        body.extend(chunk)
    if time.monotonic() > deadline:
        raise ValueError("PDP response observation deadline exceeded")
    return bytes(body)
