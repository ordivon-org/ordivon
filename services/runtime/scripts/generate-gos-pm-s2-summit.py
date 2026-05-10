#!/usr/bin/env python3
"""Generate GOS-PM-S2 Summit — consolidate PM-6 through PM-10 (PM-S2).

Recommendation: Path Governance Core is VERIFIED with known boundaries.
PM series expansion: STOP recommended.

Usage:
    python scripts/generate-gos-pm-s2-summit.py
"""

from __future__ import annotations

import json, subprocess, sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUTPUT_DIR = ROOT / "docs/governance/generated"

STAGES = [
    {"stage": "PM-6", "name": "Coverage Resolution Pipeline", "commit": "a1992d9", "status": "VERIFIED", "key_output": "850 CB-12 → 5 resolution buckets", "not_claimed": ["CB-12 fully resolved", "all files governed"]},
    {"stage": "PM-7", "name": "Coverage Batch Application", "commit": "946e11f", "status": "VERIFIED", "key_output": "3 batches applied, 40 files resolved, receipts generated", "not_claimed": ["all CB-12 resolved", "full closure"]},
    {"stage": "PM-8", "name": "Coverage Ownership Routing", "commit": "cfba3c5", "status": "VERIFIED", "key_output": "2108 objects with owner/reviewer/approver routes", "not_claimed": ["human identity system", "PolicyActivation"]},
    {"stage": "PM-9", "name": "Coverage Admission Gate", "commit": "a6b205f", "status": "VERIFIED (SHADOW)", "key_output": "10 CA rules, git diff admission evaluation", "not_claimed": ["production enforcement", "full closure"]},
    {"stage": "PM-10", "name": "Path Governance Query", "commit": "0ac549a", "status": "VERIFIED", "key_output": "explain + query commands, impact-ready", "not_claimed": ["authorization", "execution plan", "full closure"]},
]

BOUNDARIES = [
    "826 CB-12 files remain OPEN — honest coverage boundary, not failure",
    "Admission gate in SHADOW mode — observes, does not block",
    "No human identity system — owner routes are structural, not authenticated",
    "No harness pack / adapter integration",
    "No external repository governance",
    "No PolicyActivation — 4 CandidateRules, 0 activated",
    "DEP-CI-PRODUCT-TESTS-ENV remains OPEN",
    "DEP-AUDIT-PIP-CVE-2026-3219 remains OPEN (weekly cron)",
]

RECOMMENDATION = {
    "decision": "STOP_PM_EXPANSION",
    "rationale": "Path Governance Core has established a complete control plane: auto path-map, registry/path reconciliation, authority taxonomy, route taxonomy, coverage boundary, resolution pipeline, batch application with receipts, ownership/review routing, admission gate, and query/impact. Further PM expansion would add diminishing returns without external governance targets.",
    "next_candidates": [
        "GOS-N2: Gate & Lifecycle Hardening (advisory→blocking, lesson/debt lifecycle)",
        "GOS-N3: AI Output Adapter / Protocol Adhesion",
        "GOS-N4: Coverage Boundary & Externalization Dry-Run",
        "Harness Pack / Adapter integration (finance, coding, etc.)",
    ],
}


def get_state() -> dict:
    try:
        cov = json.loads((OUTPUT_DIR / "coverage-boundary.json").read_text())
        cb12 = cov["stats"]["by_status"].get("debt_or_exclusion_required", "?")
        blocked = cov["stats"]["blocked"]
        total = cov["stats"]["total"]
    except Exception:
        cb12, blocked, total = "?", "?", "?"

    try:
        rec = json.loads((OUTPUT_DIR / "registry-path-reconciliation.json").read_text())
        rpr_blocking = sum(1 for f in rec.get("findings", []) if f["severity"] == "blocking")
    except Exception:
        rpr_blocking = "?"

    try:
        excl = json.loads((ROOT / "docs/governance/schemas/governed-exclusions.json").read_text())
        excl_count = len(excl.get("entries", {}))
    except Exception:
        excl_count = "?"

    return {"cb12_open": cb12, "blocked": blocked, "total_files": total, "rpr_blocking": rpr_blocking, "exclusions": excl_count}


def main() -> int:
    state = get_state()

    summit = {
        "stage_id": "GOS-PM-S2",
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "authority": "generated_view",
        "source_refs": ["coverage-boundary.json", "registry-path-reconciliation.json", "PM-1 through PM-10 receipts"],
        "pm_chain": STAGES,
        "current_state": state,
        "open_boundaries": BOUNDARIES,
        "recommendation": RECOMMENDATION,
        "not_claimed": ["full closure", "production readiness", "external governance", "PolicyActivation", "harness adapter readiness"],
    }

    (OUTPUT_DIR / "gos-pm-s2-summit.json").write_text(json.dumps(summit, indent=2, ensure_ascii=False) + "\n")

    # Markdown
    lines = [
        "# GOS-PM-S2 — Path Governance Core Summit 2",
        "",
        "> **GENERATED VIEW — DO NOT EDIT**",
        "> Full Closure: NOT CLAIMED",
        "",
        "## PM-6 → PM-10 Status",
        "",
        "| Stage | Status | Key Output |",
        "|---|---|---|",
    ]
    for s in STAGES:
        lines.append(f"| {s['stage']} | {s['status']} | {s['key_output'][:60]} |")
    lines.extend([
        "",
        "## Current State",
        f"- CB-12 open: {state['cb12_open']}",
        f"- Blocked: {state['blocked']}",
        f"- RPR BLOCKING: {state['rpr_blocking']}",
        f"- Exclusions: {state['exclusions']}",
        "",
        "## Recommendation",
        f"**{RECOMMENDATION['decision']}**: {RECOMMENDATION['rationale']}",
        "",
        "## Next Candidates",
    ])
    for nc in RECOMMENDATION["next_candidates"]:
        lines.append(f"- {nc}")
    lines.extend([
        "",
        "## Open Boundaries",
    ])
    for b in BOUNDARIES:
        lines.append(f"- {b}")
    lines.extend(["", "---", "```text", "Path Governance Core: VERIFIED with known boundaries.", "Full Closure: NOT CLAIMED.", "```"])
    (OUTPUT_DIR / "_gos-pm-s2-summit.md").write_text("\n".join(lines) + "\n")

    # DOT
    dot_lines = [
        "digraph GOS_PM_S2 {",
        '  rankdir="TB"; node [shape=box,style=filled,fontname="JetBrains Mono"];',
        '  pm5 [label="PM-5\\nCoverage Boundary",fillcolor="#a78bfa20",color="#a78bfa"];',
        '  pm6 [label="PM-6\\nResolution Pipeline",fillcolor="#34d39920",color="#34d399"];',
        '  pm7 [label="PM-7\\nBatch Application",fillcolor="#fbbf24",color="#fbbf24"];',
        '  pm8 [label="PM-8\\nOwnership Routing",fillcolor="#fb7185",color="#fb7185"];',
        '  pm9 [label="PM-9\\nAdmission Gate",fillcolor="#22d3ee",color="#22d3ee"];',
        '  pm10 [label="PM-10\\nGovernance Query",fillcolor="#c084fc",color="#c084fc"];',
        '  s2 [label="PM-S2\\nSummit 2\\nSTOP_PM_EXPANSION",fillcolor="#fbbf24",color="#fbbf24"];',
        "  pm5 -> pm6 -> pm7 -> pm8 -> pm9 -> pm10 -> s2;",
        "}",
    ]
    (OUTPUT_DIR / "gos-pm-s2-summit.dot").write_text("\n".join(dot_lines) + "\n")

    print(f"PM-S2 Summit: {len(STAGES)} stages consolidated")
    print(f"Recommendation: {RECOMMENDATION['decision']}")
    print(f"Full Closure: NOT CLAIMED")
    return 0


if __name__ == "__main__":
    sys.exit(main())
