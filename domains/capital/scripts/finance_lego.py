#!/usr/bin/env python3
"""JSON stdin/stdout adapter for the precommitted Finance research protocol LEGO.

Only pure source contracts are callable. This is not a broker or an order gateway.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Mapping
from pathlib import Path

from ordivon_capital.research.experiment_protocol import (
    assess_holdout_evidence,
    candidate_policy_digest,
    freeze_experiment_plan,
    review_replayed_candidate,
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
        "operation", choices=(
            "freeze-experiment", "assess-holdout",
            "fingerprint-policy", "review-candidate",
        )
    )
    parser.add_argument("--manifest", type=Path)
    parser.add_argument("--source", type=Path)
    parser.add_argument("--holdout", type=Path)
    args = parser.parse_args(argv)
    try:
        request = json.load(
            sys.stdin, object_pairs_hook=_unique_object, parse_constant=_reject_nonfinite
        )
        if not isinstance(request, Mapping):
            raise ValueError("JSON input must be an object")
        if args.operation == "freeze-experiment":
            result = freeze_experiment_plan(request)
        elif args.operation == "assess-holdout":
            result = assess_holdout_evidence(request["frozen"], request.get("result"))
        elif args.operation == "fingerprint-policy":
            result = {"configDigest": candidate_policy_digest(request)}
        else:
            if not (args.manifest and args.source and args.holdout):
                raise ValueError("review-candidate needs --manifest, --source and --holdout")
            manifest = json.loads(
                args.manifest.read_text(encoding="utf-8"),
                object_pairs_hook=_unique_object, parse_constant=_reject_nonfinite,
            )
            result = review_replayed_candidate(
                frozen=request["frozen"],
                manifest=manifest,
                source_bytes=args.source.read_bytes(),
                holdout_bytes=args.holdout.read_bytes(),
                evaluated_at=request["evaluatedAt"],
            )
    except (ValueError, KeyError, TypeError, OSError, UnicodeError) as exc:
        print(f"INVALID_FINANCE_LEGO_INPUT: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(result, ensure_ascii=False, sort_keys=True, allow_nan=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
