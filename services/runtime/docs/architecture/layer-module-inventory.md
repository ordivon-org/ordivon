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

### Completed on 2026-04-22

- `Cross-layer | Phase 0 Core Primitive Freeze`
  - `DecisionLanguage`
  - `ActionRequest / ActionReceipt`
  - `Outcome`
  - `FeedbackPacket`
  - `TraceLink`
  - `Task / Run`
  - `AgentRuntime`
  - `MemoryPolicy`
- `Cross-layer | Phase 1 Core Load-Bearing Batch`
  - `GovernancePolicySource` deepening
  - `FeedbackHintConsumer`
  - `HumanApprovalGate`
  - `HintAwareContextBuilder`
  - `ExecutionAdapterRegistry`
  - `Progress / Heartbeat`
  - `TraceGraph`
  - `OutcomeGraph`
  - `CheckpointState`
  - `FeedbackRecord`
  - `RecurringIssueAggregator` formalization
  - `CandidateRule`
- `Cross-layer | Post-Phase-1 Serial Modules`
  - `Finance Pack Extraction Planning`
  - `Hermes Runtime Adapter Extraction`
  - `Orchestration HandoffArtifact`
  - `Orchestration WakeResume / Fallback`
  - `Infrastructure Scheduler`
  - `Infrastructure Monitoring History / Runbook Discipline`
  - `Experience Global Trust-tier Rollout`
  - `Experience ReviewConsole + Tabbed Workspace`
- `Cross-layer | Extraction / Workspace Refinement`
  - `Finance Pack Analyze Profile Ownership`
  - `Hermes Provider Alias Cleanup`
  - `Broader Console Workspace Behavior`
- `Cross-layer | MVP Gold Path / Finance Frontend Analyze Surface`
  - `Finance Pack Frontend Analyze Surface Extraction`
  - `Homepage / Analyze / Reviews Role Split`

## Current Active Modules

### P0

- `No active P0 modules in this batch`
- `Next batch should be selected after this serial module wave`

## Layer View

### Experience

| Layer | Module | Status | Priority | Role | Current Value | Remaining Gap | Asset | Done Criteria | Next Unlock |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Experience | Trace / Outcome / Knowledge Surface | Done | P0 | Surface real trace/outcome/knowledge signals honestly | Recommendation and pending-review dashboard cards now show real signals | Coverage is still partial | Truthful product surface | Key surfaces expose real signals without pretending closure | Trace Detail Surface |
| Experience | Review / Outcome / Feedback Surface Extension | Done | P0 | Bring review-facing signals onto existing product surfaces | Pending reviews now expose linked recommendation trace/outcome/feedback signals | No full review detail page yet | Review-facing truthful surface | Review-facing surface shows trace/outcome/feedback and honest missing states | Review Detail Surface |
| Experience | Trace Detail Surface | Done | P1 | Expose textual trace detail without graphing | `TraceDetailPanel` now exists on active dashboard surfaces | No dedicated detail page or drill-down workflow | Trace detail panel | At least one active surface can fetch and render real trace detail | Review Detail Surface |
| Experience | Trust-tier / Semantic Discipline | Done | P1 | Distinguish relation/signal/derived/artifact semantics | Shared semantic helper and trust-tier badges now constrain active dashboard copy | Not rolled out across all pages | Semantic discipline | Active surfaces stop mixing truth, hint, and artifact semantics | Global Trust-tier Rollout |
| Experience | Review Detail Surface | Done | P1 | Give review chain a richer truthful surface | Pending reviews now expose an expandable review detail panel with review fact, execution refs, outcome, and feedback packet signal | Still no standalone review detail page | Review detail surface | Review detail shows review, outcome, feedback, and execution refs truthfully | Global Trust-tier Rollout |
| Experience | Global Trust-tier Rollout | Done | P0 | Extend truthful semantics beyond current dashboard surfaces | Shared `TrustTier` typing and rendering now back dashboard and review surfaces | Product-wide rollout beyond current surfaces still remains | Full-surface semantic discipline | Key pages use shared trust-tier and honest missing semantics | ReviewConsole / Tabbed Workspace |
| Experience | ReviewConsole / Tabbed Workspace | Done | P0 | Add a dedicated review workspace and minimal object-tab shell | `/reviews` route, `ReviewConsole`, and minimal workspace tabs now exist | Full-app workspace and richer navigation remain future work | Supervisor workspace | Review supervision is no longer dashboard-only and object tabs can hold review/trace views | Workspace refinement |
| Experience | Workspace Refinement Beyond Review Console | Done | P1 | Deepen the review workspace so active tabs render richer linked object content | Review console now renders recommendation tabs and can seed initial review state from route input | Workspace remains console-local and not full-app | Linked object workspace | Review, trace, and recommendation tabs all render meaningful content | Broader workspace behavior |
| Experience | Broader Console Workspace Behavior | Done | P1 | Extend shared object-tab behavior to more console routes without becoming a full-site shell | Audits, reports, and history now sit inside the console frame, query params can seed workspace tabs, and audit surfaces can open related object tabs | Workspace still remains scoped to console pages and three object-tab types | Broader console workspace | Console workspace survives and opens object tabs across more than dashboard/reviews without adding a global shell | Richer console navigation |
| Experience | MVP Gold Path / Page Role Split | Done | P0 | Make homepage the command center, `/analyze` the execution workspace, and `/reviews` the primary supervision workbench | Product copy and route handoff now bias users through one clearer command-center -> analyze -> reviews path | Broader product-path simplification still remains | MVP role split | Homepage, analyze, and reviews stop competing for deep-work ownership | Further product-path refinement |

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
| Orchestration | HandoffArtifact | Done | P0 | Persist blocked workflow handoff as a formal orchestration object/ref | Analyze governance block can now attach a handoff artifact ref and blocked reason | Broader long-running adoption remains future work | Handoff contract | Blocked workflows produce formal handoff refs rather than UI-only story blobs | Wake / Resume / broader orchestration |
| Orchestration | WakeResume / Fallback | Done | P0 | Add minimal wake/resume semantics and degraded fallback behavior | Analyze now records wake/resume metadata and can degrade after retry exhaustion instead of silently succeeding | General resume execution remains future work | Runtime recovery semantics | Retry exhaustion can produce honest degraded fallback and task run semantics keep wake/resume refs | Long-running orchestration |

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
| Infrastructure | Scheduler | Done | P1 | Introduce infrastructure-owned low-risk trigger dispatch | `infra/scheduler/` now owns scheduled trigger registration/dispatch for capability-facing paths | No persistent scheduler backend or UI exists yet | Trigger infrastructure | Low-risk periodic work can be registered without leaking business semantics into infra | Monitoring history / deeper ops |
| Infrastructure | Runbook / Ops | Done | P1 | Turn recovery knowledge into durable operations docs and extend monitoring history | Health now exposes minimal history summary and runbooks cover blocked review/runtime/trace cases | Ops UI and richer history remain future work | Ops discipline | Common failure and recovery steps are documented and health has minimal history context | Recovery maturity |
| Infrastructure | Scheduler Persistence / Trigger Orchestration | Done | P1 | Persist low-risk triggers and support richer dispatch without changing ownership boundaries | Scheduler can now save/load triggers and dispatch all enabled entries while staying capability-facing | No database-backed scheduler or cron UI exists yet | Persistent trigger infrastructure | Trigger state survives process boundaries and batch dispatch remains infra-owned | Scheduler backend refinement |
| Infrastructure | Monitoring History Depth / Ops Refinement | Done | P1 | Deepen history summary with top failures and blocked-run refs | Health now exposes top workflow/execution failure summaries and blocked run ids | Still not a full observability product | Deeper ops summary | Operational history is richer without becoming business truth | Observability refinement |
| Infrastructure | Monitoring Ops History Endpoint | Done | P1 | Add a dedicated operational history endpoint and align runbooks to richer history state | `/api/v1/health/history` now exposes blocked runs, approval-blocked refs, recent failure rows, and scheduler trigger summary | Still not a full ops console | Operational history endpoint | Operators can inspect richer history without stretching compact health into an all-purpose surface | Further ops refinement |

### Pack Layer

| Layer | Module | Status | Priority | Role | Current Value | Remaining Gap | Asset | Done Criteria | Next Unlock |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Pack Layer | Finance Pack Extraction Planning | Done | P0 | Freeze finance-specific candidates without migrating them | `packs/finance/` planning docs and inventory now exist and candidate files are marked | No physical finance-pack migration happened yet | Finance pack plan | Finance-specific files are explicitly inventoried without re-injecting finance into core | Future staged extraction |
| Pack Layer | Finance Pack Staged Extraction | Done | P1 | Move the first finance-shaped owner into `packs/finance` while preserving compatibility shims | Finance analysis context defaults now live in `packs/finance/context.py` and orchestration modules delegate to them | Only the context owner moved; broader finance extraction remains future work | First pack-backed shim | Finance ownership starts moving out of orchestration without broad import churn | Further staged extraction |
| Pack Layer | Finance Pack Capability Defaults Extraction | Done | P1 | Move finance-specific analyze defaults out of capability ownership and into the finance pack | `AnalyzeCapability` now reads default symbol/timeframe values from `packs/finance/analyze_defaults.py` instead of hard-coding them | Broader finance-specific capability wording and policy ownership still remain | Pack-owned analyze defaults | Capability no longer owns finance defaults directly and public contract remains unchanged | Further staged extraction |
| Pack Layer | Finance Pack Policy / Tool Ownership | Done | P1 | Move finance policy/tool namespace ownership behind pack-owned facades | `packs/finance/policy.py` and `packs/finance/tool_refs.py` now own trading-limits overlay refs and finance tool namespace refs | Physical tool/domain extraction still remains future work | Pack-owned finance refs | Finance policy/tool ownership no longer needs to sit in core-facing entrypoints | Further staged extraction |
| Pack Layer | Finance Pack Analyze Profile Ownership | Done | P1 | Move finance analyze request/profile defaults and supported options behind pack-owned semantics | `packs/finance/analyze_profile.py` now owns default symbol/timeframe and supported finance options used by API/workflow entrypoints | Front-end finance-specific analyze widgets still remain separate | Pack-owned analyze profile | Finance analyze request shape no longer needs to be owned by API/workflow defaults | Deeper finance extraction |
| Pack Layer | Finance Pack Frontend Analyze Surface Extraction | Done | P0 | Move finance-shaped analyze option ownership for command-center and analyze workspace UI behind a pack-owned surface helper | `QuickAnalyze` and `AnalyzeInput` now consume pack-owned defaults/options rather than hard-coded finance strings | Broader finance-specific product wording still remains | Pack-owned frontend analyze options | Generic UI components stop owning finance analyze defaults and supported options | Deeper finance extraction |

### Adapter Layer

| Layer | Module | Status | Priority | Role | Current Value | Remaining Gap | Asset | Done Criteria | Next Unlock |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Adapter Layer | Hermes Runtime Adapter Extraction | Done | P0 | Introduce `adapters/runtimes/hermes` and demote the old provider path into a shim | Hermes runtime is now adapter-backed and the legacy provider path wraps it | Physical runtime/provider cleanup remains future work | Runtime adapter skeleton | Hermes runtime ownership no longer lives only inside `intelligence/providers/` | Broader adapter extraction |
| Adapter Layer | Hermes Runtime Provider Cleanup | Done | P1 | Point runtime resolution directly at the adapter and keep the old provider path as compatibility-only shim | `ReasoningProviderRouter` now resolves Hermes through `adapters.runtimes.factory.resolve_runtime()` | The legacy shim still exists for compatibility and broader provider cleanup remains future work | Adapter-owned runtime resolution | Router/runtime ownership is adapter-first rather than provider-first | Broader runtime/provider simplification |
| Adapter Layer | Hermes Runtime Shim Reduction | Done | P1 | Make runtime-owned health and descriptor behavior adapter-first and reduce shim behavior further | API health now resolves runtime through the adapter factory and `AgentRuntime.health()` is part of the runtime contract | Legacy provider shim still exists for compatibility | Runtime-owned health contract | Hermes health/descriptor behavior is owned by runtime implementations rather than the provider shim | Further runtime/provider simplification |
| Adapter Layer | Hermes Provider Alias Cleanup | Done | P1 | Reduce the legacy provider path to a compatibility alias over the adapter-owned runtime | `intelligence/providers/hermes_agent_provider.py` now aliases `HermesRuntime` directly | Older docs/import expectations may still describe provider-owned Hermes behavior | Compatibility alias | Legacy Hermes provider path no longer carries behavior-level ownership | Deeper legacy cleanup |

## Current Execution Rule

Every module advancement must leave:

- tests
- a status sync in:
  - `docs/architecture/layer-module-inventory.md`
  - the latest `current-state-report-YYYY-MM-DD.md`
  - `docs/tasks/README.md`
  - relevant `docs/architecture/*` batch docs

See:

- [Status Sync Workflow](../workflows/status-sync-workflow.md)
- [AegisOS Phase 1 Core Load-Bearing Batch](./aegisos-phase-1-core-load-bearing-batch.md)
- [AegisOS Next Batch Serial Modules 2026-04-22](./aegisos-next-batch-serial-modules-2026-04-22.md)
