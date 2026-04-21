# Task Template System

## Purpose

This document defines the default task template system for PFIOS.

The goal is not prettier planning. The goal is to force every task to answer:

- what layer it belongs to
- which loop it advances
- what asset it leaves behind
- why it should be done now

Use this document before implementation, refactor, integration, closure, or flywheel work.

## How To Use This

### Daily work

Use the **Minimal Template**.

### Important implementation work

Use the **Standard Template**.

### Architecture, integration, and loop work

Use the **Complex Template**.

### Daily focus

Use the **Today Board**.

## 1. Minimal Template

Use this when you need to classify a task in under one minute.

```text
[Task Name]

Layer:
Type:
Object:
Loop:
Asset:
Why now:

Done looks like:
- 
- 
- 

Not doing:
- 
- 
```

### Field Guidance

#### `Task Name`

The task name should describe the real action.

Good:

- connect Hermes analyze runtime
- add action context to recommendation state transitions
- switch reports page to real data
- add audit lineage to review completion

Bad:

- improve system
- adjust architecture
- do some governance
- clean code

#### `Layer`

Choose exactly one primary layer:

- Experience
- Capability
- Orchestration
- Governance
- Intelligence
- Execution
- State
- Knowledge
- Infrastructure

#### `Type`

Choose the dominant work type:

- Closure
- Boundary
- Enablement
- Flywheel
- Cleanup
- Refactor
- Reliability
- Observability
- Migration

#### `Object`

Name the main object:

- Recommendation
- Review
- Audit Event
- Report
- AI Task
- Runtime Adapter
- Validation Issue
- Workflow Run
- State Record
- Knowledge Entry

#### `Loop`

Attach the task to a loop:

- Analyze Chain
- Review Chain
- Execution Loop
- Learning Loop
- Validation Loop
- Runtime Ops Loop

#### `Asset`

Say what this task leaves behind:

- Contract
- Workflow
- Runtime Adapter
- Audit Trail
- State Record
- Knowledge Record
- Policy Hook
- UI Truthfulness
- Diagnostic Signal
- Metrics

#### `Why now`

Write one sentence about why this is a now-task, not a someday-task.

Good examples:

- This must happen now or analyze remains stuck in mock reasoning and cannot produce real AI samples.
- This must happen now or recommendation transitions remain untraceable and pollute the flywheel.
- This must happen now or the reports page keeps misleading users and weakens product truthfulness.

#### `Done looks like`

Write 2 to 4 observable checks.

#### `Not doing`

Explicitly write what this task will not absorb.

## 2. Standard Template

Use this for most formal implementation tasks.

```text
# [Task Name]

## 1. Task Identity
- Layer:
- Type:
- Priority: P0 / P1 / P2
- Status: Proposed / In Progress / Blocked / Done
- Owner:
- Date:
- Related Docs:
- Related Files:

## 2. Purpose
- Why now:
- Problem being solved:
- If not done, what breaks or stays fake:
- What part of the system becomes stronger:

## 3. Scope
### In Scope
- 
- 
- 

### Out of Scope
- 
- 
- 

## 4. Main Object
- Primary object:
- Upstream dependency:
- Downstream effect:
- Source of truth:
- Whether side-effect exists: Yes / No

## 5. Loop Position
- Primary loop:
- Step in loop:
- What comes before:
- What comes after:
- Whether this creates reusable history: Yes / No

## 6. Expected Asset
- Main asset produced:
- Secondary assets:
- Where the asset will live:
- How it will be reused later:

## 7. Design Decision
- Chosen approach:
- Alternatives rejected:
- Why this approach is smallest viable move:
- Boundary to preserve:

## 8. Implementation Plan
1.
2.
3.
4.

## 9. Verification
- Unit tests:
- Integration tests:
- Manual checks:
- Failure mode checks:
- Truthfulness checks:

## 10. Done Criteria
- [ ]
- [ ]
- [ ]
- [ ]

## 11. Risk Notes
- Main risk:
- Drift risk:
- What this task might accidentally absorb:
- Rollback plan:

## 12. Follow-up
- Immediate next task:
- Deferred work:
- What this unlocks:
```

## 3. Complex Template

Use this for:

- Hermes integration
- intelligence vs execution boundary hardening
- state vs knowledge split preparation
- analyze chain upgrades
- flywheel activation work
- capability migration and reclassification

```text
# [Task Name]

## A. Strategic Position
- Strategic goal:
- Which architectural gap this addresses:
- Which future flywheel this supports:
- Why this is more important than adjacent work right now:

## B. Task Identity
- Layer:
- Type:
- Priority:
- Owner:
- Date:
- Related architecture baseline:
- Related closure report:
- Related flywheel goal:

## C. Current State
- Current implementation:
- Current pain:
- Current workaround:
- Current fake / weak / mixed behavior:
- Current files/modules involved:

## D. Target State
- What should be true after this task:
- What should become explicit:
- What should stop happening:
- What remains intentionally weak after this task:

## E. Object and Boundary
- Primary object:
- Adjacent objects:
- Which layer owns business meaning:
- Which layer owns control:
- Which layer owns side-effect:
- Which layer owns truth:
- Which layer owns derived knowledge:

## F. Loop Mapping
- Primary loop:
- Entry point:
- State transition introduced:
- Audit / lineage introduced:
- Reusable signal introduced:
- Future feedback mechanism enabled:

## G. Asset Produced
- Hard asset:
- Soft asset:
- Operational asset:
- Flywheel asset:
- Where each asset is stored:

## H. Non-goals
- Not solving:
- Not refactoring:
- Not renaming:
- Not expanding into:
- Not polishing:

## I. Detailed Plan
### Step 1
- Goal:
- Files:
- Output:

### Step 2
- Goal:
- Files:
- Output:

### Step 3
- Goal:
- Files:
- Output:

### Step 4
- Goal:
- Files:
- Output:

## J. Verification Plan
- Static verification:
- Runtime verification:
- Route/UI verification:
- Failure-path verification:
- Data lineage verification:
- Side-effect boundary verification:
- Manual trust check:

## K. Done Criteria
- [ ] Main path works
- [ ] No fake success remains
- [ ] State transition is real
- [ ] Object boundary is clearer than before
- [ ] Audit/lineage exists where needed
- [ ] At least one reusable asset is produced
- [ ] Follow-up is documented

## L. Risks and Tradeoffs
- Main tradeoff:
- What got deferred:
- What remains mixed:
- What might need a second pass:

## M. Follow-up Chain
- Next immediate task:
- Next boundary task:
- Next flywheel task:
- What metric should move after this:
```

## 4. Label Dictionary

### Layer Dictionary

#### `Experience`

User entrypoints, pages, API surface, and experience semantics.

#### `Capability`

Product ability entry that answers what the user can ask the system to do.

#### `Orchestration`

Workflow and process organization that answers how work is run.

#### `Governance`

Constraint, permission, audit, and control-plane ownership.

#### `Intelligence`

AI task runtime, reasoning routing, and structured AI output.

#### `Execution`

Tool calls, external actions, artifact writes, and connectors.

#### `State`

Business fact, object truth, state machine, event, and database truth.

#### `Knowledge`

Lesson, summary, rule candidate, and accumulated narrative memory.

#### `Infrastructure`

Config, startup, deployment, secrets, monitoring, and operations.

### Type Dictionary

#### `Closure`

Tighten truth, remove fake behavior, and close structural gaps.

#### `Boundary`

Harden ownership and prevent borrowing, pollution, or overreach.

#### `Enablement`

Make a real new system ability possible.

#### `Flywheel`

Create or strengthen accumulation, feedback, evaluation, or learning loops.

#### `Reliability`

Stability, idempotency, retry, recovery, and failure handling.

#### `Observability`

Logs, traces, metrics, and diagnostics.

#### `Cleanup`

Technical cleanup without changing the main capability.

#### `Refactor`

Restructure without changing responsibility.

#### `Migration`

Move from old ownership to new boundary ownership.

### Loop Dictionary

#### `Analyze Chain`

input -> analyze -> recommendation -> report

#### `Review Chain`

recommendation -> review -> decision -> audit

#### `Execution Loop`

task -> governance -> execution -> outcome

#### `Learning Loop`

state -> report or lesson -> knowledge -> future improvement

#### `Validation Loop`

usage or result -> validation or eval -> issue or signal -> correction

#### `Runtime Ops Loop`

runtime -> monitoring -> diagnosis -> fix

### Asset Dictionary

#### `Contract`

Stable interface, schema, or object definition.

#### `Workflow`

Process definition, step order, or lineage asset.

#### `Runtime Adapter`

Bridge to an external runtime, provider, or agent system.

#### `Audit Trail`

Traceable event and action record.

#### `State Record`

Real object, transition, or database fact.

#### `Knowledge Record`

Lesson, review memory, rule candidate, or reusable insight.

#### `Policy Hook`

Governance entry point or rule attachment point.

#### `Diagnostic Signal`

Evaluation signal, failure classification, or metric.

#### `UI Truthfulness`

An improvement to product-surface honesty.

## 5. Priority Test

Add this block to the top of tasks when prioritization is unclear.

```text
## Priority Test
This task is worth doing now because it satisfies at least one:
- [ ] Main-chain critical
- [ ] Flywheel critical
- [ ] Anti-pollution critical
- [ ] Reliability critical
- [ ] Unlocks next task

This task should be delayed if:
- [ ] It only improves naming
- [ ] It only improves aesthetics
- [ ] It does not create reusable asset
- [ ] It does not clarify ownership
- [ ] It can be safely postponed without polluting future work
```

This block exists to force the question:

**is this task advancing the system, or just satisfying temporary discomfort?**

## 6. Example: Hermes Analyze Runtime

```text
# Connect Hermes analyze runtime

## 1. Task Identity
- Layer: Intelligence
- Type: Enablement
- Priority: P0
- Status: Proposed
- Owner: xzh
- Date: 2026-04-19
- Related Docs: docs/architecture/architecture-baseline.md
- Related Files: intelligence/, orchestrator/, capabilities/workflow/

## 2. Purpose
- Why now: analyze still cannot reliably produce real AI task samples, so the flywheel cannot start.
- Problem being solved: analyze is not yet a stable AI runtime execution path.
- If not done, what breaks or stays fake: analyze remains in a weak intelligence state.
- What part of the system becomes stronger: Intelligence ownership.

## 3. Scope
### In Scope
- connect Hermes analyze runtime
- return structured results
- preserve run id and lineage

### Out of Scope
- do not add execution tool calling
- do not change dashboard
- do not refactor the entire intelligence directory

## 4. Main Object
- Primary object: AI Task
- Upstream dependency: Analyze request
- Downstream effect: Recommendation generation
- Source of truth: State
- Whether side-effect exists: No

## 5. Loop Position
- Primary loop: Analyze Chain
- Step in loop: analyze execution
- What comes before: user input or capability request
- What comes after: recommendation and governance
- Whether this creates reusable history: Yes

## 6. Expected Asset
- Main asset produced: Runtime Adapter
- Secondary assets: Run lineage, structured result
- Where the asset will live: intelligence/
- How it will be reused later: as the unified entrypoint for later AI tasks

## 7. Design Decision
- Chosen approach: connect Hermes as an Intelligence runtime adapter
- Alternatives rejected: attaching Hermes directly to execution or tool ownership
- Why this approach is smallest viable move: analyze-only is the smallest valid intelligence proof
- Boundary to preserve: Hermes must not own business truth

## 8. Implementation Plan
1. connect Hermes client
2. define analyze task request and response
3. integrate through orchestrator
4. write lineage into state

## 9. Verification
- Unit tests: task adapter
- Integration tests: analyze main path
- Manual checks: analyze route
- Failure mode checks: Hermes unavailable
- Truthfulness checks: no fake AI success

## 10. Done Criteria
- [ ] analyze goes through Hermes runtime
- [ ] result returns in structured form
- [ ] failure path is real
- [ ] at least one lineage record is written to state

## 11. Risk Notes
- Main risk: execution responsibility leaking into intelligence
- Drift risk: Hermes client becoming a universal system entrypoint
- What this task might accidentally absorb: tool calling
- Rollback plan: keep original analyze fallback adapter

## 12. Follow-up
- Immediate next task: connect governance to analyze output
- Deferred work: execution tool runtime
- What this unlocks: AI runtime flywheel
```

## 7. Example: Recommendation State Boundary

```text
# Add action context to recommendation state transitions

## 1. Task Identity
- Layer: Governance
- Type: Boundary
- Priority: P0
- Status: Proposed
- Owner: xzh
- Date: 2026-04-19
- Related Files: capabilities/domain/recommendations.py, governance/, apps/api/

## 2. Purpose
- Why now: side effects without actor/context/reason/idempotency_key will pollute audit and future learning loops.
- Problem being solved: recommendation transitions lack a unified boundary context.
- If not done, what breaks or stays fake: state changes remain weakly attributable.
- What part of the system becomes stronger: Governance and auditability.
```

## 8. Today Board

Use this at the start of the day.

```text
# Today Board

## 1. Main goal today
- 

## 2. Tasks
### Task A
- Layer:
- Type:
- Object:
- Loop:
- Asset:
- Why now:
- Expected done:

### Task B
- Layer:
- Type:
- Object:
- Loop:
- Asset:
- Why now:
- Expected done:

### Task C
- Layer:
- Type:
- Object:
- Loop:
- Asset:
- Why now:
- Expected done:

## 3. Today must not drift into
- 
- 
- 

## 4. End-of-day check
- What became more real today?
- What became more traceable today?
- What became more reusable today?
- What is still mixed?
- What should be next?
```

## 9. Minimal Usage Guidance

Start simple:

- day-to-day task -> Minimal Template
- important task -> Standard Template
- architecture or loop task -> Complex Template
- daily planning -> Today Board

## Final Reminder

The purpose of this template system is not to create paperwork.

Its purpose is to force four questions before implementation:

- what layer am I changing?
- which loop does this belong to?
- what asset will remain after this?
- why is this worth doing now?

Once those four answers become habitual, task drift drops sharply.
