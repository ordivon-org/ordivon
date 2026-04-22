# Architecture Baseline

## Status

This document is the canonical architecture baseline for the repository as of `2026-04-22`.

Older migration notes, closure reports, and step reports remain historical references only. They do not override this baseline.

## Project Identity

PFIOS is not a simple AI harness, not a normal trading system, and not a chat shell wrapped around a model.

PFIOS is:

**a controlled AI operating-system foundation for high-constraint real tasks.**

Its purpose is not to maximize model freedom. Its purpose is to:

- let AI participate in judgment
- let the system decide what is allowed
- let real actions be executed under control
- let results enter the fact layer
- let history accumulate into knowledge
- let knowledge improve future behavior

Compressed further:

**PFIOS closes the loop between AI judgment, system governance, action execution, factual state, and accumulated knowledge.**

## What PFIOS Is Not

PFIOS is not:

- just a prompt-engineering project
- just a coding-agent harness
- just a trading strategy program
- just a CRUD finance backend
- just a free-form agent system with tools attached
- just a narrative AI shell with weak truth constraints

Harnesses, workflows, agent runtimes, and finance-domain applications may all exist inside PFIOS, but none of them is the full system identity.

## Who PFIOS Serves

### 1. High-constraint real tasks

Tasks where:

- AI participates in judgment
- real actions may happen
- control is mandatory
- lineage is mandatory
- experience accumulation matters

Finance is the starting domain, not the only long-term one.

### 2. The people building and running such systems

- developers
- system designers
- operators
- auditors
- governance and policy owners

### 3. Future vertical domains

PFIOS can later support any domain where:

- AI participates in judgment
- actions have real risk
- outcomes must be recorded
- history must accumulate
- governance and feedback are mandatory

## Project Goal

The project goal is:

**to build an AI operating system that performs real analysis, enables controlled execution, persists traceable fact, accumulates reusable knowledge, and keeps improving over time.**

In practice this means five core abilities:

1. judge
2. constrain
3. execute
4. record truth
5. accumulate and feed back learning

## Architecture Principles

All future design should follow these principles.

### Principle 1: the model is not the system

The model is only a cognitive component inside the system.

### Principle 2: give judgment to AI, give precision to code

- semantic judgment, candidate generation, weak planning -> AI
- precise calculation, state transition, schema validation, tool invocation -> code

### Principle 3: every real action must pass governance

No meaningful side effect should happen outside a governance boundary.

### Principle 4: State owns fact, Knowledge owns experience

Narrative must not overwrite truth.

### Principle 5: loop truth matters more than layer purity

First make the real chain run. Then continue purifying the structure.

### Principle 6: when the model fails, improve the harness first

Harness engineering is a first-class design responsibility.

### Principle 7: every completed task must leave an asset

At least one reusable asset should remain:

- contract
- workflow
- adapter
- audit trail
- state record
- knowledge record
- metrics
- policy hook

### Principle 8: generalize only stable system laws

Do not generalize everything.

Only generalize the patterns that are stable across domains.

That means:

- stable operating-system primitives belong in `core`
- domain semantics belong in `packs`
- replaceable external integrations belong in `adapters`

See:

- [Core / Pack / Adapter Baseline](./core-pack-adapter-baseline.md)
- [Core Primitives Spec v1](./core-primitives-spec-v1.md)
- [Adapter Boundary Spec v1](./adapter-boundary-spec-v1.md)
- [AegisOS Design Doctrine](./aegisos-design-doctrine.md)
- [AegisOS Phase 0 Core Primitive Freeze](./aegisos-phase-0-core-primitives-batch.md)
- [AegisOS Phase 1 Core Load-Bearing Batch](./aegisos-phase-1-core-load-bearing-batch.md)
- [AegisOS Next Batch Serial Modules 2026-04-22](./aegisos-next-batch-serial-modules-2026-04-22.md)

## Post-Phase-1 Serial Batch

Canonical truth now additionally includes:

- `packs/` in planning form, with `packs/finance/` as the first staged pack inventory
- `adapters/runtimes/hermes/` as the first explicit runtime adapter home
- orchestration-owned handoff, wake/resume, and degraded fallback semantics on analyze
- infrastructure-owned scheduler primitives and monitoring-history summary
- shared front-end `TrustTier` semantics and a dedicated `/reviews` supervision route
- pack-owned finance policy/tool reference facades for trading limits and finance tool namespaces
- pack-owned finance analyze profile defaults and supported-option semantics
- runtime-owned health through the `AgentRuntime` contract and adapter factory
- a legacy Hermes provider path reduced to compatibility alias status
- DB-backed scheduler persistence alongside file fallback
- a dedicated `/api/v1/health/history` operational history endpoint
- console-shared workspace state across dashboard and reviews without a full-site tab shell
- broader console workspace visibility across audits, reports, and history with query-param seeding
- pack-owned finance analyze surface options now drive homepage and analyze workspace input defaults
- homepage now acts as the live command center, `/analyze` as the execution workspace, and `/reviews` as the primary review workbench

These changes do not yet represent full physical pack extraction or full adapter migration.
They are the minimum real batch that makes those boundaries visible in the repository.

## Canonical Layer Model

PFIOS now formally uses **nine responsibility surfaces** for design and task planning, even though some migration-era docs still describe an eight-layer repo skeleton.

That means:

- the repo still contains the earlier eight-layer migration framing
- but the canonical design baseline is now a **nine-surface model**
- the split that matters most is `State` versus `Knowledge`

The nine responsibility surfaces are:

1. Experience
2. Capability
3. Orchestration
4. Governance
5. Intelligence
6. Execution
7. State
8. Knowledge
9. Infrastructure

These nine surfaces still answer the main ownership question:

**which responsibility layer owns which kind of work?**

The platformization question is separate:

**which parts of the system are stable `core`, which are domain `packs`, and which are replaceable `adapters`?**

That second classification is now governed by:

- [Core / Pack / Adapter Baseline](./core-pack-adapter-baseline.md)

## 1. Experience

### Definition

The human-facing entry layer.

### Responsible for

- pages
- API surface
- product semantics
- user-visible state
- object visibility
- consequence communication

### Not responsible for

- business truth
- hidden rule decisions
- silent semantic invention
- disguising failure as success or empty state

### Current state

Materially stronger than before, with truthful recommendation/review surfaces, expandable review detail, textual trace detail, and local trust-tier discipline on active dashboard views.

### Concrete home

- `apps/`

## 2. Capability

### Definition

The product ability layer that answers: **what can the user ask the system to do?**

### Responsible for

- analyze
- review
- reporting
- outcome tracing
- user-visible capability contracts

### Not responsible for

- page aggregation
- raw domain ownership
- swallowing workflows whole
- turning into a technical junk drawer

### Current state

Meaningfully stronger than before, but still vulnerable to drift through remaining compatibility facades.

### Concrete home

- `capabilities/`
- closely related `domains/` support

## 3. Orchestration

### Definition

The process organization layer that answers: **how is this thing run?**

### Responsible for

- workflow sequencing
- dependency ordering
- run lineage
- retries
- fallback
- compensation
- step status

### Not responsible for

- business truth ownership
- policy judgment
- direct external side effects
- becoming a generic glue trash layer

### Current state

Analyze is a real workflow with run lineage, retry, compensation, and a formal recovery policy object, but orchestration is still not a full control plane.

### Concrete home

- `orchestrator/`

## 4. Governance

### Definition

The unified constraint and audit layer that answers: **what is allowed, under what conditions, and how is it recorded?**

### Responsible for

- policy
- authorization
- side-effect boundary
- decision language
- auditability
- future policy feedback

### Not responsible for

- primary AI reasoning
- page behavior
- physical execution of actions
- acting as the fact store

### Current state

Stronger than before: centralized decision language, central policy-read entry, explicit advisory hint consumer contract, and a new approval primitive now exist, but governance is still not a full control plane.

### Concrete home

- `governance/`

## 5. Intelligence

### Definition

The AI runtime layer that answers: **how does AI think, route, and return bounded structured candidates?**

### Responsible for

- provider and model routing
- Hermes runtime integration
- AI task execution
- structured reasoning outputs
- AI task taxonomy
- eval hooks

### Not responsible for

- final business truth
- raw execution side effects
- governance decisions
- final knowledge ownership

### Current state

This remains a key rising layer. Hermes is real, runtime callers now target `AgentRuntime`, and feedback-derived guidance now enters analyze through an explicit hint-aware context builder under `MemoryPolicy`.

### Concrete home

- `intelligence/`

## 6. Execution

### Definition

The real action layer that answers: **how do actions actually happen?**

### Responsible for

- tool calls
- connector actions
- wiki and document writes
- notifications
- artifact publishing
- external sync
- execution requests and receipts

### Not responsible for

- business semantics
- permission decisions
- state truth ownership
- narrative knowledge

### Current state

Now materially stronger: recommendation, review, and validation action families have real request/receipt paths, a registry-based adapter contract now exists, and execution can record progress/heartbeat, but the layer still lacks fuller platform consolidation.

### Concrete home

- `execution/`
- `skills/`
- `tools/`

## 7. State

### Definition

The fact layer that answers: **what has actually happened in the system?**

### Responsible for

- business objects
- repositories
- ORM models
- state transitions
- event truth
- lineage relations
- outcome backfill

### Not responsible for

- narrative summaries
- candidate rules
- experience interpretation
- being overwritten by model prose

### Current state

One of the strongest and clearest layers in the system, with trace now explicitly formalized as a graph/query contract, outcome traversal clarified through `OutcomeGraph`, and checkpoint semantics stabilized on `WorkflowRun.lineage_refs`.

### Concrete home

- `state/`
- fact-bearing parts of `domains/`

### Active inventory

- [State Truth Inventory](./state-truth-inventory.md)

## 8. Knowledge

### Definition

The experience layer that answers: **what did the system learn from fact?**

### Responsible for

- lessons
- postmortems
- rule candidates
- recurring issue summaries
- evidence-backed narrative memory
- reusable guidance

### Not responsible for

- live source-of-truth state
- direct audit substitution
- governance source-of-truth policy
- fact overwrite

### Current state

No longer placeholder-level: extraction, feedback consumption, persisted feedback packets, retrieval, recurring issue aggregation, feedback-consumption records, and pre-policy candidate rules are all real, but knowledge is still weak in product surfacing, retrieval APIs, and rule promotion workflows.

### Concrete home

- `knowledge/`
- knowledge-facing parts of `wiki/`

## 9. Infrastructure

### Definition

The runtime conditions layer that answers: **how is the system started, deployed, monitored, and recovered?**

### Responsible for

- wiring
- startup
- config
- secrets
- health checks
- monitoring
- runbooks
- operations discipline

### Not responsible for

- business semantics
- capability ownership
- governance logic
- substituting for execution or state

### Current state

Materially better than before: runtime health now includes a monitoring snapshot over workflow, execution, and audit activity, but the layer still does not own monitoring history, runbooks, or operations discipline.

### Concrete home

- `infra/`

## Key Cross-Layer Relationships

### Experience vs Capability

- Experience answers how the system is surfaced.
- Capability answers what the user can ask it to do.
- Experience must not invent capability semantics.

### Capability vs Domain

- Domain owns business objects and business rules.
- Capability owns product action entry.
- They may remain close during migration, but they are not the same responsibility surface.

### Orchestration vs Governance

This is one of the most important relationships in the system.

- Orchestration organizes steps.
- Governance decides whether the meaningful action is allowed.

Compressed:

**Orchestration decides how it runs. Governance decides whether it may run.**

### Intelligence vs Execution

This boundary must stay hard.

- Intelligence thinks, judges, routes, and returns bounded candidates.
- Execution performs real actions and records receipts.

Compressed:

**Intelligence is the brain. Execution is the hand.**

### State vs Knowledge

This boundary must remain hard over time.

- State stores truth.
- Knowledge stores learning.

Compressed:

**State is truth. Knowledge is learning.**

## AI Behavior Baseline

All future AI-facing design should follow these rules.

1. AI may only produce structured candidates, not final system truth.
2. AI may not directly trigger consequential side effects outside governance.
3. AI output must pass contract, parser, and validator boundaries.
4. AI tasks must be task-based, not unbounded free-form runtime behavior.
5. AI errors must be isolated to debuggable steps.
6. When AI fails, improve harness and environment first, not just the prompt.
7. Every AI task should expose:
   - input boundary
   - output boundary
   - failure path
   - lineage
   - observability

## Tooling Baseline

The tool layer belongs to Execution, not Intelligence.

Execution should eventually expose:

### 1. Tool / Action Catalog

Each action should define:

- name
- input schema
- output schema
- side-effect level
- receipt type
- governance requirement

### 2. Execution Request

Each request should define:

- action type
- target
- payload
- actor
- context
- reason
- idempotency key

### 3. Execution Receipt

Each receipt should define:

- result
- external reference
- timestamp
- success or failure
- error detail
- trace id

### 4. Governance Hook

Meaningful execution should cross authorization boundaries before action.

### 5. State Hook

Execution results should be able to enter state, audit, and lineage.

## The Real Flywheel

PFIOS does not measure success as “the AI gets smarter” in the abstract.

The real flywheel is:

### Input

user or system initiates a task

### Judgment

Intelligence produces structured candidate output

### Constraint

Governance decides:

- execute
- escalate
- reject

### Action

Execution performs the real action and emits a receipt

### Fact

State records:

- objects
- transitions
- lineage
- outcomes

### Experience

Knowledge extracts from:

- reports
- validation
- outcomes
- recurring issues

into:

- lessons
- candidate rules
- future guidance

### Feedback

Knowledge and outcome then influence:

- governance policy
- intelligence context
- reporting quality
- workflow tuning

That is the real flywheel.

## Module Management Baseline

Future project management should use:

**layer -> module -> task -> asset**

Every module should carry:

- layer
- module definition
- current status
- priority
- owned objects
- served loop
- produced assets
- completion standard
- next unlocked module

Standard module statuses:

- `Done`
- `In Progress`
- `Planned`
- `Placeholder`
- `Frozen`

Every task should answer:

- Layer
- Type
- Object
- Loop
- Asset
- Why now

## Module Completion Standard

A module should not be considered done just because code exists.

At least 6 of these 8 should be true:

1. responsibility is clear
2. input and output are explicit
3. it is connected to the main chain
4. boundary borrowing is no longer obvious
5. failure path is testable
6. it leaves a real reusable asset
7. at least one test passes
8. docs or inventory are updated

## Current Priority Order

The system should not be advanced by evenly spreading effort. Priority should follow flywheel relevance.

### Current tier: immediate priorities

#### 1. Experience Supervisor Workspace Expansion

Focus:

- review console
- richer object workspaces
- broader trust-tier rollout beyond the current dashboard panels

Why now:

Because truth-bearing objects and contracts are now ahead of the supervisor-facing workspace.

#### 2. Orchestration Wake / Resume / Handoff Strengthening

Focus:

- handoff artifacts
- wake/resume policy
- broader fallback semantics

Why now:

Because Phase 1 stabilized run/checkpoint semantics, and the next gap is behavior-level recovery over time.

#### 3. Infrastructure Scheduler / Monitoring History / Ops Discipline

Focus:

- scheduled work trigger
- monitoring history
- runbook discipline

Why now:

Because the first honest monitoring snapshot now exists, and the next gap is durable operations behavior.

#### 4. Finance Pack Extraction Planning

Focus:

- explicit finance-pack boundary
- import/classification hardening
- preventing finance nouns from drifting back into core

Why now:

Because core contracts are stronger now, so pack extraction can happen against more stable semantics.

#### 5. Hermes Runtime Adapter Extraction

Focus:

- physical adapter extraction
- preserving `AgentRuntime` contract conformance

## Execution Plan

### Phase A: freeze baseline, harden main-chain truth

Goal:

Move the system from “directionally correct” to “main-chain real”.

Deliverables:

1. freeze the 9-surface baseline
2. classify all current modules
3. stabilize Hermes analyze runtime
4. add analyze workflow run id and step status foundation
5. harden state and lineage for recommendation, review, audit, and report
6. bring critical side effects under boundary coverage
7. create execution action inventory v1

Phase-complete when:

- analyze is real, traceable, and can fail honestly
- at least one recommendation -> review -> audit -> report chain can be traced cleanly
- critical actions carry context and responsibility lineage

### Phase B: turn the system into a truly controlled system

Goal:

Harden the boundaries between AI, process, action, and truth.

Deliverables:

1. intelligence vs execution boundary in docs and code
2. execution request / receipt for at least one real action family
3. first policy source of truth
4. main API entrypoints consistently through capability boundaries
5. outcome backfill
6. minimum orchestration retry / fallback support

Phase-complete when:

- at least one action family has a full request -> governance -> execution -> receipt -> state path
- AI no longer borrows execution responsibility
- governance is more than a local gate

### Phase C: activate the flywheel and knowledge system

Goal:

Make the system capable of learning, not only recording.

Deliverables:

1. knowledge object definitions
2. first lesson extraction from report, validation, and outcome
3. first lesson -> governance hint path
4. first lesson -> intelligence context path
5. first flywheel metrics set:
   - recommendations created
   - reviews completed
   - audits created
   - reports generated
   - reject / escalate / execute distribution
   - recurring issue count

Phase-complete when:

- the system records not only what happened, but what was learned
- at least one knowledge feedback path materially affects future system behavior

## Unified Task Flow

Every task should now follow this sequence:

1. locate
2. define
3. design the minimum boundary
4. implement the minimum version
5. connect it to the main chain
6. add validation
7. confirm the produced asset
8. update module status
9. record the remaining gap
10. point to the next unlocked task

## Old Failure Modes And Corrections

### Old problem 1

Concepts outran boundaries.

### Correction

Every layer must define what it owns and what it does not.

### Old problem 2

Architecture outran the loop.

### Correction

First harden the real chain, then continue purifying the structure.

### Old problem 3

AI and process were stronger than action and fact.

### Correction

Execution and State become first-class core layers.

### Old problem 4

Knowledge and State stayed too close.

### Correction

Design now uses an explicit 9-surface model.

### Old problem 5

Governance behaved like a gate, not a control plane.

### Correction

Governance should evolve into the unified side-effect and policy control surface.

### Old problem 6

Tasks had no semantic coordinate.

### Correction

Tasks are now managed through Layer / Type / Object / Loop / Asset.

## Final Summary

PFIOS is now in the stage where architecture discussion must give way to disciplined system building:

- freeze identity
- freeze responsibility
- harden the main chain
- strengthen execution
- harden governance
- separate truth from experience
- let AI participate in real work under control

The system goal is no longer vague structure improvement.

The system goal is:

**a controllable, traceable, accumulative, and evolving AI operating system for real high-constraint work.**
