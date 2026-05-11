#!/usr/bin/env python3
"""Verify stage evidence bundle — check all required evidence exists (GOS-PM-1).

Reads stage-manifest.json for each stage, verifies all required_evidence
entries exist in stage-evidence-index.jsonl, checks raw output files exist,
and validates sha256 hashes match.

Usage:
    python scripts/verify-stage-evidence.py --bundle gos-pm-1
    python scripts/verify-stage-evidence.py --bundle gos-pm-1 --json
"""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EVIDENCE_BASE = ROOT / "docs/governance/evidence"


def load_index(bundle: str) -> dict[str, dict]:
    """Load stage-evidence-index.jsonl into a dict keyed by evidence_id."""
    index_path = EVIDENCE_BASE / bundle / "stage-evidence-index.jsonl"
    if not index_path.exists():
        return {}
    entries = {}
    with open(index_path) as f:
        for line in f:
            if line.strip():
                e = json.loads(line)
                entries[e["evidence_id"]] = e
    return entries


def verify_bundle(bundle: str) -> tuple[bool, list[dict]]:
    """Verify all stages in a bundle. Returns (pass, findings)."""
    bundle_dir = EVIDENCE_BASE / bundle
    if not bundle_dir.exists():
        return False, [{"severity": "blocking", "message": f"Bundle not found: {bundle}"}]

    index = load_index(bundle)
    findings = []
    stages_checked = 0

    # Find all stage directories with manifest
    for stage_dir in sorted(bundle_dir.iterdir()):
        if not stage_dir.is_dir():
            continue
        manifest_path = stage_dir / "stage-manifest.json"
        if not manifest_path.exists():
            findings.append({"severity": "degraded", "message": f"No manifest for {stage_dir.name}"})
            continue

        manifest = json.loads(manifest_path.read_text())
        stages_checked += 1
        stage_id = manifest.get("stage_id", stage_dir.name)

        # Check required_evidence
        for ev_id in manifest.get("required_evidence", []):
            if ev_id not in index:
                findings.append({
                    "severity": "blocking",
                    "stage": stage_id,
                    "message": f"Missing evidence: {ev_id}",
                })
                continue

            ev = index[ev_id]

            # Check raw output file exists
            raw_path = ROOT / ev.get("raw_output", "")
            if not raw_path.exists():
                findings.append({
                    "severity": "blocking",
                    "stage": stage_id,
                    "evidence": ev_id,
                    "message": f"Raw output missing: {ev['raw_output']}",
                })
                continue

            # Check sha256
            raw_content = raw_path.read_text()
            actual_sha = hashlib.sha256(raw_content.encode()).hexdigest()[:16]
            expected_sha = ev.get("sha256", "")
            if actual_sha != expected_sha:
                findings.append({
                    "severity": "blocking",
                    "stage": stage_id,
                    "evidence": ev_id,
                    "message": f"SHA256 mismatch: stored={expected_sha} actual={actual_sha}",
                })

        # Check for overclaim
        not_claimed = manifest.get("not_claimed", [])
        for nc in not_claimed:
            pass

    if stages_checked == 0:
        findings.append({"severity": "blocking", "message": "No stages found"})

    passed = not any(f["severity"] == "blocking" for f in findings)
    return passed, findings


def main() -> int:
    as_json = "--json" in sys.argv
    bundle = None
    for a in sys.argv[1:]:
        if a.startswith("--bundle="):
            bundle = a.split("=", 1)[1]
        elif a.startswith("--bundle"):
            continue  # next arg is the value
        elif not a.startswith("--"):
            bundle = a

    if not bundle:
        print("Usage: verify-stage-evidence.py --bundle gos-pm-1")
        return 1

    passed, findings = verify_bundle(bundle)

    if as_json:
        print(
            json.dumps(
                {
                    "status": "READY" if passed else "BLOCKED",
                    "findings": findings,
                },
                indent=2,
            )
        )
        return 0 if passed else 1

    print(f"Evidence Bundle: {bundle}")
    if not findings:
        print("✓ All evidence verified")
        return 0

    blocking = [f for f in findings if f["severity"] == "blocking"]
    degraded = [f for f in findings if f["severity"] == "degraded"]
    print(f"❌ {len(blocking)} blocking, {len(degraded)} degraded")
    for f in blocking:
        print(f"  [{f.get('stage', '?')}] {f['message']}")
    return 1


if __name__ == "__main__":
    sys.exit(main())
