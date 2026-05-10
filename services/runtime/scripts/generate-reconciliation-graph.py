#!/usr/bin/env python3
"""Generate reconciliation graph from RPR findings (GOS-PM-2 graph view).

Graph shows WHERE — governance topology, not reasoning.
One subgraph per finding. Claim vs Observation, connected to disposition.
Generated from registry-path-reconciliation.json.

Usage:
    python scripts/generate-reconciliation-graph.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INPUT_PATH = ROOT / "docs/governance/generated/registry-path-reconciliation.json"
DOT_PATH = ROOT / "docs/governance/generated/registry-path-reconciliation.dot"

COLORS = {
    "blocking": "#fb7185",
    "degraded": "#fbbf24",
    "registry": "#a78bfa",
    "path": "#34d399",
    "finding": "#fb7185",
    "disposition": "#22d3ee",
    "A1": "#22d3ee",
    "A2": "#34d399",
    "A3": "#fbbf24",
    "A4": "#fb7185",
}


def sanitize(s: str) -> str:
    return s.replace("/", "_").replace(".", "_").replace("-", "_").replace(" ", "_")[:40]


def generate() -> str:
    if not INPUT_PATH.exists():
        return ""

    data = json.loads(INPUT_PATH.read_text())
    findings = data.get("findings", [])

    lines = [
        "digraph RegistryPathReconciliation {",
        '  rankdir="TB";',
        '  node [shape=box,style=filled,fontname="JetBrains Mono",fontsize=10];',
        '  edge [fontsize=8];',
        "",
        "  // Legend",
        '  subgraph cluster_legend {',
        '    label="Legend";',
        '    style=filled;',
        '    fillcolor="#1e293b20";',
        '    color="#475569";',
        '    registry [label="Registry Claim",fillcolor="#a78bfa20",color="#a78bfa"];',
        '    observation [label="Path Observation",fillcolor="#34d39920",color="#34d399"];',
        '    conflict [label="Finding",fillcolor="#fb718520",color="#fb7185"];',
        '    action [label="Disposition Candidate",fillcolor="#22d3ee20",color="#22d3ee"];',
        "  }",
        "",
    ]

    for i, f in enumerate(findings[:30]):
        code = f.get("code", "?")
        sev = f.get("severity", "?")
        path = f.get("path", "?")
        disp = f.get("disposition", "?")
        msg = f.get("message", "")[:60]
        reg = f.get("registry_claim", {})
        obs = f.get("path_observation", {})

        path_id = sanitize(path)
        reg_id = f"reg_{path_id}_{i}"
        obs_id = f"obs_{path_id}_{i}"
        find_id = f"find_{path_id}_{i}"
        disp_id = f"disp_{path_id}_{i}"

        reg_label = "\\n".join([f"{k}: {v}" for k, v in reg.items()][:3]) if isinstance(reg, dict) else str(reg)
        obs_label = "\\n".join([f"{k}: {v}" for k, v in obs.items()][:3]) if isinstance(obs, dict) else str(obs)

        lines.append(f"  // Finding {i+1}: {code} — {path}")
        lines.append(f'  {reg_id} [label="Registry Claim\\n{reg_label}",fillcolor="{COLORS["registry"]}20",color="{COLORS["registry"]}"];')
        lines.append(f'  {obs_id} [label="Path Observation\\n{obs_label}",fillcolor="{COLORS["path"]}20",color="{COLORS["path"]}"];')
        lines.append(f'  {find_id} [label="{code}\\n{msg}",fillcolor="{COLORS[sev]}20",color="{COLORS[sev]}"];')
        lines.append(f'  {disp_id} [label="{disp}",fillcolor="{COLORS.get(disp, "#22d3ee")}20",color="{COLORS.get(disp, "#22d3ee")}"];')
        lines.append(f"  {reg_id} -> {find_id} [label=\"claim\",color=\"{COLORS['registry']}\"];")
        lines.append(f"  {obs_id} -> {find_id} [label=\"observation\",color=\"{COLORS['path']}\"];")
        lines.append(f"  {find_id} -> {disp_id} [label=\"candidate\",color=\"{COLORS[sev]}\"];")
        lines.append("")

    lines.append("}")
    return "\n".join(lines)


def main() -> int:
    dot = generate()
    if not dot:
        print("No reconciliation data found. Run reconcile-registry-path.py first.")
        return 1
    DOT_PATH.write_text(dot + "\n")
    print(f"Generated {DOT_PATH}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
