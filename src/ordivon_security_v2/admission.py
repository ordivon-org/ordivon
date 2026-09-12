from __future__ import annotations

import json
from dataclasses import dataclass, field
from hashlib import sha256
from typing import Any

JsonObject = dict[str, Any]


def canonical_bytes(value: object) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        allow_nan=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def canonical_digest(value: object) -> str:
    return "sha256:" + sha256(canonical_bytes(value)).hexdigest()


@dataclass(slots=True)
class ReplayBinding:
    """Bind one request identity to exact immutable request content and its admission result.

    This deliberately does not execute an effect, persist a workflow, or own Range lifecycle.
    """

    _records: dict[str, tuple[str, JsonObject]] = field(default_factory=dict)

    def bind(self, *, request: JsonObject, admission: JsonObject) -> tuple[JsonObject, bool]:
        request_id = request.get("requestId")
        if not isinstance(request_id, str) or not request_id:
            raise ValueError("requestId is required")
        request_digest = canonical_digest(request)
        existing = self._records.get(request_id)
        if existing is not None:
            existing_digest, existing_admission = existing
            if existing_digest != request_digest:
                raise ValueError("effect request identity was reused with different content")
            return dict(existing_admission), True
        self._records[request_id] = (request_digest, dict(admission))
        return dict(admission), False
