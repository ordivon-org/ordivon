# Current Phase Boundaries

Status: **DOCUMENTED** (Phase 6R, updated 6L)
Date: 2026-04-29
Phase: 6R
Tags: `boundaries`, `phase`, `status`, `allowed`, `forbidden`, `NO-GO`, `ai-onboarding`

## 1. Phase Timeline

| Phase | Status | Key Outcome |
|-------|--------|-------------|
| Phase 1 | COMPLETE | Core Governance Engine |
| Phase 2 | COMPLETE | CandidateRule, Lessons, Waves 0-5 |
| Phase 3 | COMPLETE | Multi-pack Eval Framework |
| Phase 4 | COMPLETE | Dependabot + Security Platform (14 sub-phases) |
| Phase 5 | COMPLETE | Policy Platform (shadow-ready, enforcement-deferred) |
| Phase 6 | COMPLETE | Design Pack, UI Governance, Finance Observation (16 sub-phases) |
| Phase 7P-3 | COMPLETE | First Supervised Paper Trade (entry + fill captured) |
| **Phase 7P-Z** | **ACTIVE** | Paper Dogfood Review (round trip closed, formal review done) |
| Phase 8 | **DEFERRED** | $100 Manual Live Micro-Capital Dogfood (real money) |

## 2. Corrected Phase 7 Path

Phase 7 is now routed through **Alpaca Paper Trading** before any real-money live experiment.

| Phase 7P Sub-Phase | Description | Key Constraint |
|-------------------|-------------|----------------|
| 7P-1 | Alpaca Paper Trading Constitution | Paper only, no real money |
| 7P-2 | Alpaca Paper Execution Adapter | MUST be separate from ReadOnlyAdapterCapability |
| 7P-3 | First Supervised Paper Trade | Paper API, no broker write |
| 7P-Z | Paper Dogfood Review | CandidateRule only, no Policy activation |

## 2. Phase 6 Sub-Phase Status

| Sub-Phase | Status | Key Deliverable |
|-----------|--------|-----------------|
| 6A–6C | ✅ COMPLETE | Design Pack baseline, semantic tokens, 10 governance components |
| 6D | ✅ COMPLETE | Shadow Policy Workbench `/policy-shadow` |
| 6E | ✅ COMPLETE | Reviews + CandidateRule governance workbench upgrade |
| 6F | ✅ COMPLETE | `/finance-prep` initial UI (constitution, risk budget, intake, receipt) |
| 6G | ✅ COMPLETE | Finance observation domain models + ReadOnlyAdapterCapability |
| 6H | ✅ COMPLETE | Provider selection plan (Alpaca Paper primary, Futu/IB for live) |
| 6I | ✅ COMPLETE | `AlpacaObservationProvider` (paper, read-only, GET only) |
| 6I-S | ✅ COMPLETE | Verification baseline recovery (stdout/stderr separation) |
| 6J | ✅ COMPLETE | `/finance-prep` observation integration (Alpaca Paper labels) |
| 6J-S | ✅ COMPLETE | Provider status semantics (configured vs connected, account mask) |
| 6K | ✅ COMPLETE | Server-side health snapshot (`GET /health/finance-observation`) |
| 6L | ✅ COMPLETE | `/finance-prep` live health fetch + exposure guard |

## 3. Absolute NO-GO Boundaries

These are **design-time prohibitions**. No agent may violate them.

| Boundary | Status | Reason |
|----------|--------|--------|
| active_enforced policy | NO-GO | Phase 5 closure decision |
| auto-merge (any PR) | NO-GO | Governance doctrine §3.6 |
| Broker write permissions | NO-GO | Frozen ReadOnlyAdapterCapability |
| Live order placement | NO-GO | Phase 7 not started |
| Auto trading | NO-GO | Permanently disabled |
| RiskEngine policy integration | NO-GO | Policy platform is advisory only |
| Fake production UI claims | NO-GO | All preview surfaces labeled |
| Unlabeled mock data | NO-GO | PreviewDataBanner required |
| PR #7 (React) merge | HOLD | Frontend compatibility not verified |
| Finance real trading | NO-GO | Phase 7 required |
| CandidateRule → Policy without 4 criteria | NO-GO | Doctrine §3.6 |

## 4. Finance Observation Status

| Capability | Status | Where |
|-----------|--------|-------|
| can_read_market_data | ✅ READ (Alpaca Paper) | `AlpacaObservationProvider._data_get()` |
| can_read_account | ✅ READ (Alpaca Paper) | `AlpacaObservationProvider._get("/v2/account")` |
| can_read_positions | ✅ READ (Alpaca Paper) | `AlpacaObservationProvider._get("/v2/positions")` |
| can_read_fills | ✅ READ (Alpaca Paper) | `AlpacaObservationProvider._get("/v2/orders")` |
| can_place_order | ❌ BLOCKED | Frozen capability + `_request()` GET-only guard |
| can_cancel_order | ❌ BLOCKED | Frozen capability |
| can_withdraw | ❌ BLOCKED | Frozen capability |
| can_transfer | ❌ BLOCKED | Frozen capability |
| Health endpoint | ✅ `GET /health/finance-observation` | Server-side, redacted |
| Frontend health | ✅ `/finance-prep` fetches health | Loading/error/connected/degraded/unavailable |

## 5. Layer-Specific Allow/Deny Matrix

### Backend (Python)
| Action | Allowed? | Notes |
|--------|----------|-------|
| Add pure domain models | YES | No ORM, no DB, no side effects |
| Add adapters (read-only) | YES | Must implement ObservationProvider Protocol |
| Add API routes (read-only) | YES | Must redact secrets |
| Modify governance/risk_engine.py | NO | Governance bypass |
| Add broker/API integration with writes | NO | Phase 7 territory |
| Add Policy activation | NO | Enforcement deferred |

### Frontend (TypeScript/React)
| Action | Allowed? | Notes |
|--------|----------|-------|
| Add governance components | YES | Reuse from governance/index.tsx |
| Fetch read-only health endpoints | YES | `/health/finance-observation` |
| Display observation data | YES | Masked, no secrets |
| Enable high-risk actions | NO | Must stay disabled with reason |
| Add new dependencies | AVOID | Pure CSS + React preference |

## 6. Key Files Reference

| File | What It Is |
|------|-----------|
| `adapters/finance/__init__.py` | `AlpacaObservationProvider` — paper, GET-only, 4 safety guards |
| `adapters/finance/health.py` | `get_alpaca_health_snapshot()` — redacted health check |
| `domains/finance/__init__.py` | Observation models (MarketDataSnapshot, AccountSnapshot, etc.) |
| `domains/finance/read_only_adapter.py` | `ReadOnlyAdapterCapability` (frozen, write=False) |
| `apps/api/app/routers/health.py` | `GET /health/finance-observation` endpoint |
| `apps/web/src/app/finance-prep/page.tsx` | Finance prep UI with live health fetch |
| `apps/web/src/components/governance/index.tsx` | All governance UI components |
| `docs/runtime/finance-observation-provider-plan.md` | Provider selection + China operator notes |
