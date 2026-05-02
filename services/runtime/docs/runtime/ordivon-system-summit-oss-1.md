# Ordivon System Summit — OSS-1

Status: **current** | Date: 2026-05-02 | Phase: OSS-1
Tags: `system-summit`, `re-centering`, `architecture`, `core-pack-loop`, `gap-analysis`
Authority: `source_of_truth` | AI Read Priority: 1

## Executive Summary

Ordivon has completed 3 major governance tracks — Action Governance (OGAP/HAP/ADP/GOV-X),
Truth Governance (DG-1), and Exposure Governance (PV) — plus a substantive but partially
dormant Core/Pack/Adapter main loop. The question for OSS-1 is not whether to continue
meta-governance, but how to reconnect supporting governance planes back to the main loop.

**Finding**: Ordivon's Core/Pack main loop is substantively implemented (302 governance tests,
89 domain modules, 18 governance modules, 13 pack modules, 8 adapter modules, 396 product
tests). The loop is partially dormant but real and test-covered. DG/ADP/PV are supporting
planes that strengthen the loop's reliability, not replacements for it.

**Recommendation**: CPR-1 — Core/Pack Governance Loop Restoration. Re-activate the
Intent→Governance→Execution→Receipt→Outcome→Review→Lesson→CandidateRule→Policy loop
using the hardened DG truth substrate and ADP-3 detection as supporting infrastructure.

## Current Phase Chain

| Phase | Status | Commit | Notes |
|-------|--------|--------|-------|
| Phase 1-6 | CLOSED | — | Core Governance, CandidateRules, Eval, Dependabot, Policy, Design/Finance |
| Phase 7P | CLOSED | — | Alpaca Paper Dogfood (3 round trips, 4 refusals, 0 violations) |
| OGAP-Z | CLOSED | — | Protocol foundation |
| HAP-1 | CLOSED | — | Harness Adapter Protocol v0 |
| EGB-1 | CLOSED | — | External Benchmark Pack |
| ADP-1 | CLOSED | — | Agentic Pattern Taxonomy (18 patterns) |
| HAP-2 | CLOSED | — | HAP fixture dogfood with ADP scenarios |
| GOV-X | CLOSED | — | Capability-Scaled Governance |
| ADP-2 | CLOSED | — | Pattern Detector (12 rules) |
| HAP-3 | CLOSED | — | TaskPlan + ReviewRecord objects |
| ADP-2R | CLOSED | 3574039 | Red-team remediation (5/13 fixed) |
| ADP-3 | CLOSED | ebc6714 | Structure + registry + PV + debt-aware (22 rules) |
| ADP-3-S | CLOSED | ef6a549 | ADP-3 seal |
| DG-1 | CLOSED | 4821598 | Truth substrate hardening |
| PV-Z | CLOSED | — | Verify productization Stage Summit |
| PV-N1-N12 | CLOSED | — | Package prototype through release channel policy |
| COV-1R/COV-2 | CLOSED | — | Coverage governance |
| Phase 8 | DEFERRED | — | Manual Live Micro-Capital |
| DG-2 | NOT STARTED | — | Freshness backfill |
| ADP-4 | NOT STARTED | — | Detector precision |
| CPR-1 | RECOMMENDED | — | Core/Pack Loop Restoration |

**Consistency check**: AGENTS.md registers DG-1 as "Next" but DG-1 is now CLOSED.
AGENTS.md needs update to reflect current state and OSS-1 recommendation.

## Canonical Architecture Status

The canonical 10-layer architecture (L0-L10) from `ordivon-current-architecture.md`
maps to real code as follows:

| Layer | Real Code | Maturity | Gaps |
|-------|-----------|----------|------|
| L0 Constitution/Work Grammar | docs/architecture/*, docs/runbooks/* | Documented | No code enforcement |
| L1 Core Control | governance/ (18 .py) | Implemented | approval, decision, feedback, risk_engine all exist |
| L2 Domain State | domains/ (89 .py), state/ (16 .py) | Implemented | 15 domain modules with models + repos + services |
| L3 Pack Platform | packs/ (13 .py) | Implemented | Coding pack (5-gate) + Finance pack (trading discipline) |
| L4 Capability/API | capabilities/ (29 .py), apps/api/ (40 .py) | Implemented | FastAPI backend operational |
| L5 Adapter Platform | adapters/ (8 .py) | Implemented | Alpaca Paper (read-only + paper execution), Hermes runtime |
| L6 Evidence Platform | execution/ (8 .py), docs/runtime/ | Partial | Execution records exist; evidence bundles emerging via HAP |
| L7 Verification | scripts/ (49 scripts), tests/ | Implemented | 12-gate pr-fast, 302 gov tests, ADP detector |
| L8 Learning | domains/journal/, knowledge/ (8 .py) | Implemented | Review, Lesson, CandidateRule extraction |
| L9 Policy | domains/policies/, domains/candidate_rules/ | Partial | CandidateRules advisory; Policy activation NO-GO |
| L10 Product Wedges | src/ordivon_verify/, apps/web/ | Partial | Verify CLI built; web UI exists; no public release |

## Core/Pack/Adapter Main Loop Status

The 10-node governance loop audited against real code:

| Node | Implementation | Tests | Dogfooded | Risk |
|------|---------------|-------|-----------|------|
| Intent | domains/decision_intake/ | ✓ | Phase 7P paper dogfood | Low |
| Context | packs/finance/context.py, adapters/finance/ | ✓ | Paper health check | Low |
| Governance | governance/risk_engine, governance/approval | ✓ | 302 gov tests | Low |
| Execution | execution/, orchestrator/ (16 .py) | ✓ | Paper execution adapter | Low |
| Receipt | domains/execution_records/, agent-output-contract | ✓ | Phase closure receipts | Low |
| Outcome | domains/finance_outcome/, strategy/ | ✓ | Phase 7P paper outcomes | Low |
| Review | governance/review/, domains/journal/ | ✓ | ReviewRecord objects (HAP-3) | Low |
| Lesson | domains/journal/, knowledge/ | ✓ | FeedbackPacket model | Medium — no dogfood loop |
| CandidateRule | domains/candidate_rules/ | ✓ | 3 advisory rules from 7P | Medium — promotion inactive |
| Policy | domains/policies/ | Partial | CandidateRules only | High — activation NO-GO |

**Key finding**: The main loop is substantively implemented. Nodes 1-7 are real code with
tests. Nodes 8-10 have models but lack active dogfood loops. The loop was exercised during
Phase 7P paper dogfood (Alpaca Paper) but has been dormant during DG/ADP/PV meta-governance.

### What the loop currently lacks:

1. **Active dogfood**: The loop was proven in Phase 7P paper trading but hasn't been
   exercised end-to-end since then. CPR-1 should run the loop in a governance-only
   (no-live-action) dogfood cycle.
2. **Lesson→CandidateRule pipeline**: Journal entries exist, feedback models exist,
   but the extraction and promotion pathway has only been exercised manually.
3. **Policy lifecycling**: CandidateRules exist (CR-7P-001/002/003) with promotion
   criteria documented, but promotion has not been exercised.

## Governance Plane Classification

### Truth Governance (DG)
Serves: Core loop nodes 1-3 (Intent, Context, Governance), L0 Constitution

| Artifact | Status | Supports |
|----------|--------|----------|
| document-registry.jsonl (84 entries) | Stable | AI onboarding, ADP detector |
| wiki-index.md | Deterministic | New AI context |
| Classification Index | DG-1 | Doc authority model |
| Authority Model (7 types) | DG-1 | Truth semantics |
| AI Read Path Invariants | DG-1 | New AI correctness |
| Freshness/Supersession | DG-1 | Staleness prevention |
| 14 freshness gaps in L0/L1 | Open | DG-2 |

### Action Governance (OGAP/HAP/ADP/GOV-X)
Serves: Core loop nodes 4-8 (Execution, Receipt, Outcome, Review, Lesson)

| Artifact | Status | Supports |
|----------|--------|----------|
| HAP schemas + validator | CLOSED | TaskPlan, ReviewRecord |
| ADP detector (22 rules) | CLOSED | Governance verification |
| GOV-X gate matrix | CLOSED | C0-C5 risk ladder |
| OGAP protocol | CLOSED | External adapter protocol |

### Exposure Governance (PV)
Serves: Core loop node L10 (Product Wedges)

| Artifact | Status | Supports |
|----------|--------|----------|
| ordivon_verify CLI | Built | Private package prototype |
| PV schemas (5) | Extracted | Public wedge schemas |
| Public packaging boundary | Defined | Private core / public wedge |
| No release, no license, no public repo | Enforced | Boundary integrity |

**Risk assessment**: Truth Governance and Action Governance planes are mature and stable.
Exposure Governance is intentionally gated. None of the three planes has replaced the
Core/Pack main loop — they strengthen it from the sides.

## DG Status Summary

- 84 registry entries, all invariants pass
- 8 entries have last_verified; 6 have stale_after_days
- 21 L1 docs need freshness metadata (7 currently covered by ADP3-DG-STALENESS)
- 20 source_of_truth docs need freshness metadata (6 currently covered)
- Wiki: deterministic (DOC-WIKI-FLAKY-001 accepted_until)
- Debt routing complete (8 debts assigned to owner phases)

## ADP/HAP/GOV-X Status Summary

- ADP detector: 22 rules across structure (8), registry (5), PV (5), debt (1), plus broader PV detection
- Structure-aware: parses HAP-3 TaskPlan/ReviewRecord JSON
- Registry-aware: validates freshness, supersession, degraded lifecycle, receipt authority
- PV-aware: checks release overclaim, wedge collapse, READY-as-approval, package safety, changelog confusion
- Limitations: static only, no semantic understanding, regex-based, no code fence handling

## PV/Ordivon Verify Status Summary

Ordivon Verify is explicitly positioned as:
- Public wedge product (≠ full Ordivon core)
- Local-first CLI
- Prototype/v0 — not released
- READY is evidence, not authorization
- Apache-2.0 license recommended but NOT activated
- No public repo created
- No package published
- No public standard claimed

Current maturity: Private package prototype (PV-N12). Package built, schemas extracted,
public wedge boundary defined. 244 private paths block public publishing.

## Open Debt Register

| Debt ID | Owner | Severity | Impact | Due | Closure |
|---------|-------|----------|--------|-----|---------|
| CODE-FENCE-001 | ADP-4 | Medium | Safe docs flagged | ADP-4 | Code fence exclusion in detector |
| RECEIPT-SCOPE-001 | ADP-4 | Medium | 7 patterns, gaps remain | ADP-4 | Additional HARD_FAILS patterns |
| DOC-WIKI-FLAKY-001 | DG-2 | Low | Wiki flakiness | DG-2 | Currently deterministic; re-verify |
| EGB-SOURCE-FRESHNESS-001 | EGB-2 | Medium | Stale benchmarks | EGB-2 | Periodic source review |
| FRESHNESS-001 | DG-2 | Medium | 14 docs no freshness | DG-2 | Registry backfill |
| PV-N8 244 private paths | PV | High | Blocks public publish | PV-X | Package boundary completion |
| CandidateRule promotion | CPR-1 | Medium | 3 CRs staged | Phase 8 | Requires ≥2 weeks observation |

## Risk Ranking

| Risk | Prob | Impact | Mitigation | Owner |
|------|------|--------|------------|-------|
| R1: Core loop dormancy | HIGH | HIGH | CPR-1 reactivation | CPR-1 |
| R2: current_truth drift | LOW | MED | DG + AGENTS.md sync | OSS-1 |
| R3: Detector overtrust | LOW | HIGH | Explicit disclaimers | ADP-3 |
| R4: PV overclaim | LOW | HIGH | Boundary docs | PV |
| R5: Package boundary | LOW | MED | 244-path blocker | PV |
| R6: Finance NO-GO confusion | LOW | HIGH | Clear AGENTS.md | All |
| R7: Debt permanence | MED | MED | DG-2 routing | DG-2 |

## Re-centering Recommendation

**CPR-1 — Core/Pack Governance Loop Restoration**

The audit evidence supports returning to the Core/Pack main loop, not continuing deeper
into DG-2, ADP-4, or PV productization. The supporting planes (DG, ADP, PV) are mature
enough to serve as infrastructure. The main loop is substantively implemented but dormant.

CPR-1 should:
1. Re-activate the full 10-node loop in a governance-only (no-live-action) dogfood cycle.
2. Use the hardened DG truth substrate for phase documentation.
3. Use ADP-3 detection as pre-commit governance verification.
4. Exercise the Lesson→CandidateRule→Policy pipeline with existing CandidateRules.
5. NOT enable live trading, broker access, or Phase 8.

Rationale: The meta-governance tracks (DG/ADP/PV) have been built precisely to support
the main loop. Continuing to build more meta-governance without exercising the main loop
would compound the dormancy risk (R1). The loop was proven during Phase 7P paper dogfood
and is ready for reactivation.

## Verification Summary

| Checker | Result |
|---------|--------|
| Document registry | 84 entries, all invariants pass |
| Verification debt | Warning (unmanaged debt candidates) |
| Verification manifest | All invariants pass |
| Receipt integrity | 0 hard failures |
| Architecture | Clean |
| Runtime evidence | Verified |
| pr-fast baseline | 12/12 PASS |
| Governance tests | 302 passed |
| Product tests | 396 passed (10 pre-existing failures) |
| Finance tests | 214 passed |
| Ruff format/check | 12 fixable (pre-existing) |
| Frontend | Not in scope |
| DOC-WIKI-FLAKY-001 | Currently deterministic |

## New AI Context Check

A fresh AI reading AGENTS.md, OSS-1 docs, DG docs, ADP/HAP/GOV-X docs, PV docs,
and architecture docs can determine:

- Ordivon is a governance operating system, not a trading bot or AI wrapper.
- The 10-node Core/Pack governance loop is the main product pathway.
- DG/ADP/PV are supporting governance planes, not replacements.
- ADP-3 has 22 detector rules; DG has 84 registry entries.
- Ordivon Verify is a public wedge prototype, not a released product.
- No API, SDK, MCP, package, public repo, or license has been created.
- CandidateRule remains non-binding; Policy activation is NO-GO.
- Financial/broker/live action remains NO-GO. Phase 8 remains DEFERRED.
- Detector PASS is not authorization. No findings is not safety proof.
- Next recommended: CPR-1 — Core/Pack Governance Loop Restoration.
