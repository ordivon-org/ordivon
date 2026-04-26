# Documentation Inventory

> **Audit Date**: 2026-04-26
> **Phase**: Docs-D0 — Read-only inventory
> **Scope**: All .md / .mdx files in docs/ plus repo-level markdown
> **Rules**: No modifications, no moves, no deletions

## Purpose

Inventory every markdown document in the repository to identify:

1. What is authoritative vs historical
2. What carries stale PFIOS / AegisOS / Hermes-only narratives that may contaminate the current Ordivon system definition
3. What should be archived, merged, rewritten, or kept as-is
4. What documentation gaps exist for the current H-6 phase

## Summary

| Metric | Count |
|--------|-------|
| Total docs/ .md files | 89 |
| Non-docs repo .md files | ~70 (mostly README stubs) |
| Authoritative / Keep | 46 |
| Archive candidates | 28 |
| Merge candidates | 6 |
| Rewrite candidates | 7 |
| Review needed (ambiguous) | 2 |

## Current Documentation Map

### docs/architecture/ (53 files)

| Path | Topic | Category | Status | Reason | Recommended Action |
|------|-------|----------|--------|--------|-------------------|
| architecture-baseline.md | Canonical architecture baseline (2026-04-22) | architecture | keep | Authoritative reference; all other docs defer to this | None — maintain as canonical |
| LANGUAGE.md | Ordivon architecture vocabulary | architecture | keep | Shared vocabulary for all architecture discussions | None |
| aegisos-working-identity.md | Working naming convention (AegisOS/CAIOS/PFIOS/Ordivon) | architecture | keep | Authoritative naming rules while repo retains legacy names | None |
| naming.md | Project naming status (multi-name reality) | architecture | merge | Covers same ground as aegisos-working-identity.md; consolidate | Merge into aegisos-working-identity.md or replace with canonical reference |
| layer-definition.md | Layer responsibilities (9 surfaces) | architecture | keep | Defines layer boundaries; complements baseline | None |
| boundary-map.md | Ownership rules for active repo parts | architecture | keep | Reduces drift during migration | None |
| domain-map.md | Core domain definitions | architecture | keep | Maps domain ownership | None |
| runtime-flow.md | Main runtime path (apps→capabilities→orchestrator→…) | architecture | keep | Canonical data flow | None |
| system-overview.md | System overview (9-layer architecture) | architecture | keep | High-level system overview | None |
| overview.md | Compatibility entrypoint → points to baseline | architecture | archive | Superseded by architecture-baseline.md; exists only as redirect | Archive; update any cross-references to point to baseline directly |
| architecture-diagram.md | Canonical layer diagram | architecture | keep | Visual reference governed by baseline | None |
| core-pack-adapter-baseline.md | Core/Pack/Adapter baseline | architecture | keep | Foundation for platformization | None |
| core-primitives-spec-v1.md | Core primitives spec v1 | architecture | keep | Explicit core primitive definitions | None |
| adapter-boundary-spec-v1.md | Adapter boundary spec | architecture | keep | Adapter boundary rules | None |
| capability-boundary-spec.md | Capability boundary spec | architecture | keep | Product capability boundary | None |
| capability-inventory.md | Capability inventory (lifecycle status) | architecture | keep | Tracks every capability file | None |
| capability-migration-plan.md | Capability migration plan | architecture | keep | Active migration plan | None |
| execution-action-catalog.md | Execution action catalog | architecture | keep | Current execution action universe | None |
| execution-request-receipt-spec.md | Execution request/receipt spec | architecture | keep | Live execution path spec | None |
| state-transition-spec.md | State transition rules | architecture | keep | Explicit transition rules | None |
| state-truth-boundary.md | State truth boundary (SQLAlchemy vs DuckDB) | architecture | keep | Dated 2026-04-26; H-2/P4-prep; authoritative boundary | None |
| state-truth-inventory.md | State truth inventory (canonical fact objects) | architecture | keep | Defines persisted truth objects | None |
| side-effect-boundary-inventory.md | Side-effect boundary coverage | architecture | keep | Governance boundary coverage | None |
| workflow-run-lineage-spec.md | Workflow run lineage spec | architecture | keep | Workflow-level run lineage | None |
| api-bypass-inventory.md | API bypass inventory | architecture | keep | Tracks direct repo→response bypasses | None |
| finance-pack-v1-definition.md | Finance Pack v1 definition | packs | keep | Finance pack identity definition | None |
| finance-pack-extraction-plan.md | Finance pack extraction plan | packs | keep | Extraction boundary for packs/finance | None |
| finance-pack-phase2-ownership-map.md | Finance Pack Phase 2 ownership map | packs | keep | Ownership split during AegisOS migration | None |
| hermes-model-layer-integration.md | Hermes runtime integration into model layer | architecture | rewrite | Pre-H-1 design doc; describes Hermes as "execution-grade runtime beneath AI layer" — narrative predates Ordivon bridge model; references `hermes-runtime` as external, not as current bridge | Rewrite to align with current Ordivon bridge architecture (services/hermes_bridge/); or archive as historical design artifact |
| review-workflow-gap.md | Review workflow gap (orchestrator bypass) | architecture | keep | Dated 2026-04-25; linked to Phase 4 audit F-002 | None |
| layer-module-inventory.md | AegisOS layer & module inventory (factual code map) | architecture | keep | Dated 2026-04-24; strips aspirational definitions, shows what code exists where | None |
| pfios-behavioral-baseline.md | PFIOS behavioral baseline (Chinese) | architecture | rewrite | Chinese-language behavioral analysis; uses PFIOS naming throughout; valuable content but needs Ordivon/AegisOS alignment | Rewrite in English or translate; align naming with current Ordivon identity |
| pfios-organizational-baseline.md | PFIOS organizational baseline (Chinese) | architecture | rewrite | Chinese-language organizational analysis; uses PFIOS naming; valuable but naming mismatch | Rewrite in English or translate; align naming with current Ordivon identity |
| current-code-classification-map-v1.md | Current code classification map v1 | architecture | keep | Classifies repo using core/pack/adapter baseline | None |
| migration-map.md | Migration movement map | architecture | keep | Active migration tracking | None |
| aegisos-overview.md | AegisOS overview (governance-first OS) | architecture | keep | Authoritative AegisOS positioning | None |
| aegisos-design-doctrine.md | AegisOS design doctrine | architecture | keep | Philosophy→design rule→ownership mapping | None |
| aegisos-layer-roadmap.md | AegisOS layer roadmap | roadmap | keep | Turns overview into execution map | None |
| aegisos-next-round-execution-plan.md | AegisOS corrected next-round execution table | roadmap | keep | Current execution plan | None |
| current-state-report-2026-04-24.md | AegisOS architecture current state (Phase 4 entry) | architecture | keep | Most recent state report; Phase 4 entry snapshot | None |
| current-state-report-2026-04-22.md | Current state after Phase 1 batch | architecture | archive | Superseded by 2026-04-24 report | Move to archive/ |
| current-state-report-2026-04-21.md | Current state snapshot | architecture | archive | Superseded by 2026-04-22 and 2026-04-24 | Move to archive/ |
| current-state-report-2026-04-20.md | Current state snapshot | architecture | archive | Self-declares "historical snapshot only"; superseded | Move to archive/ |
| step-1-foundation-report-2026-04-18.md | Step 1 foundation closure | architecture | archive | Completed step report; historical only | Move to archive/ |
| step-2-boundary-prep-2026-04-18.md | Step 2 boundary preparation | architecture | archive | Preparation doc; executed and closed | Move to archive/ |
| step-2-boundary-report-2026-04-18.md | Step 2 boundary closure | architecture | archive | Completed step report; historical only | Move to archive/ |
| step-3-capability-prep-2026-04-18.md | Step 3 capability preparation | architecture | archive | Preparation doc; executed and closed | Move to archive/ |
| modularity-audit-2026-04-18.md | Modularity audit (8-layer target) | architecture | archive | Historical audit; superseded by Layer & Module Inventory (2026-04-24) | Move to archive/ |
| design_spec_v0_1.md | Design spec v0.1 (original skeleton) | architecture | archive | v0.1 superseded by current baseline | Move to archive/ |
| aegisos-phase-0-core-primitives-batch.md | Phase 0 core primitive freeze (completed) | architecture | archive | Completed batch record; results absorbed into baseline | Move to archive/ |
| aegisos-phase-1-core-load-bearing-batch.md | Phase 1 core load-bearing batch (completed) | architecture | archive | Completed batch record; results absorbed into baseline | Move to archive/ |
| aegisos-next-batch-serial-modules-2026-04-22.md | Serial modules batch (completed) | architecture | archive | Completed batch record; 8 modules done | Move to archive/ |
| aegisos-extraction-workspace-refinement-2026-04-22.md | Extraction/workspace refinement | architecture | archive | Refinement wave record; superseded | Move to archive/ |
| aegisos-post-serial-batch-refinement-2026-04-22.md | Post-serial-batch refinement | architecture | archive | Refinement wave record; superseded | Move to archive/ |
| aegisos-post-mvp-refinement-execution-plan.md | Post-MVP refinement order | roadmap | merge | May be superseded by next-round-execution-plan | Review and merge into aegisos-next-round-execution-plan.md if still relevant |

### docs/runtime/ (1 file)

| Path | Topic | Category | Status | Reason | Recommended Action |
|------|-------|----------|--------|--------|-------------------|
| h1-real-model-under-control.md | H-1: One Real Model Under Ordivon Control (CLOSED) | runtime | keep | Authoritative H-1 completion record; proves real model runs inside governance | None — H-1 is closed and this is the canonical record |

### docs/audits/ (3 files + this inventory = 4)

| Path | Topic | Category | Status | Reason | Recommended Action |
|------|-------|----------|--------|--------|-------------------|
| phase-4-readiness/phase-4-readiness-audit-report.md | Phase 4 readiness audit report | audits | keep | Active audit; Phase 4 entry gate | None |
| phase-4-readiness/findings-register.md | Phase 4 findings register (F-001 through F-010) | audits | keep | Active findings; linked to remediation | None |
| phase-4-readiness/remediation-plan.md | Phase 4 remediation plan | audits | keep | Active remediation; pre-Phase-4 batch | None |

### docs/decisions/ (5 files)

| Path | Topic | Category | Status | Reason | Recommended Action |
|------|-------|----------|--------|--------|-------------------|
| ADR-001-repo-structure.md | 8-layer repository structure | architecture | keep | Accepted ADR; canonical interpretation lives in architecture-baseline | None |
| ADR-002-knowledge-vs-state.md | Knowledge vs State separation | architecture | keep | Accepted ADR | None |
| ADR-003-python-first-rust-later.md | Python first, Rust later | architecture | keep | Accepted ADR | None |
| ADR-004-governance-layer-mandatory.md | Governance layer is mandatory | architecture | keep | Accepted ADR | None |
| ADR-005-tool-vs-skill-boundary.md | Tool vs Skill boundary | architecture | keep | Accepted ADR | None |

### docs/product/ (10 files)

| Path | Topic | Category | Status | Reason | Recommended Action |
|------|-------|----------|--------|--------|-------------------|
| ai-financial-assistant-roadmap.md | AI Financial Assistant roadmap | roadmap | rewrite | Finance-only narrative; predates Ordivon general-platform identity; title suggests finance-specific product | Rewrite as general AegisOS product roadmap; or archive and replace with platform roadmap |
| aegisos-mvp-brief.md | AegisOS MVP definition | roadmap | keep | Clear MVP definition (single-agent, finance-seed, governance-aware) | None |
| aegisos-mvp-execution-checklist.md | AegisOS MVP execution checklist | roadmap | archive | Likely completed; checklist for MVP delivery | Archive if MVP is delivered; otherwise update |
| aegisos-quality-matrix.md | AegisOS quality matrix | architecture | keep | Maps quality responsibilities to workflows/commands | None |
| personal-control-loop-v0.md | Personal Control Loop v0 (P4) | roadmap | keep | Current Phase 4 product brief | None |
| module-definition-template-v2.md | Module definition template v2 | architecture | keep | Template for module-shaped work | None |
| task-template-system.md | Task template system | architecture | keep | Default task template format | None |
| experience-state-spec.md | Experience state spec | architecture | keep | Shared state vocabulary for product widgets | None |
| product-closure-report-2026-04-19.md | Product closure report (completed pass) | roadmap | archive | Completed work report; historical only | Move to archive/ |
| product-closure-todo.md | Product closure master TODO | roadmap | archive | Likely completed; review before archiving | Archive if all items complete; otherwise update |

### docs/tasks/ (11 files)

| Path | Topic | Category | Status | Reason | Recommended Action |
|------|-------|----------|--------|--------|-------------------|
| T1-hermes-runtime-stabilization.md | Hermes runtime stabilization task | runtime | archive | Completed task card; Hermes runtime stabilized | Move to archive/ |
| T2-intelligence-io-contract.md | Intelligence IO contract task | runtime | archive | Completed task card | Move to archive/ |
| T3-core-state-truth-inventory.md | Core state truth inventory task | runtime | archive | Completed task card | Move to archive/ |
| T4-side-effect-boundary-expansion.md | Side-effect boundary expansion task | runtime | archive | Completed task card | Move to archive/ |
| T5-execution-action-catalog.md | Execution action catalog task | runtime | archive | Completed task card | Move to archive/ |
| T6-intelligence-run.md | Intelligence run task | runtime | archive | Completed task card | Move to archive/ |
| T7-execution-request-receipt.md | Execution request/receipt task | runtime | archive | Completed task card | Move to archive/ |
| T8-state-transition.md | State transition task | runtime | archive | Completed task card | Move to archive/ |
| T9-orchestration-run-lineage.md | Orchestration run lineage task | runtime | archive | Completed task card | Move to archive/ |
| module-closure-summary-2026-04-19.md | Module closure summary (T1-T3 batch) | runtime | archive | Historical closure note; completed batch | Move to archive/ |
| phase-4-personal-control-loop-brief.md | Phase 4: Personal Control Loop brief | roadmap | keep | Current Phase 4 task brief | None |
| today-board-template.md | Today board template | architecture | keep | Reusable template | None |

### docs/runbooks/ (8 files)

| Path | Topic | Category | Status | Reason | Recommended Action |
|------|-------|----------|--------|--------|-------------------|
| local-dev.md | Local dev runbook | runtime | keep | Operational entrypoint doc | None |
| aegisos-operations.md | AegisOS operations checks | runtime | keep | Current operational procedures | None |
| hermes-runtime-bridge.md | Hermes runtime bridge runbook | runtime | rewrite | References `hermes-runtime` as external; predates Ordivon bridge; uses PFIOS naming for env vars | Rewrite to align with current services/hermes_bridge/ architecture and Ordivon naming |
| monitoring-signals.md | Monitoring signals | runtime | keep | Health endpoint signal docs | None |
| review-blocked.md | Review blocked runbook | runtime | keep | Operational procedure | None |
| runtime-unhealthy.md | Runtime unhealthy runbook | runtime | keep | Operational procedure | None |
| scheduler-stalled.md | Scheduler stalled runbook | runtime | keep | Operational procedure | None |
| trace-inconsistency.md | Trace inconsistency runbook | runtime | keep | Operational procedure | None |

### docs/ (root-level, 4 files)

| Path | Topic | Category | Status | Reason | Recommended Action |
|------|-------|----------|--------|--------|-------------------|
| context_design.md | PFIOS context substrate design (Chinese) | architecture | rewrite | Chinese-language; PFIOS-specific naming; valuable 5-layer context model | Translate to English and align naming with Ordivon/AegisOS |
| prompt_tuning_notes.md | PFIOS prompt tuning log (Chinese) | runtime | archive | Chinese-language; prompt tuning history; PFIOS-specific; likely stale | Move to archive/ |
| reasoning_contract.md | PFIOS reasoning module contract (Chinese) | architecture | rewrite | Chinese-language; PFIOS-specific naming; core reasoning contract still relevant | Translate to English and align naming with Ordivon/AegisOS |
| naming.md | Project naming status | architecture | merge | Overlaps with aegisos-working-identity.md | See architecture section above |

### docs/schemas/ (1 file)

| Path | Topic | Category | Status | Reason | Recommended Action |
|------|-------|----------|--------|--------|-------------------|
| schemas/README.md | Schema docs placeholder | architecture | keep | Directory placeholder; no substantive content | None — populate with actual schema docs when ready |

### docs/workflows/ (2 files)

| Path | Topic | Category | Status | Reason | Recommended Action |
|------|-------|----------|--------|--------|-------------------|
| workflows/README.md | Workflow docs placeholder | architecture | keep | Directory placeholder | None |
| status-sync-workflow.md | Status sync workflow (repo state updates after modules) | architecture | keep | Defines how status docs stay in sync | None |

### Non-docs Repo Markdown (selected substantive files)

| Path | Topic | Category | Status | Reason | Recommended Action |
|------|-------|----------|--------|--------|-------------------|
| README.md | Root project readme (Financial AI OS → AegisOS/CAIOS) | architecture | keep | Primary project entrypoint; already references AegisOS | None — verify H-6 updates don't need README changes |
| policies/constitution.md | PFIOS Constitution (Chinese) | architecture | rewrite | Chinese-language; PFIOS naming; core values still relevant | Translate to English; align naming with Ordivon |
| packs/finance/inventory.md | Finance pack file inventory | packs | keep | Active pack inventory | None |
| apps/web/CLAUDE.md | Next.js agent rules (delegates to AGENTS.md) | runtime | keep | Agent instruction file | None |
| apps/web/AGENTS.md | Next.js agent rules for Claude Code | runtime | keep | Agent instruction file | None |
| knowledge/memory/MAS_Command_Explanation.md | PowerShell MAS activation (Chinese) | unknown | archive | Completely irrelevant to project; appears to be misplaced | Remove from repo or move to personal notes |
| wiki/reports/analysis_*.md (4 files) | Generated analysis reports for BTC_USDT | runtime | archive | Auto-generated analysis output; runtime artifacts, not docs | Move to data output directory or archive |

## Authoritative Docs Found

These documents form the current documentation backbone and should be treated as canonical:

1. **docs/architecture/architecture-baseline.md** — Canonical architecture baseline (2026-04-22)
2. **docs/architecture/LANGUAGE.md** — Ordivon architecture vocabulary
3. **docs/architecture/aegisos-working-identity.md** — Working naming convention
4. **docs/runtime/h1-real-model-under-control.md** — H-1 closed (2026-04-26); real model under governance proof
5. **docs/architecture/layer-definition.md** — Layer responsibilities
6. **docs/architecture/boundary-map.md** — Ownership rules
7. **docs/architecture/state-truth-boundary.md** — SQLAlchemy vs DuckDB boundary (2026-04-26)
8. **docs/decisions/ADR-001 through ADR-005** — All accepted ADRs
9. **docs/architecture/core-pack-adapter-baseline.md** — Platformization baseline
10. **docs/product/aegisos-mvp-brief.md** — MVP definition

## Archive Candidates

28 files should be moved to an archive directory (e.g., `docs/archive/`):

### Superseded state reports
- docs/architecture/current-state-report-2026-04-20.md
- docs/architecture/current-state-report-2026-04-21.md
- docs/architecture/current-state-report-2026-04-22.md

### Completed step reports
- docs/architecture/step-1-foundation-report-2026-04-18.md
- docs/architecture/step-2-boundary-prep-2026-04-18.md
- docs/architecture/step-2-boundary-report-2026-04-18.md
- docs/architecture/step-3-capability-prep-2026-04-18.md

### Historical audits and specs
- docs/architecture/modularity-audit-2026-04-18.md
- docs/architecture/design_spec_v0_1.md

### Completed AegisOS batch records
- docs/architecture/aegisos-phase-0-core-primitives-batch.md
- docs/architecture/aegisos-phase-1-core-load-bearing-batch.md
- docs/architecture/aegisos-next-batch-serial-modules-2026-04-22.md
- docs/architecture/aegisos-extraction-workspace-refinement-2026-04-22.md
- docs/architecture/aegisos-post-serial-batch-refinement-2026-04-22.md

### Completed product docs
- docs/product/product-closure-report-2026-04-19.md
- docs/product/product-closure-todo.md (review first)
- docs/product/aegisos-mvp-execution-checklist.md (review first)

### Completed task cards
- docs/tasks/T1 through T9 (9 files)
- docs/tasks/module-closure-summary-2026-04-19.md

### Stale/irrelevant
- docs/prompt_tuning_notes.md (Chinese, PFIOS-specific, stale)
- knowledge/memory/MAS_Command_Explanation.md (irrelevant)

### Auto-generated artifacts
- wiki/reports/analysis_*.md (4 files)

## Merge Candidates

6 files have overlapping content that could be consolidated:

| Overlap | Files | Recommendation |
|---------|-------|----------------|
| Project naming | docs/naming.md + docs/architecture/aegisos-working-identity.md | Merge into aegisos-working-identity.md; add cross-reference from naming.md |
| Architecture entrypoints | docs/architecture/overview.md + docs/architecture/architecture-baseline.md | Archive overview.md (it already redirects to baseline) |
| AegisOS execution plans | docs/architecture/aegisos-post-mvp-refinement-execution-plan.md + docs/architecture/aegisos-next-round-execution-plan.md | Review and merge if post-MVP plan is superseded |
| Schema docs | docs/schemas/README.md (empty) + docs/architecture/state-truth-boundary.md | State-truth-boundary already covers schema boundaries; schemas/README should reference it |

## Missing Docs

Documentation gaps identified during inventory:

| Gap | Priority | Notes |
|-----|----------|-------|
| H-2 documentation | High | state-truth-boundary.md exists but no dedicated H-2 closure doc like h1-real-model-under-control.md |
| H-3 through H-5 closure docs | High | No dedicated closure documents found for H-3, H-4, H-5 |
| H-6 spec/plan | Critical | Current phase has no implementation plan document |
| Ordivon bridge architecture | Medium | hermes-model-layer-integration.md is pre-H-1 and outdated; no canonical bridge architecture doc exists |
| API contract documentation | Medium | schemas/README.md is a placeholder; no cross-layer contract docs |
| Test architecture | Low | No dedicated test strategy or test architecture document |
| Deployment/ops architecture | Low | Runbooks cover operations but no deployment architecture doc |

## Recommended Next Batch

Immediate (Docs-D1, before any file moves):

1. **Create docs/archive/ directory** — staging area for archive candidates
2. **Write H-6 implementation plan** — highest priority gap
3. **Write H-2 through H-5 closure summaries** — even if brief, to match H-1 pattern
4. **Translate/rewrite critical Chinese docs** — pfios-behavioral-baseline.md and pfios-organizational-baseline.md are architecturally valuable but inaccessible to English-reading contributors
5. **Resolve merge candidates** — consolidate naming docs, archive overview.md redirect

Before H-6 completion:

6. **Move archive candidates** to docs/archive/ (28 files)
7. **Rewrite hermes-model-layer-integration.md** to reflect current Ordivon bridge architecture
8. **Rewrite hermes-runtime-bridge.md runbook** to align with services/hermes_bridge/
9. **Translate reasoning_contract.md and context_design.md** to English
10. **Translate policies/constitution.md** to English

## Out-of-Scope (not audited)

- Source code files (.py, .ts, .tsx, .js)
- Test files
- Configuration files (.toml, .yml, .yaml, .json)
- Docker/compose files
- CI/CD files (.github/)
- Binary files, databases, logs
- Node modules, virtual environments
- Git objects and history

## Audit Compliance

- [x] No existing documents modified
- [x] No documents moved
- [x] No documents deleted
- [x] No source code changed
- [x] No tests changed
- [x] No H-6 functionality touched
- [x] No Hermes bridge changes
- [x] No governance/orchestrator/ORM changes
- [x] Only new file created: docs/audits/docs-inventory.md
