# Current Phase Boundaries

Status: **DOCUMENTED** (Phase 6R)
Date: 2026-04-29
Phase: 6R
Tags: `boundaries`, `phase`, `status`, `allowed`, `forbidden`, `NO-GO`, `ai-onboarding`

## 1. Phase Timeline

| Phase | Status | Key Outcome |
|-------|--------|-------------|
| Phase 1 | COMPLETE | Governance engine POC |
| Phase 2 | COMPLETE | CandidateRule, lessons, Waves 0-5 |
| Phase 3 | COMPLETE | Multi-pack eval framework |
| Phase 4 | COMPLETE | Dependabot + security platform (14 sub-phases) |
| Phase 5 | COMPLETE | Policy Platform (shadow-ready, enforcement-deferred) |
| **Phase 6** | **ACTIVE** | Design Pack, UI Governance, Finance Observation |
| Phase 7 | NOT STARTED | Finance Live Micro-Capital Dogfood |

## 2. Phase 6 Active Areas

### 6A–6C — Design Pack Baseline
- Design Pack contract, Ordivon Application Object, UI Console Inventory
- Design system architecture, token spec, governance component spec
- 60 CSS semantic tokens (`--ordivon-` prefix)
- 10 governance UI components (pure CSS + React)

### 6D–6E — Workbench Surfaces
- `/policy-shadow` — Shadow Policy Workbench (advisory only)
- `/reviews` — Reviews governance upgrade (advisory banners, CandidateRule≠Policy)
- `/design` — Component workbench

### 6F–6G — Finance Observation
- `/finance-prep` — Finance Live Prep UI (observation layer)
- `domains/finance/` — MarketDataSnapshot, AccountSnapshot, ReadOnlyAdapterCapability
- Read-only adapter boundary (write permissions permanently False)

### 6H — Provider Selection (Current)
- Alpaca Paper Trading selected for Phase 6I-6J observation (global, no KYC)
- Polygon.io as backup market data provider
- Phase 7 live: Futu (富途) or Interactive Brokers (盈透) for China operator
- Paper trading first validates governance pipeline at zero risk
- see `docs/runtime/finance-observation-provider-plan.md`

### 6I — Alpaca Paper Adapter (Next)
- Implement `AlpacaObservationProvider` as read-only adapter
- Connect to Alpaca Paper Trading (paper-api.alpaca.markets)
- No order placement, no broker write
- China operator: no region constraint for paper trading

## 3. Absolute NO-GO Boundaries

These are **design-time prohibitions**. No agent may violate them.

| Boundary | Status | Reason |
|----------|--------|--------|
| active_enforced policy | NO-GO | Phase 5 closure decision |
| auto-merge (any PR) | NO-GO | Governance doctrine §3.6 |
| Broker write permissions | NO-GO | Finance Constitution |
| Live order placement | NO-GO | Phase 7 not started |
| Auto trading | NO-GO | Permanently disabled |
| RiskEngine policy integration | NO-GO | Policy platform is advisory only |
| Fake production UI claims | NO-GO | All preview surfaces must be labeled |
| Unlabeled mock data | NO-GO | PreviewDataBanner required |
| PR #7 (React) merge | HOLD | Frontend compatibility not verified |
| Finance real trading | NO-GO | Phase 7 required |
| CandidateRule → Policy without 4 criteria | NO-GO | Doctrine §3.6 |

## 4. Layer-Specific Allow/Deny Matrix

### Backend (Python)
| Action | Allowed? | Notes |
|--------|----------|-------|
| Add pure domain models | YES | No ORM, no DB, no side effects |
| Add state machines | YES | Immutable transitions |
| Add tests | YES | Standard pytest naming |
| Modify governance/risk_engine.py | NO | Governance bypass |
| Add ORM/schema/migration | NO | Unless explicitly justified |
| Add broker/API integration | NO | Phase 7 territory |
| Add Policy activation | NO | Enforcement deferred |

### Frontend (TypeScript/React)
| Action | Allowed? | Notes |
|--------|----------|-------|
| Add governance components | YES | Reuse from governance/index.tsx |
| Add preview surfaces | YES | Must use PreviewDataBanner |
| Add advisory surfaces | YES | Must use AdvisoryBoundaryBanner |
| Enable high-risk actions | NO | Must stay disabled with reason |
| Add new dependencies | AVOID | Pure CSS + React preference |
| Rewrite existing pages | NO | Incremental upgrades only |
| Remove preview/advisory labels | NO | Design contract violation |

### CI / Infrastructure
| Action | Allowed? | Notes |
|--------|----------|-------|
| Add verification scripts | YES | Check architecture boundaries |
| Modify check_architecture.py | YES | Whitelist exemptions |
| Add Dependabot ecosystem | NO | Requires separate phase |
| Modify CI workflow | NO | Unless explicitly scoped |
| Enable auto-merge | NO | Permanently prohibited |

## 5. Policy Platform Status

| State | Status |
|-------|--------|
| draft | Available |
| proposed | Available |
| approved | Available |
| active_shadow | Design-ready, runtime deferred |
| active_enforced | **NO-GO** |
| deprecated | Available |
| rolled_back | Available |
| rejected | Available |

Shadow evaluation is advisory only. No Policy may be activated for enforcement.

## 6. Finance Observation Status

| Capability | Status |
|-----------|--------|
| can_read_market_data | Available (mock only) |
| can_read_account | Available (mock only) |
| can_read_positions | Available (mock only) |
| can_read_fills | Available (mock/manual) |
| can_place_order | **BLOCKED** |
| can_cancel_order | **BLOCKED** |
| can_withdraw | **BLOCKED** |
| can_transfer | **BLOCKED** |

All data sources: MockObservationProvider. No broker connection exists.

## 7. What To Do When Starting a New Task

1. Identify which phase the task belongs to
2. Check this document for active boundaries
3. If touching a forbidden layer, stop and escalate
4. If in allowed territory, proceed with minimal changes
5. Run full verification before completing
6. Produce a receipt per task-prompt-template
