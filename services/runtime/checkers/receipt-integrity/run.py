"""Receipt Integrity Checker — detects overclaims in phase closure documents.

Entry point: `def run() -> CheckerResult`

Scans governance/runtime/product docs for contradictory receipt language.
Auto-discovered by the checker registry via checkers/ directory structure.
"""

from __future__ import annotations

import re
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


# ── Hard-fail patterns ──────────────────────────────────────────────

HARD_FAILS: list[tuple[re.Pattern, str, re.Pattern | None]] = [
    (re.compile(r"Skipped Verification:\s*None", re.IGNORECASE),
     "claims 'Skipped: None' but nearby text suggests gate was not run", None),
    (re.compile(r"(?:Status:\s*\*?\*?SEALED|FULLY SEALED)", re.IGNORECASE),
     "claims SEALED but nearby text suggests incomplete verification", None),
    (re.compile(r"clean working tree", re.IGNORECASE),
     "claims 'clean working tree' — should say 'Tracked working tree clean' if untracked residue exists",
     re.compile(r"tracked working tree clean|tracked clean", re.IGNORECASE)),
    (re.compile(r"7\/7\s+(?:baseline|hard\s+gates?)", re.IGNORECASE),
     "stale baseline count '7/7' — baseline is now larger",
     re.compile(r"before\s+DG-5|7\/7\s*→\s*8\/8|historical", re.IGNORECASE)),
    (re.compile(r"Ruff\s+clean", re.IGNORECASE),
     "claims 'Ruff clean' globally — should qualify with scope if pre-existing debt exists",
     re.compile(r"DG\s+scope\s+clean|DG\s+files\s+clean|forbidden|anti.pattern|\"Ruff clean\"|Ruff clean.*don't|Ruff clean.*do not", re.IGNORECASE)),
    (re.compile(r"CandidateRule\s+validated", re.IGNORECASE),
     "claims 'CandidateRule validated' — should say 'advisory' or 'supported by evidence'",
     re.compile(r"advisory|not\s+Policy|supported\s+by\s+evidence", re.IGNORECASE)),
    (re.compile(r"(?:can_place_order|order\s+placement)", re.IGNORECASE),
     "work summary describes order capability — boundary claim may lack paper-only evidence",
     re.compile(r"paper.only|no\s+live|NO-GO|BLOCKED|not\s+execution", re.IGNORECASE)),
]

SKIP_CONTEXT_WORDS = [
    "not run", "not separately executed", "skipped", "omitted",
    "will verify after commit", "pending verification", "not yet run",
    "addendum required", "pending",
]

DEFAULT_SCAN_PATHS = [
    ROOT / "docs" / "ai",
    ROOT / "docs" / "governance",
    ROOT / "AGENTS.md",
    ROOT / "docs" / "architecture" / "ordivon-core-pack-adapter-ontology.md",
]


def _has_skip_context(text_window: str) -> bool:
    lower = text_window.lower()
    return any(w in lower for w in SKIP_CONTEXT_WORDS)


def _scan_one(filepath: Path, failures: list[str], stats: Counter) -> None:
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


def run() -> "CheckerResult":
    """Run receipt integrity checks. Returns structured result.

    This function signature is the auto-discovery contract —
    the checker registry finds and calls `run()` on each checker.
    """
    from ordivon_verify.checker_registry import CheckerResult

    failures: list[str] = []
    stats: Counter = Counter()
    stats["scanned"] = 0

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
    import sys
    result = run()
    print(f"  Files scanned: {result.stats.get('scanned', 0)}")
    print(f"  Failures:      {len(result.findings)}")
    for f in result.findings:
        print(f"    {f}")
    sys.exit(result.exit_code)
