#!/usr/bin/env python3
"""Generate reconciliation report from RPR findings (GOS-PM-2 text view).

Text explains WHY — governance reasoning, not topology.
Generated from registry-path-reconciliation.json.
Not source of truth. Not evidence. Generated view.

Usage:
    python scripts/generate-reconciliation-report.py
"""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INPUT_PATH = ROOT / "docs/governance/generated/registry-path-reconciliation.json"
OUTPUT_PATH = ROOT / "docs/governance/generated/_registry-path-reconciliation.md"

A_DESCRIPTIONS = {
    "A1": "Fix the Registry claim — owner, doc_type, authority, or lifecycle is incorrect. The declaration does not match the governed reality.",
    "A2": "Refine the Path Map observation rule — a new doc_type is not covered, a route is too narrow, or a classification rule needs updating.",
    "A3": "Redesign the governance mechanism — Registry and Path Map are both locally correct, but the system lacks an intermediate model to reconcile them.",
    "A4": "Record as formal debt — this gap is intentional (legacy, external, not yet governable). Must not be silently ignored.",
}


def generate() -> str:
    if not INPUT_PATH.exists():
        return "ERROR: registry-path-reconciliation.json not found. Run reconcile-registry-path.py first."

    data = json.loads(INPUT_PATH.read_text())
    stats = data.get("stats", {})
    findings = data.get("findings", [])

    blocking = [f for f in findings if f["severity"] == "blocking"]
    degraded = [f for f in findings if f["severity"] == "degraded"]
    generated_at = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    lines = [
        "# Registry–Path Reconciliation Report",
        "",
        f"> **GENERATED VIEW — DO NOT EDIT**",
        f"> Generated: {generated_at}",
        f"> Source: `docs/governance/generated/registry-path-reconciliation.json`",
        f"> Authority: supporting_evidence",
        "> **Not source of truth. Not raw evidence. Text view only.**",
        "",
        "---",
        "",
        "## Summary",
        "",
        f"- Registry entries: {stats.get('registry_entries', '?')}",
        f"- Path Map nodes: {stats.get('path_map_nodes', '?')}",
        f"- In both: {stats.get('in_both', '?')}",
        f"- Only registry: {stats.get('only_registry', '?')}",
        f"- Only path map: {stats.get('only_path_map', '?')}",
        f"- Findings: {len(blocking)} BLOCKING, {len(degraded)} DEGRADED",
        "",
        "---",
        "",
    ]

    if blocking:
        lines.append("## BLOCKING Findings")
        lines.append("")
        for f in blocking:
            lines.extend(format_finding(f))
    else:
        lines.append("## No BLOCKING Findings")
        lines.append("")

    if degraded:
        lines.append("---")
        lines.append("")
        lines.append("## DEGRADED Findings")
        lines.append("")
        for f in degraded[:20]:
            lines.extend(format_finding(f))
        if len(degraded) > 20:
            lines.append(f"_... and {len(degraded) - 20} more DEGRADED findings_")
            lines.append("")

    lines.append("---")
    lines.append("")
    lines.append("## Disposition Reference")
    lines.append("")
    for a, desc in A_DESCRIPTIONS.items():
        lines.append(f"- **{a}**: {desc}")
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("```text")
    lines.append("READY means selected checks passed; it does not authorize execution.")
    lines.append("```")

    return "\n".join(lines)


def format_finding(f: dict) -> list[str]:
    code = f.get("code", "?")
    sev = f.get("severity", "?")
    path = f.get("path", "?")
    msg = f.get("message", "")
    disp = f.get("disposition", "?")
    reg = f.get("registry_claim", {})
    obs = f.get("path_observation", {})

    lines = [
        f"### {code} [{sev.upper()}] — `{path}`",
        "",
        f"**Finding**: {msg}",
        f"**Disposition Candidate**: {disp} — {A_DESCRIPTIONS.get(disp, '')}",
        "",
    ]

    if reg:
        lines.append("**Registry Claim**:")
        if isinstance(reg, dict):
            for k, v in reg.items():
                lines.append(f"- {k}: `{v}`")
        lines.append("")

    if obs:
        lines.append("**Path Observation**:")
        if isinstance(obs, dict):
            for k, v in obs.items():
                lines.append(f"- {k}: `{v}`")
        lines.append("")

    lines.append("**Not Claimed**:")
    lines.append("- This finding does not prove Registry is wrong.")
    lines.append("- This finding does not prove Path Map is wrong.")
    lines.append("- This finding requires A1/A2/A3/A4 review before action.")
    lines.append("")

    return lines


def main() -> int:
    report = generate()
    OUTPUT_PATH.write_text(report + "\n")
    print(f"Generated {OUTPUT_PATH}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
