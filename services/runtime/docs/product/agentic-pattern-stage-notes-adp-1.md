# Agentic Pattern Governance Mapping — Stage Notes (ADP-1)

> **Status:** OPEN
> **Date:** 2026-05-02
> **Authority:** current_truth

## 1. Purpose

ADP-1 creates a source-ledger-first agentic pattern governance mapping
that translates common AI agent failure modes into Ordivon-native
controls via HAP objects, OGAP boundaries, and EGB benchmark findings.

## 2. Strategic Position

```
OGAP → external adapter governance (CLOSED)
HAP  → harness capability description (CLOSED)
EGB  → external benchmark reference (CLOSED)
ADP  → agentic pattern → governance control mapping (OPEN)
```

ADP-1 connects the dots: external frameworks → internal protocols →
agent failure patterns → governance controls → CandidateRule suggestions.

## 3. Source-Ledger-First Methodology

ADP-1 builds its taxonomy from a source intake ledger (14 sources across
3 categories), not from abstract principles. Every pattern has source
seeds with citation, freshness status, and overclaim warnings.

## 4. Phase Inventory

| Deliverable | Path | Content |
|------------|------|---------|
| Source intake ledger | `docs/governance/agentic-pattern-source-ledger-adp-1.md` | 14 sources, 10 verified-current, 4 freshness-pending |
| Pattern taxonomy | `docs/governance/agentic-pattern-taxonomy-adp-1.md` | 18 patterns with full mapping format |
| Governance mapping | `docs/governance/agentic-pattern-governance-mapping-adp-1.md` | HAP, EGB, Ordivon control mappings + checker opportunities |
| Runtime boundaries | `docs/runtime/agentic-pattern-runtime-boundaries-adp-1.md` | AP-R0 boundary confirmation |
| Stage notes | `docs/product/agentic-pattern-stage-notes-adp-1.md` | This document |

## 5. What ADP-1 Creates

| Artifact | Count |
|----------|-------|
| Pattern taxonomy entries | 18 |
| CandidateRule suggestions (non-binding) | 18 |
| Source intake entries | 14 |
| HAP object mappings | 10 objects mapped |
| EGB gap mappings | 6 gaps addressed |
| Ordivon control mappings | 13 controls referenced |
| Future checker opportunities | 12 identified |

## 6. What ADP-1 Does Not Create

- ❌ Live API, SDK, MCP server, SaaS endpoint, package release
- ❌ Public standard, public repo
- ❌ Live adapter, live harness transport
- ❌ Broker/API integration
- ❌ Credential access
- ❌ External tool execution
- ❌ Action authorization
- ❌ Binding policy
- ❌ Compliance/certification/endorsement/equivalence claim
- ❌ Financial/broker/live action (remains NO-GO)
- ❌ Phase 8 (remains DEFERRED)

## 7. Known Debt at Start

| Debt ID | Status |
|---------|--------|
| DOC-WIKI-FLAKY-001 | open |
| EGB-SOURCE-FRESHNESS-001 | open |

## 8. Next Recommended Phase

**ADP-2** (Pattern detection implementation — light checker/schema
extensions based on ADP-1 findings) or **HAP-2** (HAP fixture dogfood
with ADP-1 pattern scenarios).

*Created: 2026-05-02 | ADP-1 foundation*
