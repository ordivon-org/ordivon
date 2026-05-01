# Ordivon

Ordivon is a governance operating system for agent-native work.
Its core object is not transactions, documents, or CLIs — it is the question:

> **How are actions proposed, verified, authorized, executed, evidenced, and reviewed — without self-deception?**

## What Ordivon Is

Ordivon is built around a governance loop:

```
Intent → Evaluation → Authority → Execution → Receipt → Debt → Gate → Review → Policy
```

- **Core** (`governance/`) — domain-invariant decision algebra. Never imports Pack.
- **Packs** (`packs/`) — domain governance (Finance, Document, Coding, Verify). Imports Core.
- **Adapters** (`adapters/`) — external boundary with capability declarations and safety guards.

## Current Product Wedge: Ordivon Verify

The first externalizable product wedge is **Ordivon Verify** — a local read-only
verification CLI that checks whether AI/agent work can be trusted.

It validates:
- Receipts (claims vs evidence)
- Debt (hidden failures)
- Gates (boundary enforcement)
- Documents (current truth vs staleness)

Status: `READY` means selected checks pass — it does **not** authorize execution.

Package: `src/ordivon_verify/` (private prototype, not published).

Run: `uv run python scripts/ordivon_verify.py all`

## Historical Context

This repository began as **PFIOS** (Personal Financial Intelligence Operating System)
and was later tracked under the working identity **AegisOS / CAIOS**. Those identities
are historical. The current system is **Ordivon**.

Legacy PFIOS/AegisOS directories (`orchestrator/`, `capabilities/`, `intelligence/`,
`state/`, `infra/`, `services/`, `apps/`, `domains/`, `adapters/`) remain in the
repository as deferred technical debt. They are not part of the Ordivon Verify
public wedge and are not actively maintained in the current phase line.

See: `docs/runtime/legacy-identity-hygiene-pv-n2h.md`

## Current Phase

| Phase | Status |
|-------|--------|
| Phase 7P (Paper Dogfood) | CLOSED |
| DG Pack (Document Governance) | CLOSED |
| PV-Z (Verify Productization Summit) | CLOSED |
| PV-N1 (Private Package Prototype) | CLOSED |
| PV-N2 (Schema Extraction) | CLOSED |
| PV-N2H (Legacy Identity Hygiene) | ACTIVE |
| Phase 8 (Live Trading) | DEFERRED |

**pr-fast:** 11/11 PASS. **Tests:** 520+ (product 140, governance 192, finance 188).
**Registered debt:** 4 closed, 0 open.

## Key Documents

For AI agents onboarding into this project, start here:

| Priority | Document |
|----------|----------|
| 0 | `AGENTS.md` — status header + living docs |
| 1 | `docs/ai/current-phase-boundaries.md` — active/deferred/NO-GO |
| 1 | `docs/ai/agent-output-contract.md` — required output shape |
| 2 | `docs/architecture/ordivon-core-pack-adapter-ontology.md` — architecture |
| 2 | `docs/architecture/ordivon-moat-and-product-identity.md` — what can't be lost |
| 2 | `docs/runtime/ordivon-value-philosophy.md` — why not a trading bot |

## Development

```bash
# Python
uv sync --extra dev

# Frontend
pnpm install --frozen-lockfile

# Tests (Ordivon)
uv run pytest tests/unit/product tests/unit/governance tests/unit/finance -q

# Frontend
pnpm lint:web && pnpm typecheck:web && pnpm build:web
```

## Hard Rules

1. Core never imports Pack.
2. Evidence ≠ Authority. READY ≠ Authorization.
3. CandidateRule ≠ Policy.
4. Receipt is immutable, append-only evidence — not review.
5. Debt may exist; hidden debt may not become truth.
6. Checkers validate consistency/honesty; they do not authorize action.
7. Phase 8 (live trading) remains DEFERRED until explicit GO.
8. No broker write, no auto trading, no Policy/RiskEngine activation without Stage Summit.
