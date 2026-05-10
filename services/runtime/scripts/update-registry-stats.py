#!/usr/bin/env python3
"""Generate registry statistics from document-registry.jsonl.

K8s hack/update-* pattern: reads the single source of truth
(document-registry.jsonl), computes derived statistics, writes generated views.

Usage:
    python scripts/update-registry-stats.py              # Generate stats
    python scripts/update-registry-stats.py --check      # Verify no drift (CI mode)

Output:
    docs/ai/_registry-stats.md  — generated_view, not source of truth
"""

from __future__ import annotations

import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "docs/governance/document-registry.jsonl"
OUTPUT = ROOT / "docs/ai/_registry-stats.md"

HEADER = """<!-- GENERATED FILE — DO NOT EDIT -->
<!-- Source: docs/governance/document-registry.jsonl -->
<!-- Generator: scripts/update-registry-stats.py -->
<!-- Generated: {generated_at} -->
<!-- Authority: generated_view — not source_of_truth -->

# Document Registry Statistics

> **This file is auto-generated.** It is a derived view of
> `docs/governance/document-registry.jsonl`. Do not edit it directly.
> Run `uv run python scripts/update-registry-stats.py` to regenerate.
> This file is evidence, not authorization.
"""


def load_registry() -> list[dict]:
    """Load all entries from the document registry."""
    entries = []
    with open(REGISTRY) as f:
        for line in f:
            line = line.strip()
            if line:
                entries.append(json.loads(line))
    return entries


def compute_stats(entries: list[dict]) -> dict:
    """Compute statistics from registry entries."""
    total = len(entries)
    by_status = {}
    by_type = {}
    by_layer = {}
    by_authority = {}
    stale_entries = []
    now = datetime.now(timezone.utc).isoformat()[:10]

    for e in entries:
        s = e.get("status", "unknown")
        t = e.get("doc_type", "unknown")
        layer = e.get("doc_layer", "unknown")
        auth = e.get("doc_authority", e.get("authority", "unknown"))

        by_status[s] = by_status.get(s, 0) + 1
        by_type[t] = by_type.get(t, 0) + 1
        by_layer[layer] = by_layer.get(layer, 0) + 1
        by_authority[auth] = by_authority.get(auth, 0) + 1

        # Check staleness
        freshness = e.get("freshness", "")
        stale_days = e.get("stale_after_days")
        if freshness and stale_days:
            # Simple stale check — production would use actual date diff
            if freshness < now:
                stale_entries.append({
                    "doc_id": e.get("doc_id"),
                    "path": e.get("path"),
                    "freshness": freshness,
                    "stale_after_days": stale_days,
                })

    return {
        "total": total,
        "by_status": by_status,
        "by_type": by_type,
        "by_layer": by_layer,
        "by_authority": by_authority,
        "doc_type_count": len(by_type),
        "stale_count": len(stale_entries),
        "stale_entries": stale_entries,
    }


def format_stats(stats: dict) -> str:
    """Format statistics as markdown."""
    lines = []
    now = datetime.now(timezone.utc).isoformat()[:19] + "Z"

    lines.append(HEADER.format(generated_at=now))
    lines.append("")
    lines.append("## Summary")
    lines.append("")
    lines.append(f"- **Total registered documents**: {stats['total']}")
    lines.append(f"- **Document types**: {stats['doc_type_count']}")
    lines.append(f"- **Potentially stale**: {stats['stale_count']}")
    lines.append("")
    lines.append("## By Status")
    lines.append("")
    lines.append("| Status | Count |")
    lines.append("|--------|-------|")
    for s, c in sorted(stats["by_status"].items()):
        lines.append(f"| {s} | {c} |")
    lines.append("")
    lines.append("## By Document Type")
    lines.append("")
    lines.append("| Type | Count |")
    lines.append("|------|-------|")
    for t, c in sorted(stats["by_type"].items()):
        lines.append(f"| {t} | {c} |")
    lines.append("")
    lines.append("## By Layer")
    lines.append("")
    lines.append("| Layer | Count |")
    lines.append("|-------|-------|")
    for layer, c in sorted(stats["by_layer"].items()):
        lines.append(f"| {layer} | {c} |")
    lines.append("")
    lines.append("## By Authority")
    lines.append("")
    lines.append("| Authority | Count |")
    lines.append("|-----------|-------|")
    for a, c in sorted(stats["by_authority"].items()):
        lines.append(f"| {a} | {c} |")

    if stats["stale_entries"]:
        lines.append("")
        lines.append("## Potentially Stale Documents")
        lines.append("")
        for se in stats["stale_entries"][:20]:
            lines.append(f"- `{se['path']}` (freshness: {se['freshness']}, stale after {se['stale_after_days']}d)")

    lines.append("")
    return "\n".join(lines)


def main() -> int:
    check_mode = "--check" in sys.argv

    entries = load_registry()
    stats = compute_stats(entries)
    generated = format_stats(stats)

    if check_mode:
        # CI mode: compare with committed file (ignore timestamp line)
        if not OUTPUT.exists():
            print(f"ERROR: {OUTPUT} does not exist. Run scripts/update-registry-stats.py to generate it.")
            return 1

        committed = OUTPUT.read_text()

        # Strip timestamp line for stable comparison
        def _strip_ts(text: str) -> str:
            return re.sub(r"<!-- Generated: .* -->\n", "", text)

        if _strip_ts(committed) != _strip_ts(generated):
            print(f"DRIFT DETECTED: {OUTPUT} is out of date.")
            print(f"  Registry has {stats['total']} entries, {stats['doc_type_count']} types.")
            print("  Fix: uv run python scripts/update-registry-stats.py")
            return 1

        print(f"✓ Registry stats consistent: {stats['total']} entries, {stats['doc_type_count']} types")
        return 0

    # Generate mode
    OUTPUT.write_text(generated)
    print(f"Generated {OUTPUT}")
    print(f"  {stats['total']} entries, {stats['doc_type_count']} types")
    print(f"  Statuses: {dict(sorted(stats['by_status'].items()))}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
