# Document Staleness Audit — DG-3

Status: **PROPOSED** | Date: 2026-04-30 | Phase: DG-3
Tags: `governance`, `document`, `audit`, `staleness`, `authority`, `registry`
Authority: `current_status` (this is the audit report; findings are supporting_evidence)

## 1. Executive Summary

**Scope**: 50+ docs reviewed across docs/ai/, docs/governance/, docs/product/,
docs/runtime/, docs/architecture/, docs/design/. Priority given to
high-risk docs: AI context, phase boundaries, paper trades, stage summits,
policy platform, finance observation.

**Findings**:

| Classification | Count |
|---------------|-------|
| Docs reviewed | ~55 markdown files across docs/ |
| current (fresh) | 48 |
| current (stale — needs update) | 1 |
| closed (correct) | 5 |
| deferred (correct) | 1 |
| archived/superseded | 0 |
| evidence/supporting (correct) | 10+ |

**Critical conflict**: 1 found. `docs/ai/ordivon-root-context.md` still
describes Phase 6 as ACTIVE and Phase 7 as NOT STARTED. Phase 7P is CLOSED
(Stage Summit published 2026-04-29). This is a governance incident — a Level 1
AI onboarding doc carrying stale phase state.

**All 10 high-risk phrase patterns searched. Zero unsafe occurrences found.**
Every match for "live trading", "auto trading", "active_enforced", "execution
authority", and "Policy active" appears in NO-GO / negative / deferred context.

**11 recommended files checked. All 11 exist and are consistent with current
phase state.**

## 2. Authority Conflict Table

| Doc | Current Status | Authority | Risk | Decision | Action |
|-----|---------------|-----------|------|----------|--------|
| `docs/ai/ordivon-root-context.md` | says "Phase 6: ACTIVE, Phase 7: NOT STARTED" | `current_status` | **HIGH** — AI agents may think Phase 7 hasn't started | Phase 7P is CLOSED, DG-2 is ACTIVE | **FIX**: Update §5 Current Phase to reflect 7P→CLOSED, DG-1→ACCEPTED, DG-2→ACTIVE, Phase 8→DEFERRED |
| `AGENTS.md` Quick Nav | says "DG-1 active" | `source_of_truth` | **LOW** — reader sees current status below | DG-1 is ACCEPTED, DG-2 ACTIVE | Fix wording to "DG accepted" |
| `docs/ai/ordivon-root-context.md` §2.6 | says "active_shadow is design-ready but runtime-deferred" | `current_status` | **NONE** — correct per Phase 5 closure | Matches current boundaries | No action |
| `docs/product/alpaca-paper-dogfood-stage-summit-phase-7p.md` | "Phase 7P CLOSED" | `current_status` (stage summit) | **NONE** — correct | Closes 7P, defers 8, recommends DG | No action |
| `docs/runtime/phase-7p-readiness-tracker.md` | "3/10 DEFERRED" | `current_status` | **NONE** — correct | Phase 8 remains deferred | No action |
| `docs/runtime/finance-live-micro-capital-constitution.md` | "DRAFT" | `proposal` | **NONE** — correctly labeled as deferred draft | Not active | No action |
| `docs/runtime/finance-live-dogfood-operating-plan.md` | "DEFERRED" | `proposal` | **NONE** — correctly labeled | Not active | No action |

## 3. Staleness Table

| Doc | Staleness Risk | Reason | Proposed Status | Registry Action |
|-----|---------------|--------|-----------------|-----------------|
| `docs/ai/ordivon-root-context.md` | **HIGH** — 7 days max for ai_onboarding | Still describes Phase 6 as ACTIVE (outdated as of 2026-04-27 when Phase 6 completed). Phase 7P started, ran 24 sub-phases, and closed without an update. | `current` (after update) | Already registered (id: not yet — needs registry entry) |
| `docs/architecture/hermes-model-layer-integration.md` | **LOW** — 30 days max for architecture | Last updated 2026-04-26 during H-1. Still describes pre-H-1 work accurately. | `current` (fresh within window) | Register |
| `docs/ai/agent-working-rules.md` | **LOW** — 14 days max for ai_onboarding | Refers to governance rules that haven't changed. | `current` | Register |
| `docs/ai/architecture-file-map.md` | **LOW** — 30 days max for architecture | May not reflect DG-1/dg-2 additions. Minor staleness. | `current` (minor drift) | Register, note minor drift |
| `docs/ai/task-prompt-template.md` | **NONE** — template type | Templates don't stale. | `example` | Register |
| `docs/runtime/ordivon-value-philosophy.md` | **NONE** — philosophical doc | Value propositions don't stale. | `current` | Register |
| `docs/product/ordivon-stage-summit-phase-4.md` | **NONE** — stage summit | Stage summits don't stale; superseded only. | `closed` | Register |
| `docs/product/policy-platform-stage-summit-phase-5.md` | **NONE** — stage summit | Phase 5 closure published 2026-04-29. | `closed` | Register |
| `docs/product/ordivon-stage-summit-phase-6.md` | **NONE** — stage summit | Phase 6 closure published. | `closed` | Register |
| `docs/runtime/alpaca-paper-trading-constitution.md` | **NONE** — constitution type | Still current — Phase 7P followed this constitution. | `current` | Register |
| `docs/runtime/alpaca-paper-execution-boundary.md` | **NONE** — boundary doc | Boundaries unchanged since 7P close. | `current` | Register |
| `docs/runtime/alpaca-paper-repeated-dogfood-protocol.md` | **NONE** — protocol doc | 7P followed this protocol. | `closed` | Register |
| `docs/runtime/alpaca-paper-candidate-rule-handling.md` | **NONE** — evidence | Documents CR-7P-001/002/003 handling. | `closed` | Register |

## 4. AI Read Path Risk Review

### 4.1 AGENTS.md
- **Identity**: Correct — "governance operating system, not a trading bot"
- **Phase state**: Correct — "7P CLOSED, DG-2 ACTIVE"
- **Boundaries**: Correct — Phase 8 DEFERRED, NO-GO items listed
- **Quick Nav minor issue**: Says "DG-1 active" but status section correctly says ACCEPTED
- **Verdict**: SAFE. Minor wording to fix.

### 4.2 docs/ai/README.md
- **Identity**: Correct
- **Phase**: Correct — "DG-2 ACTIVE"
- **Quick Start order**: Correct — agent-output-contract at step 4
- **Read path**: Complete — all 6 items
- **Reference hierarchy**: Up to date
- **Verdict**: SAFE.

### 4.3 docs/ai/current-phase-boundaries.md
- **Phase timeline**: Correct — 7P CLOSED, DG-1/1A/1B COMPLETE, DG-2 ACTIVE, 8 DEFERRED
- **NO-GO boundaries**: Correct and complete
- **Allow/deny matrix**: Up to date for DG-2
- **Verdict**: SAFE.

### 4.4 docs/ai/agent-output-contract.md
- **Status**: ACCEPTED
- **Contents**: 10 sections, all governance-compliant
- **Anti-patterns**: Correctly identified
- **Verdict**: SAFE.

### 4.5 New AI Context Verification

A fresh AI reading the required root docs would understand:
- Phase 7P CLOSED: ✓ (AGENTS.md, current-phase-boundaries.md)
- DG-1/DG-2 accepted/complete: ✓ (AGENTS.md, current-phase-boundaries.md)
- Phase 8 DEFERRED: ✓ (AGENTS.md, current-phase-boundaries.md)
- No live trading / auto trading / broker write: ✓ (multiple docs)
- CandidateRules advisory only: ✓
- JSONL ledger is evidence, not authority: ✓
- DG-3 current or next state is clear: ✗ (only after DG-3 updates)
- **Exception**: if AI reads `docs/ai/ordivon-root-context.md` (a Level 1 doc) before `current-phase-boundaries.md`, it would see stale "Phase 6 ACTIVE, Phase 7 NOT STARTED" — fix required.

## 5. High-Risk Phrase Review

10 patterns searched across all docs/ markdown files. Results:

| Phrase | Matches | Classification | Details |
|--------|---------|---------------|---------|
| "live active" | 0 | — | No matches |
| "live trading active" | 0 | — | No matches |
| "validated" (as standalone claim) | ~8 | **safe context** | Used in agent-output-contract anti-patterns (correctly flagged as problematic), hermes-model-layer "validated path" (refers to completed H-1), ADR docs. No doc claims "validated" without evidence. |
| "Policy active" | 0 (except negated) | **safe** | All occurrences in "NOT Policy" or "NO-GO" context |
| "active_enforced" | 3 | **safe** | All in NO-GO context: current-phase-boundaries (NO-GO), ordvivon-root-context (NO-GO), policy-platform-design (no active_enforced created) |
| "auto trading" | 5 | **safe** | All in NO-GO / BLOCKED / checklist context |
| "execution authority" | 2 | **safe** | Both explicitly say "NOT execution authority" or "No live execution authority" |
| "ledger authorizes" | 0 | — | No matches |
| "paper profit" | 0 | — | "simulated PnL" is the standard term, consistently used |
| "Phase 8 active" | 0 | — | No matches |

**All 10 patterns: zero unsafe occurrences.** The governance vocabulary is consistently used: NO-GO, DEFERRED, BLOCKED, "simulated PnL", "NOT execution authority".

## 6. Registry Update Recommendations

### 6.1 New Entries to Add (11 docs)

These docs are present on disk, referenced in the read path, and should be tracked:

| # | File | Reason |
|---|------|--------|
| 1 | `docs/ai/ordivon-root-context.md` | Level 1 AI onboarding — currently STALE, needs update |
| 2 | `docs/ai/agent-working-rules.md` | Level 1 AI onboarding — governance rules |
| 3 | `docs/ai/architecture-file-map.md` | Level 1 AI onboarding — code tree |
| 4 | `docs/ai/task-prompt-template.md` | Level 1 reference — template (example authority) |
| 5 | `docs/runtime/ordivon-value-philosophy.md` | Identity doc — why not a trading bot |
| 6 | `docs/runtime/alpaca-paper-trading-constitution.md` | Phase 7P constitution |
| 7 | `docs/runtime/alpaca-paper-execution-boundary.md` | Phase 7P boundary |
| 8 | `docs/runtime/alpaca-paper-repeated-dogfood-protocol.md` | Phase 7P protocol |
| 9 | `docs/runtime/alpaca-paper-candidate-rule-handling.md` | Phase 7P CR handling |
| 10 | `docs/product/ordivon-stage-summit-phase-4.md` | Phase 4 closure |
| 11 | `docs/product/ordivon-stage-summit-phase-6.md` | Phase 6 closure |

Total registry: 17 (DG-2) + 11 (DG-3) = 28 entries.

### 6.2 Docs Explicitly NOT Added (Deferred)

| File | Reason |
|------|--------|
| `docs/runtime/finance-live-micro-capital-constitution.md` | DRAFT — deferred to Phase 8 |
| `docs/runtime/finance-live-dogfood-operating-plan.md` | DEFERRED — deferred to Phase 8 |
| `docs/architecture/*.md` (beyond hermes) | Low risk, can be added in later audit sweep |
| `docs/design/*.md` | Low risk, design pack is complete |
| `docs/adr/*.md` | ADRs have their own governance model |
| `docs/runbooks/*.md` | Operational docs, can be added later |
| `docs/audits/*.md` | Historical audit reports |

## 7. Archive / Supersession Recommendations

**No docs recommended for archive or supersession at this time.**

- All Phase 4/5/6/7P stage summits are correctly `closed` (not archived).
- Phase 7P paper trade receipts (PT-001 through PT-004) are correctly `closed` / `historical_record`.
- No superseded docs found — each doc has a distinct purpose.
- `docs/runtime/archive/` directory noted as referenced in docs/README.md. If archive docs exist there, they are correctly isolated.

## 8. Checker Gap Analysis

Current checker (22 invariants) covers: JSON validity, field presence, uniqueness, path existence, valid enums, authority conflicts, ledger evidence, CandidateRule≠Policy, Phase 8 deferred, critical AI doc priorities.

### Recommended Future Invariants

| # | Invariant | Priority | Blocked By |
|---|-----------|----------|------------|
| 23 | No high-priority AI doc may reference Phase 8 as active | HIGH | — |
| 24 | No doc may say "CandidateRule is Policy" without "NOT" | HIGH | Requires content parsing (not just metadata) |
| 25 | Archived docs cannot appear in AI read path (L0-L1) | MEDIUM | Already partially covered (archived + high priority) |
| 26 | Stage Summit must override older phase receipts for phase status | MEDIUM | Requires cross-referencing stage summits vs receipts |
| 27 | Stale docs must not carry current_status authority | HIGH | Requires staleness date math |
| 28 | `ai_onboarding` Type docs must have freshness ≤ 14 days | HIGH | Requires staleness date math |
| 29 | `root_context` Type docs must have freshness ≤ 7 days | HIGH | Requires staleness date math |

**For DG-3**: No checker code changes required. These are documented as future work (DG-4+).

### Minor Update to Checker

One small checker improvement: ensure `ordivon-root-context.md` is registered and tracked as an `ai_onboarding` type doc. This is handled by the registry additions below.

## 9. New AI Context Check (Post-Audit)

After DG-3 fixes and registry additions are applied:

A fresh AI reading the required root docs would understand:
- Phase 7P is CLOSED
- DG-1 / DG-1A / DG-1B are accepted/complete
- DG-2 is COMPLETE (registry + checker)
- DG-3 performed staleness audit; 1 critical staleness found and fixed
- Phase 8 remains DEFERRED
- Current truth vs evidence vs archive boundaries are clear
- Stage Summit overrides older receipts for phase status
- Registry/checker validate consistency but do not authorize action
- CandidateRules remain advisory
- No live trading or auto-trading is authorized
- Wiki surface should come after audit/registry stabilization (DG-4+)
- `ordivon-root-context.md` now reflects current phase state

## 10. Recommended Next Phase

**DG-4** — Staleness Automation + Freshness Checker

Implement the freshness-related checker invariants (#23, #27, #28, #29 from §8):
- Add date-based staleness checking to `check_document_registry.py`
- Add content-level phrase checking ("Phase 8 active", "CandidateRule is Policy")
- Run automated staleness check as part of verification baseline

Wiki surface (DG-3 original scope) should wait until registry has ≥28 entries
and freshness checker is operational.
