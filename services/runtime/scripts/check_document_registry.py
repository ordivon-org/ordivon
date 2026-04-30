#!/usr/bin/env python3
"""Phase DG-2: Document Registry Consistency Checker.

Reads docs/governance/document-registry.jsonl and verifies core document
governance invariants. Never calls Alpaca. Never requires API keys.
Read-only evidence validation.
"""

from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REGISTRY_PATH = ROOT / "docs" / "governance" / "document-registry.jsonl"

# ── Valid values from governance docs ──────────────────────────────────

VALID_DOC_TYPES = {
    "root_context",
    "ai_onboarding",
    "phase_boundary",
    "architecture",
    "design_spec",
    "runbook",
    "receipt",
    "stage_summit",
    "red_team",
    "ledger",
    "tracker",
    "schema",
    "template",
    "adr",
    "archive_index",
    "product",
    "runtime",
    "governance_pack",
}

# Valid lifecycle statuses (accepted is alias for current)
VALID_STATUSES = {
    "draft",
    "proposed",
    "current",
    "accepted",       # alias for current
    "implemented",
    "closed",
    "deferred",
    "superseded",
    "archived",
    "stale",
}

# Statuses that imply the document is actively authoritative
ACTIVE_STATUSES = {"current", "accepted", "implemented"}

VALID_AUTHORITIES = {
    "source_of_truth",
    "current_status",
    "supporting_evidence",
    "historical_record",
    "proposal",
    "example",
    "archive",
}

# Authority levels that carry decision-making weight
DECISION_AUTHORITIES = {"source_of_truth", "current_status"}

# High-priority AI read levels (0, 1)
HIGH_PRIORITY_AI_READ = {0, 1}

# Low-priority archive/reference levels
LOW_PRIORITY_AI_READ = {4}

# AI onboarding / root context types that must never be stale/archived
NEVER_STALE_TYPES = {"root_context", "phase_boundary", "ai_onboarding"}
NEVER_ARCHIVE_TYPES = {"root_context", "phase_boundary", "ai_onboarding"}


def load_registry(path: Path) -> list[dict]:
    """Load entries from JSONL."""
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
    """Return list of invariant violations."""
    errors: list[str] = []
    ids: set[str] = set()

    REQUIRED_FIELDS = {
        "doc_id", "path", "title", "doc_type", "status",
        "authority", "phase", "owner", "freshness", "ai_read_priority",
        "supersedes", "superseded_by", "related_docs", "related_ledgers",
        "related_receipts", "notes",
    }

    for e in entries:
        did = e.get("doc_id", f"<missing doc_id at index {entries.index(e)}>")

        # --- Required fields ---
        missing = REQUIRED_FIELDS - set(e.keys())
        if missing:
            errors.append(f"{did}: missing required fields: {missing}")

        # --- Unique doc_id ---
        if did in ids:
            errors.append(f"{did}: duplicate doc_id")
        ids.add(did)

        # --- doc_type ---
        dt = e.get("doc_type", "")
        if dt not in VALID_DOC_TYPES:
            errors.append(f"{did}: invalid doc_type '{dt}'")
        if not dt:
            continue

        # --- status ---
        status = e.get("status", "")
        if status not in VALID_STATUSES:
            errors.append(f"{did}: invalid status '{status}'")

        # --- authority ---
        authority = e.get("authority", "")
        if authority not in VALID_AUTHORITIES:
            errors.append(f"{did}: invalid authority '{authority}'")

        # --- path must exist ---
        path_str = e.get("path", "")
        if path_str:
            full_path = ROOT / path_str
            if not full_path.exists():
                errors.append(f"{did}: registered path does not exist: {path_str}")

        # --- ai_read_priority ---
        priority = e.get("ai_read_priority")
        if priority is not None and (not isinstance(priority, int) or priority not in (0, 1, 2, 3, 4)):
            errors.append(f"{did}: invalid ai_read_priority '{priority}'")

        # --- source_of_truth docs cannot be stale/archived ---
        if authority == "source_of_truth" and status in ("stale", "archived"):
            errors.append(f"{did}: source_of_truth doc has status '{status}' — must be current")

        # --- root_context / phase_boundary cannot be stale ---
        if dt in NEVER_STALE_TYPES and status == "stale":
            errors.append(f"{did}: {dt} doc has status 'stale' — governance incident")

        # --- root_context / phase_boundary / ai_onboarding cannot be archived ---
        if dt in NEVER_ARCHIVE_TYPES and status == "archived":
            errors.append(f"{did}: {dt} doc has status 'archived' — never archived while project active")

        # --- Archived docs cannot be high-priority AI read ---
        if status == "archived" and priority in HIGH_PRIORITY_AI_READ:
            errors.append(f"{did}: archived doc has AI read priority {priority} — should be level 4")

        # --- Ledger docs must be supporting_evidence, not source_of_truth ---
        if dt == "ledger" and authority == "source_of_truth":
            errors.append(f"{did}: ledger doc has authority 'source_of_truth' — must be 'supporting_evidence'")

        # --- Paper dogfood ledger: evidence, NOT execution authority ---
        if "paper-dogfood-ledger" in did.lower() and dt == "ledger":
            notes = e.get("notes", "")
            if "execution authority" in notes.lower() and "not" not in notes.lower():
                errors.append(f"{did}: paper dogfood ledger described as execution authority")
            if "evidence" not in notes.lower():
                errors.append(f"{did}: paper dogfood ledger must be labeled as evidence")

        # --- CandidateRule docs must not be marked Policy / active authority ---
        if "candidate" in did.lower() or "candidate" in e.get("title", "").lower():
            if authority in DECISION_AUTHORITIES and dt != "root_context":
                errors.append(
                    f"{did}: CandidateRule doc has authority '{authority}' — "
                    "must be 'supporting_evidence' or 'proposal', NOT 'source_of_truth'/'current_status'"
                )
            notes = e.get("notes", "").lower()
            if "policy" in notes and "not policy" not in notes:
                errors.append(f"{did}: CandidateRule doc may describe itself as Policy")

        # --- Phase 8 docs must remain deferred ---
        if "phase-8" in did.lower() or "phase 8" in e.get("title", "").lower():
            if status not in ("deferred", "closed", "archived"):
                errors.append(f"{did}: Phase 8 doc has status '{status}' — must remain deferred")

        # --- Trackers referencing Phase 8 must be deferred ---
        if dt == "tracker" and "phase-8" in did.lower():
            if status != "deferred":
                errors.append(f"{did}: Phase 8 tracker must be deferred, got '{status}'")

    # --- Supersedes / superseded_by references must resolve ---
    for e in entries:
        did = e.get("doc_id", "")
        for ref_field in ("supersedes", "superseded_by"):
            ref = e.get(ref_field)
            if ref and ref not in ids:
                errors.append(f"{did}: {ref_field} references unknown doc_id '{ref}'")

    # --- Critical AI onboarding docs must be high-priority ---
    critical_ai_docs = {"agents-md", "ai-readme", "phase-boundaries", "agent-output-contract"}
    for e in entries:
        did = e.get("doc_id", "")
        if did in critical_ai_docs:
            priority = e.get("ai_read_priority")
            if priority not in (0, 1):
                errors.append(f"{did}: critical AI onboarding doc has priority {priority}, expected 0 or 1")

    # --- current-phase-boundaries must be source_of_truth ---
    for e in entries:
        if e.get("doc_id") == "phase-boundaries":
            if e.get("authority") != "source_of_truth":
                errors.append("phase-boundaries: must have authority 'source_of_truth'")

    return errors


def print_summary(entries: list[dict]) -> None:
    """Print compact registry summary."""
    type_counter = Counter(e.get("doc_type", "unknown") for e in entries)
    authority_counter = Counter(e.get("authority", "unknown") for e in entries)
    status_counter = Counter(e.get("status", "unknown") for e in entries)

    source_of_truth_count = authority_counter.get("source_of_truth", 0)
    current_status_count = authority_counter.get("current_status", 0)
    supporting_evidence_count = authority_counter.get("supporting_evidence", 0)
    archive_count = authority_counter.get("archive", 0)
    stale_count = status_counter.get("stale", 0)
    superseded_count = status_counter.get("superseded", 0)
    high_priority_count = sum(
        1 for e in entries if e.get("ai_read_priority") in HIGH_PRIORITY_AI_READ
    )

    print("=" * 60)
    print("DOCUMENT REGISTRY SUMMARY")
    print("=" * 60)
    print(f"  Total registered docs:     {len(entries)}")
    print(f"  source_of_truth:           {source_of_truth_count}")
    print(f"  current_status:            {current_status_count}")
    print(f"  supporting_evidence:       {supporting_evidence_count}")
    print(f"  archive:                   {archive_count}")
    print(f"  stale + superseded:        {stale_count + superseded_count}")
    print(f"  High-priority AI read:     {high_priority_count}")
    print(f"  Doc types:                 {len(type_counter)}")
    print(f"  Statuses:                  {len(status_counter)}")


def main() -> int:
    path = Path(sys.argv[1]) if len(sys.argv) > 1 else REGISTRY_PATH
    if not path.exists():
        print(f"ERROR: registry not found at {path}")
        return 1

    entries = load_registry(path)
    errors = check_invariants(entries)

    if errors:
        print(f"\n❌ {len(errors)} INVARIANT VIOLATION(S):\n")
        for err in errors:
            print(f"  - {err}")
        print()
        return 1

    print_summary(entries)
    print("\n✅ All document registry invariants pass.\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
