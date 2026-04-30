# Document Governance Pack

Phase: **DG-1** | Status: **ACCEPTED** | Date: 2026-04-30

Phase 7P exposed a new system risk: documentation, receipts, ledgers, archive
state, wiki structure, and AI onboarding can become inconsistent or bloated
unless governed as first-class system objects.

This pack defines how Ordivon governs its own knowledge — documents, AI context,
receipts, ledgers — with the same discipline applied to paper trades.

## Quick Index

| Document | Purpose |
|----------|---------|
| [document-governance-pack-contract.md](document-governance-pack-contract.md) | Pack charter: purpose, scope, governed objects, principles |
| [document-taxonomy.md](document-taxonomy.md) | 18 document types with authority, freshness, archive rules |
| [document-lifecycle.md](document-lifecycle.md) | 9 statuses, transition rules, staleness policy, archive rules |
| [wiki-architecture.md](wiki-architecture.md) | Future wiki structure: site map, page types, metadata display |
| [ai-onboarding-doc-policy.md](ai-onboarding-doc-policy.md) | Leveled AI read path (L0–L4), verification, maintenance |
| [document-registry-schema.md](document-registry-schema.md) | Future manifest format: fields, validation rules, samples |
| [document-staleness-audit-dg-3.md](document-staleness-audit-dg-3.md) | DG-3 staleness audit: 55 docs, 1 critical fix, 10 safe phrases |
| [document-registry.jsonl](document-registry.jsonl) | Machine-readable document registry — 28 entries |
| [../../scripts/check_document_registry.py](../../scripts/check_document_registry.py) | Registry checker — 22 invariants, exit 0 on pass |

## Key Principles at a Glance

1. **Documents are governed objects** — they carry type, status, authority, freshness.
2. **Markdown = explanation; JSONL = evidence** — different tools, different roles.
3. **Freshness decays authority** — stale docs cannot be treated as current truth.
4. **Receipt is evidence, not authority** — archives record history; boundaries define current rules.
5. **AI onboarding must stay current** — root context updated at every phase transition.
6. **Stage Summit closes a phase; it does not open a new one** — closure ≠ activation.

## Current Phase Context

- **Phase 7P**: CLOSED (Alpaca Paper Dogfood — Stage Summit published)
- **Phase 8**: DEFERRED (Live Micro-Capital — 3/10 readiness criteria)
- **DG-1-DG-5**: COMPLETE — Document Governance Pack through Baseline Integration
- **DG-6**: ACTIVE — Wiki Navigation Prototype (15 tests, 28 entries)
- **No live trading, no broker write, no auto-trading, no Policy activation is authorized.**

## Relationship to Phase 7P

The JSONL ledger (30 events, 16 invariants) at `docs/runtime/paper-trades/paper-dogfood-ledger.jsonl`
is governed as a `ledger`-type document under this pack's taxonomy. It is
evidence, not execution authority.

## Next Steps After DG-1 Acceptance

1. ✅ Document registry populated — 28 entries (DG-2 + DG-3)
2. ✅ Staleness audit of existing documentation — 55 docs, 1 critical fix (DG-3)
3. ✅ Document checker built — `scripts/check_document_registry.py` (DG-2)
4. ⬜ Staleness automation + freshness checker (DG-4)
5. ⬜ Wiki surface implemented (navigation + metadata display)
6. ⬜ AI onboarding freshness automated (CI check)
