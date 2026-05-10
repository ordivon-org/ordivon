#!/usr/bin/env python3
"""Add content hashes to JSONL ledger entries (RT-09 fix).

Computes a SHA256 hash of each entry's governable fields and adds a
`content_hash` field. This provides tamper-EVIDENCE: modifying an entry's
status, description, or resolution will break the hash.

Usage:
    python scripts/hash_ledger.py <ledger.jsonl>        # Add hashes
    python scripts/hash_ledger.py --verify <ledger.jsonl>  # Verify (CI mode)
"""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

# Fields included in the content hash (governable fields).
# Excludes: metadata fields that change on re-generation (created, etc.)
HASH_FIELDS = [
    "debt_id",
    "lesson_id",
    "status",
    "classification",
    "description",
    "package",
    "advisory",
    "reason",
    "detected_version",
    "mitigation",
    "resolution",
    "body",
    "severity",
    "tags",
    "source_checker",
    "source_phase",
    "evidence_count",
]

FIXED_FIELDS = {
    "created",
    "review_trigger",
    "review_schedule",
    "resolution_criteria",
    "ci_ignore",
    "ci_config",
    "remediation_plan",
    "outcome_ref_type",
    "outcome_ref_id",
    "review_id",
    "recommendation_id",
    "review_script",
    "review_command",
}


def hash_entry(entry: dict) -> str:
    """Compute content hash from governable fields."""
    data = {}
    for k in HASH_FIELDS:
        if k in entry:
            val = entry[k]
            if isinstance(val, list):
                val = json.dumps(val, sort_keys=True)
            data[k] = str(val)
    canonical = json.dumps(data, sort_keys=True, ensure_ascii=False)
    return hashlib.sha256(canonical.encode()).hexdigest()[:16]


def process_ledger(path: Path, verify_only: bool = False) -> tuple[int, int]:
    """Process a ledger file: add hashes or verify existing ones."""
    entries = []
    with open(path) as f:
        for line in f:
            if line.strip():
                entries.append(json.loads(line))

    ok = 0
    fail = 0

    for e in entries:
        computed = hash_entry(e)
        existing = e.get("content_hash", "")

        if verify_only:
            if existing and existing == computed:
                ok += 1
            elif existing:
                eid = e.get("debt_id") or e.get("lesson_id") or "unknown"
                print(f"  HASH MISMATCH: {eid} (stored={existing[:8]}... computed={computed[:8]}...)")
                fail += 1
            else:
                # No hash yet — first run, not a failure
                ok += 1
        else:
            e["content_hash"] = computed
            ok += 1

    if not verify_only:
        with open(path, "w") as f:
            for e in entries:
                f.write(json.dumps(e, ensure_ascii=False) + "\n")

    return ok, fail


def main() -> int:
    if len(sys.argv) < 2:
        print("Usage: python scripts/hash_ledger.py <ledger.jsonl>")
        print("       python scripts/hash_ledger.py --verify <ledger.jsonl>")
        return 1

    verify_only = "--verify" in sys.argv
    args = [a for a in sys.argv[1:] if not a.startswith("--")]

    if not args:
        print("ERROR: no ledger file specified")
        return 1

    total_ok = 0
    total_fail = 0

    for arg in args:
        path = Path(arg)
        if not path.exists():
            print(f"ERROR: {path} not found")
            return 1

        ok, fail = process_ledger(path, verify_only)
        total_ok += ok
        total_fail += fail

        if verify_only:
            if fail > 0:
                print(f"✗ {path.name}: {ok} ok, {fail} HASH MISMATCH")
            else:
                print(f"✓ {path.name}: {ok} entries verified")
        else:
            print(f"✓ {path.name}: {ok} entries hashed")

    return 1 if total_fail > 0 else 0


if __name__ == "__main__":
    sys.exit(main())
