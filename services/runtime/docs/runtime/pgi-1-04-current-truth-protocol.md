# PGI-1.04 Current Truth Protocol

Status: **CLOSED** | Date: 2026-05-03
Phase: PGI-1.04
Tags: `pgi`, `runtime-evidence`, `current-truth`, `freshness`
Authority: `supporting_evidence` | AI Read Priority: 2

## Intent

Prevent current truth from being treated as permanent truth, and add a focused
checker for freshness metadata on source-of-truth entries.

## Constraints

- Local static scanning only.
- Does not replace document registry checker.
- Does not authorize action.
- Does not make any document permanently true.

## Actions

Created:

```text
docs/governance/current-truth-protocol-pgi-1.md
scripts/check_current_truth_protocol.py
tests/fixtures/pgi_current_truth/clean/current-truth.md
tests/fixtures/pgi_current_truth/unsafe/permanent-truth.md
tests/fixtures/pgi_current_truth/clean/registry.jsonl
tests/fixtures/pgi_current_truth/unsafe/registry.jsonl
tests/unit/governance/test_pgi_current_truth_checker.py
```

Updated:

```text
docs/governance/philosophical-governance-gap-ledger.jsonl
```

## Evidence

Expected fixture behavior:

| Fixture | Expected |
|---------|----------|
| clean current_truth + fresh registry | PASS |
| permanent current_truth + missing registry freshness | BLOCKED |

## Review

PGI-1.04 is locally closed as a semantic hardening stage. It does not create a
new lifecycle system; it reinforces the existing DG freshness/supersession
model with a philosophical truth boundary.

## Rule Update

CandidateRule proposal:

```text
PGI-CR-004: Any current_truth claim must be revisable and must not be described
as permanent, final, or impossible to supersede.
```

Status: **candidate only**. This is not Policy.

## Next Action

```text
PGI-1.05 - Confidence and Calibration Model
```
