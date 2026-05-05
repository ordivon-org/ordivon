#!/usr/bin/env python3
# DEPRECATED: Migrated to checkers/ ecosystem. See checkers/*/run.py.
# Kept for historical reference. Use: python scripts/run_baseline.py
"""Phase COV-2: Verification Debt Ledger Checker with Candidate Discovery.

Reads docs/governance/verification-debt-ledger.jsonl and verifies debt invariants.
COV-2 adds conservative debt-candidate discovery across runtime/product/governance
docs to detect likely unregistered debt.

Never calls Alpaca. Never requires API keys. Read-only evidence validation.
"""

from __future__ import annotations

import json
import os
import re
import sys
from collections import Counter
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LEDGER_PATH = ROOT / "docs" / "governance" / "verification-debt-ledger.jsonl"
EXCLUSIONS_PATH = ROOT / "docs" / "governance" / "verification-debt-discovery-exclusions.json"

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

# ── Debt Candidate Discovery ─────────────────────────────────────────

DISCOVERY_DIRS = [
    "docs/runtime",
    "docs/product",
    "docs/governance",
    "docs/architecture",
]

DISCOVERY_ROOT_FILES = [
    "AGENTS.md",
    "README.md",
]

# Patterns that suggest unresolved debt when found in a non-historical context
DEBT_SIGNAL_PATTERNS: list[tuple[re.Pattern, str]] = [
    (re.compile(r"\bBLOCKED\b", re.IGNORECASE), "BLOCKED"),
    (re.compile(r"\bunresolved\b", re.IGNORECASE), "unresolved"),
    (re.compile(r"\bopen\s+blocker\b", re.IGNORECASE), "open blocker"),
    (re.compile(r"\bskipped\s+verification\b", re.IGNORECASE), "skipped verification"),
    (re.compile(r"\bnot\s+run\b", re.IGNORECASE), "not run"),
    (re.compile(r"\bworkaround\b", re.IGNORECASE), "workaround"),
    (re.compile(r"\bpending verification\b", re.IGNORECASE), "pending verification"),
    (re.compile(r"\bknown\s+gap\b", re.IGNORECASE), "known gap"),
    (re.compile(r"\bdegraded\b", re.IGNORECASE), "degraded"),
]

# Headers that signal a debt/issue section
DEBT_SECTION_HEADERS = [
    re.compile(r"^#+\s*(?:Blocked|Remaining\s+Work|Open\s+Issues|Known\s+Gaps|Debt|Outstanding)", re.IGNORECASE),
]

# Patterns that mark a context as historical/closed
CLOSED_CONTEXT_PATTERNS = [
    re.compile(r"\bCLOSED\b"),
    re.compile(r"\bSEALED\b"),
    re.compile(r"\bclosed_by\b"),
    re.compile(r"\bresolved\b", re.IGNORECASE),
    re.compile(r"\bfixed\b", re.IGNORECASE),
    re.compile(r"VD-\d{4}-\d{2}-\d{2}-\d{3}"),  # References a registered VD-ID
    re.compile(r"\bDependabot\b"),  # Dependabot issues are externally tracked
    re.compile(r"\bpre-existing\b", re.IGNORECASE),
    re.compile(r"\bhistorical\b", re.IGNORECASE),
    re.compile(r"\bdeferred\b", re.IGNORECASE),
]

# Files/dirs to skip in discovery
DISCOVERY_SKIP = [
    "docs/archive",
    "docs/runtime/paper-trades/PT-0",
    ".tmp",
    "audit",
]


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

        if status in ("open", "accepted_until"):
            for field in ("owner", "follow_up", "expires_before_phase", "evidence"):
                if not e.get(field):
                    errors.append(f"{did}: {status} debt missing '{field}'")

        expiry = e.get("expires_before_phase", "")
        if status in ("open", "accepted_until") and expiry:
            try:
                expiry_date = date.fromisoformat(expiry)
            except (ValueError, TypeError):
                pass
            else:
                if REFERENCE_DATE > expiry_date:
                    errors.append(f"{did}: overdue — expires_before_phase={expiry}, reference date={REFERENCE_DATE}")

        if status == "closed" and not e.get("closed_at"):
            errors.append(f"{did}: closed debt missing closed_at")

    return errors


def _is_overdue(expiry: str) -> bool:
    try:
        return REFERENCE_DATE > date.fromisoformat(expiry)
    except (ValueError, TypeError):
        return False


def _should_skip_discovery_path(rel: str) -> bool:
    return any(p in rel for p in DISCOVERY_SKIP)


def _has_closed_context(text_window: str) -> bool:
    return any(p.search(text_window) for p in CLOSED_CONTEXT_PATTERNS)


def load_discovery_exclusions() -> dict[str, dict]:
    """Load explicit exclusion entries keyed by file:lineno."""
    if not EXCLUSIONS_PATH.exists():
        return {}
    with open(EXCLUSIONS_PATH) as f:
        data = json.load(f)
    result = {}
    for entry in data.get("exclusions", []):
        key = f"{entry['file']}:{entry.get('line', '*')}"
        result[key] = entry
    return result


def discover_debt_candidates(
    ledger_entries: list[dict],
) -> tuple[list[dict], list[dict], list[dict]]:
    """Scan docs for likely unregistered debt.

    Returns (candidates, excluded, unmanaged).
    """
    registered_ids = {e.get("debt_id", "") for e in ledger_entries}
    exclusions = load_discovery_exclusions()
    candidates: list[dict] = []
    excluded: list[dict] = []
    unmanaged: list[dict] = []

    # Collect files
    files: list[Path] = []
    for d in DISCOVERY_DIRS:
        dp = ROOT / d
        if dp.is_dir():
            files.extend(sorted(dp.rglob("*.md")))
    for rf in DISCOVERY_ROOT_FILES:
        fp = ROOT / rf
        if fp.is_file():
            files.append(fp)

    for fp in files:
        try:
            rel = str(fp.relative_to(ROOT))
        except ValueError:
            rel = str(fp)
        if _should_skip_discovery_path(rel):
            continue

        try:
            content = fp.read_text()
        except Exception:
            continue
        lines = content.split("\n")

        for i, line in enumerate(lines, 1):
            # Check if we're in a debt section
            is_debt_section = any(h.search(line) for h in DEBT_SECTION_HEADERS)

            for pattern, label in DEBT_SIGNAL_PATTERNS:
                if not pattern.search(line):
                    continue

                # Check if context is clearly closed/historical
                ctx_start = max(0, i - 3)
                ctx_end = min(len(lines), i + 3)
                ctx_text = "\n".join(lines[ctx_start:ctx_end])

                if _has_closed_context(ctx_text):
                    continue

                # Check if references a registered VD-ID
                vd_ref = re.search(r"VD-\d{4}-\d{2}-\d{2}-\d{3}", ctx_text)
                if vd_ref and vd_ref.group() in registered_ids:
                    continue

                # Check explicit exclusion
                excl_key = f"{rel}:{i}"
                excl_wild = f"{rel}:*"
                if excl_key in exclusions:
                    excluded.append({
                        "file": rel,
                        "line": i,
                        "signal": label,
                        "exclusion": exclusions[excl_key].get("reason", "unknown"),
                    })
                    continue
                if excl_wild in exclusions:
                    excluded.append({
                        "file": rel,
                        "line": i,
                        "signal": label,
                        "exclusion": exclusions[excl_wild].get("reason", "unknown"),
                    })
                    continue

                # Flag as candidate
                # But only if in a debt section, or the signal is specific enough
                if is_debt_section or label in ("BLOCKED", "skipped verification", "known gap", "pending verification"):
                    candidates.append({
                        "file": rel,
                        "line": i,
                        "signal": label,
                        "context": ctx_text[:200],
                    })

    # Classify: candidates without VD reference are unmanaged
    unmanaged = [c for c in candidates]

    return candidates, excluded, unmanaged


def print_summary(entries: list[dict]) -> None:
    status_counter = Counter(e.get("status", "?") for e in entries)
    sev_counter = Counter(e.get("severity", "?") for e in entries)

    print("=" * 60)
    print("VERIFICATION DEBT LEDGER SUMMARY")
    print("=" * 60)
    print(f"  Ledger entries:            {len(entries)}")
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


def print_discovery_summary(
    candidates: list[dict],
    excluded: list[dict],
    unmanaged: list[dict],
) -> None:
    print()
    print("=" * 60)
    print("DEBT CANDIDATE DISCOVERY")
    print("=" * 60)
    print(f"  Discovered candidates:     {len(candidates)}")
    print(f"  Excluded candidates:       {len(excluded)}")
    print(f"  Unmanaged candidates:      {len(unmanaged)}")
    if unmanaged:
        print("\n  Unmanaged debt-like signals found (warning):\n")
        for c in unmanaged:
            print(f"    {c['file']}:{c['line']}  [{c['signal']}]")
            print(f"      {c['context'][:120]}")
        print("\n  NOTE: These are conservative signals — may be false positives.")
        print("  Register as verification debt if they represent unresolved issues.")
        print("  Add explicit exclusions if they are benign.")
    if excluded:
        print(f"\n  {len(excluded)} excluded with reason.")


def main() -> int:
    args = [a for a in sys.argv[1:] if a != "--warn-only"]
    path = Path(args[0]) if args else LEDGER_PATH
    warn_only = "--warn-only" in sys.argv[1:]

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

    # Debt candidate discovery (COV-2)
    candidates, excluded, unmanaged = discover_debt_candidates(entries)
    print_discovery_summary(candidates, excluded, unmanaged)

    if unmanaged and not warn_only:
        print("\n❌ Unmanaged debt candidates found (warning).\n")
        return 0  # Warning only — does not block

    print("\n✅ All verification debt invariants pass.\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
