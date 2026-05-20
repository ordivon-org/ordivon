#!/usr/bin/env python3
"""Migrate governance data from JSONL files to PostgreSQL (or SQLite fallback).

Phase 1: JSONL → PG migration. JSONL stays as export/audit artifact, not source of truth.

Usage:
    python3 scripts/migrate_governance_to_pg.py --dry-run
    python3 scripts/migrate_governance_to_pg.py
    python3 scripts/migrate_governance_to_pg.py --table document_registry
    python3 scripts/migrate_governance_to_pg.py --create-only

Data sources:
    docs/governance/document-registry.jsonl         → document_registry
    docs/governance/current-truth-entry-map.jsonl   → current_truth_entries
    docs/governance/verification-debt-ledger.jsonl  → governance_debts
    docs/governance/phase-closure-ledger.jsonl      → phase_closures
    docs/governance/lesson-ledger.jsonl             → lessons
    docs/governance/owner-routing-rules.jsonl       → owner_routing_rules
"""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from state.db.base import Base
from state.db.governance_schema import (
    DocumentRegistry,
    CurrentTruthEntry,
    GovernanceDebt,
    Lesson,
    PhaseClosure,
    OwnerRoutingRule,
)
from state.db.session import SessionLocal, engine


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def create_tables(dry: bool = False) -> None:
    """Create all governance tables."""
    if dry:
        print("[DRY-RUN] Would create all governance tables")
        tables = sorted(Base.metadata.tables.keys())
        for t in tables:
            print(f"  - {t}")
        return
    Base.metadata.create_all(bind=engine)
    print(f"Created {len(Base.metadata.tables)} governance tables")


def _load_jsonl(path: Path) -> list[dict]:
    if not path.exists():
        return []
    entries = []
    for line in open(path):
        if not line.strip():
            continue
        try:
            entries.append(json.loads(line))
        except json.JSONDecodeError as e:
            print(f"  WARN: skipping bad line in {path.name}: {e}")
    return entries


# ── Per-table migrations ───────────────────────────────────────────────────


def migrate_registry(dry: bool = False) -> int:
    path = ROOT / "docs/governance/document-registry.jsonl"
    if not path.exists():
        print("  document-registry.jsonl not found — skipping")
        return 0

    entries = _load_jsonl(path)
    rows = []
    for d in entries:
        rows.append(
            DocumentRegistry(
                doc_id=d.get("doc_id", ""),
                path=d.get("path", ""),
                title=d.get("title", ""),
                doc_type=d.get("doc_type", ""),
                status=d.get("status", "current"),
                authority=d.get("authority", ""),
                phase=d.get("phase"),
                owner=d.get("owner", ""),
                freshness=d.get("freshness", ""),
                ai_read_priority=d.get("ai_read_priority", 0),
                supersedes=d.get("supersedes"),
                superseded_by=d.get("superseded_by"),
                related_docs=d.get("related_docs", []),
                related_ledgers=d.get("related_ledgers", []),
                related_receipts=d.get("related_receipts", []),
                notes=d.get("notes", ""),
                last_verified=d.get("last_verified", ""),
                stale_after_days=d.get("stale_after_days"),
                doc_layer=d.get("doc_layer", ""),
                doc_authority=d.get("doc_authority", ""),
                authority_domain=d.get("authority_domain", ""),
                authority_role=d.get("authority_role", ""),
                authority_scope=d.get("authority_scope", ""),
            )
        )

    if dry:
        print(f"  [DRY-RUN] Would migrate {len(rows)} document_registry entries")
        return len(rows)
    return _upsert_rows(rows, DocumentRegistry, "doc_id")


def migrate_current_truth(dry: bool = False) -> int:
    path = ROOT / "docs/governance/current-truth-entry-map.jsonl"
    if not path.exists():
        print("  current-truth-entry-map.jsonl not found — skipping")
        return 0

    entries = _load_jsonl(path)
    rows = []
    for d in entries:
        rows.append(
            CurrentTruthEntry(
                entry_id=d.get("entry_id", ""),
                doc_id=d.get("doc_id", ""),
                path=d.get("path", ""),
                authority_type=d.get("authority_type", ""),
                authority_tier=d.get("authority_tier", ""),
                current_truth_allowed=d.get("current_truth_allowed", True),
                owner=d.get("owner", ""),
                last_verified=d.get("last_verified", ""),
                review_date=d.get("review_date", ""),
                source_registry=d.get("source_registry", ""),
                notes=d.get("notes", ""),
            )
        )

    if dry:
        print(f"  [DRY-RUN] Would migrate {len(rows)} current_truth_entries")
        return len(rows)
    return _upsert_rows(rows, CurrentTruthEntry, "entry_id")


def migrate_debts(dry: bool = False) -> int:
    """Migrate from all known debt JSONL files."""
    debt_paths = [
        ROOT / "docs/governance/verification-debt-ledger.jsonl",
        ROOT / "docs/governance/dependency-audit-debts.jsonl",
    ]

    all_entries = []
    for dp in debt_paths:
        if dp.exists():
            all_entries.extend(_load_jsonl(dp))

    if not all_entries:
        print("  No debt JSONL files found — skipping")
        return 0

    rows = []
    for d in all_entries:
        debt_id = d.get("debt_id", d.get("finding_id", ""))
        if not debt_id:
            continue  # Skip entries without a unique identifier
        rows.append(
            GovernanceDebt(
                debt_id=debt_id,
                status=d.get("status", "OPEN"),
                severity=d.get("severity", "medium"),
                description=d.get("reason", d.get("description", d.get("summary", ""))),
                source_path=d.get("source_path", d.get("path", "")),
                owner=d.get("owner_candidate", d.get("owner", "")),
                due_stage=d.get("due_stage", ""),
                close_criteria=d.get("close_criteria", ""),
                evidence_refs=d.get("evidence_refs", []),
                not_claimed=d.get("not_claimed", []),
            )
        )

    if dry:
        print(f"  [DRY-RUN] Would migrate {len(rows)} governance_debts from {len(debt_paths)} files")
        return len(rows)
    return _upsert_rows(rows, GovernanceDebt, "debt_id")


def migrate_phase_closures(dry: bool = False) -> int:
    path = ROOT / "docs/governance/phase-closure-ledger.jsonl"
    if not path.exists():
        print("  phase-closure-ledger.jsonl not found — skipping")
        return 0

    entries = _load_jsonl(path)
    rows = []
    for d in entries:
        rows.append(
            PhaseClosure(
                closure_id=d.get("closure_id", d.get("phase", "")),
                phase=d.get("phase", ""),
                status=d.get("status", "CLOSED"),
                summary=d.get("summary", ""),
                receipt_ref=d.get("receipt_ref", ""),
                debt_count=d.get("debt_count"),
                evidence_refs=d.get("evidence_refs", []),
                extra=d.get("extra", d.get("metadata")),
            )
        )

    if dry:
        print(f"  [DRY-RUN] Would migrate {len(rows)} phase_closures")
        return len(rows)
    return _upsert_rows(rows, PhaseClosure, "closure_id")


def migrate_lessons(dry: bool = False) -> int:
    path = ROOT / "docs/governance/lesson-ledger.jsonl"
    if not path.exists():
        print("  lesson-ledger.jsonl not found — skipping")
        return 0

    entries = _load_jsonl(path)
    rows = []
    for d in entries:
        rows.append(
            Lesson(
                lesson_id=d.get("lesson_id", ""),
                source_type=d.get("source_type", "debt"),
                source_ref=d.get("source_ref", ""),
                category=d.get("category", ""),
                summary=d.get("summary", d.get("description", "")),
                severity=d.get("severity", "medium"),
                candidate_rule_ids=d.get("candidate_rule_ids", []),
                related_lessons=d.get("related_lessons", []),
            )
        )

    if dry:
        print(f"  [DRY-RUN] Would migrate {len(rows)} lessons")
        return len(rows)
    return _upsert_rows(rows, Lesson, "lesson_id")


def migrate_owner_routing(dry: bool = False) -> int:
    path = ROOT / "docs/governance/owner-routing-rules.jsonl"
    if not path.exists():
        print("  owner-routing-rules.jsonl not found — skipping")
        return 0

    entries = _load_jsonl(path)
    rows = []
    for i, d in enumerate(entries):
        rule_id = d.get("rule_id", d.get("id", ""))
        path_pattern = d.get("path_pattern", d.get("path", ""))
        if not path_pattern:
            continue  # Skip empty entries
        if not rule_id and path_pattern:
            # Generate ID from path pattern
            import hashlib

            rule_id = "orr-" + hashlib.sha256(path_pattern.encode()).hexdigest()[:12]
        if not rule_id:
            continue
        rows.append(
            OwnerRoutingRule(
                rule_id=rule_id,
                path_pattern=path_pattern,
                owner=d.get("default_owner", d.get("owner", "")),
                priority=d.get("priority", 0),
                notes=d.get("routing_rule", d.get("notes", "")),
            )
        )

    if dry:
        print(f"  [DRY-RUN] Would migrate {len(rows)} owner_routing_rules")
        return len(rows)
    return _upsert_rows(rows, OwnerRoutingRule, "rule_id")


# ── Helpers ────────────────────────────────────────────────────────────────


def _upsert_rows(rows: list, model, unique_col: str) -> int:
    """Insert rows, skip duplicates by unique column."""
    db = SessionLocal()
    count = 0
    try:
        col = getattr(model, unique_col)
        for r in rows:
            val = getattr(r, unique_col)
            existing = db.query(model).filter(col == val).first()
            if not existing:
                db.add(r)
                count += 1
        db.commit()
    except Exception as e:
        db.rollback()
        print(f"  ERROR: {e}")
        raise
    finally:
        db.close()
    return count


MIGRATIONS = {
    "document_registry": migrate_registry,
    "current_truth_entries": migrate_current_truth,
    "governance_debts": migrate_debts,
    "phase_closures": migrate_phase_closures,
    "lessons": migrate_lessons,
    "owner_routing_rules": migrate_owner_routing,
}


def main() -> None:
    dry = "--dry-run" in sys.argv
    create_only = "--create-only" in sys.argv
    table_filter = None

    for arg in sys.argv:
        if arg.startswith("--table="):
            table_filter = arg.split("=", 1)[1]

    print("=== Ordivon Governance → Database Migration ===")
    create_tables(dry=dry)

    if create_only:
        print("Tables created. Skipping data migration (--create-only).")
        return

    if table_filter:
        if table_filter in MIGRATIONS:
            print(f"\n-- Migrating: {table_filter} --")
            count = MIGRATIONS[table_filter](dry=dry)
            print(f"  {table_filter}: {count} rows")
        else:
            print(f"Unknown table: {table_filter}")
            print(f"Available: {', '.join(sorted(MIGRATIONS))}")
            sys.exit(1)
        return

    results = {}
    for name, fn in MIGRATIONS.items():
        print(f"\n-- Migrating: {name} --")
        count = fn(dry=dry)
        results[name] = count

    print(f"\n=== Migration {'dry-run' if dry else 'complete'} ===")
    for name, count in results.items():
        print(f"  {name}: {count}")


if __name__ == "__main__":
    main()
