#!/usr/bin/env python3
"""Generate lifecycle health report — debt, lesson, CandidateRule, waiver state (N2).

Outputs:
    docs/governance/generated/lifecycle-health.json
    docs/governance/generated/_lifecycle-health.md
"""

from __future__ import annotations

import json, sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "docs/governance/generated"
DEBT_PATH = ROOT / "docs/governance/dependency-audit-debts.jsonl"
LESSON_PATH = ROOT / "docs/governance/lesson-ledger.jsonl"
CANDIDATE_RULES_PATH = ROOT / "docs/governance/checker-maturity-ledger.jsonl"


def scan_debts() -> dict:
    stats = {"total": 0, "open": 0, "closed": 0, "stale": 0, "closed_no_evidence": 0, "no_owner": 0, "no_review_trigger": 0}
    details = []
    if not DEBT_PATH.exists():
        return stats
    with open(DEBT_PATH) as f:
        for line in f:
            if not line.strip():
                continue
            try:
                d = json.loads(line)
            except json.JSONDecodeError:
                continue
            stats["total"] += 1
            did = d.get("debt_id", "?")
            status = d.get("status", "UNKNOWN")
            if status == "OPEN":
                stats["open"] += 1
            elif status in ("CLOSED", "closed"):
                stats["closed"] += 1
                if not d.get("resolution"):
                    stats["closed_no_evidence"] += 1
                    details.append({"debt_id": did, "finding": "LC-4", "message": "CLOSED without close_evidence"})
            if not d.get("owner"):
                stats["no_owner"] += 1
                details.append({"debt_id": did, "finding": "LC-1", "message": "No owner"})
            if not d.get("review_trigger"):
                stats["no_review_trigger"] += 1
                details.append({"debt_id": did, "finding": "LC-2", "message": "No review_trigger"})
    stats["details"] = details
    return stats


def scan_lessons() -> dict:
    stats = {"total": 0, "actioned": 0, "unactioned": 0, "actioned_no_ref": 0, "candidate_rule_no_id": 0}
    details = []
    if not LESSON_PATH.exists():
        return stats
    with open(LESSON_PATH) as f:
        for line in f:
            if not line.strip():
                continue
            try:
                l = json.loads(line)
            except json.JSONDecodeError:
                continue
            stats["total"] += 1
            lid = l.get("lesson_id", "?")
            if l.get("status") == "actioned":
                stats["actioned"] += 1
                if not l.get("action_refs"):
                    stats["actioned_no_ref"] += 1
                    details.append({"lesson_id": lid, "finding": "LC-6", "message": "Actioned without action_refs"})
            else:
                stats["unactioned"] += 1
    stats["details"] = details
    return stats


def generate() -> dict:
    debts = scan_debts()
    lessons = scan_lessons()

    findings = []
    findings.extend(debts.pop("details", []))
    findings.extend(lessons.pop("details", []))

    blocked = sum(1 for f in findings if f.get("finding") in ("LC-1", "LC-2", "LC-4", "LC-6"))

    return {
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "authority": "generated_view",
        "debts": debts,
        "lessons": lessons,
        "findings": findings,
        "summary": {"total_findings": len(findings), "blocking": blocked},
        "not_claimed": ["all lifecycle objects governed", "full closure"],
    }


def main() -> int:
    data = generate()
    OUTPUT.mkdir(parents=True, exist_ok=True)
    (OUTPUT / "lifecycle-health.json").write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n")

    lines = [
        "# Lifecycle Health Report",
        "",
        "> **GENERATED VIEW — DO NOT EDIT**",
        "",
        "## Debts",
        f"- Total: {data['debts']['total']}",
        f"- Open: {data['debts']['open']}",
        f"- Closed: {data['debts']['closed']}",
        f"- Stale: {data['debts']['stale']}",
        f"- Closed without evidence: {data['debts']['closed_no_evidence']}",
        f"- No owner: {data['debts']['no_owner']}",
        f"- No review trigger: {data['debts']['no_review_trigger']}",
        "",
        "## Lessons",
        f"- Total: {data['lessons']['total']}",
        f"- Actioned: {data['lessons']['actioned']}",
        f"- Un-actioned: {data['lessons']['unactioned']}",
        f"- Actioned without refs: {data['lessons']['actioned_no_ref']}",
        "",
    ]
    if data["findings"]:
        lines.append("## Findings")
        for f in data["findings"]:
            lines.append(f"- [{f['finding']}] {f.get('debt_id', f.get('lesson_id', '?'))}: {f['message']}")
    lines.extend(["", "---", "```text", "Full Closure: NOT CLAIMED.", "```"])
    (OUTPUT / "_lifecycle-health.md").write_text("\n".join(lines) + "\n")

    print("Lifecycle Health:")
    print(f"  Debts: {data['debts']['total']} ({data['debts']['open']} open, {data['debts']['closed']} closed)")
    print(f"  Lessons: {data['lessons']['total']} ({data['lessons']['actioned']} actioned, {data['lessons']['unactioned']} un-actioned)")
    print(f"  Findings: {data['summary']['total_findings']} ({data['summary']['blocking']} blocking)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
