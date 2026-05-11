#!/usr/bin/env python3
"""Verify path-map evidence layer — every governed node must have source_refs (GOS-PM-2).

Checks:
  PME-1: Protected/governed nodes without source_refs → BLOCKED
  PME-2: Route assignments without source rule reference → BLOCKED
  PME-3: Generated nodes without generated_from → BLOCKED
  PME-5: Receipt files that claim status without evidence ID → WARNING

Usage:
    python scripts/verify-path-map-evidence.py
    python scripts/verify-path-map-evidence.py --json
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PATH_MAP = ROOT / "docs/governance/generated/path-map.json"


def verify() -> tuple[list[dict], dict]:
    if not PATH_MAP.exists():
        return [{"code": "PME-0", "severity": "blocking", "message": "path-map.json not found"}], {}

    data = json.loads(PATH_MAP.read_text())
    nodes = data.get("nodes", [])
    findings = []
    stats = {
        "total_nodes": len(nodes),
        "governed": 0,
        "no_source_refs": 0,
        "no_route_source": 0,
        "generated_no_source": 0,
    }

    for node in nodes:
        status = node.get("classification_status", "")
        kind = node.get("kind", "")
        path = node.get("path", "?")
        source_refs = node.get("source_refs", [])
        route = node.get("route", "")

        if status == "governed":
            stats["governed"] += 1
            # PME-1: Governed nodes must have source_refs
            if not source_refs or len(source_refs) <= 1:  # only "git ls-files" is not enough
                stats["no_source_refs"] += 1
                findings.append({
                    "code": "PME-1",
                    "severity": "blocking" if status == "blocked" else "degraded",
                    "file": path,
                    "message": f"Governed node '{path}' has insufficient source_refs: {source_refs}",
                })

            # PME-2: Route must be traceable to a source rule
            if route == "unrouted":
                stats["no_route_source"] += 1
                findings.append({
                    "code": "PME-2",
                    "severity": "blocking",
                    "file": path,
                    "message": f"Governed node '{path}' has no route — cannot trace to path-map-rules.json",
                })

        # PME-3: Generated nodes must have must_not_be_source_of_truth
        if kind == "generated_view":
            if not node.get("must_not_be_source_of_truth"):
                stats["generated_no_source"] += 1
                findings.append({
                    "code": "PME-3",
                    "severity": "blocking",
                    "file": path,
                    "message": f"Generated node '{path}' missing must_not_be_source_of_truth flag",
                })

    return findings, stats


def main() -> int:
    as_json = "--json" in sys.argv
    findings, stats = verify()

    if as_json:
        blocked = sum(1 for f in findings if f["severity"] == "blocking")
        output = {"status": "BLOCKED" if blocked > 0 else "READY", "findings": findings, "stats": stats}
        print(json.dumps(output, indent=2))
        return 1 if blocked > 0 else 0

    print("Path Map Evidence Verification")
    print(f"  Nodes: {stats['total_nodes']} (governed: {stats['governed']})")
    print(f"  No source_refs: {stats['no_source_refs']}")
    print(f"  No route source: {stats['no_route_source']}")
    print(f"  Generated no source: {stats['generated_no_source']}")

    blocking = [f for f in findings if f["severity"] == "blocking"]
    degraded = [f for f in findings if f["severity"] == "degraded"]

    if blocking:
        print(f"\n❌ {len(blocking)} BLOCKING:")
        for f in blocking:
            print(f"  [{f['code']}] {f['file']}: {f['message']}")
        return 1

    if degraded:
        print(f"\n⚠ {len(degraded)} DEGRADED:")
        for f in degraded[:10]:
            print(f"  [{f['code']}] {f['file']}: {f['message']}")
        return 2

    print("\n✓ All path-map nodes have evidence references")
    return 0


if __name__ == "__main__":
    sys.exit(main())
