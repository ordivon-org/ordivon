#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import tomllib
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(description="Parse repository JSON/TOML assets under one or more roots.")
    parser.add_argument("roots", nargs="+")
    args = parser.parse_args()
    checked = 0
    for root_text in args.roots:
        root = Path(root_text)
        if not root.exists():
            raise SystemExit(f"structured-data root missing: {root}")
        for path in sorted(p for p in root.rglob("*") if p.is_file()):
            if path.suffix == ".json":
                json.loads(path.read_text(encoding="utf-8"))
                checked += 1
            elif path.suffix == ".toml":
                tomllib.loads(path.read_text(encoding="utf-8"))
                checked += 1
    print(f"structured data: valid (files={checked})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
