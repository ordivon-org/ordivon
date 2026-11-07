#!/usr/bin/env python3
"""Storage-neutral wake identity validation shared by PG and legacy readers.

These checks define input semantics; neither backend owns them or can
change them during a storage cutover.
"""

from __future__ import annotations

import re

_DIGEST_RE = re.compile(r"^sha256:[0-9a-f]{64}$")


class WakeTurnConflict(RuntimeError):
    pass


def _text(value: str, label: str, *, max_bytes: int = 4096) -> str:
    if (
        not isinstance(value, str)
        or not value
        or value != value.strip()
        or len(value.encode("utf-8")) > max_bytes
    ):
        raise ValueError(f"{label} must be non-empty, trimmed, and <= {max_bytes} UTF-8 bytes")
    return value


def _digest(value: str, label: str) -> str:
    if not isinstance(value, str) or _DIGEST_RE.fullmatch(value) is None:
        raise ValueError(f"{label} must be canonical sha256:<lowercase-hex>")
    return value
