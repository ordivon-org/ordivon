#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

from ordivon_security_v2 import BrowserSecurityWitnessBundle, compare_browser_security_pool


def _load_bundle(path: Path) -> BrowserSecurityWitnessBundle:
    value = json.loads(path.read_text(encoding="utf-8"))
    return BrowserSecurityWitnessBundle.from_dict(value)


def _load_manifest(path: Path) -> dict[str, tuple[BrowserSecurityWitnessBundle, BrowserSecurityWitnessBundle]]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict) or set(value) != {"schemaVersion", "carriers"}:
        raise ValueError("pool comparison manifest must contain schemaVersion and carriers")
    if value["schemaVersion"] != 1:
        raise ValueError("schemaVersion=1 required")
    rows = value["carriers"]
    if not isinstance(rows, list) or len(rows) < 2:
        raise ValueError("pool comparison manifest requires at least two carriers")
    result: dict[str, tuple[BrowserSecurityWitnessBundle, BrowserSecurityWitnessBundle]] = {}
    for row in rows:
        if not isinstance(row, dict) or set(row) != {
            "carrierId",
            "baselineBundle",
            "candidateBundle",
        }:
            raise ValueError("carrier row must contain carrierId, baselineBundle and candidateBundle")
        carrier_id = row["carrierId"]
        if not isinstance(carrier_id, str) or not carrier_id or carrier_id != carrier_id.strip():
            raise ValueError("carrierId must be a non-empty trimmed string")
        if carrier_id in result:
            raise ValueError(f"duplicate carrierId: {carrier_id}")
        baseline = row["baselineBundle"]
        candidate = row["candidateBundle"]
        if not isinstance(baseline, str) or not baseline or not isinstance(candidate, str) or not candidate:
            raise ValueError("bundle paths must be non-empty strings")
        result[carrier_id] = (
            _load_bundle(path.parent / baseline),
            _load_bundle(path.parent / candidate),
        )
    return result


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Compare same-carrier browser-security LKG/candidate pairs and classify pool drift."
    )
    parser.add_argument("manifest", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = compare_browser_security_pool(_load_manifest(args.manifest))
    text = json.dumps(result, sort_keys=True, indent=2) + "\n"
    if args.output is None:
        print(text, end="")
    else:
        args.output.write_text(text, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
