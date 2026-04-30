#!/usr/bin/env python3
"""Phase DG-6: Document Wiki Generator.

Reads docs/governance/document-registry.jsonl and generates
docs/governance/wiki-index.md — a registry-derived navigation surface.
Wiki is navigation, NOT source of truth.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REGISTRY_PATH = ROOT / "docs" / "governance" / "document-registry.jsonl"
WIKI_OUTPUT = ROOT / "docs" / "governance" / "wiki-index.md"

AUTHORITY_ORDER = {
    "source_of_truth": 0,
    "current_status": 1,
    "supporting_evidence": 2,
    "historical_record": 3,
    "proposal": 4,
    "example": 5,
    "archive": 6,
}


def load_registry(path: Path) -> list[dict]:
    """Load registry entries, exit non-zero on invalid JSON."""
    entries = []
    with open(path) as f:
        for i, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            try:
                entries.append(json.loads(line))
            except json.JSONDecodeError as e:
                print(f"ERROR line {i}: invalid JSON: {e}", file=sys.stderr)
                sys.exit(1)
    return entries


def sort_entries(entries: list[dict]) -> list[dict]:
    """Sort by ai_read_priority, then authority rank, then doc_type, then title."""
    return sorted(
        entries,
        key=lambda e: (
            e.get("ai_read_priority", 99) or 99,
            AUTHORITY_ORDER.get(e.get("authority", ""), 99),
            e.get("doc_type", ""),
            e.get("title", ""),
        ),
    )


def _row(e: dict) -> str:
    """Render a table row for a registry entry."""
    title = e.get("title", "?")
    path = e.get("path", "")
    # Link relative from docs/governance/ to repo root
    link = f"../../{path}" if not path.startswith("docs/") else f"../{path[5:]}"
    return (
        f"| [{title}]({link}) "
        f"| `{path}` "
        f"| {e.get('doc_type', '?')} "
        f"| {e.get('status', '?')} "
        f"| {e.get('authority', '?')} "
        f"| L{e.get('ai_read_priority', '?')} "
        f"| {e.get('freshness', '?')} |"
    )


def _section_header(title: str) -> str:
    return f"\n## {title}\n\n| Document | Path | Type | Status | Authority | AI Prio | Freshness |\n|----------|------|------|--------|-----------|---------|-----------|"


def _filter(entries: list[dict], **kwargs) -> list[dict]:
    result = []
    for e in entries:
        match = True
        for k, v in kwargs.items():
            if isinstance(v, (list, set, tuple)):
                if e.get(k) not in v:
                    match = False
            else:
                if e.get(k) != v:
                    match = False
        if match:
            result.append(e)
    return result


def generate_wiki(entries: list[dict]) -> str:
    """Generate wiki-index.md content from registry entries."""
    sorted_entries = sort_entries(entries)

    lines: list[str] = []

    # ── Header ────────────────────────────────────────────────────────
    lines.append("# Wiki Navigation Prototype")
    lines.append("")
    lines.append("> **Generated from `document-registry.jsonl`** — do not edit by hand.")
    lines.append("> **Navigation layer only — not source of truth.**")
    lines.append("> Registry/checker validate consistency; wiki does not authorize action.")
    lines.append("")
    lines.append(f"**Total registered docs**: {len(entries)}")
    lines.append(f"**Generated**: 2026-04-30 (DG-6)")
    lines.append("")

    # ── 1. Current Truth ──────────────────────────────────────────────
    lines.append(_section_header("1. Current Truth"))
    truth_docs = _filter(
        sorted_entries, authority=["source_of_truth", "current_status"]
    )
    for e in truth_docs:
        lines.append(_row(e))
    lines.append("")

    # ── 2. AI Onboarding ──────────────────────────────────────────────
    lines.append(_section_header("2. AI Onboarding"))
    ai_types = {"root_context", "ai_onboarding", "phase_boundary"}
    ai_docs = [e for e in sorted_entries if e.get("doc_type") in ai_types]
    for e in ai_docs:
        lines.append(_row(e))
    lines.append("")
    lines.append("**AI read path**: AGENTS.md (L0) → docs/ai/ (L1) → governance pack (L2) → evidence (L3) → archive (L4)")
    lines.append("")

    # ── 3. Governance Pack ────────────────────────────────────────────
    lines.append(_section_header("3. Governance Pack"))
    gov_docs = _filter(sorted_entries, doc_type="governance_pack")
    for e in gov_docs:
        lines.append(_row(e))
    lines.append("")

    # ── 4. Evidence / Ledger ──────────────────────────────────────────
    lines.append(_section_header("4. Evidence / Ledger"))
    ev_types = {"ledger", "schema", "stage_summit", "runtime"}
    ev_docs = [
        e for e in sorted_entries
        if e.get("doc_type") in ev_types or e.get("authority") == "supporting_evidence"
    ]
    seen = set()
    for e in ev_docs:
        did = e.get("doc_id")
        if did not in seen:
            seen.add(did)
            lines.append(_row(e))
    lines.append("")
    lines.append("> ⚠ **Evidence only — does not authorize execution.**")
    lines.append("> JSONL ledger is machine-readable evidence, not execution authority.")
    lines.append("")

    # ── 5. Phase & Readiness ──────────────────────────────────────────
    lines.append("## 5. Phase & Readiness")
    lines.append("")
    lines.append("| Phase | Status |")
    lines.append("|-------|--------|")
    lines.append("| Phase 1–5 | COMPLETE |")
    lines.append("| Phase 6 | COMPLETE |")
    lines.append("| Phase 7P | CLOSED |")
    lines.append("| DG-1 through DG-5 | COMPLETE / ACCEPTED |")
    lines.append("| **DG-6** | **ACTIVE** (Wiki Navigation Prototype) |")
    lines.append("| **Phase 8** | **DEFERRED** (3/10 readiness) |")
    lines.append("")

    # ── 6. Deferred / Tracker ─────────────────────────────────────────
    lines.append(_section_header("6. Deferred / Tracker"))
    tracker_docs = _filter(sorted_entries, doc_type="tracker")
    for e in tracker_docs:
        lines.append(_row(e))
    lines.append("")

    # ── 7. Risk / NO-GO Reminder ──────────────────────────────────────
    lines.append("## 7. Risk / NO-GO Boundaries")
    lines.append("")
    lines.append("| Boundary | Status |")
    lines.append("|----------|--------|")
    lines.append("| Live trading | **NO-GO** (Phase 8 DEFERRED) |")
    lines.append("| Broker live write | **NO-GO** |")
    lines.append("| Auto trading | **NO-GO** (permanently disabled) |")
    lines.append("| Policy activation | **NO-GO** |")
    lines.append("| RiskEngine active enforcement | **NO-GO** |")
    lines.append("| CandidateRules | **advisory only** — NOT Policy |")
    lines.append("| JSONL ledger | **evidence only** — not execution authority |")
    lines.append("| Archive | **historical only** — not current truth |")
    lines.append("")

    # ── 8. Archive / Historical ───────────────────────────────────────
    lines.append(_section_header("8. Archive / Historical"))
    archive_docs = _filter(sorted_entries, authority="archive")
    if archive_docs:
        for e in archive_docs:
            lines.append(_row(e))
    else:
        lines.append("")
        lines.append("*No archive entries registered yet.*")
    lines.append("")

    # ── Footer ────────────────────────────────────────────────────────
    lines.append("---")
    lines.append("")
    lines.append("*Generated by `scripts/generate_document_wiki.py` from `docs/governance/document-registry.jsonl`.*")
    lines.append("*Wiki is navigation, not source of truth. Registry/checker validate consistency; wiki does not authorize action.*")
    lines.append("")

    return "\n".join(lines)


def main() -> int:
    if not REGISTRY_PATH.exists():
        print(f"ERROR: registry not found at {REGISTRY_PATH}", file=sys.stderr)
        return 1

    entries = load_registry(REGISTRY_PATH)
    wiki_content = generate_wiki(entries)
    WIKI_OUTPUT.write_text(wiki_content)
    print(f"Wiki generated: {WIKI_OUTPUT} ({len(entries)} entries)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
