#!/usr/bin/env python3
"""Verify gate enforcement matrix — blocking gates need CI + owner + rollback (N2)."""

from __future__ import annotations

import json, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INVENTORY = ROOT / "docs/governance/generated/gate-inventory.json"


def verify() -> tuple[list[dict], dict]:
    if not INVENTORY.exists():
        return [{"code": "GE-1", "severity": "blocking", "message": "Gate inventory not found"}], {}

    data = json.loads(INVENTORY.read_text())
    findings = []
    stats = {"total": len(data.get("gates", []))}

    for g in data.get("gates", []):
        gid = g["gate_id"]
        mode = g.get("mode", "")

        # GE-1: gate without mode
        if not mode:
            findings.append({"code": "GE-1", "severity": "blocking", "gate": gid, "message": "Gate missing mode"})

        # GE-3: blocking without CI job
        if mode in ("BLOCKING", "HARD_BLOCKING") and not g.get("ci_job"):
            findings.append({"code": "GE-3", "severity": "blocking", "gate": gid, "message": "BLOCKING gate without CI job"})

        # GE-7: gate without owner
        if not g.get("owner"):
            findings.append({"code": "GE-7", "severity": "blocking", "gate": gid, "message": "Gate missing owner"})

        # GE-9: gate without rollback path
        if not g.get("rollback_path"):
            findings.append({"code": "GE-9", "severity": "degraded", "gate": gid, "message": "Gate missing rollback path"})

    return findings, stats


def main() -> int:
    findings, stats = verify()
    blocking = [f for f in findings if f["severity"] == "blocking"]

    if "--json" in sys.argv:
        print(json.dumps({"findings": findings, "stats": stats}, indent=2))
        return 1 if blocking else 0

    print(f"Gate Enforcement Matrix: {stats['total']} gates")
    if not findings:
        print("✓ All gates compliant")
        return 0
    print(f"{len(blocking)} BLOCKING, {len(findings) - len(blocking)} DEGRADED")
    for f in findings[:10]:
        print(f"  [{f['code']}] {f.get('gate','?')}: {f['message']}")
    return 1 if blocking else 0


if __name__ == "__main__":
    sys.exit(main())
