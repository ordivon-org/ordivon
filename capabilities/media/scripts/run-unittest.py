"""Qualify existing unittest discovery results, without a second runner."""
from __future__ import annotations

import argparse
import os
import unittest


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory")
    parser.add_argument("--pattern", default="test*.py")
    parser.add_argument("--strict", action="store_true")
    args = parser.parse_args()
    strict = args.strict or os.environ.get("ORDIVON_MEDIA_STRICT_TESTS") == "1"
    suite = unittest.TestLoader().discover(args.directory, pattern=args.pattern)
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    print(
        f"qualification={'strict' if strict else 'bounded'} "
        f"executed={result.testsRun} skipped={len(result.skipped)} "
        f"expectedFailures={len(result.expectedFailures)}"
    )
    if not result.testsRun or not result.wasSuccessful():
        return 1
    if strict and (result.skipped or result.expectedFailures):
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
