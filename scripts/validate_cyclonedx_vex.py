#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

from ordivon_security_v2.vex import load_and_validate_vex


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--vex", type=Path, required=True)
    p.add_argument("--sbom", type=Path, required=True)
    args = p.parse_args()
    print(json.dumps(load_and_validate_vex(args.vex, args.sbom), sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
