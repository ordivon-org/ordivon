#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

from ordivon_security_v2 import BrowserSecurityWitnessBundle, compare_browser_security_bundles


def load(path: Path) -> BrowserSecurityWitnessBundle:
    return BrowserSecurityWitnessBundle.from_dict(json.loads(path.read_text(encoding="utf-8")))


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Compare two Browser Security witness bundles and report detector-family and public-observation drift."
    )
    parser.add_argument("baseline", type=Path)
    parser.add_argument("candidate", type=Path)
    args = parser.parse_args()
    print(
        json.dumps(
            compare_browser_security_bundles(load(args.baseline), load(args.candidate)),
            sort_keys=True,
            indent=2,
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
