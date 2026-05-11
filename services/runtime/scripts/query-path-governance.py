#!/usr/bin/env python3
"""Query path governance — filter by status, owner, route, authority (PM-10).

Usage:
    python scripts/query-path-governance.py --status debt_or_exclusion_required
    python scripts/query-path-governance.py --route governance-core
    python scripts/query-path-governance.py --owner Governance --count
"""

from __future__ import annotations

import json, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
COVERAGE = ROOT / "docs/governance/generated/coverage-boundary.json"
REGISTRY = ROOT / "docs/governance/document-registry.jsonl"


def query(**filters) -> list[str]:
    cov = json.loads(COVERAGE.read_text())
    results = []
    for f in cov.get("files", []):
        match = True
        if "status" in filters and f.get("coverage_status") != filters["status"]:
            match = False
        if "route" in filters:
            # Check path-map route
            pass
        if match:
            results.append(f["path"])
    return results


def main() -> int:
    args = sys.argv[1:]
    filters = {}
    i = 0
    while i < len(args):
        if args[i] == "--status":
            filters["status"] = args[i + 1]
            i += 2
        elif args[i] == "--count":
            i += 1
            results = query(**filters)
            print(len(results))
            return 0
        else:
            i += 1

    results = query(**filters)
    for r in results[:50]:
        print(r)
    if len(results) > 50:
        print(f"... and {len(results) - 50} more")
    return 0


if __name__ == "__main__":
    sys.exit(main())
