#!/usr/bin/env python3
"""Overclaim Detection — flag governance claims that have no verifiable truth condition.

Ordivon prevents the 'overclaim' error class by restricting status claims
to a controlled vocabulary. Words like "complete", "honest", "all done" have
no machine-verifiable condition and are FORBIDDEN in governance contexts.

This checker scans receipts, stage summits, and methodology documents for
forbidden claim words and flags them. It enforces the Epistemic Invariants:
  Evidence ≠ Claim
  Summary ≠ Current Truth

Usage:
    python scripts/detect_overclaim.py                    # Scan docs/
    python scripts/detect_overclaim.py --json             # CI mode
    python scripts/detect_overclaim.py <file>             # Single file
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VOCAB_PATH = ROOT / "docs/governance/schemas/claim-vocabulary.json"

# ── Scan targets: documents where governance claims are made ──────────
SCAN_PATHS = [
    "docs/product/",
    "docs/governance/ordivon-methodology-core.md",
    "docs/ai/current-phase-boundaries.md",
    "docs/ai/current-system-map.md",
]

# Exclusions: documents that are NOT governance claims
EXCLUDE_PREFIXES = [
    "docs/governance/ordivon-methodology-core.md",  # Defines the vocabulary, quotes forbidden words as examples
    "docs/governance/schemas/claim-vocabulary.json",  # The vocabulary itself
    "docs/product/aegisos",
    "docs/product/task-template",
    "docs/product/ai-financial",
]


def load_vocabulary() -> tuple[list[str], list[str]]:
    with open(VOCAB_PATH) as f:
        vocab = json.load(f)
    forbidden = vocab["forbidden_words"]["words"]
    exceptions = vocab["forbidden_words"]["exceptions"]["patterns"]
    return forbidden, exceptions


def scan_file(filepath: Path, forbidden: list[str]) -> list[dict]:
    """Scan a single file for overclaim patterns."""
    findings = []
    try:
        lines = filepath.read_text(encoding="utf-8", errors="replace").split("\n")
    except Exception:
        return findings

    for i, line in enumerate(lines, 1):
        line_lower = line.lower()
        for word in forbidden:
            # Use word boundary to avoid matching 'completeness' when checking 'complete'
            pattern = r'\b' + re.escape(word) + r'\b'
            if re.search(pattern, line, re.IGNORECASE):
                # Skip if it's a code block or technical reference
                if line.strip().startswith("```") or line.strip().startswith("$"):
                    continue
                # Skip if it's in the controlled vocabulary itself
                if "forbidden_words" in line or "claim-vocabulary" in str(filepath):
                    continue

                findings.append({
                    "rule": "OC-1",
                    "severity": "warning",
                    "file": str(filepath.resolve().relative_to(ROOT)),
                    "line": i,
                    "word": word,
                    "context": line.strip()[:120],
                    "message": f"'{word}' has no verifiable truth condition in Ordivon. Use READY, BLOCKED, OPEN, CLOSED, VERIFIED instead.",
                })
                break  # One finding per line

    return findings


def main() -> int:
    as_json = "--json" in sys.argv
    forbidden, _ = load_vocabulary()

    # Determine what to scan
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    if args:
        files = [(ROOT / a).resolve() if not Path(a).is_absolute() else Path(a) for a in args]
    else:
        files = []
        for sp in SCAN_PATHS:
            p = ROOT / sp
            if p.is_file():
                files.append(p)
            elif p.is_dir():
                for f in p.rglob("*.md"):
                    rel = str(f.relative_to(ROOT))
                    if not any(rel.startswith(ep) for ep in EXCLUDE_PREFIXES):
                        files.append(f)

    # Scan
    all_findings = []
    for fp in files:
        if not fp.exists():
            continue
        all_findings.extend(scan_file(fp, forbidden))

    stats = {
        "files_scanned": len(files),
        "findings": len(all_findings),
        "forbidden_words_used": len(set(f["word"] for f in all_findings)),
    }

    if as_json:
        output = {
            "status": "WARNING" if all_findings else "READY",
            "findings": all_findings,
            "stats": stats,
        }
        print(json.dumps(output, indent=2, ensure_ascii=False))
        return 0  # Advisory only — does not block CI (yet)

    print(f"Overclaim Detection")
    print(f"  Files: {stats['files_scanned']}")
    print(f"  Findings: {stats['findings']}")

    if all_findings:
        print(f"\n  Forbidden claim words found:")
        for f in all_findings[:20]:
            print(f"    [{f['rule']}] {f['file']}:{f['line']} — '{f['word']}'")
            print(f"      {f['context'][:100]}")

    return 0  # Advisory


if __name__ == "__main__":
    sys.exit(main())
