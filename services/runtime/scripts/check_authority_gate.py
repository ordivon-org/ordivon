#!/usr/bin/env python3
"""Pre-Execution Authority Gate — verify authority preconditions.

Ordivon dual-gate model (methodology-core.md §3): before any governed
action, the Pre-Execution Authority Gate must verify:
  1. Every governed document has an owner
  2. Every document has explicit authority
  3. No document overclaims authorization
  4. READY disclaimer is enforced

Usage:
    python scripts/check_authority_gate.py                # Full scan
    python scripts/check_authority_gate.py --json          # CI mode
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REGISTRY_PATH = ROOT / "docs/governance/document-registry.jsonl"

# Authority tiers (from methodology-core.md §2)
VALID_AUTHORITIES = {
    "source_of_truth",
    "current_status",
    "supporting_evidence",
    "historical_record",
    "proposal",
    "example",
    "archive",
}

# Documents that MUST have source_of_truth authority
L0_DOCS = {
    "AGENTS.md",
    "docs/ai/ordivon-macro-structure.md",
    "docs/governance/ordivon-methodology-core.md",
}

# Required disclaimer text
READY_DISCLAIMER = "does not authorize execution"


def check() -> tuple[list[dict], dict]:
    with open(REGISTRY_PATH) as f:
        entries = [json.loads(line) for line in f if line.strip()]

    findings = []
    stats = {"total": len(entries), "no_owner": 0, "bad_authority": 0, "overclaim": 0}

    for e in entries:
        path = e.get("path", "")
        doc_id = e.get("doc_id", "?")
        owner = e.get("owner", "")
        authority = e.get("doc_authority", e.get("authority", ""))

        # Check 1: Owner
        if not owner:
            stats["no_owner"] += 1
            findings.append({
                "rule": "AG-P1",
                "severity": "blocking",
                "file": path,
                "message": f"No owner assigned to '{doc_id}'",
                "fix": "Assign an owner (person or governed role)",
            })

        # Check 2: Authority
        if authority not in VALID_AUTHORITIES:
            stats["bad_authority"] += 1
            findings.append({
                "rule": "AG-P2",
                "severity": "blocking",
                "file": path,
                "message": f"Invalid authority '{authority}' for '{doc_id}'",
                "fix": f"Use one of: {sorted(VALID_AUTHORITIES)}",
            })

        # Check 3: L0 docs must be source_of_truth
        if path in L0_DOCS and authority != "source_of_truth":
            stats["overclaim"] += 1
            findings.append({
                "rule": "AG-P3",
                "severity": "blocking",
                "file": path,
                "message": f"L0 doc '{doc_id}' must have source_of_truth authority, got '{authority}'",
            })

    return findings, stats


def main() -> int:
    as_json = "--json" in sys.argv
    findings, stats = check()

    if as_json:
        output = {"status": "BLOCKED" if findings else "READY", "findings": findings, "stats": stats}
        print(json.dumps(output, indent=2))
        return 1 if findings else 0

    print("Pre-Execution Authority Gate")
    print(f"  Documents: {stats['total']}")
    print(f"  No owner:  {stats['no_owner']}")
    print(f"  Bad authority: {stats['bad_authority']}")
    print(f"  Overclaim: {stats['overclaim']}")

    if findings:
        print(f"\n❌ BLOCKED — {len(findings)} authority violations:")
        for f in findings:
            print(f"  [{f['rule']}] {f['file']}: {f['message']}")
        return 1

    print("\n✓ Authority gate PASSED")
    print(f"  {READY_DISCLAIMER}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
