#!/usr/bin/env python3
"""JSON stdin/stdout adapter for the precommitted Finance research protocol LEGO.

Only pure source contracts are callable. This is not a broker or an order gateway.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Mapping

from ordivon_capital.research.experiment_protocol import (
    assess_holdout_evidence,
    freeze_experiment_plan,
)


def _unique_object(pairs: list[tuple[str, object]]) -> dict[str, object]:
    output: dict[str, object] = {}
    for key, value in pairs:
        if key in output:
            raise ValueError(f"duplicate JSON key: {key}")
        output[key] = value
    return output


def _reject_nonfinite(value: str) -> None:
    raise ValueError(f"non-finite JSON constant: {value}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "operation", choices=("freeze-experiment", "assess-holdout")
    )
    args = parser.parse_args(argv)
    try:
        request = json.load(
            sys.stdin, object_pairs_hook=_unique_object, parse_constant=_reject_nonfinite
        )
        if not isinstance(request, Mapping):
            raise ValueError("JSON input must be an object")
        if args.operation == "freeze-experiment":
            result = freeze_experiment_plan(request)
        else:
            result = assess_holdout_evidence(request["frozen"], request.get("result"))
    except (ValueError, KeyError, TypeError) as exc:
        print(f"INVALID_FINANCE_LEGO_INPUT: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(result, ensure_ascii=False, sort_keys=True, allow_nan=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
