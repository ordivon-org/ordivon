# Core / Pack / Adapter Baseline

## Status

This document defines the first repository-level baseline for platformizing PFIOS as:

- `core` for stable system primitives
- `packs` for domain implementations
- `adapters` for external/runtime/storage/tooling integrations

It is intentionally a classification and migration baseline, not a directory-rewrite order.

## Purpose

PFIOS has already achieved meaningful responsibility layering:

- Experience
- Capability
- Orchestration
- Governance
- Intelligence
- Execution
- State
- Knowledge
- Infrastructure

That layer model answers:

**which responsibility surface owns which kind of work?**

The next platform question is different:

**which parts of the system are stable operating-system primitives, which are domain packs, and which are replaceable adapters?**

This document answers that second question.

## One-Sentence Rule

Do not generalize everything.

Generalize only the stable cross-domain rules.

That means:

- `core` owns order
- `pack` owns domain semantics
- `adapter` owns implementation integration

## Classification Tests

When deciding whether something belongs in `core`, `pack`, or `adapter`, use these tests.

### Core tests

A thing is a strong `core` candidate when at least two of these are true:

- it exists across multiple domains
- it defines system sovereignty, truth, or action discipline
- it changes slowly
- changing it affects many layers

### Pack tests

A thing is a strong `pack` candidate when any of these are true:

- it is finance-specific or otherwise domain-specific
- it is strongly coupled to one family of business objects
- it is likely to be replaced by another domain implementation later

### Adapter tests

A thing is a strong `adapter` candidate when any of these are true:

- it integrates an external provider or runtime
- it integrates a tool, connector, or storage backend
- the implementation detail changes faster than the system semantics
- it should be swappable without redefining the system model

## What Belongs In Core

PFIOS `core` should contain only stable cross-domain primitives.

### 1. Workflow primitives

- `Task`
- `Workflow`
- `Step`
- `Run`
- `StepResult`
- `RetryPolicy`
- `FallbackPolicy`
- `CompensationAction`
- `Pause / Resume / Cancel`

Why:

These are process laws, not finance laws.

### 2. Governance primitives

- `DecisionLanguage`
- `ActionContext`
- `ApprovalRequirement`
- `Policy`
- `RiskFlag`
- `EligibilityCheck`
- `HumanReviewGate`

Why:

These define what the system may do under constraint.

### 3. Execution primitives

- `ActionFamily`
- `ActionRequest`
- `ActionReceipt`
- `ActionResult`
- `FailureModel`
- `Adapter`
- `IdempotencyKey`
- `Heartbeat / Progress`
- `SideEffectClass`

Why:

The discipline of action is cross-domain even when specific actions are not.

### 4. State primitives

- `EntityRef`
- `StateRecord`
- `LifecycleState`
- `StateTransition`
- `SourceOfTruth`
- `Relation`
- `TraceLink`
- `Outcome`
- `ArtifactRef`

Why:

All domains need formal fact, lifecycle, and relation semantics.

### 5. Trace and audit primitives

- `AuditEvent`
- `EventType`
- `TraceBundle`
- `RequestReceiptRefs`
- `Actor`
- `Timestamp`
- `CausalityEdge`

Why:

Auditability and lineage mechanics are system-level, not finance-level.

### 6. Knowledge primitives

- `Lesson`
- `KnowledgeEntry`
- `FeedbackPacket`
- `Hint`
- `EvidenceBundle`
- `CandidateRule`
- `RecurringIssue`
- `FeedbackConsumptionRecord`

Why:

The learning loop is cross-domain even if its extraction rules are not.

### 7. Runtime primitives

- `AgentRuntime`
- `TaskRuntime`
- `Session`
- `ContextBuilder`
- `MemoryPolicy`
- `ToolPolicy`
- `RuntimeHealth`
- `Wake / Sleep / Resume`

Why:

Runtime semantics should remain stable when providers change.

### 8. Experience primitives

- `WorkView`
- `ObjectView`
- `DetailPane`
- `SupervisorAction`
- `MissingState`
- `TrustTier`
- `StatusSurface`
- `TraceSurface`
- `OutcomeSurface`
- `HintSurface`

Why:

Front-end truthful semantics are reusable even when domain pages change.

## What Belongs In Packs

`packs` contain domain meaning, domain objects, and domain-specific workflows.

### Finance pack examples

These should be treated as `finance pack` responsibilities, even if the code is not yet moved into `packs/finance/`:

- `Recommendation`
- `Review`
- recommendation status semantics
- recommendation workflows
- review completion semantics
- finance-specific validation semantics
- BTC/USDT-style symbol-centered analysis inputs
- outcome interpretation rules tied to finance recommendation lifecycle
- finance lesson extraction and recurring-issue normalization rules

Why:

These are not system primitives. They are the first concrete domain mounted on the system.

### Future pack examples

- `research pack`
- `ops pack`
- `compliance pack`
- `personal cognition pack`

Each pack should own:

- domain objects
- domain workflows
- domain policies
- domain action families
- domain extractors
- domain surfaces

## What Belongs In Adapters

`adapters` connect the stable system model to replaceable implementations.

### Runtime adapters

- Hermes runtime bridge
- OpenAI runtime integration
- Anthropic runtime integration
- future model-router/provider implementations

### Execution adapters

- wiki/document writers
- notification senders
- tool connectors
- external side-effect bridges

### Storage adapters

- DuckDB backend
- future PostgreSQL backend
- blob/vector storage integrations

### Knowledge adapters

- external research connectors
- future NotebookLM or similar external knowledge-source bridges

Why:

These change faster than system semantics and should not define the platform model.

## Current Repository Mapping

The repository is not yet physically organized as `core/`, `packs/`, and `adapters/`.

But conceptually it already contains all three.

### Closest current core zones

- `orchestrator/`
- `governance/`
- `execution/` primitive and receipt discipline
- `state/` fact and trace primitives
- `knowledge/` primitives and feedback mechanics
- `intelligence/` runtime/task abstractions
- Experience semantic helpers in `apps/web`

Important caveat:

These directories are not pure `core` yet. Some still contain finance-heavy semantics and should be progressively separated.

### Closest current finance-pack zones

- `domains/strategy/`
- `domains/journal/`
- finance-facing parts of `capabilities/workflow/`
- finance recommendation/review/outcome/validation surfaces in `apps/`
- finance-specific lesson extraction and recurring issue logic in `knowledge/`

Important caveat:

These are not yet packaged as a formal `finance pack`. They are finance-domain implementations living inside the current layered repo.

### Closest current adapter zones

- Hermes bridge and Hermes runtime client paths
- provider integrations in `intelligence/providers/`
- storage bootstrap/backend wiring
- report/wiki writing flows
- concrete execution connectors in `tools/` and `skills/`

Important caveat:

Some adapter code still sits next to higher-level semantics. The long-term job is clearer interface separation, not adapter proliferation for its own sake.

## Migration Guidance For The Current Repo

Do not start with a giant directory rewrite.

Use this sequence instead.

### Phase 1: freeze primitives

Define and stabilize the operating-system primitives first:

- `DecisionLanguage`
- `ActionRequest / ActionReceipt`
- `Outcome`
- `FeedbackPacket`
- `TraceLink`
- `Task / Workflow / Run`
- `AgentRuntime`
- `TrustTier / MissingState`

### Phase 2: classify current code

Every major object should get one of three labels:

- `core primitive`
- `finance-pack implementation`
- `adapter`

This classification should happen before moving directories.

### Phase 3: extract interfaces, not folders first

Before moving code, make the interfaces explicit:

- runtime interfaces
- execution adapter contracts
- knowledge extractor interfaces
- front-end surface semantics

### Phase 4: name finance as the first pack

Treat current recommendation/review/outcome/feedback workflows as:

**Finance Pack v1**

That gives the current system a stable domain identity without pretending those objects are universal.

### Phase 5: only then consider physical repo moves

Once primitives and interfaces are stable:

- create `core/`
- create `packs/finance/`
- create `adapters/`

Until then, logical classification matters more than folder purity.

## Immediate Practical Rules

Use these rules for new work now, even before repo moves happen.

### Rule 1

If a new object is likely to exist in finance, research, ops, and compliance, design it as `core`.

### Rule 2

If a new object only makes sense for recommendations, reviews, market symbols, or finance risk posture, treat it as `finance pack`, not `core`.

### Rule 3

If a new integration touches a provider, tool, or backend implementation, treat it as an `adapter`.

### Rule 4

Do not put domain nouns into `core` just because they are currently central to the product.

### Rule 5

Do not put external implementation details into `core` just because they are currently the only working version.

## Non-Goals

This baseline does not do the following:

- it does not declare an immediate repo rewrite
- it does not make finance secondary; finance remains the active first domain
- it does not force every current directory into a new top-level folder now
- it does not pretend current modules are already perfectly pure

## Final Summary

PFIOS should evolve toward a platform model where:

- `core` owns stable system order
- `pack` owns domain meaning
- `adapter` owns replaceable implementation detail

In the current repository, the right next step is not a large rewrite.

The right next step is:

1. freeze primitives
2. classify current code
3. name finance as `pack v1`
4. gradually separate adapters from semantics

Compressed:

**Core owns order. Pack owns domain. Adapter owns integration.**
