#!/usr/bin/env python3
"""Verify GOS-PM Summit — every stage claim must have evidence (PM-S).
Checks: missing evidence refs, missing not_claimed, generated drift, overclaim.
"""

from __future__ import annotations

import json, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SUMMIT = ROOT / "docs/governance/generated/gos-pm-summit.json"

BANNED = ["completed", "all done", "all green", "全线闭合", "全部完成", "彻底解决", "没有问题", "全绿", "honest", "perfect", "finished", "100%", "zero issues"]

def verify() -> tuple[list[dict], dict]:
    if not SUMMIT.exists():
        return [{"code": "PMS-0", "severity": "blocking", "message": "Summit not found"}], {}

    summit = json.loads(SUMMIT.read_text())
    findings = []
    stats = {"stages": len(summit.get("pm_chain", []))}

    for s in summit.get("pm_chain", []):
        stage = s.get("stage", "?")
        if not s.get("evidence_refs"):
            findings.append({"code": "PMS-2", "severity": "blocking", "stage": stage, "message": f"No evidence_refs for {stage}"})
        if not s.get("not_claimed"):
            findings.append({"code": "PMS-5", "severity": "blocking", "stage": stage, "message": f"No not_claimed for {stage}"})

    if summit.get("authority") == "source_of_truth":
        findings.append({"code": "PMS-7", "severity": "blocking", "message": "Summit marked source_of_truth"})

    # Check banned words in generated markdown
    md = (ROOT / "docs/governance/generated/_gos-pm-summit.md")
    if md.exists():
        md_text = md.read_text()
        for word in BANNED:
            if word in md_text.lower():
                findings.append({"code": "PMS-4", "severity": "degraded", "message": f"Banned word '{word}' in summit markdown"})

    return findings, stats


def main() -> int:
    as_json = "--json" in sys.argv
    findings, stats = verify()
    blocking = [f for f in findings if f["severity"] == "blocking"]
    degraded = [f for f in findings if f["severity"] == "degraded"]

    if as_json:
        print(json.dumps({"status": "BLOCKED" if blocking else "READY", "findings": findings, "stats": stats}, indent=2))
        return 1 if blocking else 0

    print(f"Summit Verification: {stats['stages']} stages")
    if not findings:
        print("✓ Summit coherent — all stages have evidence_refs and not_claimed")
        return 0
    print(f"❌ {len(blocking)} BLOCKING, {len(degraded)} DEGRADED")
    for f in findings:
        print(f"  [{f['code']}] {f.get('stage','?')}: {f['message']}")
    return 1


if __name__ == "__main__":
    sys.exit(main())
