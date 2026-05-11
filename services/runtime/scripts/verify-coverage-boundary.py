#!/usr/bin/env python3
"""Verify coverage boundary — no unknown protected files, all exclusions have metadata (PM-5)."""

from __future__ import annotations

import json, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
COVERAGE = ROOT / "docs/governance/generated/coverage-boundary.json"


def verify() -> tuple[list[dict], dict]:
    if not COVERAGE.exists():
        return [{"code": "CB-0", "severity": "blocking", "message": "coverage-boundary.json not found"}], {}

    data = json.loads(COVERAGE.read_text())
    findings = []
    stats = {"total": data["stats"]["total"], "blocked": data["stats"]["blocked"]}

    for f in data.get("files", []):
        status = f["coverage_status"]
        path = f.get("path", "?")
        meta = f.get("metadata", {})

        if status == "blocked":
            findings.append({"code": "CB-1", "severity": "blocking", "path": path, "message": "Unknown protected file"})
        elif status == "excluded":
            if not meta.get("reason") or len(str(meta.get("reason", ""))) < 3:
                findings.append({
                    "code": "CB-2",
                    "severity": "degraded",
                    "path": path,
                    "message": "Exclusion missing reason",
                })
        elif status == "debt_parked":
            if not meta.get("debt_id"):
                findings.append({
                    "code": "CB-4",
                    "severity": "blocking",
                    "path": path,
                    "message": "Debt-parked without debt_id",
                })
        elif status == "debt_or_exclusion_required":
            findings.append({
                "code": "CB-12",
                "severity": "degraded",
                "path": path,
                "message": "Non-protected file requires debt or exclusion",
            })

    return findings, stats


def main() -> int:
    as_json = "--json" in sys.argv
    findings, stats = verify()
    blocking = [f for f in findings if f["severity"] == "blocking"]
    degraded = [f for f in findings if f["severity"] == "degraded"]

    if as_json:
        print(
            json.dumps({"status": "BLOCKED" if blocking else "READY", "findings": findings, "stats": stats}, indent=2)
        )
        return 1 if blocking else 0

    print(f"Coverage Boundary: {stats['total']} files, {stats['blocked']} blocked")
    if not findings:
        print("✓ All files classified — 0 unknown protected files")
        return 0
    print(f"❌ {len(blocking)} BLOCKING, {len(degraded)} DEGRADED")
    for f in findings[:10]:
        print(f"  [{f['code']}] {f.get('path', '?')}: {f['message']}")
    return 1


if __name__ == "__main__":
    sys.exit(main())
