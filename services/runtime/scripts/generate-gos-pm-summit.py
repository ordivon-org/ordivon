#!/usr/bin/env python3
"""Generate GOS-PM Stage Summit from existing governance data (PM-S).

Reads PM-1..PM-4 generated views, registries, taxonomies, and current
verification state. Emits consolidated summit JSON + markdown + DOT.
Summit is a generated view — not source of truth.

Usage:
    python scripts/generate-gos-pm-summit.py
"""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUTPUT_DIR = ROOT / "docs/governance/generated"

STAGES = [
    {
        "stage": "PM-1",
        "name": "Auto-Maintained Path Map",
        "commit_base": "432e9e8",
        "claim": "Auto Path Map",
        "status": "VERIFIED",
        "key_output": "update-path-map.py + verify-path-map.py + checkers/path-map",
        "evidence_refs": ["EV-PM1-stage-evidence"],
        "not_claimed": ["Full closure", "Global file coverage", "External governance"],
    },
    {
        "stage": "PM-2",
        "name": "Registry–Path Reconciliation",
        "commit_base": "beed0fa",
        "claim": "Registry–Path Reconciliation",
        "status": "VERIFIED_AS_OPERATIONAL",
        "key_output": "reconcile-registry-path.py + text+graph views + evidence bundle",
        "evidence_refs": ["EV-PM2-reconciler", "EV-PM2-views"],
        "not_claimed": ["Findings automatically fixed", "Registry-path sync"],
    },
    {
        "stage": "PM-2S",
        "name": "Enforcement Semantics",
        "commit_base": "3af90b9",
        "claim": "Severity/Enforcement Separation",
        "status": "VERIFIED",
        "key_output": "triage-rpr-findings.py + enforcement_status",
        "evidence_refs": ["EV-PM2S-triage"],
        "not_claimed": ["All findings resolved"],
    },
    {
        "stage": "PM-3",
        "name": "Authority Taxonomy",
        "commit_base": "6a6e832",
        "claim": "Domain-Aware Authority",
        "status": "VERIFIED",
        "key_output": "authority-taxonomy.json + 457 entries migrated",
        "evidence_refs": ["EV-PM3-taxonomy", "EV-PM3-migration"],
        "not_claimed": ["Taxonomy final forever"],
    },
    {
        "stage": "PM-4",
        "name": "Route Taxonomy / Doc-Type Map",
        "commit_base": "4f9f4e6",
        "claim": "Doc-Type/Route Compatibility",
        "status": "VERIFIED",
        "key_output": "route-taxonomy.json + RPR-3: 119→0",
        "evidence_refs": ["EV-PM4-route-taxonomy", "EV-PM4-rpr-reduction"],
        "not_claimed": ["Route taxonomy final"],
    },
]

BOUNDARIES = [
    "External governance: NOT CLAIMED — Ordivon governs itself only",
    "AI Output Adapter: NOT IMPLEMENTED — AI can bypass vocabulary",
    "PolicyActivation: ABSENT — 4 CandidateRules, 0 activated",
    "Full file coverage: PARTIAL — 809/2090 governed, 68 excluded, 1133 debt-parked",
    "CI parity: DEGRADED — DEP-CI-PRODUCT-TESTS-ENV remains OPEN",
    "Future drift: NOT PREVENTED — taxonomies will need maintenance",
]

NEXT_CANDIDATES = [
    "GOS-N2: Gate & Lifecycle Hardening — promote advisory gates to blocking",
    "GOS-N3: AI Output Adapter — enforce structured vocabulary on AI output",
    "GOS-N4: Coverage Boundary & Externalization Dry-Run",
    "Authority taxonomy review cadence — prevent stale domain assignments",
    "Route taxonomy maintenance schedule — new doc_types need route compatibility",
]


def get_current_state() -> dict:
    """Read current governance state from generated views."""
    try:
        rec = json.loads((OUTPUT_DIR / "registry-path-reconciliation.json").read_text())
        rpr_findings = rec.get("findings", [])
        rpr_blocking = sum(1 for f in rpr_findings if f["severity"] == "blocking")
        rpr_degraded = sum(1 for f in rpr_findings if f["severity"] == "degraded")
    except Exception:
        rpr_blocking = "?"
        rpr_degraded = "?"

    try:
        pm = json.loads((OUTPUT_DIR / "path-map.json").read_text())
        pm_blocked = pm["stats"].get("blocked", "?")
        pm_governed = pm["stats"].get("governed", "?")
        pm_tracked = pm["stats"].get("tracked_files", "?")
    except Exception:
        pm_blocked = "?"
        pm_governed = "?"
        pm_tracked = "?"

    try:
        reg = []
        with open(ROOT / "docs/governance/document-registry.jsonl") as f:
            for line in f:
                if line.strip():
                    reg.append(json.loads(line))
        reg_count = len(reg)
    except Exception:
        reg_count = "?"

    return {
        "rpr_blocking": rpr_blocking,
        "rpr_degraded": rpr_degraded,
        "path_map_blocked": pm_blocked,
        "path_map_governed": pm_governed,
        "path_map_tracked": pm_tracked,
        "registry_entries": reg_count,
    }


def generate_summit() -> dict:
    state = get_current_state()
    return {
        "stage_id": "GOS-PM-S",
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "authority": "generated_view",
        "source_refs": [
            "path-map.json",
            "registry-path-reconciliation.json",
            "authority-taxonomy.json",
            "route-taxonomy.json",
            "document-registry.jsonl",
        ],
        "pm_chain": STAGES,
        "current_status": state,
        "what_was_eliminated": [
            "hand-maintained path map counts (PM-1: generated from git ls-files + registry)",
            "flat source_of_truth authority (PM-3: 8 domains × 27 roles)",
            "hardcoded route_doc_type_map in reconciler (PM-4: route-taxonomy.json)",
            "severity/enforcement READY ambiguity (PM-2S: explicit semantics)",
            "silent unregistered files in governed dirs (PM-1: atomic governance gate)",
            "manual drift in generated views (PM-1/PM-2: CI verify detects drift)",
        ],
        "open_boundaries": BOUNDARIES,
        "next_stage_candidates": NEXT_CANDIDATES,
    }


def generate_markdown(summit: dict) -> str:
    state = summit["current_status"]
    lines = [
        "# GOS-PM Stage Summit",
        "",
        "> **GENERATED VIEW — DO NOT EDIT**",
        f"> Generated: {summit['generated_at']}",
        "> Source: path-map.json + registry-path-reconciliation.json + taxonomies",
        "> Authority: generated_view · Not source of truth",
        "",
        "---",
        "",
        "## 1. Stage Chain",
        "",
        "| Stage | Status | Core Output |",
        "|---|---|---|",
    ]
    for s in STAGES:
        lines.append(f"| {s['stage']} | {s['status']} | {s['key_output'][:60]} |")
    lines.extend([
        "",
        "## 2. Current Governance State",
        "",
        f"- RPR BLOCKING: {state['rpr_blocking']}",
        f"- RPR DEGRADED: {state['rpr_degraded']}",
        f"- Path Map blocked: {state['path_map_blocked']}",
        f"- Path Map governed: {state['path_map_governed']} / {state['path_map_tracked']} tracked",
        f"- Registry entries: {state['registry_entries']}",
        "",
        "## 3. What Was Structurally Eliminated",
        "",
    ])
    for item in summit.get("what_was_eliminated", []):
        lines.append(f"- {item}")
    lines.extend([
        "",
        "## 4. Not Claimed Per Stage",
        "",
    ])
    for s in STAGES:
        for nc in s["not_claimed"]:
            lines.append(f"- [{s['stage']}] {nc}")
    lines.extend([
        "",
        "## 5. Open Boundaries",
        "",
    ])
    for b in summit.get("open_boundaries", []):
        lines.append(f"- {b}")
    lines.extend([
        "",
        "## 6. Next Stage Candidates",
        "",
    ])
    for nc in summit.get("next_stage_candidates", []):
        lines.append(f"- {nc}")
    lines.extend([
        "",
        "---",
        "```text",
        "READY means selected checks passed; it does not authorize execution.",
        "Full Closure: NOT CLAIMED.",
        "```",
    ])
    return "\n".join(lines)


def generate_dot(summit: dict) -> str:
    lines = [
        "digraph GOS_PM_Summit {",
        '  rankdir="TB";',
        '  node [shape=box,style=filled,fontname="JetBrains Mono"];',
        '  edge [color="#64748b"];',
        "",
        '  repo [label="Repo Reality\\ngit ls-files",fillcolor="#94a3b820",color="#94a3b8"];',
    ]
    colors = {
        "PM-1": "#a78bfa",
        "PM-2": "#34d399",
        "PM-2S": "#fbbf24",
        "PM-3": "#fb7185",
        "PM-4": "#22d3ee",
        "PM-S": "#c084fc",
    }
    prev = "repo"
    for s in STAGES:
        sid = s["stage"].replace("-", "_")
        color = colors.get(s["stage"], "#94a3b8")
        lines.append(
            f'  {sid} [label="{s["stage"]}\\n{s["name"]}\\n{s["status"]}",fillcolor="{color}20",color="{color}"];'
        )
        lines.append(f"  {prev} -> {sid};")
        prev = sid
    lines.append('  summit [label="PM-Summit\\nEvidence+Boundary",fillcolor="#c084fc20",color="#c084fc"];')
    lines.append(f"  {prev} -> summit;")
    lines.append("}")
    return "\n".join(lines)


def main() -> int:
    summit = generate_summit()

    # Write JSON
    (OUTPUT_DIR / "gos-pm-summit.json").write_text(json.dumps(summit, indent=2, ensure_ascii=False) + "\n")
    print("Generated gos-pm-summit.json")

    # Write MD
    (OUTPUT_DIR / "_gos-pm-summit.md").write_text(generate_markdown(summit) + "\n")
    print("Generated _gos-pm-summit.md")

    # Write DOT
    (OUTPUT_DIR / "gos-pm-summit.dot").write_text(generate_dot(summit) + "\n")
    print("Generated gos-pm-summit.dot")

    print(
        f"\nStages: {len(STAGES)} · RPR: {summit['current_status']['rpr_blocking']} BLOCKING, {summit['current_status']['rpr_degraded']} DEGRADED"
    )
    print("Full Closure: NOT CLAIMED")
    return 0


if __name__ == "__main__":
    sys.exit(main())
