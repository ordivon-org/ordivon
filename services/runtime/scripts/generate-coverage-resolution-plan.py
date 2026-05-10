#!/usr/bin/env python3
"""Generate coverage resolution plan — bucket CB-12 files for resolution (PM-6).

Reads coverage-boundary.json, applies coverage-resolution-rules.json.
Emits plan JSON + markdown with buckets, counts, batch candidates.
Resolution candidate ≠ resolved. Batch plan ≠ execution.

Usage:
    python scripts/generate-coverage-resolution-plan.py
"""

from __future__ import annotations

import fnmatch, json, sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUTPUT_DIR = ROOT / "docs/governance/generated"
SCHEMA_DIR = ROOT / "docs/governance/schemas"
COVERAGE = OUTPUT_DIR / "coverage-boundary.json"
RULES = SCHEMA_DIR / "coverage-resolution-rules.json"


def match_any(filepath: str, patterns: list[str]) -> bool:
    return any(fnmatch.fnmatch(filepath, p) for p in patterns)


def generate() -> dict:
    coverage = json.loads(COVERAGE.read_text())
    rules = json.loads(RULES.read_text())

    cb12_files = [f for f in coverage.get("files", []) if f.get("coverage_status") == "debt_or_exclusion_required"]
    buckets_data = rules.get("buckets", [])
    fallback = rules.get("fallback", {"bucket_id": "debt-park-candidate"})

    bucketed = {b["bucket_id"]: [] for b in buckets_data}
    bucketed[fallback["bucket_id"]] = []
    unmatched = []

    for f in cb12_files:
        fp = f["path"]
        matched = False
        for bucket in buckets_data:
            if match_any(fp, bucket.get("match_patterns", [])):
                bucketed[bucket["bucket_id"]].append(f)
                matched = True
                break
        if not matched:
            bucketed[fallback["bucket_id"]].append(f)

    plan_buckets = []
    for bucket in buckets_data + [fallback]:
        files = bucketed.get(bucket["bucket_id"], [])
        if not files:
            continue
        plan_buckets.append({
            "bucket_id": bucket["bucket_id"],
            "candidate_status": bucket["bucket_id"],
            "file_count": len(files),
            "sample_paths": [f["path"] for f in files[:5]],
            "resolution_target": bucket.get("target_status", "debt_parked"),
            "required_metadata": bucket.get("required_metadata", []),
            "disposition": bucket.get("disposition", "A4"),
            "status": "TRIAGED",
            "review_trigger": f"batch review for {bucket['bucket_id']}",
        })

    return {
        "stage": "GOS-PM-6",
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "authority": "generated_view",
        "source_status": "debt_or_exclusion_required",
        "source_count": len(cb12_files),
        "buckets": plan_buckets,
        "unmatched_count": len(unmatched),
        "not_claimed": ["CB-12 fully resolved", "all files governed", "full closure"],
    }


def generate_md(plan: dict) -> str:
    lines = [
        "# Coverage Resolution Plan",
        "",
        "> **GENERATED VIEW — DO NOT EDIT**",
        f"> Source: {plan['source_count']} debt_or_exclusion_required files",
        "> Resolution candidate ≠ resolved. Batch plan ≠ execution.",
        "",
        f"## Summary: {plan['source_count']} files → {len(plan['buckets'])} buckets",
        "",
        "| Bucket | Count | Target | Disposition |",
        "|---|---|---|---|",
    ]
    for b in plan["buckets"]:
        lines.append(f"| {b['bucket_id']} | {b['file_count']} | {b['resolution_target']} | {b['disposition']} |")
    lines.extend([
        "",
        "## Not Claimed",
        "- CB-12 fully resolved",
        "- All files governed",
        "- Full closure",
        "",
        "---",
        "```text",
        "Resolution candidate ≠ resolved. Batch plan ≠ execution.",
        "Full Closure: NOT CLAIMED.",
        "```",
    ])
    return "\n".join(lines)


def main() -> int:
    plan = generate()
    (OUTPUT_DIR / "coverage-resolution-plan.json").write_text(json.dumps(plan, indent=2, ensure_ascii=False) + "\n")
    (OUTPUT_DIR / "_coverage-resolution-plan.md").write_text(generate_md(plan) + "\n")
    print(f"Resolution Plan: {plan['source_count']} CB-12 files → {len(plan['buckets'])} buckets")
    for b in plan["buckets"]:
        print(f"  {b['bucket_id']}: {b['file_count']} → {b['resolution_target']} ({b['disposition']})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
