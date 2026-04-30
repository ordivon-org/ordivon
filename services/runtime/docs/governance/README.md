# Document Governance Pack

Phase: **DG-Z** (Stage Summit) | Status: **CLOSING** | Date: 2026-04-30

The Document Governance Pack (DG-1 through DG-6D-S) is closing as a
foundational governance stage. See the Stage Summit at:
[document-governance-stage-summit-dg-z.md](../product/document-governance-stage-summit-dg-z.md)

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
| [document-registry.jsonl](document-registry.jsonl) | Machine-readable document registry — 30 entries |
| [../../scripts/check_document_registry.py](../../scripts/check_document_registry.py) | Registry checker — invariants, exit 0 on pass |
| [verification-debt-policy.md](verification-debt-policy.md) | 8 debt categories, 4 severities, lifecycle rules |
| [verification-debt-ledger.jsonl](verification-debt-ledger.jsonl) | 4 entries, all closed (VD-001 through VD-004) |
| [verification-gate-manifest.json](verification-gate-manifest.json) | 11-gate manifest, mirrors pr-fast |
| [verification-signal-classification.md](verification-signal-classification.md) | Before-you-fix checklist: classify checker failures before acting |
| [../product/document-governance-stage-summit-dg-z.md](../product/document-governance-stage-summit-dg-z.md) | DG Pack Stage Summit (this closure) |

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
- **DG Pack**: CLOSING — 18 sub-phases, 94 governance tests, 30 registry entries
- **pr-fast**: 11/11 hard gates
- **Open debt**: VD-001 (low, AGENTS.md markdown), VD-002/003 closed in DG-6D
- **No live trading, no broker write, no auto-trading, no Policy activation is authorized.**

## Relationship to Phase 7P

The JSONL ledger (30 events, 16 invariants) at `docs/runtime/paper-trades/paper-dogfood-ledger.jsonl`
is governed as a `ledger`-type document under this pack's taxonomy. It is
evidence, not execution authority.

## Post DG-Z

1. Knowledge Navigation / Wiki Extension (low risk)
2. Global Tooling Hygiene (VD-001 + 4 non-DG F401)
3. Rust Kernel Scoping (planning only)
4. Phase 8 remains gated by readiness requirements
