# DG-1 Truth Substrate Hardening — Runtime Evidence

Status: **current** | Date: 2026-05-02 | Phase: DG-1
Tags: `dg-1`, `runtime`, `closure`, `truth-substrate`
Authority: `supporting_evidence` | AI Read Priority: 2

## Summary

DG-1 hardens Ordivon's Document Governance Pack into a stable truth substrate
consumable by ADP-3 detectors, PV surface checks, New AI Context Checks,
and future Ordivon Verify users.

## What DG-1 Created

| Doc | Purpose |
|-----|---------|
| `document-classification-index-dg-1.md` | Canonical classification: plane, type, authority, AI priority, freshness, detector-consumable, public-surface |
| `document-authority-model-dg-1.md` | 7 authority types with invariants: receipts≠authorization, stage summits≠permission, detector PASS≠approval |
| `document-ai-read-path-invariants-dg-1.md` | L0-L4 read path invariants with freshness requirements and ADP-3 enforcement rules |
| `document-freshness-supersession-dg-1.md` | Freshness requirements by priority/authority, supersession rules, DEGRADED lifecycle, DOC-WIKI-FLAKY-001 disposition |

## Debt Ownership Routing

| Debt ID | Owner Phase | Status | DG-1 Action |
|---------|------------|--------|-------------|
| CODE-FENCE-001 | ADP-4 | open | Routed to ADP-4 for detector precision hardening |
| RECEIPT-SCOPE-001 | ADP-4 + Receipt | open | Routed to receipt integrity/ADP-4; DG involvement for receipt lifecycle |
| DOC-WIKI-FLAKY-001 | DG-2 | accepted_until | Wiki currently deterministic; re-verify at next registry change |
| EGB-SOURCE-FRESHNESS-001 | EGB-2 | open | External benchmark freshness; requires periodic review |
| CONFIG-GUARD-001 | ADP-3 (mitigated) | partially mitigated | AP-RT-CONFIG-GUARD rule active |
| DEGRADED-LIFECYCLE-001 | ADP-3 (mitigated) | mitigated | ADP3-DG-DEGRADED-LIFECYCLE rule active |
| PATH-BRITTLENESS | ADP-3 (mitigated) | partially mitigated | Broader PV detection active |
| FRESHNESS-001 | DG-2 | partially mitigated | ADP3-DG-STALENESS rule active; registry schema upgrade needed |

## Registry Gap Baseline

DG-1 documents the current registry gaps without fixing them inline:

- 8/79 docs have `last_verified` (target: ~30 for L0/L1 + source_of_truth)
- 6/79 docs have `stale_after_days` (target: ~30)
- 21 L1 docs need freshness metadata (7 currently covered)
- 20 source_of_truth docs need freshness metadata (6 currently covered)

Closing these gaps is DG-2 work: systematic freshness metadata backfill.

## Known Limitations

- Registry metadata can drift unless maintained.
- Checker coverage is not semantic completeness.
- Wiki generation can pass while content is stale.
- Freshness metadata does not prove correctness.
- AI onboarding can still be misunderstood without New AI Context Check.
- External benchmark freshness requires periodic review.
- Document governance does not authorize action.

## Verification

pr-fast: 12/12 PASS | Registry: 79 entries, all invariants pass | Wiki: 79 entries, deterministic
