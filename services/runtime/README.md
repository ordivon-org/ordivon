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

## Companion Governance Origin

Ordivon exists first as a companion governance system for its creator: to make
decisions traceable, actions accountable, outcomes reviewable, knowledge
accumulative, and the self progressively more coherent under uncertainty.

Commercialization, public release, users, community, and company formation are
possible externalization paths. They are not the origin of Ordivon's meaning.

See: `docs/architecture/ordivon-companion-governance-constitution.md`

Its highest operating layer is philosophical governance: how Ordivon judges
truth, chooses values, constrains action, interprets pain, and supports
self-evolution under uncertainty.

See: `docs/governance/philosophical-governance-layer.md`

The implementation line for that layer is PGI:

```text
docs/product/philosophical-governance-implementation-roadmap.md
```

## Current Product Wedge: Ordivon Verify

The first externalizable product wedge is **Ordivon Verify** — a local read-only
verification CLI that checks whether AI/agent work can be trusted.

It validates:
- Receipts (claims vs evidence)
- Debt (hidden failures)
- Gates (boundary enforcement)
- Documents (current truth vs staleness)

Status: `READY` means selected checks pass — it does **not** authorize execution.
Alpha-0 tightens this public signal as `READY_WITHOUT_AUTHORIZATION`.

Package: `src/ordivon_verify/` (private prototype, not published).

Run: `uv run python scripts/ordivon_verify.py check .`

## Current External Direction: Alpha-0

Alpha-0 is **Evidence of Governed Work**. The first external use case is AI
coding agent trust audit before teams trust agent output.

Ordivon should not run agents. Ordivon should make agent work trustworthy.

Alpha-0 uses one Verify entry point and one report. It does not create a new
agent framework, CI replacement, GitHub bot, public schema standard, MCP server,
SDK, package release, or adapter platform. Casebook evidence comes before
schema claims.

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
| PV-N2H (Legacy Identity Hygiene) | CLOSED |
| OSS-1 (System Summit) | CLOSED |
| CPR-1/2/3 (Core/Pack Loop Restoration) | CLOSED |
| Alpha-0 (Evidence of Governed Work) | ACTIVE |
| Phase 8 (Live Trading) | DEFERRED |

**pr-fast:** 12/12 PASS. **Registered debt:** 0 open.

## Key Documents

For AI agents onboarding into this project, start here:

| Priority | Document |
|----------|----------|
| 0 | `AGENTS.md` — status header + living docs |
| 1 | `docs/ai/current-phase-boundaries.md` — active/deferred/NO-GO |
| 1 | `docs/ai/agent-output-contract.md` — required output shape |
| 1 | `docs/product/alpha-roadmap.md` — full Alpha roadmap + trust flywheel |
| 1 | `docs/product/alpha-0-evidence-of-governed-work.md` — current external direction |
| 2 | `docs/runtime/alpha-0-casebook.md` — governed work evidence |
| 2 | `docs/architecture/ordivon-core-pack-adapter-ontology.md` — architecture |
| 2 | `docs/architecture/ordivon-moat-and-product-identity.md` — what can't be lost |
| 2 | `docs/architecture/ordivon-companion-governance-constitution.md` — companion governance origin |
| 2 | `docs/governance/philosophical-governance-layer.md` — philosophical operating layer |
| 2 | `docs/product/philosophical-governance-implementation-roadmap.md` — PGI implementation roadmap |
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
