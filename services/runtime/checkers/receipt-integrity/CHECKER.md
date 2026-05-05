---
gate_id: receipt_integrity
display_name: Receipt Integrity
layer: L7B
hardness: hard
purpose: Receipt honesty and contradiction detection
protects_against: "Skipped None+not run, SEALED+pending, clean working tree+untracked, stale baseline count, overclaim language, CandidateRule validated claim, boundary claim mismatch"
profiles: [pr-fast, full]
timeout: 120
tags: [receipt, contradiction, governance, verification]
metadata:
  ordivon:
    related_checkers: [verification_debt, gate_manifest]
    ai_read_priority: 2
---

# Receipt Integrity Checker

## Purpose

Detects receipt overclaims — contradictory language in phase closure
documents where a claim of completion coexists with evidence of
incompletion.

## Detection Rules

1. **Skipped Verification: None** — claims nothing was skipped, but
   nearby text uses "not run", "skipped", "pending verification" etc.

2. **SEALED / FULLY SEALED** — claims phase is sealed, but nearby text
   shows pending checks, addendum requirements, or deferred verification.

3. **clean working tree** — claims a clean state without qualifying
   "Tracked working tree clean" when untracked residue exists.

4. **stale baseline count** — uses hardcoded cardinality (e.g. "7/7")
   when the baseline has grown beyond that number.

5. **Ruff clean** — claims Ruff is clean globally without qualifying
   the scope when pre-existing debt (excluded files) exists.

6. **CandidateRule validated** — claims CandidateRule is "validated"
   without the "advisory" or "supported by evidence" qualifier.

7. **Boundary claim mismatch** — work summary describes order/execution
   capability but boundary claim lacks explicit paper-only evidence.

## Usage

```bash
python -m ordivon_verify run receipt_integrity
```

## Implementation

See `run.py` for the detection logic.
