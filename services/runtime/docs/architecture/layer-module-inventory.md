# Layer Module Inventory

## Purpose

This document is the live execution map beneath the canonical baseline.

It answers:

**what module is done, what is still active, and what should be advanced next?**

## Status Legend

- `Done`
- `In Progress`
- `Planned`
- `Placeholder`
- `Frozen`

## Priority Legend

- `P0`
- `P1`
- `P2`

## Completion Sync

### Completed on 2026-04-19

- `Intelligence | Hermes Runtime Integration`
- `Intelligence | Intelligence IO Contract`
- `State | Core State Truth Inventory`
- `Governance | Side-effect Boundary`
- `Execution | Action Catalog`
- `Execution | Request / Receipt`
- `State | State Transition`
- `Orchestration | Run Lineage`
- `Intelligence | Intelligence Run`

### Completed on 2026-04-20

- `State | Lineage / Trace`
- `Governance | Decision Language`
- `Execution | Request / Receipt (second family)`
- `Knowledge | Knowledge Definition`
- `State | Outcome Backfill`
- `Knowledge | Lesson Extraction`
- `Orchestration | Retry / Fallback / Compensation`
- `Capability | API Boundary Cleanup`
- `Knowledge | Knowledge Feedback`
- `Experience | Trace / Outcome / Knowledge Surface`
- `Execution | Additional Action Families / Adapter Consolidation`
- `Governance | Decision Language Centralization`
- `Execution | Review Family Execution`
- `Knowledge | Feedback Consumption into Governance`
- `Experience | Review / Outcome / Feedback Surface Extension`
- `State | Trace Graph Deepening`
- `Execution | Review Submit Execution`
- `Execution | Validation Family Execution`
- `Knowledge | Feedback Consumption into Intelligence`

### Completed on 2026-04-21

- `Governance | Policy Source of Truth`
- `Experience | Trace Detail Surface`
- `Experience | Trust-tier / Semantic Discipline`
- `Knowledge | Feedback Packet Objectization`
- `Execution | Success Audit Ownership Consolidation`
- `Orchestration | Recovery Policy Object`
- `Experience | Review Detail Surface`
- `State | Trace Relation Hardening`
- `Knowledge | Retrieval / Recurring Issue Aggregation`
- `Infrastructure | Health / Monitoring`

## Current Active Modules

### P2

- `Execution | Adapter Registry / Platform`
- `Experience | Global Trust-tier Rollout`
- `Intelligence | Task Taxonomy Expansion`

## Layer View

### Experience

| Layer | Module | Status | Priority | Role | Current Value | Remaining Gap | Asset | Done Criteria | Next Unlock |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Experience | Trace / Outcome / Knowledge Surface | Done | P0 | Surface real trace/outcome/knowledge signals honestly | Recommendation and pending-review dashboard cards now show real signals | Coverage is still partial | Truthful product surface | Key surfaces expose real signals without pretending closure | Trace Detail Surface |
| Experience | Review / Outcome / Feedback Surface Extension | Done | P0 | Bring review-facing signals onto existing product surfaces | Pending reviews now expose linked recommendation trace/outcome/feedback signals | No full review detail page yet | Review-facing truthful surface | Review-facing surface shows trace/outcome/feedback and honest missing states | Review Detail Surface |
| Experience | Trace Detail Surface | Done | P1 | Expose textual trace detail without graphing | `TraceDetailPanel` now exists on active dashboard surfaces | No dedicated detail page or drill-down workflow | Trace detail panel | At least one active surface can fetch and render real trace detail | Review Detail Surface |
| Experience | Trust-tier / Semantic Discipline | Done | P1 | Distinguish relation/signal/derived/artifact semantics | Shared semantic helper and trust-tier badges now constrain active dashboard copy | Not rolled out across all pages | Semantic discipline | Active surfaces stop mixing truth, hint, and artifact semantics | Global Trust-tier Rollout |
| Experience | Review Detail Surface | Done | P1 | Give review chain a richer truthful surface | Pending reviews now expose an expandable review detail panel with review fact, execution refs, outcome, and feedback packet signal | Still no standalone review detail page | Review detail surface | Review detail shows review, outcome, feedback, and execution refs truthfully | Global Trust-tier Rollout |
| Experience | Global Trust-tier Rollout | Planned | P2 | Extend truthful semantics beyond current dashboard surfaces | Local discipline exists | Not global yet | Full-surface semantic discipline | All key pages use shared trust-tier and honest missing semantics | Product-wide consistency |

### Capability

| Layer | Module | Status | Priority | Role | Current Value | Remaining Gap | Asset | Done Criteria | Next Unlock |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Capability | Boundary Spec | Done | P0 | Keep capability as product-ability layer | Boundaries are documented and used in recent modules | Drift remains possible | Boundary spec | New capability work follows explicit ownership | API Boundary Cleanup |
| Capability | API Boundary Cleanup | Done | P1 | Move routes away from router-local repo logic | High-value routes already cross capability boundaries | Compatibility facades still exist | Unified entry semantics | Core routes stop bypassing capability | Remaining facade cleanup |
| Capability | Remaining API Boundary Cleanup | In Progress | P1 | Remove remaining route/service bypasses incrementally | Inventory and pattern exist | Not complete across all read-side facades | Boundary hygiene | Core API routes can explain why they pass through capability | View adapter cleanup |

### Orchestration

| Layer | Module | Status | Priority | Role | Current Value | Remaining Gap | Asset | Done Criteria | Next Unlock |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Orchestration | Analyze Workflow | In Progress | P0 | Organize the main single-agent chain | Analyze workflow, runs, retries, compensation, and recovery policy are real | Still narrow and partly bespoke | Workflow backbone | Main chain stays controlled and traceable | Review Detail Surface |
| Orchestration | Retry / Fallback / Compensation | Done | P1 | Make failure handling explicit | Retry and compensation now exist on analyze path | Fallback and policy formalization remain weak | Recovery discipline | Main-chain failure no longer depends on hidden behavior | Recovery Policy Object |
| Orchestration | Recovery Policy Object | Done | P1 | Centralize retry/fallback/compensation semantics | Analyze recovery now runs through a formal policy object and shared recovery detail helpers | Fallback and cross-workflow policy still remain weak | Recovery policy | Steps stop relying only on ad hoc retry conventions and persisted step statuses keep honest recovery detail | Cross-workflow coordination |

### Governance

| Layer | Module | Status | Priority | Role | Current Value | Remaining Gap | Asset | Done Criteria | Next Unlock |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Governance | Side-effect Boundary | Done | P0 | Require meaningful actions to cross governance boundary | ActionContext is active on critical families | Coverage still incomplete | Policy hook | Critical side effects never bypass context and auditability | Decision Language |
| Governance | Decision Language | Done | P0 | Unify execute/escalate/reject semantics | Shared decision model is real | Not every path is fully centralized | Decision contract | Response, workflow, and audit share the same language | Policy Source of Truth |
| Governance | Decision Language Centralization | Done | P0 | Push decision language beyond analyze-only usage | Analyze and recommendation surfaces share the same payload shape | Broader path adoption still remains | Centralized decision shape | Parallel allow/block semantics stop growing | Policy Source of Truth |
| Governance | Policy Source of Truth | Done | P1 | Give governance a single active policy snapshot | Policy refs now flow through response, metadata, report, and recommendation surface | Still minimal and in-code | Policy snapshot | Governance paths stop inventing policy source ad hoc | Success Audit Ownership / richer control plane |

### Intelligence

| Layer | Module | Status | Priority | Role | Current Value | Remaining Gap | Asset | Done Criteria | Next Unlock |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Intelligence | Hermes Runtime Integration | Done | P0 | Run real analyze tasks through Hermes | Hermes-backed analyze execution is real | Broader task coverage remains narrow | Runtime adapter | Analyze no longer depends on mock-only reasoning | Intelligence feedback consumption |
| Intelligence | Intelligence Run | Done | P0 | Persist AI task run lineage | `IntelligenceRun` is a real object | More task families are needed | Run record | AI runs are queryable and traceable | Task taxonomy |
| Intelligence | Feedback Consumption into Intelligence | Done | P0 | Feed derived guidance into later reasoning context | Analyze can now consume `memory_lessons` and `related_reviews` | Still analyze-only and non-persistent | Guidance injection | Subsequent analyze runs can use derived guidance without rewriting truth | Task taxonomy |
| Intelligence | Task Taxonomy Expansion | Planned | P2 | Add more real AI task families | Analyze task is strong | Taxonomy remains narrow | Task catalog | At least one new task family exists with run persistence | Routing and eval |

### Execution

| Layer | Module | Status | Priority | Role | Current Value | Remaining Gap | Asset | Done Criteria | Next Unlock |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Execution | Action Catalog | Done | P0 | Name real actions and side-effect classes | Catalog exists and guides follow-on execution work | Ownership is still uneven | Action catalog | Real actions are named and classified | Request / Receipt |
| Execution | Request / Receipt | Done | P0 | Objectify real action execution | Multiple families now use request/receipt | Platform behavior is incomplete | Execution receipt discipline | Request/receipt is real on consequential action families | Family adapters |
| Execution | Additional Action Families / Adapter Consolidation | Done | P1 | Extend request/receipt and family adapters | Recommendation family has unified execution facade | Not generalized across all families | Family adapter pattern | More than one family is receipt-backed and adapterized | Review family execution |
| Execution | Review Family Execution | Done | P0 | Bring review completion under execution discipline | `review_complete` has request/receipt/failure refs | Submit was still missing until later | Review execution family | Review completion is execution-backed and traceable | Review Submit Execution |
| Execution | Review Submit Execution | Done | P0 | Bring review submission under same execution discipline | `review_submit` now matches response/audit/request/receipt consistency | Review downstream ownership remains split | Unified review family execution | `submit` and `complete` share one family execution pattern | Success Audit Ownership |
| Execution | Validation Family Execution | Done | P1 | Bring validation issue reporting under execution discipline | `validation_issue_report` now has request/receipt/failure refs | Validation breadth is still small | Validation execution family | Validation no longer bypasses execution semantics | Success Audit Ownership |
| Execution | Success Audit Ownership Consolidation | Done | P0 | Make success audit ownership singular per family | Recommendation status update now suppresses domain success audit and leaves adapter as sole owner | Other families may still need the same pattern as the layer grows | Audit ownership discipline | No family emits duplicate or split success ownership on consolidated paths | Adapter platform |
| Execution | Adapter Registry / Platform | Planned | P2 | Generalize discovery/common behavior for adapters | Several family adapters now exist | No platform/registry yet | Execution platform skeleton | Multi-family adapter lookup and common hooks exist | Broader execution scale |

### State

| Layer | Module | Status | Priority | Role | Current Value | Remaining Gap | Asset | Done Criteria | Next Unlock |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| State | Core Truth Inventory | Done | P0 | Define what counts as system fact | Fact-bearing objects are documented and implemented | Some relations remain softer than desired | State truth inventory | Core objects have owners and truth boundaries | Trace / Outcome |
| State | State Transition | Done | P0 | Constrain lifecycle changes on key objects | Recommendation/review/intelligence transition rules exist | Richer lifecycle coordination remains incomplete | State machine discipline | Key transitions are explicit and testable | Lineage / Trace |
| State | Lineage / Trace | Done | P0 | Build main-chain queryable relations | Trace roots for workflow and recommendation exist | Review chain used to be partial | Trace bundle | Main-chain objects are queryable together | Trace Graph Deepening |
| State | Outcome Backfill | Done | P0 | Record downstream recommendation aftermath | Review completion now backfills `OutcomeSnapshot` | Still not a richer lifecycle policy | Outcome record | Recommendation aftermath becomes state, not just narrative | Trace Graph Deepening |
| State | Trace Graph Deepening | Done | P0 | Bring review/outcome/feedback signals into trace path | `trace_review` and richer recommendation trace now exist | Some relations still rely on audit refs | Deeper trace query path | Review-side chain is visible without inventing relations | Trace Relation Hardening |
| State | Trace Relation Hardening | Done | P1 | Replace weaker audit/metadata relations where practical | Review-side execution refs and feedback packet refs now have harder persisted links and trace prefers them over audit reconstruction | Some main-chain relations are still still softer than ideal beyond the review side | Harder relation model | More main-chain relations become first-class and less audit-derived | Richer graph behavior |

### Knowledge

| Layer | Module | Status | Priority | Role | Current Value | Remaining Gap | Asset | Done Criteria | Next Unlock |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Knowledge | Knowledge Definition | Done | P0 | Separate knowledge from truth in code | Knowledge-layer objects and invariants exist | Still minimal | Boundary discipline | Narrative no longer pretends to be fact | Lesson Extraction |
| Knowledge | Lesson Extraction | Done | P0 | Extract reusable guidance from lesson/outcome fact | `LessonExtractionService` is real | Retrieval and aggregation do not exist | Derived knowledge object | Persisted lessons/outcomes can become structured knowledge entries | Knowledge Feedback |
| Knowledge | Knowledge Feedback | Done | P1 | Turn extracted knowledge into usable hints | Feedback packet is real | Packet is not persisted as first-class object | Feedback packet | Derived hints can be produced from fact-backed knowledge | Governance / Intelligence consumption |
| Knowledge | Feedback Consumption into Governance | Done | P0 | Feed derived hints into governance as advisory input | Analyze governance now reads advisory hints | Still advisory-only | Governance hint consumption | Governance can consume hints without rewriting policy | Feedback objectization |
| Knowledge | Feedback Consumption into Intelligence | Done | P0 | Feed derived hints into reasoning context | Analyze reasoning now consumes guidance hints | Still analyze-only and non-persistent | Intelligence hint consumption | Later reasoning context can use derived guidance | Feedback objectization |
| Knowledge | Feedback Packet Objectization | Done | P0 | Persist feedback packet as queryable object | Feedback packet is now a first-class persisted object and downstream readers can prefer it over recomputation | Retrieval, aggregation, and analytics still do not exist | Feedback record | Feedback packets are queryable, traceable, and remain derived rather than truth | Retrieval / aggregation |
| Knowledge | Retrieval / Recurring Issue Aggregation | Done | P1 | Make knowledge queryable and aggregatable | Retrieval by recommendation/review/symbol and recurring-issue summaries now exist over persisted lessons, outcomes, and feedback packets | No query API or rule-candidate promotion yet | Retrieval and aggregation layer | Relevant knowledge can be pulled by object/symbol and recurring issues can be identified without inventing truth | Rule candidates |

### Infrastructure

| Layer | Module | Status | Priority | Role | Current Value | Remaining Gap | Asset | Done Criteria | Next Unlock |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Infrastructure | Wiring / Startup | In Progress | P1 | Keep local runtime bootable and understandable | Current runtime is bootable | Responsibility is still scattered | Startup spec | Runtime startup no longer depends on hidden knowledge | Health / Monitoring |
| Infrastructure | Health / Monitoring | Done | P1 | Surface runtime and failure health honestly | `/api/v1/health` now exposes monitoring snapshot fields backed by workflow, execution, and audit data, and the system status bar reflects them honestly | Monitoring history and ops discipline are still minimal | Health signals | Key runtime components and recent failure counts are visible without overstating certainty | Runbook / Ops |
| Infrastructure | Runbook / Ops | Planned | P2 | Turn recovery knowledge into durable operations docs | Some runbooks exist | System ops discipline is still weak | Ops runbook | Common failure and recovery steps are documented | Recovery maturity |

## Current Execution Rule

Every module advancement must leave:

- a module card in `knowledge/wiki/architecture/module-cards/`
- tests
- a status sync in:
  - `docs/architecture/layer-module-inventory.md`
  - the latest `current-state-report-YYYY-MM-DD.md`
  - `docs/tasks/README.md`

See:

- [Status Sync Workflow](../workflows/status-sync-workflow.md)
