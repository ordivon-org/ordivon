from __future__ import annotations

import base64
import json
from typing import Any

from .canonical import canonical_digest


def encode_cursor(kind: str, scope: dict[str, Any], position: dict[str, Any]) -> str:
    payload = {
        "v": 1,
        "kind": kind,
        "scopeDigest": canonical_digest(scope),
        "position": position,
    }
    raw = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    return base64.urlsafe_b64encode(raw).rstrip(b"=").decode()


def decode_cursor(cursor: str, kind: str, scope: dict[str, Any]) -> dict[str, Any]:
    if not cursor or cursor != cursor.strip():
        raise ValueError("cursor is invalid")
    try:
        raw = base64.urlsafe_b64decode(cursor + "=" * (-len(cursor) % 4))
        payload = json.loads(raw)
    except Exception as exc:
        raise ValueError("cursor is invalid") from exc
    if not isinstance(payload, dict) or payload.get("v") != 1 or payload.get("kind") != kind:
        raise ValueError("cursor is invalid")
    if payload.get("scopeDigest") != canonical_digest(scope):
        raise ValueError("cursor does not match query scope")
    position = payload.get("position")
    if not isinstance(position, dict):
        raise TypeError("cursor position is invalid")
    return position
