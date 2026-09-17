#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

from ordivon_security_v2 import BrowserSecurityWitness, compare_browser_security_witnesses


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Compare two browser-security detector witnesses without treating a protected challenge as a detector oracle."
    )
    parser.add_argument("baseline", type=Path)
    parser.add_argument("candidate", type=Path)
    args = parser.parse_args()

    baseline = BrowserSecurityWitness.from_dict(json.loads(args.baseline.read_text(encoding="utf-8")))
    candidate = BrowserSecurityWitness.from_dict(json.loads(args.candidate.read_text(encoding="utf-8")))
    print(json.dumps(compare_browser_security_witnesses(baseline, candidate), sort_keys=True, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
