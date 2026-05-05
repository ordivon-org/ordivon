#!/usr/bin/env python3
"""Phase COV-2: Receipt Integrity Checker with Universe Discovery.

Self-registers via @register_checker. Adding this file to scripts/ is sufficient
— the registry auto-discovers it, the manifest auto-generates, and the baseline
runner auto-includes it. No manual manifest/edit/runner edits needed.

Never calls external APIs. Never requires credentials. Read-only evidence validation.
"""

from __future__ import annotations

import re
import sys
from collections import Counter
from pathlib import Path

# Ensure src/ is importable for ordivon_verify.registry
_src = Path(__file__).resolve().parents[1] / "src"
if str(_src) not in sys.path:
    sys.path.insert(0, str(_src))

from ordivon_verify.registry import register_checker, CheckerResult

ROOT = Path(__file__).resolve().parents[1]

EXCLUSIONS_PATH = ROOT / "docs" / "governance" / "receipt-integrity-scope-exclusions.json"

DEFAULT_SCAN_PATHS = [
    ROOT / "docs" / "ai",
    ROOT / "docs" / "governance",
    ROOT / "AGENTS.md",
    ROOT / "docs" / "architecture" / "ordivon-core-pack-adapter-ontology.md",
]

RECEIPT_UNIVERSE_DIRS = [
    "docs/runtime",
    "docs/product",
    "docs/governance",
    "docs/ai",
    "docs/architecture",
]
RECEIPT_UNIVERSE_ROOT_FILES = ["AGENTS.md", "README.md"]
RECEIPT_SKIP_PATTERNS = ["docs/archive/", "docs/runtime/paper-trades/PT-0", ".tmp", "audit"]

# ── Hard-fail patterns ──────────────────────────────────────────────
HARD_FAILS: list[tuple[re.Pattern, str, re.Pattern | None]] = [
    (
        re.compile(r"Skipped Verification:\s*None", re.IGNORECASE),
        "claims 'Skipped: None' but nearby text suggests gate was not run",
        None,
    ),
    (
        re.compile(r"(?:Status:\s*\*?\*?SEALED|FULLY SEALED)", re.IGNORECASE),
        "claims SEALED but nearby text suggests incomplete verification",
        None,
    ),
    (
        re.compile(r"clean working tree", re.IGNORECASE),
        "claims 'clean working tree' — should say 'Tracked working tree clean' if untracked residue exists",
        re.compile(r"tracked working tree clean|tracked clean", re.IGNORECASE),
    ),
    (
        re.compile(r"7\/7\s+(?:baseline|hard\s+gates?)", re.IGNORECASE),
        "stale baseline count '7/7' — baseline is now 8/8 (or 10/10 after DG-6B)",
        re.compile(r"before\s+DG-5|7\/7\s*→\s*8\/8|historical", re.IGNORECASE),
    ),
    (
        re.compile(r"Ruff\s+clean", re.IGNORECASE),
        "claims 'Ruff clean' globally — should qualify with scope if pre-existing debt exists",
        re.compile(r"DG\s+\S*\s+scope\s+clean|DG\s+\S*\s+files\s+clean", re.IGNORECASE),
    ),
    (
        re.compile(r"CandidateRule\s+validated", re.IGNORECASE),
        "claims 'CandidateRule validated' — should say 'advisory' or 'supported by evidence'",
        re.compile(r"advisory|not\s+Policy|supported\s+by\s+evidence", re.IGNORECASE),
    ),
    (
        re.compile(r"(?:can_place_order|order\s+placement|order\s+status)", re.IGNORECASE),
        "work summary describes order/execution capability — boundary claim may lack paper-only evidence",
        re.compile(r"paper.only|paper\s+environment|no\s+live|NO-GO|BLOCKED", re.IGNORECASE),
    ),
]

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

RECEIPT_MARKERS = [
    r"RECEIPT",
    r"Receipt",
    r"Seal Receipt",
    r"Completion Receipt",
    r"Stage Summit",
    r"Verification Results",
    r"Boundary Confirmation",
    r"\bPhase:",
    r"\bStatus:",
    r"\bCLOSED\b",
    r"\bSEALED\b",
]
RECEIPT_MARKER_RE = re.compile("|".join(RECEIPT_MARKERS))


def _has_skip_context(text_window: str) -> bool:
    lower = text_window.lower()
    return any(w in lower for w in SKIP_CONTEXT_WORDS)


def _file_is_archived(filepath: Path) -> bool:
    sp = str(filepath)
    return any(p in sp for p in RECEIPT_SKIP_PATTERNS)


def _is_receipt_bearing(content: str) -> bool:
    return bool(RECEIPT_MARKER_RE.search(content))


def _scan_one(filepath: Path, failures: list[str], stats: Counter) -> None:
    if _file_is_archived(filepath):
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
                ctx_start = max(0, i - 5)
                ctx_end = min(len(lines), i + 5)
                ctx_text = "\n".join(lines[ctx_start:ctx_end])
                if safe_pattern and safe_pattern.search(ctx_text):
                    continue
                if pattern is HARD_FAILS[0][0] or pattern is HARD_FAILS[1][0]:
                    if _has_skip_context(ctx_text):
                        failures.append(f"{rel}:{i}: {desc}")
                        stats[f"fail_{desc[:30]}"] += 1
                    continue
                failures.append(f"{rel}:{i}: {desc}")
                stats[f"fail_{desc[:30]}"] += 1


@register_checker(
    gate_id="receipt_integrity",
    display_name="Receipt integrity",
    layer="L7B",
    hardness="hard",
    purpose="Receipt honesty and contradiction detection",
    protects_against=(
        "Skipped None+not run, SEALED+pending, clean working tree+untracked, "
        "stale baseline count, overclaim language, CandidateRule validated claim, "
        "boundary claim mismatch"
    ),
    profiles=("pr-fast", "full"),
    timeout=120,
)
def run() -> CheckerResult:
    """Run receipt integrity checks. Returns structured CheckerResult."""
    failures: list[str] = []
    stats: Counter = Counter()
    stats["scanned"] = 0
    stats["skipped_historical"] = 0

    for p in DEFAULT_SCAN_PATHS:
        if p.is_dir():
            for md_file in sorted(p.rglob("*.md")):
                _scan_one(md_file, failures, stats)
        elif p.is_file() and p.suffix == ".md":
            _scan_one(p, failures, stats)

    if failures:
        return CheckerResult(
            status="fail",
            exit_code=1,
            findings=failures,
            stats=dict(stats),
        )
    return CheckerResult(
        status="pass",
        exit_code=0,
        stats=dict(stats),
    )


if __name__ == "__main__":
    result = run()
    print(f"  Files scanned: {result.stats.get('scanned', 0)}")
    print(f"  Failures:      {len(result.findings)}")
    if result.findings:
        for f in result.findings:
            print(f"    {f}")
        print(f"\n❌ {len(result.findings)} receipt integrity violation(s).")
    else:
        print("✅ All receipt integrity checks pass.")
    sys.exit(result.exit_code)
