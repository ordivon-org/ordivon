#!/usr/bin/env python3
"""Phase DG-6B: Verification Debt Ledger Checker.

Reads docs/governance/verification-debt-ledger.jsonl and verifies debt invariants.
Never calls Alpaca. Never requires API keys. Read-only evidence validation.
"""

from __future__ import annotations

import json
import os
import sys
from collections import Counter
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LEDGER_PATH = ROOT / "docs" / "governance" / "verification-debt-ledger.jsonl"

_REF_DATE = os.environ.get("REFERENCE_DATE", "")
REFERENCE_DATE = date.fromisoformat(_REF_DATE) if _REF_DATE else date.today()

VALID_CATEGORIES = {
    "skipped_verification",
    "pre_existing_tooling_debt",
    "untracked_residue",
    "baseline_gate_gap",
    "receipt_integrity_gap",
    "checker_degradation",
    "stale_baseline_count",
    "semantic_overclaim",
}

VALID_SEVERITIES = {"low", "medium", "high", "blocking"}

VALID_STATUSES = {"open", "closed", "accepted_until", "superseded"}

REQUIRED_FIELDS = {
    "debt_id",
    "opened_phase",
    "category",
    "scope",
    "description",
    "risk",
    "severity",
    "introduced_by_current_phase",
    "owner",
    "follow_up",
    "expires_before_phase",
    "status",
    "opened_at",
    "closed_at",
    "evidence",
    "notes",
}


def load_ledger(path: Path) -> list[dict]:
    entries = []
    with open(path) as f:
        for i, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            try:
                entries.append(json.loads(line))
            except json.JSONDecodeError as e:
                print(f"ERROR line {i}: invalid JSON: {e}")
                sys.exit(1)
    return entries


def check_invariants(entries: list[dict]) -> list[str]:
    errors: list[str] = []
    ids: set[str] = set()

    for e in entries:
        did = e.get("debt_id", "<missing>")

        missing = REQUIRED_FIELDS - set(e.keys())
        if missing:
            errors.append(f"{did}: missing required fields: {missing}")

        if did in ids:
            errors.append(f"{did}: duplicate debt_id")
        ids.add(did)

        cat = e.get("category", "")
        if cat not in VALID_CATEGORIES:
            errors.append(f"{did}: invalid category '{cat}'")

        sev = e.get("severity", "")
        if sev not in VALID_SEVERITIES:
            errors.append(f"{did}: invalid severity '{sev}'")

        status = e.get("status", "")
        if status not in VALID_STATUSES:
            errors.append(f"{did}: invalid status '{status}'")

        # Open/accepted_until debt must have owner, follow_up, expiry, evidence
        if status in ("open", "accepted_until"):
            for field in ("owner", "follow_up", "expires_before_phase", "evidence"):
                if not e.get(field):
                    errors.append(f"{did}: {status} debt missing '{field}'")

        # Expiry check: if expires_before_phase is an ISO date, check it
        expiry = e.get("expires_before_phase", "")
        if status in ("open", "accepted_until") and expiry:
            try:
                expiry_date = date.fromisoformat(expiry)
            except (ValueError, TypeError):
                pass  # phase name, not date — skip date check
            else:
                if REFERENCE_DATE > expiry_date:
                    errors.append(f"{did}: overdue — expires_before_phase={expiry}, reference date={REFERENCE_DATE}")

        # Closed debt must have closed_at
        if status == "closed" and not e.get("closed_at"):
            errors.append(f"{did}: closed debt missing closed_at")

    return errors


def print_summary(entries: list[dict]) -> None:
    status_counter = Counter(e.get("status", "?") for e in entries)
    sev_counter = Counter(e.get("severity", "?") for e in entries)

    print("=" * 60)
    print("VERIFICATION DEBT LEDGER SUMMARY")
    print("=" * 60)
    print(f"  Total debts:               {len(entries)}")
    print(f"  Open:                      {status_counter.get('open', 0)}")
    print(f"  Closed:                    {status_counter.get('closed', 0)}")
    print(f"  Accepted until:            {status_counter.get('accepted_until', 0)}")
    print(f"  Superseded:                {status_counter.get('superseded', 0)}")
    overdue = sum(
        1
        for e in entries
        if e.get("status") in ("open", "accepted_until")
        and e.get("expires_before_phase", "")
        and _is_overdue(e.get("expires_before_phase", ""))
    )
    print(f"  Overdue:                   {overdue}")
    high_block = sev_counter.get("high", 0) + sev_counter.get("blocking", 0)
    print(f"  High + blocking:           {high_block}")


def _is_overdue(expiry: str) -> bool:
    try:
        return REFERENCE_DATE > date.fromisoformat(expiry)
    except (ValueError, TypeError):
        return False


def main() -> int:
    path = Path(sys.argv[1]) if len(sys.argv) > 1 else LEDGER_PATH
    if not path.exists():
        print(f"ERROR: ledger not found at {path}")
        return 1

    entries = load_ledger(path)
    errors = check_invariants(entries)

    if errors:
        print(f"\n❌ {len(errors)} INVARIANT VIOLATION(S):\n")
        for err in errors:
            print(f"  - {err}")
        print()
        return 1

    print_summary(entries)
    print("\n✅ All verification debt invariants pass.\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
