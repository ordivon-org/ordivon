#!/usr/bin/env python3
"""Real stdin consumer of Portfolio's read-only paper valuation composition."""

from __future__ import annotations

import json
import sys
from typing import Any

from ordivon_capital.portfolio.daily_valuation import (
    DailyValuationError,
    value_paper_portfolio,
)


def _unique_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    obj: dict[str, Any] = {}
    for key, value in pairs:
        if key in obj:
            raise ValueError(f"duplicate JSON key: {key}")
        obj[key] = value
    return obj


def _no_nan(value: str) -> None:
    raise ValueError(f"invalid JSON nonfinite constant: {value}")


def main() -> int:
    try:
        request = json.loads(
            sys.stdin.read(),
            object_pairs_hook=_unique_object,
            parse_constant=_no_nan,
        )
        output = value_paper_portfolio(request)
        rendered = json.dumps(output, sort_keys=True, allow_nan=False, indent=2)
    except (DailyValuationError, ValueError, TypeError, OSError) as exc:
        print(f"paper valuation rejected: {exc}", file=sys.stderr)
        return 2
    print(rendered)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
