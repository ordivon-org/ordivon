#!/usr/bin/env python
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

from bound_refs import occurrence_ref


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=("compute", "verify"))
    parser.add_argument("path", type=Path)
    args = parser.parse_args()
    value = json.loads(args.path.read_text())
    intent = value.get("intent", value)
    actual = occurrence_ref(intent)
    if args.mode == "compute":
        print(actual)
        return 0
    expected = intent.get("occurrenceRef")
    if expected != actual:
        print(f"occurrenceRef mismatch expected={expected!r} actual={actual!r}", file=sys.stderr)
        return 1
    print(actual)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
