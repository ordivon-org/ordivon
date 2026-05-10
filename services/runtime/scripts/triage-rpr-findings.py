#!/usr/bin/env python3
"""Generate RPR finding triage from reconciliation data (PM-2S).

Buckets all RPR findings into A1/A2/A3/A4 disposition groups.
Does NOT fix findings. Does NOT close findings. Only classifies.

Usage:
    python scripts/triage-rpr-findings.py
    python scripts/triage-rpr-findings.py --json
"""

from __future__ import annotations

import json
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INPUT_PATH = ROOT / "docs/governance/generated/registry-path-reconciliation.json"
OUTPUT_JSON = ROOT / "docs/governance/generated/rpr-triage.json"
OUTPUT_MD = ROOT / "docs/governance/generated/_rpr-triage.md"

# Disposition routing rules
ROUTES = {
    "RPR-1": "A1",  # file missing → fix registry claim
    "RPR-2": "A4",  # no registry → A4 debt required
    "RPR-3": "A2",  # doc_type/route mismatch → refine path-map-rules
    "RPR-4": "A3",  # authority/risk mismatch → authority model gap
    "RPR-5": "A1",  # owner unsupported → fix claim
    "RPR-6": "A3",  # generated view authority → mechanism gap
    "RPR-7": "A2",  # exclusion conflict → refine rules
    "RPR-8": "A2",  # path rule gap → refine rules
    "RPR-9": "A4",  # intentional gap → debt required
    "RPR-10": "A3", # observation overrides claim → mechanism gap
}

# Enforcement status per finding code
ENFORCEMENT = {
    "RPR-1": "NOT_ENFORCED",
    "RPR-2": "NOT_ENFORCED",
    "RPR-3": "NOT_ENFORCED",
    "RPR-4": "ENFORCED",      # BLOCKING → should be CI-enforced
    "RPR-5": "NOT_ENFORCED",
    "RPR-6": "NOT_ENFORCED",
    "RPR-7": "NOT_ENFORCED",
    "RPR-8": "NOT_ENFORCED",
    "RPR-9": "NOT_ENFORCED",
    "RPR-10": "NOT_ENFORCED",
}


def triage() -> dict:
    if not INPUT_PATH.exists():
        return {"error": "reconciliation data not found"}

    data = json.loads(INPUT_PATH.read_text())
    findings = data.get("findings", [])

    # Group by disposition
    by_disposition = {"A1": [], "A2": [], "A3": [], "A4": []}
    by_code = Counter()
    by_severity = Counter()

    for f in findings:
        code = f.get("code", "?")
        disp = ROUTES.get(code, "A1")
        if f.get("severity") == "blocking":
            disp = "A3" if code == "RPR-4" else disp
        by_disposition[disp].append(f)
        by_code[code] += 1
        by_severity[f.get("severity", "?")] += 1

    stats = {
        "total": len(findings),
        "by_severity": dict(by_severity),
        "by_code": dict(by_code),
        "by_disposition": {k: len(v) for k, v in by_disposition.items()},
        "enforcement": {code: ENFORCEMENT.get(code, "NOT_ENFORCED") for code in by_code},
    }

    triaged = []
    for disp, items in by_disposition.items():
        if not items:
            continue
        group = {
            "disposition": disp,
            "count": len(items),
            "summary": {
                "A1": "Fix registry claims — stale owner, wrong doc_type, incorrect lifecycle",
                "A2": "Refine path-map rules — missing route, narrow coverage, rule conflict",
                "A3": "Redesign authority/mechanism model — source_of_truth too coarse, route risk model incomplete",
                "A4": "Record formal debt — intentional gap, legacy, external, not yet governable",
            }.get(disp, ""),
            "samples": [
                {
                    "code": f.get("code"),
                    "path": f.get("path"),
                    "message": f.get("message", "")[:100],
                    "severity": f.get("severity"),
                    "enforcement": ENFORCEMENT.get(f.get("code", ""), "NOT_ENFORCED"),
                }
                for f in items[:5]
            ],
        }
        triaged.append(group)

    return {"generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"), "stats": stats, "groups": triaged}


def generate_markdown(data: dict) -> str:
    stats = data.get("stats", {})
    groups = data.get("groups", [])

    lines = [
        "# RPR Finding Triage",
        "",
        "> **GENERATED VIEW — DO NOT EDIT**",
        f"> Generated: {data.get('generated_at', '?')}",
        "> Source: `docs/governance/generated/registry-path-reconciliation.json`",
        "> This report classifies findings. It does NOT fix them.",
        "",
        "---",
        "",
        "## Enforcement Semantics",
        "",
        "Finding severity and gate enforcement are separate dimensions:",
        "",
        "| Finding Severity | Gate Enforcement | Meaning |",
        "|---|---|---|",
        "| BLOCKING | ENFORCED | CI gate blocks on this finding |",
        "| BLOCKING | NOT_ENFORCED | Finding severity is BLOCKING but gate is advisory — STATE SEMANTICS GAP |",
        "| DEGRADED | NOT_ENFORCED | Non-blocking observation, informational |",
        "| DEGRADED | SHADOW | Non-blocking, shadow-mode collection |",
        "",
        "**Critical rule**: BLOCKING while NOT_ENFORCED creates a state semantics gap.",
        "This must be resolved — either enforce or reclassify.",
        "",
        "---",
        "",
        "## Summary",
        "",
        f"- Total findings: {stats.get('total', '?')}",
        f"- By severity: {stats.get('by_severity', {})}",
        f"- By code: {stats.get('by_code', {})}",
        f"- By disposition: {stats.get('by_disposition', {})}",
        "",
        "---",
        "",
    ]

    for g in groups:
        disp = g["disposition"]
        lines.append(f"## A{disp[-1]} — {g['summary'][:60]}")
        lines.append(f"")
        lines.append(f"- Count: {g['count']}")
        lines.append(f"")
        lines.append("| Code | Severity | Enforced | Path | Message |")
        lines.append("|---|---|---|---|---|")
        for s in g.get("samples", []):
            enf = "YES" if s["enforcement"] == "ENFORCED" else "no"
            lines.append(f"| {s['code']} | {s['severity']} | {enf} | `{s['path']}` | {s['message'][:60]} |")

        if g["count"] > len(g.get("samples", [])):
            lines.append(f"| ... | ... | ... | _and {g['count'] - len(g.get('samples', []))} more_ | |")
        lines.append("")

    lines.append("---")
    lines.append("")
    lines.append("## RPR-4 Disposition (Authority Model Gap)")
    lines.append("")
    lines.append("The 2 BLOCKING RPR-4 findings reveal that `source_of_truth` is used for both")
    lines.append("document truth AND implementation/schema authority. These are different")
    lines.append("authority domains.")
    lines.append("")
    lines.append("**Disposition**: A3 — Authority Taxonomy Redesign")
    lines.append("")
    lines.append("Not A1 (fixing the claim) because the files ARE authoritative for their domains.")
    lines.append("Not A2 (fixing the route) because the route risk model is correct.")
    lines.append("")
    lines.append("The authority model needs to distinguish:")
    lines.append("- Document truth: `doc_source_of_truth` / `current_status` / `supporting_evidence`")
    lines.append("- Implementation source: `implementation_source`")
    lines.append("- Schema definition: `schema_source`")
    lines.append("- Generated view: `generated_view` / `derived_view`")
    lines.append("")
    lines.append("**Status**: OPEN — pending authority model redesign (PM-3 or later).")

    return "\n".join(lines)


def main() -> int:
    as_json = "--json" in sys.argv
    data = triage()

    if "error" in data:
        print(data["error"])
        return 1

    OUTPUT_JSON.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n")
    OUTPUT_MD.write_text(generate_markdown(data) + "\n")
    print(f"Generated {OUTPUT_JSON}")
    print(f"Generated {OUTPUT_MD}")
    print(f"Findings: {data['stats']['total']} → grouped into {len(data['groups'])} disposition buckets")
    return 0


if __name__ == "__main__":
    sys.exit(main())
