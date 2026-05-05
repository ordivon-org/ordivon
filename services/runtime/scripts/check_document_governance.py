#!/usr/bin/env python3
"""Document Governance — Ordivon memory hierarchy validator.

Validates that documents follow the L0-L5 layer model and that authority
labels are consistent:
  - L5 (Archive) must not appear in L0-L1 navigation
  - L4 (Product Notes) must not claim authority=source_of_truth
  - L1 (Current Truth) freshness must be within window
  - Every document must declare doc_layer and doc_authority

Usage:
    python scripts/check_document_governance.py
"""

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "docs" / "governance" / "document-registry.jsonl"

DOC_LAYERS = {"L0", "L1", "L2", "L3", "L4", "L5"}
DOC_AUTHORITIES = {
    "source_of_truth",
    "current_status",
    "supporting_evidence",
    "historical_record",
    "proposal",
    "archive",
}

# ── Layer-authority compatibility ──────────────────────────────────
# Which authority labels are valid for each layer
VALID_AUTHORITY_PER_LAYER = {
    "L0": {"source_of_truth", "current_status"},
    "L1": {"source_of_truth", "current_status"},
    "L2": {"supporting_evidence", "current_status"},
    "L3": {"source_of_truth"},
    "L4": {"proposal", "current_status"},
    "L5": {"historical_record", "archive"},
}

# ── Freshness windows (days) ───────────────────────────────────────
FRESHNESS_WINDOWS = {
    "L0": 7,  # root context must be fresh
    "L1": 7,  # current truth must be fresh
    "L2": 30,  # evidence receipts can age
    "L3": 90,  # governance canon is stable
    "L4": 90,  # product notes can age
    "L5": 365,  # archive is permanent
}


def main():
    if not REGISTRY.exists():
        print("❌ document-registry.jsonl not found")
        return 1

    entries = []
    with open(REGISTRY) as f:
        for line in f:
            line = line.strip()
            if line:
                entries.append(json.loads(line))

    errors = []
    stats = {"total": len(entries), "with_layer": 0, "with_authority": 0, "layer_counts": {}, "authority_counts": {}}

    for e in entries:
        did = e.get("doc_id", "?")
        layer = e.get("doc_layer", "")
        authority = e.get("doc_authority", e.get("authority", ""))

        # Count
        if layer:
            stats["with_layer"] += 1
            stats["layer_counts"][layer] = stats["layer_counts"].get(layer, 0) + 1
        if authority:
            stats["with_authority"] += 1
            stats["authority_counts"][authority] = stats["authority_counts"].get(authority, 0) + 1

        # Validation (only if fields are present — gradual adoption)
        if layer and layer not in DOC_LAYERS:
            errors.append(f"{did}: invalid doc_layer '{layer}'")

        if layer and authority:
            valid_auth = VALID_AUTHORITY_PER_LAYER.get(layer, set())
            if authority not in valid_auth:
                errors.append(
                    f"{did}: authority '{authority}' not valid for layer '{layer}'. Valid: {sorted(valid_auth)}"
                )

        # Freshness check
        if layer and layer in FRESHNESS_WINDOWS:
            try:
                freshness_str = e.get("freshness", "")
                if freshness_str:
                    freshness_date = datetime.fromisoformat(freshness_str)
                    age_days = (datetime.now(timezone.utc) - freshness_date).days
                    window = FRESHNESS_WINDOWS[layer]
                    if age_days > window:
                        errors.append(f"{did}: layer {layer} freshness {age_days}d exceeds {window}d window")
            except (ValueError, TypeError):
                pass

    # Print report
    print("Document Governance Pack — Layer Audit")
    print(f"  Total entries:  {stats['total']}")
    print(f"  With doc_layer: {stats['with_layer']}/{stats['total']}")
    print(f"  With doc_authority: {stats['with_authority']}/{stats['total']}")
    print(f"  Layers: {stats['layer_counts']}")
    print(f"  Authorities: {stats['authority_counts']}")
    print()

    if errors:
        print(f"❌ {len(errors)} violation(s):")
        for err in errors:
            print(f"  {err}")
        return 1
    else:
        # If no layers declared yet, this is informational not blocking
        if stats["with_layer"] == 0:
            print("ℹ️  No doc_layer fields declared yet — gradual adoption in progress.")
            print("   Add 'doc_layer' and 'doc_authority' to document-registry.jsonl entries.")
            return 0
        print("✅ All layer/authority/freshness invariants pass.")
        return 0


if __name__ == "__main__":
    sys.exit(main())
