#!/usr/bin/env python3
"""Validate debt transition AOS objects."""

import json, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEBT_PATH = ROOT / "aos/debts/aos0-entry-debts.jsonl"


def load_debt(debt_id: str) -> dict:
    if DEBT_PATH.exists():
        for line in open(DEBT_PATH):
            if not line.strip():
                continue
            d = json.loads(line)
            if d.get("debt_id") == debt_id:
                return d
    return {}


def validate(filepath: Path) -> tuple[bool, list[str]]:
    obj = json.loads(filepath.read_text())
    errors = []

    # Required fields
    for f in [
        "object_id",
        "object_kind",
        "debt_id",
        "from_status",
        "to_status",
        "evidence_refs",
        "reason",
        "not_claimed",
    ]:
        if f not in obj or not obj[f]:
            errors.append(f"MISSING: {f}")

    if errors:
        return False, errors

    # Debt must exist
    debt = load_debt(obj["debt_id"])
    if not debt:
        errors.append(f"DEBT_NOT_FOUND: {obj['debt_id']}")
        return False, errors

    # Status must match current
    current = debt.get("status", "")
    if obj["from_status"] != current:
        errors.append(f"STATUS_MISMATCH: declared from_status={obj['from_status']}, actual={current}")

    # CLOSED requires evidence
    if obj["to_status"] == "CLOSED" and len(obj.get("evidence_refs", [])) < 1:
        errors.append("CLOSE_REQUIRES_EVIDENCE")

    # not_claimed non-empty
    if len(obj.get("not_claimed", [])) == 0:
        errors.append("NOT_CLAIMED_EMPTY")

    return len(errors) == 0, errors


def main():
    if len(sys.argv) < 2:
        print("Usage: validate-debt-transition.py <file.json>")
        sys.exit(1)
    ok, errors = validate(Path(sys.argv[1]))
    if ok:
        print("✓ debt transition valid")
        sys.exit(0)
    else:
        for e in errors:
            print(f"  ✗ {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
