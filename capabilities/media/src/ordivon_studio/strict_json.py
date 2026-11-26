"""Strict owner-local JSON representation admission, without a new parser.

Use the standard library decoder and its duplicate/member/number hooks.
This module deliberately depends only on Python's standard library: both
Studio Core and the native Python 3.13 OTIO environment consume it.
"""
from __future__ import annotations

import json
import math
import sys
from pathlib import Path
from typing import Any


def _unique_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"ambiguous duplicate manifest key: {key}")
        result[key] = value
    return result


def _reject_constant(value: str) -> Any:
    raise ValueError(f"nonfinite JSON constant: {value}")


def _finite_float(value: str) -> float:
    number = float(value)
    if not math.isfinite(number):
        raise ValueError(f"nonfinite JSON number: {value}")
    return number


def decode_object(raw: bytes) -> dict[str, Any]:
    value = json.loads(
        raw.decode("utf-8"),
        object_pairs_hook=_unique_object,
        parse_constant=_reject_constant,
        parse_float=_finite_float,
    )
    if not isinstance(value, dict):
        raise TypeError("expected one JSON object")
    return value


def decode_profile(raw: bytes) -> dict[str, Any]:
    value = decode_object(raw)
    if (
        type(value.get("schemaVersion")) is not int or value["schemaVersion"] != 1
        or not isinstance(value.get("id"), str) or not value["id"].strip()
        or not isinstance(value.get("kind"), str) or not value["kind"].strip()
    ):
        raise ValueError("invalid Media processing profile envelope")
    return value


def main() -> int:
    """Admit and retain the exact profile bytes before native provider use."""
    if len(sys.argv) != 3:
        return 64
    source, snapshot = map(Path, sys.argv[1:])
    try:
        raw = source.read_bytes()
        decode_profile(raw)
        with snapshot.open("xb") as stream:
            stream.write(raw)
    except (ValueError, TypeError, OSError) as exc:
        print(f"invalid profile: {exc}", file=sys.stderr)
        return 65
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
