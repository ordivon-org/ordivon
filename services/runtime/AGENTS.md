# Ordivon — AI Agent Entry Point

Ordivon is a **governance operating system**, not a trading bot, AI wrapper, or generic dashboard.

## Quick Navigation

```
docs/ai/README.md                          ← AI onboarding index
docs/ai/ordivon-root-context.md            ← What Ordivon is + governance doctrine
docs/ai/architecture-file-map.md           ← Where everything lives
docs/ai/current-phase-boundaries.md        ← What's allowed, what's NO-GO
docs/ai/agent-working-rules.md             ← How to operate (verification, receipt, self-check)
docs/ai/task-prompt-template.md            ← Compressed phase prompt format

docs/runbooks/ordivon-agent-operating-doctrine.md  ← Full canonical doctrine
```

## Critical Rules (Read Before Editing)

1. **Evidence before belief** — verify, don't assume
2. **Fresh > stale** — check timestamps on all evidence
3. **Actor identity from metadata** — `pr.user.login`, never title/body
4. **CandidateRule ≠ Policy** — advisory ≠ enforcement
5. **No auto-merge ever** — governance violation
6. **High-risk actions disabled** — Place Live Order, Broker API, Auto Trading
7. **Label all previews** — PreviewDataBanner required for mock data
8. **uv + pnpm** — never pip / npm

## Active Phase

Phase 1–6 — **COMPLETE** (Core, Repo Governance, Security, Policy, Design, Finance Observation)
Phase 7A-R — Roadmap Correction — **ACTIVE** (docs only)
  → Alpaca Paper is the next dogfood stage, not live trading.
  → The $100 live constitution is a future draft, not active authorization.

## Corrected Roadmap

| Phase | Stage | Status | Key Constraint |
|-------|-------|--------|----------------|
| 7A-R | Boundary correction | **ACTIVE** | Docs only |
| 7P-1 | Alpaca Paper Trading Constitution | Next | Paper only, no real money |
| 7P-2 | Alpaca Paper Execution Adapter | Planned | Separate from ReadOnlyAdapterCapability |
| 7P-3 | First Supervised Paper Trade | Planned | Paper API, no broker write |
| 7P-Z | Paper Dogfood Review | Planned | CandidateRule only |
| 8 | $100 Manual Live Micro-Capital Dogfood | **DEFERRED** | Real money, manual only, no API orders |

**Critical**: Real-money live trading has NOT started. Phase 7P tests paper execution only.
The $100 live constitution exists as a draft but is not active authorization.
Live broker write / API order placement remains NO-GO.

## Finance Observation Status

| Component | Status |
|-----------|--------|
| Observation domain models | ✅ Phase 6G |
| ReadOnlyAdapterCapability | ✅ Phase 6G |
| Provider selection (Alpaca + Futu/IB) | ✅ Phase 6H |
| AlpacaObservationProvider | ✅ Phase 6I |
| Health snapshot (server-side) | ✅ Phase 6K |
| /finance-prep health integration | ✅ Phase 6L |
| Live Alpaca API calls | ✅ Via /health/finance-observation (read-only GET) |
| Order placement | ❌ BLOCKED (frozen capability) |
| Broker write | ❌ BLOCKED |
| Live real-money trading | ❌ Phase 7 |

## Tool Truth

| Language | Use |
|----------|-----|
| Python | `uv run`, `uv run python`, `uv run python -m pytest` |
| Node | `pnpm`, `pnpm test`, `pnpm build` |

## Before Committing

```bash
cd apps/web && pnpm test -- --run && pnpm build
uv run python -m pytest tests/unit/ -q
uv run python evals/run_evals.py
uv run python scripts/run_verification_baseline.py --profile pr-fast
uv run ruff format --check docs && uv run ruff check docs
```
