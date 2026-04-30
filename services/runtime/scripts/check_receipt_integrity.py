#!/usr/bin/env python3
"""Phase DG-6B: Receipt Integrity Checker.

Scans current governance and AI onboarding docs for contradictory receipt
language: skipped verification claimed as none, SEALED with pending checks,
clean working tree with untracked residue, stale baseline counts, etc.

Never calls Alpaca. Never requires API keys. Read-only evidence validation.
"""

from __future__ import annotations

import re
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

# Default scan paths — current/high-priority docs
DEFAULT_SCAN_PATHS = [
    ROOT / "docs" / "ai",
    ROOT / "docs" / "governance",
    ROOT / "AGENTS.md",
    ROOT / "docs" / "architecture" / "ordivon-core-pack-adapter-ontology.md",
]

# Files to skip (archived/historical — not scanned as hard failures)
SKIP_PATTERNS = [
    "archive/",
    "audits/",
    "paper-trades/PT-0",
    "phase-7p-b1-",
    "phase-7p-h1-",
    "phase-7p-n1-",
    "phase-7p-cr-",
]

# ── Hard-fail patterns ────────────────────────────────────────────────

# (regex, error description, safe_context_regex)
HARD_FAILS: list[tuple[re.Pattern, str, re.Pattern | None]] = [
    # 1. Skipped Verification: None + not run / skipped nearby
    (
        re.compile(r"Skipped Verification:\s*None", re.IGNORECASE),
        "claims 'Skipped: None' but nearby text suggests gate was not run",
        None,
    ),
    # 2. SEALED / FULLY SEALED + pending / not run / will verify nearby
    (
        re.compile(r"(?:Status:\s*\*?\*?SEALED|FULLY SEALED)", re.IGNORECASE),
        "claims SEALED but nearby text suggests incomplete verification",
        None,
    ),
    # 3. "clean working tree" without "tracked"
    (
        re.compile(r"clean working tree", re.IGNORECASE),
        "claims 'clean working tree' — should say 'Tracked working tree clean' if untracked residue exists",
        re.compile(r"tracked working tree clean|tracked clean", re.IGNORECASE),
    ),
    # 4. Stale baseline count: 7/7 in current docs after DG-5
    (
        re.compile(r"7\/7\s+(?:baseline|hard\s+gates?)", re.IGNORECASE),
        "stale baseline count '7/7' — baseline is now 8/8 (or 10/10 after DG-6B)",
        re.compile(r"before\s+DG-5|7\/7\s*→\s*8\/8|historical", re.IGNORECASE),
    ),
    # 5. "Ruff clean" + pre-existing / skipped / not run nearby
    (
        re.compile(r"Ruff\s+clean", re.IGNORECASE),
        "claims 'Ruff clean' globally — should qualify with scope if pre-existing debt exists",
        re.compile(
            r"DG\s+\S*\s+scope\s+clean|DG\s+\S*\s+files\s+clean|anti.pattern|forbidden|\"Ruff clean\"|Ruff clean.*don't|Ruff clean.*do not",
            re.IGNORECASE,
        ),
    ),
    # 6. "CandidateRule validated" without safe qualifier
    (
        re.compile(r"CandidateRule\s+validated", re.IGNORECASE),
        "claims 'CandidateRule validated' — should say 'advisory' or 'supported by evidence'",
        re.compile(r"advisory|not\s+Policy|supported\s+by\s+evidence|observed\s+effective", re.IGNORECASE),
    ),
]

# Context words that make the surrounding text look like a skip/not-run
SKIP_CONTEXT_WORDS = [
    "not run",
    "not separately executed",
    "skipped",
    "omitted",
    "will verify after commit",
    "pending verification",
    "not yet run",
    "addendum required",
    "pending",
]


def _has_skip_context(text_window: str) -> bool:
    """Check if nearby text suggests verification was skipped."""
    lower = text_window.lower()
    return any(w in lower for w in SKIP_CONTEXT_WORDS)


def _file_should_skip(filepath: Path) -> bool:
    """Check if this file is historical/archived and should be excluded."""
    sp = str(filepath)
    return any(p in sp for p in SKIP_PATTERNS)


def scan_files(paths: list[Path]) -> tuple[list[str], Counter]:
    """Scan files, return (failures, stats_counter)."""
    failures: list[str] = []
    stats: Counter = Counter()
    stats["scanned"] = 0
    stats["skipped_historical"] = 0

    for p in paths:
        if p.is_dir():
            for md_file in sorted(p.rglob("*.md")):
                _scan_one(md_file, failures, stats)
        elif p.is_file() and p.suffix == ".md":
            _scan_one(p, failures, stats)

    return failures, stats


def _scan_one(filepath: Path, failures: list[str], stats: Counter) -> None:
    if _file_should_skip(filepath):
        stats["skipped_historical"] += 1
        return

    stats["scanned"] += 1
    try:
        content = filepath.read_text()
    except Exception:
        return
    lines = content.split("\n")
    try:
        rel = str(filepath.relative_to(ROOT))
    except ValueError:
        rel = str(filepath)

    for pattern, desc, safe_pattern in HARD_FAILS:
        for i, line in enumerate(lines, 1):
            if pattern.search(line):
                # Check safe context
                ctx_start = max(0, i - 5)
                ctx_end = min(len(lines), i + 5)
                ctx_text = "\n".join(lines[ctx_start:ctx_end])

                if safe_pattern and safe_pattern.search(ctx_text):
                    continue

                # For pattern 1 and 2: also check skip context words
                if pattern is HARD_FAILS[0][0] or pattern is HARD_FAILS[1][0]:
                    if _has_skip_context(ctx_text):
                        failures.append(f"{rel}:{i}: {desc}")
                        stats[f"fail_{desc[:30]}"] += 1
                    continue

                # For other patterns: fail directly
                failures.append(f"{rel}:{i}: {desc}")
                stats[f"fail_{desc[:30]}"] += 1


def print_summary(failures: list[str], stats: Counter) -> None:
    print("=" * 60)
    print("RECEIPT INTEGRITY CHECKER SUMMARY")
    print("=" * 60)
    print(f"  Files scanned:             {stats['scanned']}")
    print(f"  Skipped (historical):      {stats['skipped_historical']}")
    print(f"  Hard failures:             {len(failures)}")
    if failures:
        for f in failures:
            print(f"    {f}")


def main() -> int:
    if len(sys.argv) > 1:
        paths = [Path(p) for p in sys.argv[1:]]
    else:
        paths = DEFAULT_SCAN_PATHS

    failures, stats = scan_files(paths)

    if failures:
        print_summary(failures, stats)
        print(f"\n❌ {len(failures)} receipt integrity violation(s).\n")
        return 1

    print_summary(failures, stats)
    print("\n✅ All receipt integrity checks pass.\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
