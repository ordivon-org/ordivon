#!/usr/bin/env python3
"""Lesson pipeline review — identify un-actioned lessons and suggest CandidateRules.

Reads lesson-ledger.jsonl, finds lessons without outcome_ref_type (not actioned),
and reports them. This activates the lesson→CandidateRule pipeline.

Usage:
    python scripts/review_lessons.py                    # Human review
    python scripts/review_lessons.py --json             # Machine-readable (CI)
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LESSON_PATH = ROOT / "docs/governance/lesson-ledger.jsonl"


def load_lessons() -> list[dict]:
    with open(LESSON_PATH) as f:
        return [json.loads(line) for line in f if line.strip()]


def review() -> tuple[list[dict], dict]:
    lessons = load_lessons()
    actioned = [l for l in lessons if l.get("outcome_ref_type")]
    unactioned = [l for l in lessons if not l.get("outcome_ref_type")]

    stats = {
        "total": len(lessons),
        "actioned": len(actioned),
        "unactioned": len(unactioned),
        "pipeline_health": "active" if len(actioned) >= len(lessons) * 0.5 else "needs_review",
    }

    suggestions = []
    for l in unactioned:
        suggestion = {
            "lesson_id": l["lesson_id"],
            "lesson_type": l.get("lesson_type", "unknown"),
            "severity": l.get("severity", "medium"),
            "summary": l["body"][:120],
            "suggested_action": (
                "Create CandidateRule"
                if l.get("lesson_type") == "rule_candidate"
                else "Create methodology update"
                if l.get("lesson_type") == "methodology_extraction"
                else "Review and classify"
            ),
        }
        suggestions.append(suggestion)

    return suggestions, stats


def main() -> int:
    as_json = "--json" in sys.argv
    suggestions, stats = review()

    if as_json:
        output = {
            "stats": stats,
            "unactioned_lessons": suggestions,
            "pipeline_status": "BLOCKED"
            if stats["pipeline_health"] == "needs_review" and stats["unactioned"] > 5
            else "READY",
        }
        print(json.dumps(output, indent=2))
        return 1 if output["pipeline_status"] == "BLOCKED" else 0

    print("Lesson Pipeline Review")
    print(f"  Total:     {stats['total']}")
    print(f"  Actioned:  {stats['actioned']}")
    print(f"  Unactioned: {stats['unactioned']}")
    print(f"  Health:    {stats['pipeline_health']}")

    if suggestions:
        print("\n  Un-actioned lessons:")
        for s in suggestions:
            tag = "⚠" if s["severity"] == "high" else "•"
            print(f"    {tag} {s['lesson_id']} [{s['lesson_type']}]")
            print(f"       {s['summary'][:100]}")
            print(f"       → {s['suggested_action']}")

    if stats["pipeline_health"] == "needs_review":
        print(f"\n  ⚠ Lesson pipeline needs review: {stats['unactioned']} un-actioned lessons.")
        print("    Run `python scripts/review_lessons.py` to review.")
        return 0  # Advisory — does not block CI

    print("\n  ✓ Lesson pipeline active.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
