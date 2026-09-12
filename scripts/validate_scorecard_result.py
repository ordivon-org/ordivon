#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

from ordivon_security_v2.scorecard import load_and_validate_scorecard_report


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("report", type=Path)
    p.add_argument("--repo", required=True)
    p.add_argument("--commit", required=True)
    p.add_argument("--require-check", action="append", default=[])
    args = p.parse_args()
    result = load_and_validate_scorecard_report(
        args.report,
        expected_repo=args.repo,
        expected_commit=args.commit,
        required_checks=args.require_check,
    )
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
