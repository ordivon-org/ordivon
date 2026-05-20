#!/usr/bin/env python3
"""Validate candidate rule AOS objects."""

import json, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LESSON_PATH = ROOT / "docs/governance/lesson-ledger.jsonl"


def load_lessons() -> set:
    ids = set()
    if LESSON_PATH.exists():
        for line in open(LESSON_PATH):
            if not line.strip():
                continue
            d = json.loads(line)
            if d.get("lesson_id"):
                ids.add(d["lesson_id"])
    return ids


def validate(filepath: Path) -> tuple[bool, list[str]]:
    obj = json.loads(filepath.read_text())
    errors = []
    for f in [
        "object_id",
        "object_kind",
        "rule_id",
        "source_lesson_ref",
        "rule_body",
        "proposed_enforcement",
        "not_claimed",
    ]:
        if f not in obj or not obj[f]:
            errors.append(f"MISSING: {f}")
    if errors:
        return False, errors

    lessons = load_lessons()
    if obj["source_lesson_ref"] not in lessons:
        errors.append(f"LESSON_NOT_FOUND: {obj['source_lesson_ref']}")

    if obj.get("proposed_enforcement") == "blocking":
        errors.append("BLOCKING_REQUIRES_SHADOW_FIRST: proposed_enforcement must be advisory or shadow initially")

    nc = " ".join(obj.get("not_claimed", []))
    if "candidaterule" not in nc.lower() or "policy" not in nc.lower():
        errors.append("NOT_CLAIMED_MUST_STATE: CandidateRule is not Policy")

    return len(errors) == 0, errors


def main():
    if len(sys.argv) < 2:
        print("Usage: validate-candidate-rule.py <file.json>")
        sys.exit(1)
    ok, errors = validate(Path(sys.argv[1]))
    if ok:
        print("✓ candidate rule valid")
        sys.exit(0)
    for e in errors:
        print(f"  ✗ {e}")
    sys.exit(1)


if __name__ == "__main__":
    main()
