# Architecture Docs

Canonical architecture documentation for Ordivon / AegisOS / PFIOS.

## Authoritative Documents

| Document | Purpose | Date |
|----------|---------|------|
| [architecture-baseline.md](architecture-baseline.md) | Canonical architecture baseline — **start here** | 2026-04-22 |
| [LANGUAGE.md](LANGUAGE.md) | Shared architecture vocabulary | — |
| [aegisos-working-identity.md](aegisos-working-identity.md) | Working naming convention | — |
| [state-truth-boundary.md](state-truth-boundary.md) | SQLAlchemy vs DuckDB hard boundary (H-2) | 2026-04-26 |
| [layer-definition.md](layer-definition.md) | Layer responsibilities | — |
| [system-overview.md](system-overview.md) | High-level system overview | — |

## Core Baseline (Docs-D2)

| Document | Purpose |
|----------|---------|
| [ordivon-system-definition.md](ordivon-system-definition.md) | **What is Ordivon, and what is it not** — canonical identity document |
| [systems-engineering-baseline.md](systems-engineering-baseline.md) | **How the system must be built** — engineering rules and constraints |
| [core-pack-adapter-boundary.md](core-pack-adapter-boundary.md) | **Who owns what** — anti-contamination rules for Core/Pack/Adapter |
| [harness-adapter-boundary.md](harness-adapter-boundary.md) | **Harness must not pollute Core** — external runtime boundary rules |
| [governance-receipt-review-loop.md](governance-receipt-review-loop.md) | **Receipt → Review → CandidateRule lifecycle** — the control loop |

## Governance & Work Language

| Document | Purpose |
|----------|---------|
| [ordivon-work-grammar.md](ordivon-work-grammar.md) | **Ordivon Work Grammar** — 12 rules, vocabulary, anti-bureaucracy guard |
| [repo-governance-baseline.md](repo-governance-baseline.md) | **Repo Governance Baseline** — 12-layer reflexive governance matrix |
| [prompt-patterns.md](../runbooks/prompt-patterns.md) | **Ordivon Prompt Patterns** — task templates for IDE/AI/audit/dogfood |
| [repo-governance-pack-architecture.md](repo-governance-pack-architecture.md) | **Repo Governance Pack Architecture** — Phase 3 product wedge design |

## Platformization

| Document | Purpose |
|----------|---------|
| [ordivon-platform-map.md](ordivon-platform-map.md) | **Ordivon Platform Map** — 9 platforms, responsibilities, promotion rules (Phase 3.4) |
| [github-tooling-landscape.md](github-tooling-landscape.md) | **GitHub Tooling Landscape** — tool categories, build/buy decisions (Phase 3.12) |
| [security-platform-baseline.md](security-platform-baseline.md) | **Security Platform Baseline** — security gates, tool placement, classification (Phase 3.13) |
| [verification-platform.md](verification-platform.md) | **Verification Platform** — 10-layer gate classification, baseline runner (Phase 3.4) |
| [core-pack-adapter-baseline.md](core-pack-adapter-baseline.md) | Core / Pack / Adapter baseline |
| [core-primitives-spec-v1.md](core-primitives-spec-v1.md) | Core primitives spec v1 |
| [adapter-boundary-spec-v1.md](adapter-boundary-spec-v1.md) | Adapter boundary rules |
| [current-code-classification-map-v1.md](current-code-classification-map-v1.md) | Current code classification map |
| [migration-map.md](migration-map.md) | Active migration tracking |

## Boundaries and Ownership

| Document | Purpose |
|----------|---------|
| [boundary-map.md](boundary-map.md) | Ownership rules |
| [domain-map.md](domain-map.md) | Core domain definitions |
| [capability-boundary-spec.md](capability-boundary-spec.md) | Capability boundary |
| [capability-inventory.md](capability-inventory.md) | Capability lifecycle status |
| [capability-migration-plan.md](capability-migration-plan.md) | Capability migration plan |
| [api-bypass-inventory.md](api-bypass-inventory.md) | API bypass tracking |

## Execution and State

| Document | Purpose |
|----------|---------|
| [runtime-flow.md](runtime-flow.md) | Main data flow path |
| [execution-action-catalog.md](execution-action-catalog.md) | Execution action catalog |
| [execution-request-receipt-spec.md](execution-request-receipt-spec.md) | Execution request/receipt spec |
| [state-transition-spec.md](state-transition-spec.md) | State transition rules |
| [state-truth-inventory.md](state-truth-inventory.md) | Canonical fact objects |
| [side-effect-boundary-inventory.md](side-effect-boundary-inventory.md) | Governance boundary coverage |
| [workflow-run-lineage-spec.md](workflow-run-lineage-spec.md) | Workflow run lineage |

## Finance Pack

| Document | Purpose |
|----------|---------|
| [finance-pack-v1-definition.md](finance-pack-v1-definition.md) | Finance pack identity |
| [finance-pack-extraction-plan.md](finance-pack-extraction-plan.md) | Extraction boundary |
| [finance-pack-phase2-ownership-map.md](finance-pack-phase2-ownership-map.md) | Phase 2 ownership split |

## AegisOS

| Document | Purpose |
|----------|---------|
| [aegisos-overview.md](aegisos-overview.md) | AegisOS positioning |
| [aegisos-design-doctrine.md](aegisos-design-doctrine.md) | Design doctrine |
| [aegisos-layer-roadmap.md](aegisos-layer-roadmap.md) | Layer roadmap |

## Current State

| Document | Purpose |
|----------|---------|
| [current-state-report-2026-04-24.md](current-state-report-2026-04-24.md) | Most recent state report (Phase 4 entry) |
| [layer-module-inventory.md](layer-module-inventory.md) | Factual code mapping (strips aspirational definitions) |
| [review-workflow-gap.md](review-workflow-gap.md) | Review workflow gap (F-002) |

## Historical (Archive Candidates)

These are superseded and will be moved to `docs/archive/`:
- `current-state-report-2026-04-20.md` through `2026-04-22.md`
- `step-1-foundation-report-2026-04-18.md` through `step-3-capability-prep-2026-04-18.md`
- `modularity-audit-2026-04-18.md`
- `design_spec_v0_1.md`
- `aegisos-phase-0-core-primitives-batch.md` through `aegisos-post-serial-batch-refinement-2026-04-22.md`
- `hermes-model-layer-integration.md` (pre-H-1, needs rewrite)
- `pfios-behavioral-baseline.md` and `pfios-organizational-baseline.md` (Chinese, needs translation)
- `overview.md` (redirect to baseline)

See [docs-inventory.md](../audits/docs-inventory.md) for full classification.
