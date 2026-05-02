# Current Phase Boundaries

Status: **DOCUMENTED** (DG-Z stage summit closed)
Date: 2026-05-01
Phase: OGAP-Z
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
| **Phase 7P** | **CLOSED** | Alpaca Paper Dogfood — 24 sub-phases, Stage Summit published |
| **DG-1** | **COMPLETE** | Document Governance Pack — 7 doc files, taxonomy + lifecycle + wiki |
| **DG-1A** | **COMPLETE** | AI Output Contract Middleware — receipt template + verification discipline |
| **DG-1B** | **COMPLETE** | Document Governance Pack Acceptance Seal — commit + tag |
| **DG-2** | **COMPLETE** | Document Registry Prototype + Doc Consistency Checker — 28 entries |
| **DG-3** | **COMPLETE** | Document Staleness Audit + Authority Conflict Review |
| **DG-4** | **COMPLETE** | Staleness Automation + Freshness Checker — 33 tests, semantic scan |
| **DG-5** | **COMPLETE** | Baseline Integration — document checker in pr-fast (8/8 gates) |
| **DG-6** | **COMPLETE** | Wiki Navigation Prototype — registry-derived wiki-index.md |
| **DG-6A** | **COMPLETE** | Core/Pack/Adapter Ontology Consolidation |
| **DG-6A-S** | **COMPLETE** | Ontology Registry Landing + Metadata Checker — 29 entries, 40 tests |
| **DG-6B** | **COMPLETE** | Verification Debt Ledger + Receipt Integrity — 10/10 baseline |
| **DG-6C** | **COMPLETE** | Verification Gate Manifest + Baseline Integrity — 11/11 |
| **DG-6D** | **COMPLETE** | Tooling Residue Triage — VD-002/003 closed |
| **DG-6D-S** | **COMPLETE** | Ruff Debt Clarification — 4 non-DG F401 out-of-scope |
| **DG-Z** | **CLOSED** | Document Governance Pack Stage Summit / Closure |
| **Post-DG-H1** | **CLOSED** | Fix VD-004 manifest test instability (shallow copy bug) |
| **Post-DG-H2-R** | **CLOSED** | Close VD-001 by reclassification (tool_limitation + command_mismatch) |
| **Post-DG-H3** | **CLOSED** | Clean 4 non-DG F401 historical imports from governance tests |
| **PV-1** | **PROPOSAL** | Ordivon Verify CLI product contract (product brief + CLI contract + user journey) |
| **PV-2** | **COMPLETE** | Ordivon Verify CLI skeleton |
| **PV-3** | **COMPLETE** | External fixture dogfood + --root/--config/--mode support |
| **PV-4** | **COMPLETE** | Trust report polish — rich human + JSON output |
| **PV-5** | **ACTIVE** | Agent skill + CI adoption pack |
| **OGAP-1** | **CLOSED** | Protocol semantics + object model |
| **OGAP-2** | **CLOSED** | Schemas + local validator |
| **OGAP-3** | **CLOSED** | Adapter fixture dogfood |
| **HAP-1** | **CLOSED** | Harness Adapter Protocol v0 foundation |
| **ADP-2** | **ACTIVE** | Agentic pattern detection implementation |
| Phase 8 | **DEFERRED** | Manual Live Micro-Capital Dogfood |

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
| OGAP API/SDK/MCP server creation | NO-GO | Protocol foundation only — no implementation opened |
| OGAP public standard claim | NO-GO | v0/prototype, no external adoption |
| OGAP package publishing | NO-GO | No release program opened |
| OGAP public repo creation | NO-GO | Private core, public wedge model |
| OGAP action authorization | NO-GO | Valid payloads do not authorize execution |
| HAP API/SDK/MCP/live adapter creation | NO-GO | HAP-1 is local design/prototype only |
| HAP action authorization | NO-GO | Harness capability ≠ authorization |
| HAP credential access | NO-GO | can_read_credentials is a declaration, not access |
| EGB-1 compliance claim | NO-GO | External benchmarks are reference-only, no certification |
| EGB-1 endorsement claim | NO-GO | No endorsement, partnership, or equivalence claimed |
| Financial/broker/live action via OGAP | NO-GO | NO-GO at schema level |

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

### Document Governance (DG-1 through DG-5)
| Action | Allowed? | Notes |
|--------|----------|-------|
| Run registry checker | YES | uv run python scripts/check_document_registry.py |
| Run pr-fast baseline (includes doc checker) | YES | uv run python scripts/run_verification_baseline.py --profile pr-fast |
| Document registry is hard gate | YES | DG-5 — L6 gate in pr-fast (11/11) |
| Update AI context files | YES | AGENTS.md, docs/ai/*.md |
| Modify trading/execution code | NO | Not in DG scope |
| Activate Policy or RiskEngine rules | NO | Design phase only |
| Enable live trading or broker write | NO | Phase 8 DEFERRED |
| Build Wiki surface | NO | DG-6+ |

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
| `docs/ai/agent-output-contract.md` | Required output contract for every AI task — receipt template + verification discipline |
| `docs/architecture/harness-adapter-protocol-hap-1.md` | HAP v0 protocol architecture |
| `docs/runtime/hap-foundation-hap-1.md` | HAP object model + closure predicate |
| `docs/product/harness-adapter-protocol-stage-notes-hap-1.md` | HAP-1 stage notes |
| `src/ordivon_verify/schemas/hap-*.schema.json` | HAP JSON schemas (3 total) |
| `examples/hap/` | HAP example fixtures (basic + 5 scenarios) |
| `scripts/validate_hap_payload.py` | HAP payload validator |
| `docs/governance/external-ai-governance-benchmark-pack-egb-1.md` | External governance benchmark pack |
| `docs/governance/external-ai-governance-benchmark-matrix-egb-1.md` | External-to-Ordivon concept mapping matrix |
| `docs/governance/external-ai-governance-gap-analysis-egb-1.md` | Gap analysis vs external benchmarks |
| `docs/ai/external-benchmark-reading-guide.md` | EGB-1 AI reading guide |
| `scripts/check_document_registry.py` | Document registry checker — 22 invariants, DG-2 |
| `docs/governance/document-registry.jsonl` | Machine-readable document registry — 17 entries, DG-2 |
