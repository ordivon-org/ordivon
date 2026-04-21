# Current Code Classification Map v1

## Status

This document classifies the current repository using the platform baseline introduced in:

- [Core / Pack / Adapter Baseline](./core-pack-adapter-baseline.md)

It does **not** rewrite the repository structure.

It answers a narrower question:

**given the code that exists today, which parts should be treated as stable core primitives, which parts are finance-pack implementations, and which parts are adapters?**

## Purpose

PFIOS already has a working layered system.

What it does not yet have is a frozen platformization map.

This document exists to prevent three common mistakes:

1. putting finance-domain nouns into `core`
2. putting provider/backend details into `core`
3. rewriting directories before the semantics are classified

## Classification Labels

Use these labels exactly.

- `Core Primitive`
- `Finance-Pack Implementation`
- `Adapter`
- `Mixed / Transitional`

`Mixed / Transitional` means:

- the directory is useful now
- but it currently contains more than one future responsibility
- so it should be refactored gradually rather than force-labeled as pure

## Repository-Level Classification

| Current Area | Current Role | Classification | Why |
| --- | --- | --- | --- |
| `apps/` | Experience entrypoints and user-facing surfaces | Mixed / Transitional | Surface semantics are core-like, but current pages are finance-first |
| `capabilities/` | product entry contracts and workflow-facing abilities | Mixed / Transitional | Capability contracts are reusable, but active capabilities are mostly finance workflows |
| `domains/` | business/domain object implementations | Finance-Pack Implementation | Current dominant nouns are recommendation/review/outcome/journal/portfolio/market |
| `execution/` | action discipline and family adapters | Mixed / Transitional | request/receipt primitives are core-like; concrete families are finance-heavy |
| `governance/` | policy, decision language, audit discipline | Core Primitive | these define allowed action and traceability across domains |
| `infra/` | startup, health, monitoring wiring | Mixed / Transitional | infra primitives are core-like, but concrete backend/runtime wiring is adapter-heavy |
| `intelligence/` | runtime abstraction, task contracts, provider integration | Mixed / Transitional | task/runtime interfaces are core-like; provider implementations are adapters |
| `knowledge/` | learning primitives, extraction, retrieval, aggregation | Mixed / Transitional | feedback/lesson primitives are core-like, but active extractors are finance-heavy |
| `orchestrator/` | workflow runtime and step control | Core Primitive | workflow laws are system-level |
| `state/` | fact persistence, trace, lineage, snapshots | Core Primitive | truth/trace primitives are system-level |
| `tools/` | concrete execution integrations and helper utilities | Adapter | tool integrations should remain replaceable |
| `skills/` | execution-side helper affordances | Adapter | these are integration behavior, not system truth |
| `shared/` | shared config/errors/enums | Mixed / Transitional | some shared primitives are stable, some enums are finance-specific |

## Detailed Classification By Major Area

### 1. Orchestrator

| Path | Classification | Reason | Future Home |
| --- | --- | --- | --- |
| `orchestrator/runtime/` | Core Primitive | workflow engine, step running, recovery policy, lifecycle control | `core/workflow/` |
| `orchestrator/workflows/analyze.py` | Mixed / Transitional | built on workflow primitives but implements finance analyze flow | split into `core/workflow/` + `packs/finance/workflows/` |

Key take:

- the workflow engine is `core`
- concrete finance analyze flow is `finance pack`

### 2. Governance

| Path | Classification | Reason | Future Home |
| --- | --- | --- | --- |
| `governance/decision.py` | Core Primitive | unified decision language is cross-domain | `core/governance/` |
| `governance/policy_source.py` | Core Primitive | source-of-truth policy mechanism is system-level | `core/governance/` |
| `governance/audit/` | Core Primitive | audit lineage and proof mechanics are system-level | `core/trace/` or `core/governance/audit/` |
| `governance/risk_engine/` | Mixed / Transitional | decision discipline is core-like, active policies/rules are finance-first | split policy framework into `core`, finance rules into `packs/finance/policies/` |
| `governance/feedback.py` | Mixed / Transitional | hint-consumption mechanism is core-like, current hint semantics are finance-derived | split feedback interface vs finance mappings |

### 3. Execution

| Path | Classification | Reason | Future Home |
| --- | --- | --- | --- |
| `execution/catalog.py` | Core Primitive | action family inventory and side-effect classes are system-level | `core/execution/` |
| `execution/adapters/recommendations.py` | Finance-Pack Implementation | recommendation action families are finance-domain actions | `packs/finance/actions/` |
| `execution/adapters/reviews.py` | Finance-Pack Implementation | review submit/complete are finance-domain family semantics | `packs/finance/actions/` |
| `execution/adapters/validation.py` | Finance-Pack Implementation | current validation issue reporting is finance/product-domain specific | `packs/finance/actions/` |
| `domains/execution_records/` | Core Primitive | request/receipt persistence and services are reusable across domains | `core/execution/` |

Key take:

- request/receipt discipline is `core`
- recommendation/review/validation families are `finance pack`

### 4. State

| Path | Classification | Reason | Future Home |
| --- | --- | --- | --- |
| `state/trace/` | Core Primitive | trace bundle, relation resolution, lineage query are system primitives | `core/state/trace/` |
| `state/db/` | Adapter | DB bootstrap/backend wiring is implementation-specific | `adapters/storage/` with thin core contracts |
| `state/usage/` | Core Primitive | operational usage fact model is reusable | `core/state/usage/` |
| `state/snapshots/` | Mixed / Transitional | snapshot primitive is reusable, active snapshot shapes are app-specific | split primitives from concrete snapshot shapes |
| `domains/workflow_runs/` | Core Primitive | workflow run truth is system-level | `core/state/workflow_runs/` |
| `domains/intelligence_runs/` | Core Primitive | intelligence run truth is system-level | `core/state/intelligence_runs/` |
| `domains/ai_actions/` | Core Primitive | agent action truth is system-level | `core/state/ai_actions/` |

### 5. Knowledge

| Path | Classification | Reason | Future Home |
| --- | --- | --- | --- |
| `knowledge/feedback.py` | Core Primitive | feedback packet primitive and semantics are cross-domain | `core/knowledge/` |
| `knowledge/retrieval.py` | Core Primitive | retrieval contract and recurring issue mechanics are reusable | `core/knowledge/` with domain plugins |
| `knowledge/retrieval/` | Mixed / Transitional | retrieval infra is reusable, active indexes may become backend/domain-specific | split interfaces from concrete index adapters |
| `knowledge/memory/` | Core Primitive | memory semantics should be runtime/knowledge primitives | `core/knowledge/` or `core/runtime/` |
| `knowledge/ingestion/` | Adapter | ingestion of external sources is connector-facing | `adapters/knowledge/` |
| `domains/knowledge_feedback/` | Core Primitive | persisted feedback packet object is reusable across domains | `core/knowledge/feedback/` |
| finance lesson extraction rules in `domains/journal/` + `knowledge/` | Finance-Pack Implementation | current extraction semantics are recommendation/review/outcome-specific | `packs/finance/knowledge/` |

### 6. Intelligence

| Path | Classification | Reason | Future Home |
| --- | --- | --- | --- |
| `intelligence/tasks/contracts.py` | Core Primitive | bounded task contract is reusable | `core/runtime/tasks/` |
| `intelligence/runtime/` | Mixed / Transitional | runtime client abstractions are core-like, concrete Hermes calls are adapter-like | split runtime interface from adapter implementations |
| `intelligence/providers/hermes_agent_provider.py` | Adapter | provider integration is replaceable | `adapters/runtimes/hermes/` |
| `intelligence/models/router.py` | Mixed / Transitional | routing policy is core-like, provider table is adapter-aware | split interface from provider registry |
| `intelligence/tasks/hermes.py` | Mixed / Transitional | task-building contract is reusable, Hermes payload shaping is adapter/provider-specific | split normalized task schema from Hermes adapter |
| `intelligence/feedback.py` | Mixed / Transitional | feedback consumption interface is core-like, current mapping is finance-derived | split generic contract from finance hint mapping |

### 7. Domains

Treat `domains/` as the strongest current `finance pack` signal.

| Path | Classification | Reason | Future Home |
| --- | --- | --- | --- |
| `domains/strategy/` | Finance-Pack Implementation | recommendation and outcome semantics are finance-domain objects | `packs/finance/strategy/` |
| `domains/journal/` | Finance-Pack Implementation | review/lesson/issue semantics are currently finance/product-specific | `packs/finance/journal/` |
| `domains/market/` | Finance-Pack Implementation | symbol and market-facing concepts are finance-domain concepts | `packs/finance/market/` |
| `domains/portfolio/` | Finance-Pack Implementation | holdings/exposure/cash state are finance-domain concepts | `packs/finance/portfolio/` |
| `domains/research/` | Finance-Pack Implementation | current research is finance thesis/recommendation analysis | `packs/finance/research/` |
| `domains/reporting/` | Mixed / Transitional | artifact/report primitive is reusable, active report content is finance-specific | split report primitive from finance report formats |
| `domains/risk/` | Mixed / Transitional | risk primitives may be core-like, current rules and meanings are finance-heavy | split cross-domain risk flags from finance risk policies |
| `domains/trading/` | Finance-Pack Implementation | action/business objects are finance-specific | `packs/finance/trading/` |
| `domains/userprefs/` | Mixed / Transitional | user preference primitive is reusable, active defaults may be app-specific | split preference primitives from app-specific choices |

### 8. Capabilities

| Path | Classification | Reason | Future Home |
| --- | --- | --- | --- |
| `capabilities/contracts/` | Mixed / Transitional | contract shapes are reusable, many still encode finance nouns | split generic work contracts from finance contracts |
| `capabilities/workflow/analyze.py` | Finance-Pack Implementation | this is finance analyze flow surfaced as product ability | `packs/finance/capabilities/` |
| `capabilities/workflow/reviews.py` | Finance-Pack Implementation | review capability is finance-domain | `packs/finance/capabilities/` |
| `capabilities/domain/recommendations.py` | Finance-Pack Implementation | recommendation capability is finance-domain | `packs/finance/capabilities/` |
| `capabilities/diagnostic/validation.py` | Finance-Pack Implementation | current validation semantics are app/finance-bound | `packs/finance/capabilities/` |

### 9. Experience

| Path | Classification | Reason | Future Home |
| --- | --- | --- | --- |
| `apps/web/src/lib/semanticSignals.ts` | Core Primitive | trust-tier and honest-missing semantics are reusable | `core/experience/` |
| `apps/web/src/components/state/` | Mixed / Transitional | state surface semantics are reusable, active cards still embed finance concepts | split generic view primitives from finance cards |
| `apps/web/src/components/features/dashboard/` | Finance-Pack Implementation | current dashboard is recommendation/review/report/validation finance product surface | `packs/finance/surfaces/` |
| `apps/web/src/app/analyze/` | Finance-Pack Implementation | current reasoning workspace is finance-analysis specific | `packs/finance/surfaces/` |
| `apps/api/app/api/v1/health.py` | Mixed / Transitional | health/monitoring surface is reusable, active payload still tuned to current product | split ops surface primitive from current app shape |
| `apps/api/app/api/v1/analyze.py` | Finance-Pack Implementation | analyze-and-suggest is finance-domain capability surface | `packs/finance/api/` |
| `apps/api/app/api/v1/recommendations.py` | Finance-Pack Implementation | finance-domain object surface | `packs/finance/api/` |
| `apps/api/app/api/v1/reviews.py` | Finance-Pack Implementation | finance-domain object surface | `packs/finance/api/` |
| `apps/api/app/api/v1/traces.py` | Mixed / Transitional | trace API is reusable, current root paths target finance objects | split generic trace API patterns from finance roots |

## Object-Level Classification

The following object-level judgments should guide future refactors.

| Object | Classification | Why |
| --- | --- | --- |
| `WorkflowRun` | Core Primitive | any domain workflow needs persisted runs |
| `IntelligenceRun` | Core Primitive | any bounded AI task system needs run lineage |
| `ActionContext` | Core Primitive | governance and execution need this across domains |
| `ExecutionRequest` / `ExecutionReceipt` | Core Primitive | action discipline is cross-domain |
| `AuditEvent` | Core Primitive | proof and lineage are cross-domain |
| `TraceBundle` | Core Primitive | relation-query surface is cross-domain |
| `OutcomeSnapshot` | Core Primitive | outcome as a primitive is reusable, even if current meaning is finance-shaped |
| `KnowledgeFeedbackPacket` | Core Primitive | derived feedback object is reusable |
| `Lesson` | Core Primitive | experience object is reusable |
| `RecurringIssue` | Core Primitive | repeated issue aggregation is reusable |
| `Recommendation` | Finance-Pack Implementation | current recommendation meaning is finance-domain |
| `Review` | Finance-Pack Implementation | current review semantics are tied to recommendation lifecycle |
| `Issue` in current validation/journal path | Finance-Pack Implementation | current usage is app/finance validation, not generic governance incident |
| `Symbol` / `MarketRegime` / `RiskBudget` / `Portfolio` | Finance-Pack Implementation | domain-specific nouns |
| Hermes bridge health/task transport | Adapter | provider runtime integration |
| DuckDB engine/bootstrap | Adapter | storage backend integration |

## Immediate Refactor Targets

These are the safest next classification-driven moves.

### Target 1: freeze explicit core primitives

Prioritize explicit contracts for:

- `DecisionLanguage`
- `ActionRequest / ActionReceipt`
- `TraceLink`
- `Outcome`
- `FeedbackPacket`
- `AgentRuntime`
- `TrustTier / MissingState`

### Target 2: declare current finance system as `Finance Pack v1`

Treat the active recommendation/review/outcome/validation stack as the first domain pack, even before folder moves.

### Target 3: split runtime/provider semantics

Extract clear seams between:

- runtime interfaces
- Hermes/OpenAI/provider implementations

### Target 4: split execution discipline from action families

Keep request/receipt in reusable `core` semantics.

Move recommendation/review/validation family meaning toward `finance pack`.

### Target 5: split knowledge primitives from finance extractors

Keep:

- `FeedbackPacket`
- retrieval contracts
- recurring issue primitives

as reusable system semantics.

Move finance-specific lesson/outcome mappings toward pack-local logic.

## What Not To Do Next

Do not do these yet:

- do not rename every folder into `core/`, `packs/`, and `adapters/` immediately
- do not force every current mixed directory into a pure bucket
- do not treat current finance nouns as universal just because they are central today
- do not turn every helper into an adapter abstraction

## Final Summary

The current repository already contains the seeds of:

- `core`
- `finance pack`
- `adapters`

But they are still interleaved.

The most important current judgment is:

- workflow, governance, execution discipline, state truth, trace, audit, runtime contracts, and learning primitives should be treated as `core`
- recommendation/review/outcome/validation and most current domain nouns should be treated as `finance-pack implementation`
- Hermes/provider/storage/tool integrations should be treated as `adapters`

Compressed:

**PFIOS already has a platform shape. This map exists to stop the next refactor from pretending finance is core and integrations are semantics.**
