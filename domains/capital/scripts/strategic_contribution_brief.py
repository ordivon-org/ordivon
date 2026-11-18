#!/usr/bin/env python3
"""Agent-readable Finance strategic contribution brief, without broker effects."""

from __future__ import annotations

import json
import sys
from typing import Any

from ordivon_capital.portfolio.strategic_contribution import (
    AllocationPolicyError,
    plan_strategic_contribution,
)


def _no_duplicate_json_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def _no_nonfinite(value: str) -> None:
    raise ValueError(f"nonfinite JSON value: {value}")


def main() -> int:
    try:
        raw = json.loads(
            sys.stdin.read(),
            object_pairs_hook=_no_duplicate_json_keys,
            parse_constant=_no_nonfinite,
        )
        result = plan_strategic_contribution(raw)
        rendered = json.dumps(result, sort_keys=True, indent=2, allow_nan=False)
    except (AllocationPolicyError, ValueError, TypeError, OSError) as exc:
        print(f"strategic contribution rejected: {exc}", file=sys.stderr)
        return 2
    print(rendered)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
