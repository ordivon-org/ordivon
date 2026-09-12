#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

from ordivon_security_v2.threat_model import load_and_validate


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("model", type=Path)
    p.add_argument("--repo-root", type=Path, default=Path.cwd())
    args = p.parse_args()
    result = load_and_validate(args.model, args.repo_root)
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
