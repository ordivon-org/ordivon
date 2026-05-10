# Ordivon

Ordivon is a governance operating system for agent-native work.
Its core question:

> **How are actions proposed, verified, authorized, executed, evidenced, and reviewed — without self-deception?**

## What Ordivon Is

Ordivon is built around a governance loop:

```
Intent → Evaluation → Authority → Execution → Receipt → Debt → Gate → Review → Policy
```

Three layers:

- **Core** — domain-invariant governance kernel. Never imports Pack.
  - 40 checkers, schema-first authority/route taxonomy, registry-path reconciliation.
  - `checkers/`, `scripts/`, `src/`, `governance_engine/`, `docs/`
- **Packs** — domain governance (Coding, Finance). Imports Core.
  - `packs/coding/`, `packs/finance/`
- **Adapters** — external boundary with capability declarations and safety guards.
  - `adapters/finance/` (Alpaca Paper, GET-only, 4 safety locks)

## Governance Control Plane

Ordivon has a self-calibrating governance control plane built through GOS-PM-1
through GOS-PM-10:

| Layer | System | Status |
|-------|--------|--------|
| Path Map | Auto-maintained repo topology from git + registry | VERIFIED |
| Reconciliation | Registry claims vs path observations | VERIFIED |
| Authority | Domain-aware taxonomy (8 domains x 27 roles) | VERIFIED |
| Route | Doc-type/route compatibility matrix | VERIFIED |
| Coverage | Every tracked file classified (10 statuses) | VERIFIED |
| Ownership | Owner/reviewer/approver routing per coverage object | VERIFIED |
| Admission | Pre-merge gate for coverage mutations | VERIFIED (SHADOW) |
| Query | Single-command governance context per file | VERIFIED |

```
2121 files · 457 registry entries · 40 checkers · 0 blocked
ordivon-verify: READY (40/40) · Full Closure: NOT CLAIMED
```

## Methodology

Ordivon's governance methodology is documented in:

- `docs/governance/ordivon-methodology-core.md` — 12 invariants, dual-gate, A1-A4 matrix
- `docs/governance/assessment-template.md` — evidence-first state ledger format
- `docs/governance/schemas/claim-vocabulary.json` — controlled vocabulary (forbidden: complete, done, honest, 全绿)

Core invariants:

1. Evidence ≠ Claim. READY ≠ Authorization.
2. Summary ≠ Current Truth. Checker PASS ≠ Governance Truth.
3. Registry declares. Path Map observes. Reconciler judges drift.
4. Derived ≠ Duplicated. Generated View ≠ Source of Truth.
5. Reconciled ≠ Synchronized. Admission Pass ≠ Full Closure.

## Current Phase

| Phase | Status |
|-------|--------|
| CI-SelfCalibration | CLOSED |
| GOS-PM-1 through PM-10 (Path Governance) | VERIFIED |
| Alpha-0 (Evidence of Governed Work) | ACTIVE |
| Phase 8 (Live Trading) | DEFERRED |

## Current State

```
ordivon-verify:    READY (40/40)
Path map:          2117 files → 813 governed, 0 blocked
RPR findings:      0 BLOCKING, 0 DEGRADED
Registry:          457 entries, 23 doc_types
Debts:             8 (1 OPEN CVE, 1 OPEN CI parity, 1 OPEN non-governed code)
CandidateRules:    4 drafts, 0 activated
Coverage boundary: 0 blocked, 821 CB-12 OPEN (known, classified)
Full Closure:      NOT CLAIMED
```

## Key Documents

For AI agents onboarding:

| Priority | Document |
|----------|----------|
| 0 | `AGENTS.md` |
| 1 | `docs/ai/current-phase-boundaries.md` |
| 1 | `docs/ai/agent-output-contract.md` |
| 1 | `docs/governance/ordivon-methodology-core.md` |
| 1 | `docs/governance/assessment-template.md` |
| 2 | `docs/architecture/ordivon-core-pack-adapter-ontology.md` |
| 2 | `docs/ai/ordivon-macro-structure.md` |
| 2 | `docs/product/ordivon-gos-hardening-roadmap.md` |

## Development

```bash
uv sync --extra dev
pnpm install --frozen-lockfile
uv run pytest tests/unit/product tests/unit/governance -q
uv run python scripts/ordivon_verify.py all
```

## Hard Rules

1. Core never imports Pack.
2. Evidence ≠ Claim. READY ≠ Authorization.
3. Not clean. Governed.
4. Registry Claim ≠ Path Observation. Reconciled ≠ Synchronized.
5. No banned completion vocabulary. Say READY/BLOCKED/OPEN, not complete/done/全绿.
6. Phase 8 (live trading) remains DEFERRED until explicit GO.
7. No broker write, no auto trading, no Policy/RiskEngine activation without Stage Summit.
