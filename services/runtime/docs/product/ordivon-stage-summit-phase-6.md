# Design + Finance Observation — Stage Summit (Phase 6 Close)

Status: **PUBLISHED** (Phase 6Z)
Date: 2026-04-29
Phase: 6Z
Tags: `stage-summit`, `closure`, `design`, `finance`, `observation`, `alpaca`, `ui`, `phase-7-ready`

## 1. Executive Summary

Phase 6 has built the Ordivon Design Pack, UI Governance surface, and Finance
Observation layer from zero to a running, tested, red-team-verified state. It
can render governance components, display CandidateRule≠Policy boundaries,
connect to Alpaca Paper Trading in read-only mode, and expose a redacted health
snapshot to a frontend that never calls the broker directly.

Phase 6 has NOT enabled any live trading, broker write, order placement, or
active policy enforcement.

**Key numbers**: 16 sub-phases, 20+ new files (domains, adapters, frontend, docs),
76 finance tests, 57 frontend tests, 810 total unit tests, 6 Alpaca safety guards,
7 hard gates passing, 4 Alpaca write capabilities permanently blocked.

**Key decision**: Phase 7A may begin as Manual Live Micro-Capital Constitution +
Dogfood Plan only. Real-money execution must be manual. Broker API must remain read-only.
active_enforced remains NO-GO. auto-merge remains NO-GO.

## 2. Phase 6 Timeline

| Phase | Description | Key Artifact | Tests | Outcome |
|-------|-------------|-------------|-------|---------|
| 6A | Design Pack + App Object | `docs/design/design-pack-contract.md` | — | 15 governance objects defined |
| 6B | Design System Architecture | `docs/design/design-system-architecture.md` | — | 6-layer architecture, 8 ADRs |
| 6C | Runtime Baseline + Components | `components/governance/index.tsx` | — | 10 governance components, 60 tokens |
| 6D | Shadow Policy Workbench | `/policy-shadow` | — | Advisory-only surface |
| 6E | Reviews + CR Workbench | `/reviews` | 39 | Advisory banners, CR≠Policy |
| 6F | Finance Prep UI | `/finance-prep` | 11 | Preview surface, 9 UI sections |
| 6G | Finance Observation Models | `domains/finance/__init__.py` | 47 | 6 data models, ReadOnlyAdapterCapability |
| 6H | Provider Selection | `docs/runtime/finance-observation-provider-plan.md` | — | Alpaca primary, Futu/IB for live |
| 6I | Alpaca Paper Provider | `adapters/finance/__init__.py` | 31 | 4 safety guards, GET-only |
| 6I-S | Baseline Recovery | `scripts/run_verification_baseline.py` | — | stdout/stderr parse fix |
| 6J | Finance Prep Integration | `/finance-prep` (updated) | 57 | Alpaca Paper labels, provider banner |
| 6J-S | Provider Semantics Seal | `/finance-prep` (patched) | 59 | "configured" vs "connected", account mask |
| 6K | Health Snapshot | `adapters/finance/health.py` | 14 | `GET /health/finance-observation` |
| 6L | Runtime Health Integration | `/finance-prep` (live fetch) | 57 | useEffect fetch, 5 states |
| 6L-S | Exposure Boundary Seal | `docs/runtime/...plan.md` §13 | — | Paper-only guarantees documented |
| 6R | AI Root Context Pack | `AGENTS.md`, `docs/ai/` (7 files) | — | Agent onboarding for fresh context |
| **6Z** | **Stage Closure** | This document | — | Phase 6 complete |

## 3. What Phase 6 Proved

### 3.1 Design can be governed as a Pack

```
DesignIntent → DesignBrief → DesignDecision → DesignReceipt
  → Review → Lesson → CandidateRule → PolicyProposal (advisory)
```

The Design Pack contract treats UI decisions as governed objects with the same
intake → governance → review → lesson lifecycle as Finance and Coding. No
design change bypasses governance.

### 3.2 Governance UI semantics are implementable and testable

10 components (Phase 6C) + 6 additional (Phases 6E-6L) implement all specified
governance semantics: EvidenceFreshnessBadge, ActorIdentityBadge, PolicyStateBadge,
ShadowVerdictBadge, AdvisoryBoundaryBanner, PreviewDataBanner, DisabledHighRiskAction,
CandidateRuleStatusLabel, ProviderStatusBanner, ObservationSourcePanel, and more.
All are pure CSS + React, no external dependencies.

### 3.3 Shadow / advisory / preview states are visually enforced

- "ADVISORY ONLY — NOT A GOVERNANCE DECISION" on all shadow surfaces
- "PREVIEW — NOT PRODUCTION" on all preview surfaces
- "CandidateRule ≠ Policy" on all knowledge/candidate-rule surfaces
- High-risk actions permanently disabled with governance reasons
- active_enforced shown as "NOT AVAILABLE (Phase 5 NO-GO)"

### 3.4 Finance Observation reaches server-side Alpaca Paper read-only

The path:
```
/finance-prep (browser)
  → GET /health/finance-observation (API, server-side)
    → AlpacaObservationProvider (paper-api.alpaca.markets, GET only)
      → AccountSnapshot, MarketDataSnapshot
    → Redacted response (masked ID, no secrets)
  → ProviderStatusBanner + ObservationSourcePanel + AdapterCapabilityTable
```

This entire chain was implemented, tested, and verified with real Alpaca Paper
API keys. The frontend never calls Alpaca directly. All broker communication
is server-side only, through the health endpoint.

### 3.5 Paper / read-only status is displayed without secret exposure

- Account ID masked server-side (PA37AKH0E5AT → PA37****E5AT)
- API keys read from `.env` only, never in any response
- write_capabilities always `[]`
- environment always `"paper"`
- No raw key patterns in rendered HTML (verified by tests)

### 3.6 AI agents can onboard through AGENTS.md + docs/ai

The AI Root Context Pack (Phase 6R, updated through 6L) provides:
- 7 files covering identity, architecture, file map, boundaries, working rules, prompt template
- `AGENTS.md` at repo root — 30-second entry point
- Updated to reflect Phase 6A–6L completion
- A fresh AI agent reading AGENTS.md can immediately understand current status

## 4. What Phase 6 Did NOT Do

| Action | Status |
|--------|--------|
| Live trading | ❌ NOT DONE |
| Broker write permission | ❌ NOT DONE (frozen False) |
| Order placement | ❌ NOT DONE (GET-only guard) |
| Cancel / withdraw / transfer | ❌ NOT DONE |
| active_enforced policy | ❌ NOT DONE (Phase 5 NO-GO) |
| RiskEngine policy integration | ❌ NOT DONE |
| Auto-merge | ❌ NOT DONE |
| Finance execution with real money | ❌ NOT DONE |
| Live brokerage connection | ❌ NOT DONE (paper only) |
| Futu/IB adapter implementation | ❌ NOT DONE (decision deferred) |
| WebSocket streaming | ❌ NOT DONE |
| Historical data pipeline | ❌ NOT DONE |

## 5. Finance Observation Red-Team Results

See `docs/runtime/finance-observation-red-team-closure.md` for full report.
Summary of 10 vectors:

| # | Vector | Status |
|---|--------|--------|
| 1 | Paper equity mistaken as real money | CLEARED — "paper" environment, disclaimers |
| 2 | Health endpoint mistaken as broker control plane | CLEARED — No POST/PATCH/DELETE |
| 3 | Provider connected mistaken as trade-enabled | CLEARED — BLOCKED capabilities displayed |
| 4 | Account alias exposure | CLEARED — masked server-side |
| 5 | Secret exposure | CLEARED — 3-layer defense |
| 6 | Stale data shown as current | CLEARED — freshness computed |
| 7 | Browser directly calling broker | CLEARED — all calls server-side |
| 8 | write_capabilities becoming non-empty | CLEARED — frozen dataclass |
| 9 | Future live endpoint lacking auth | DOCUMENTED — must require auth |
| 10 | UI action implying order placement | CLEARED — no order buttons |

## 6. AI Context Check

A fresh AI agent reading `AGENTS.md` + `docs/ai/README.md` → boundary docs will see:

- Ordivon identity: ✅ governance OS, not trading bot
- Phase 6A–6L: ✅ listed with statuses
- Paper / read-only / no-live boundaries: ✅ clear
- Key files reference: ✅ table with paths
- Finance Observation capabilities: ✅ 4 READ / 4 BLOCKED matrix
- Next steps: ✅ Phase 7A defined

**Verdict**: AI context is current and sufficient. A new agent can onboard without
external briefing.

## 7. Phase 7 Go / No-Go Decision

**Phase 7A may begin** with the following constraints:

### Allowed
- $100 micro-capital constitution document
- Manual execution only workflow design
- Pre-trade intake / plan receipt / outcome capture / review templates
- Alpaca Paper may continue as paper observation
- No new provider integration

### Forbidden
- No live order placement via API
- No broker write integration
- No automated trading
- No leverage / margin / derivatives
- No active policy activation
- No RiskEngine behavioral changes
- No dependency / lockfile changes

### China Operator Note
- Alpaca Paper is globally available (no KYC) — continues through Phase 7
- Live brokerage (Futu or IB) selection remains deferred to Phase 7
- Paper observation is the canonical observation path until live broker is selected

## 8. Recommended Phase 7A Scope

**Phase 7A — Manual Live Micro-Capital Constitution + Dogfood Plan**

- Define $100 micro-capital constitution
- Manual execution workflow (no API orders)
- Max loss: $50 hard stop
- Max per-trade risk: $5 (5% of capital)
- No leverage, no margin, no derivatives
- Mandatory pre-trade intake
- Mandatory plan receipt
- Mandatory outcome capture (entry, exit, fees, slippage, rule-check)
- Mandatory post-trade review
- CandidateRule only — no policy activation
- Read-only Alpaca Paper observation continues

### Boundaries
- No broker API integration
- No live order via API
- No active policy
- No RiskEngine changes

## 9. Key Numbers

| Metric | Value |
|--------|-------|
| Sub-phases completed | 16 (6A through 6L + 6R + 6Z) |
| New source files | 20+ (domains, adapters, frontend, docs) |
| Finance backend tests | 76 |
| Frontend tests | 57 |
| Total unit tests | 810 |
| Eval corpus | 24/24 PASS |
| Alpaca safety guards | 6 (keys, paper flag, paper URL, key prefix, HTTP method, frozen capability) |
| Alpaca write capabilities | 4, all permanently BLOCKED |
| Health endpoint response | Redacted (masked ID, no secrets, paper only) |
| AI onboarding files | 7 (AGENTS.md + 6 docs/ai/) |

## 10. Phase 6 Key Files

| File | What It Is |
|------|-----------|
| `domains/finance/__init__.py` | Observation domain models |
| `domains/finance/read_only_adapter.py` | ReadOnlyAdapterCapability (frozen, write=False) |
| `adapters/finance/__init__.py` | AlpacaObservationProvider (6 guards, GET-only) |
| `adapters/finance/health.py` | get_alpaca_health_snapshot() |
| `apps/api/app/routers/health.py` | GET /health/finance-observation |
| `apps/web/src/components/governance/index.tsx` | 16 governance UI components |
| `apps/web/src/app/finance-prep/page.tsx` | Finance prep with live health fetch |
| `apps/web/src/app/policy-shadow/page.tsx` | Shadow Policy Workbench |
| `docs/runtime/finance-observation-provider-plan.md` | Provider selection + exposure boundary |
| `docs/design/design-pack-contract.md` | Design Pack governance objects |
| `AGENTS.md` | AI agent root entry point |
