#!/usr/bin/env python3
"""Validate gate promotion AOS objects."""

import json, sys
from pathlib import Path


def validate(filepath: Path) -> tuple[bool, list[str]]:
    obj = json.loads(filepath.read_text())
    errors = []
    for f in [
        "object_id",
        "object_kind",
        "promotion_id",
        "target_class",
        "gate_assessment_refs",
        "authority_boundary",
        "not_claimed",
    ]:
        if f not in obj or not obj[f]:
            errors.append(f"MISSING: {f}")
    if errors:
        return False, errors
    if obj["target_class"] not in ("P1", "P2", "P3", "P4", "P5"):
        errors.append(f"INVALID_TARGET_CLASS: {obj['target_class']}")
    if len(obj.get("not_claimed", [])) == 0:
        errors.append("NOT_CLAIMED_EMPTY")
    nc = " ".join(obj["not_claimed"])
    if "promotion" not in nc.lower():
        errors.append("NOT_CLAIMED_MUST_STATE: promotion boundaries")
    return len(errors) == 0, errors


def main():
    if len(sys.argv) < 2:
        print("Usage: validate-gate-promotion.py <file>")
        sys.exit(1)
    ok, errors = validate(Path(sys.argv[1]))
    if ok:
        print("✓ gate promotion valid")
        sys.exit(0)
    for e in errors:
        print(f"  ✗ {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
