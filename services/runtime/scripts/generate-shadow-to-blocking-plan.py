#!/usr/bin/env python3
"""Generate shadow-to-blocking plan — identify candidate gates for upgrade dogfood (N2)."""

from __future__ import annotations

import json, sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "docs/governance/generated"
INVENTORY = OUTPUT / "gate-inventory.json"

CANDIDATES = [
    {
        "gate_id": "overclaim",
        "current_mode": "ADVISORY",
        "target_mode": "BLOCKING",
        "reason": "Banned completion vocabulary is well-defined and low false-positive. Already listed in controlled vocabulary schema. 0 false positives in PM series.",
        "negative_demo": "Add '全部完成' to a receipt → BLOCKED",
        "false_positive_review": "Check if file is a doc defining the vocabulary itself",
        "rollback_path": "git revert. Re-promote to SHADOW first if uncertain.",
        "owner": "governance-core-maintainer",
        "review_trigger": "After 7 days with 0 false positives",
    },
    {
        "gate_id": "debt_close_evidence",
        "current_mode": "ADVISORY",
        "target_mode": "BLOCKING",
        "reason": "CLOSED debt without close_evidence is a hard governance invariant. Currently 3 of 8 debts closed without evidence. Dogfood: enforce close_evidence on new closures.",
        "negative_demo": "Mark debt CLOSED without resolution field → BLOCKED",
        "false_positive_review": "Legacy debts closed before N2 have waiver",
        "rollback_path": "git revert. Legacy debts given migration waiver.",
        "owner": "governance-core-maintainer",
        "review_trigger": "After first debt closure with evidence",
    },
    {
        "gate_id": "generated_view_source_authority",
        "current_mode": "ADVISORY",
        "target_mode": "SHADOW",
        "reason": "Generated view claiming source authority is a core PM invariant. Currently enforced by coverage boundary classification but not as a standalone blocking gate. Promote to SHADOW first for 7-day observation.",
        "negative_demo": "Generated view doc_type = source_of_truth → BLOCKED (shadow)",
        "false_positive_review": "Check authority-taxonomy for generated domain compatibility",
        "rollback_path": "git revert to ADVISORY",
        "owner": "governance-core-maintainer",
        "review_trigger": "After 7 shadow days with 0 unexpected findings",
    },
    {
        "gate_id": "protected_unknown_path",
        "current_mode": "BLOCKING",
        "target_mode": "BLOCKING",
        "reason": "Already BLOCKING via coverage-boundary CB-1. Verify-gate-enforcement-matrix shows CI job present. No dogfood needed — already enforced.",
        "negative_demo": "Add file to docs/governance/ without registry → CB-1 BLOCKED",
        "false_positive_review": "N/A — already blocking",
        "rollback_path": "N/A",
        "owner": "governance-core-maintainer",
        "review_trigger": "N/A — already enforced",
    },
]


def generate() -> dict:
    candidates = CANDIDATES
    return {
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "authority": "generated_view",
        "summary": {"total_candidates": len(candidates), "for_dogfood": 2, "already_blocking": 1, "deferred": 1},
        "candidates": candidates,
        "not_claimed": ["all gates upgraded", "full enforcement", "PolicyActivation", "full closure"],
    }


def main() -> int:
    data = generate()
    (OUTPUT / "shadow-to-blocking-plan.json").write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n")

    lines = [
        "# Shadow-to-Blocking Plan",
        "",
        "> **GENERATED VIEW — DO NOT EDIT**",
        "",
        "| Gate | Current | Target | Dogfood |",
        "|---|---|---|---|",
    ]
    for c in data["candidates"]:
        dogfood = "✓" if c["gate_id"] in ("overclaim", "debt_close_evidence") else ("shadow" if c["gate_id"] == "generated_view_source_authority" else "already")
        lines.append(f"| {c['gate_id']} | {c['current_mode']} | {c['target_mode']} | {dogfood} |")
    lines.extend([
        "",
        "## Dogfood Candidates (N2)",
        "",
        "### 1. Overclaim Gate: ADVISORY → BLOCKING",
        "Well-defined controlled vocabulary. 0 false positives in PM series.",
        "Banned words: complete, done, 全绿, 已完成, honest, perfect, finished.",
        "",
        "### 2. Debt Close Evidence: ADVISORY → BLOCKING",
        "CLOSED debt requires close_evidence. Core invariant.",
        "3 legacy debts grandfathered with waiver.",
        "",
        "## Shadow Candidate",
        "",
        "### Generated View Source Authority: ADVISORY → SHADOW",
        "Shadow only — 7-day observation before blocking.",
        "",
        "## Already Enforcing",
        "",
        "### Protected Unknown Path: BLOCKING",
        "Already enforced via coverage-boundary CB-1.",
    ])
    lines.extend(["", "---", "```text", "Full Closure: NOT CLAIMED.", "```"])
    (OUTPUT / "_shadow-to-blocking-plan.md").write_text("\n".join(lines) + "\n")

    print(f"Shadow-to-Blocking Plan: {len(data['candidates'])} candidates")
    print("  Dogfood: overclaim + debt_close_evidence")
    print("  Shadow: generated_view_source_authority")
    print("  Already: protected_unknown_path")
    return 0


if __name__ == "__main__":
    sys.exit(main())
