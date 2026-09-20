# Provider: Temporal

Status: **PROTOTYPE-READY / DURABLE-WORKFLOW PROVIDER / NOT LOCALLY ACTIVE**
Role: durable execution platform for long-lived deterministic workflows whose state must survive process, machine and network failure.

## One-sentence understanding

**Temporal persists a Workflow's Event History, replays deterministic Workflow code to reconstruct state, and dispatches retryable side-effecting Activities to Workers through Task Queues so long-running processes can resume after failures without the application owning a custom workflow-state machine.**

## Current upstream observation — 2026-09-14

- upstream server repository: `temporalio/temporal`;
- license: MIT;
- current GitHub scale observed during study: about 23k stars;
- latest listed server release observed: `v1.31.2` (2026-07-08).

## Current local observation

No active `temporal` CLI or Temporal container image was observed on this workstation during this study.

`/root/projects/ordivon-workstation-v2/temporal/` contains Temporal-oriented deployment/configuration material, so Temporal is already represented in historical Operations knowledge, but it is not a currently proven local runtime dependency.

Do not install/start a Temporal cluster merely because the architecture passes study. Activate it when a real durable workflow requires crash-proof state, timers/retries, message passing or distributed Worker routing.

## Core architecture

Temporal separates orchestration state from application execution:

```text
Client
  ↓ start/signal/update/query
Temporal Service
  ├─ durable Event History / Workflow state
  ├─ Task Queues / Matching
  ├─ timers/retries/visibility
  └─ scheduling of Workflow + Activity Tasks
          ↓
       Workers
       ├─ deterministic Workflow code
       └─ non-deterministic Activities
```

The Temporal Service does **not** execute the application's Workflow or Activity code. Workers do that. The Service persists state/history, schedules Tasks and receives Commands/results.

## Workflow

A Workflow Definition is durable control logic.

It must be deterministic under replay: given the same recorded history/input, it must produce the same sequence of Temporal Commands.

Therefore ordinary non-deterministic operations do not belong directly in Workflow code:

- network calls;
- database queries/writes;
- local filesystem/process execution;
- direct wall-clock/randomness outside SDK deterministic APIs;
- arbitrary LLM/model calls.

Those belong in Activities or other Temporal-supported deterministic abstractions.

### Commands and Events

Workflow code issues Commands such as scheduling an Activity or Timer. The Temporal Service records resulting Events in the Workflow Event History.

On recovery, the Worker re-executes Workflow code and matches generated Commands against already-recorded Events rather than repeating completed external work. When replay reaches the end of History, new Commands can be emitted normally.

This Event History is the key durability mechanism.

## Activities

Activities are the boundary for non-deterministic or external work.

Typical Activities include:

- API calls;
- database operations;
- file/process operations;
- cloud/provider actions;
- LLM/model calls;
- invoking Ordivon Runtime for exact local physical execution.

Activities execute on Workers and are generally retryable. Temporal Activities therefore do **not** provide exactly-once external effects by themselves.

A robust Activity should normally use the downstream system's strongest available semantics:

- idempotency key;
- conditional write / upsert;
- transaction identifier;
- provider receipt/state query;
- Runtime structured Effect Contract where applicable.

If an Activity is fundamentally non-idempotent/opaque, retry policy must be constrained and ambiguity handled explicitly rather than assuming Temporal retry makes the effect safe.

## Retry / timeout / heartbeat

Activities have Retry Policies and timeouts. Default Activity behavior includes automatic retry with exponential backoff until success/cancellation unless changed by policy.

Long-running Activities can heartbeat. Heartbeat state can carry bounded progress information and can be supplied to a later attempt so work may resume from the last durable progress marker.

These mechanisms provide durable operation orchestration; they do not prove downstream side-effect idempotency.

## Task Queues and Workers

Task Queues decouple durable scheduling from Worker placement.

Workers poll queues for:

- Workflow Tasks;
- Activity Tasks;
- other supported operation types.

Any compatible Worker polling the queue may process work. Worker crashes do not destroy Workflow state because the Temporal Service owns Event History.

Sticky execution is an optimization: a Worker may cache reconstructed Workflow state locally, but failure falls back to the shared queue and replay.

## Workflow message passing

Temporal provides explicit interaction primitives for running Workflows.

### Signal

Asynchronous write/message to a running Workflow.

Use when the caller does not need an immediate tracked result.

### Update

Synchronous tracked write/message. The caller can wait for completion or failure.

Use when a state change needs request/response semantics.

### Query

Read current Workflow state without using Visibility as business state.

Use for inspection/progress/debug views that do not mutate Workflow state.

This separation is useful: read, asynchronous write and synchronous tracked write are different interaction classes.

## Timers / waiting

Workflow timers and awaitable conditions are persisted through History. A Worker process does not need to stay alive while a Workflow sleeps for minutes, days or months.

This is a major reason to use Temporal instead of keeping local processes alive or writing polling/retry loops into an Agent/Runtime.

## Continue-As-New

Long-running Workflows can checkpoint relevant state into a new Workflow Run with the same Workflow Id but a fresh Event History.

Use this to bound history growth and periodically move long-lived entities onto newer Workflow code/versioning boundaries.

## Visibility / Search Attributes

Temporal provides indexed Visibility metadata for finding/filtering Workflow Executions.

Search Attributes are useful operational/index metadata, **not a general business database**. Temporal documentation explicitly recommends Workflow local state + Query or an external datastore for business logic that needs current data.

Do not turn Visibility into Ordivon's task/domain source of truth.

## Versioning boundary

Workflow replay creates a compatibility obligation: deployed Workflow code must remain replay-compatible with existing Histories or use supported Worker/Workflow versioning strategies.

This is the cost side of durable replay. Ordinary Activity implementation can evolve more freely than Workflow command structure.

## Ordivon / Runtime comparison

Temporal and Ordivon Runtime solve adjacent but different problems.

### Temporal owns well

- generic durable Workflow state;
- Event History + deterministic replay;
- durable timers/waits;
- Activity retries/backoff/timeouts/heartbeats;
- Task Queues and Worker routing/scaling;
- Signals/Updates/Queries;
- Child Workflows / Continue-As-New and other workflow-lifecycle mechanisms;
- Workflow Visibility and operational search;
- long-running business/system process orchestration.

Ordivon Runtime should **not** implement competing generic versions of these features.

### Runtime still owns a narrower physical-effect boundary

Current Runtime evidence shows a deliberately different contract:

- exact Git Workspace/source-state commitment;
- digest-bound executable/provider contract and selected Host Dependency commitments;
- immutable bound inputs for supported operations;
- one Attempt crossing the physical dispatch boundary at most once;
- cgroup/systemd ownership of a concrete local process tree;
- Linux/Windows local execution authority boundaries;
- bounded identity-bound Artifacts and terminal evidence;
- fail-closed ambiguity (`lost`/`orphaned`) rather than speculative redispatch of opaque local effects;
- structured reconciliation receipts for the few effect classes that actually support them.

These are not generic durable-workflow semantics. They bind one Agent-proposed physical local action to a particular source/executable/world precondition and preserve uncertainty about whether that physical effect occurred.

### Important retry distinction

Temporal's normal Activity model is retry-oriented and expects Activities touching external systems to be idempotent/reconcilable.

Runtime's arbitrary local `workspace.exec` is intentionally treated as **OPAQUE**: a committed Attempt is not silently dispatched twice merely because the caller lost a response.

Therefore:

```text
Temporal Workflow durability
!=
exactly-once Activity effect
!=
Runtime at-most-once physical dispatch per Attempt
```

Runtime's at-most-once dispatch is also **not** exactly-once external effect: the launched process may itself perform zero, one or many outside effects.

## Recommended composition

The natural composition is:

```text
Temporal Workflow
   ↓ deterministic orchestration
Temporal Activity
   ↓
Runtime Tool / other provider
   ↓ exact physical/provider action
external reality
   ↓
Activity result / provider receipt
   ↓
Temporal Event History
```

Temporal provides durable orchestration around the Activity. Runtime/provider semantics establish the strongest available physical/effect evidence inside that Activity.

For ordinary idempotent HTTP/database/provider Activities, Runtime may be unnecessary; call the provider directly.

For exact local Workspace-bound actions where Runtime's source/authority/evidence boundary matters, use Runtime as the Activity implementation/provider.

## Boundary with MCP Tasks

MCP Tasks standardizes how a client observes/interacts with a long-running operation.

Temporal implements the actual durable process state/history. A Temporal Workflow can be projected through MCP Tasks or a Tool without making MCP the execution authority.

```text
Temporal Workflow Execution
        ↓ projection
MCP Task / Tool
        ↓
Agent client
```

## Boundary with n8n

Prefer n8n for API/SaaS/event integration where the workflow is primarily deterministic connector automation and full durable program semantics are unnecessary.

Prefer Temporal when the process itself is a durable application object requiring reliable state, timers, retries, message passing, long waits and code-level orchestration across failures.

The two can call one another; neither should become a universal Ordivon workflow layer.

## Self-hosting boundary

Temporal Server is substantial distributed infrastructure: Frontend, History, Matching, persistence/Visibility and operational scaling concerns.

Default to Temporal Cloud or an already-operated mature Temporal deployment when policy/economics permit. Self-host only when a real requirement justifies operating this control plane.

Do not embed Temporal Server internals into Ordivon.

## Prototype recipe

A minimal Temporal-like durable-execution prototype can demonstrate the mechanism with:

1. persist a Workflow Event History in a database;
2. define deterministic Workflow code that consumes history and emits Commands;
3. store `ActivityScheduled`, `ActivityCompleted/Failed` and Timer events;
4. put Activity Tasks into a durable queue;
5. let Workers poll/execute Activities and return results;
6. on Worker restart, replay Workflow code from History without repeating already-recorded Activities;
7. retry failed Activity Tasks according to a bounded policy;
8. support one asynchronous Signal and one read-only Query;
9. crash a Worker midway and prove the Workflow resumes from durable History.

This is sufficient to understand the architecture. Production Temporal adds distributed services, scaling, consistency, versioning, Visibility, multi-cluster/cloud operations and mature SDKs; Ordivon should consume those rather than reimplement them.

## Prototype readiness gate

**PASS.** Workflow/Event History replay, Activity boundary, Task Queue/Worker model, retry/heartbeat/message semantics and Runtime distinction are explicit enough to implement a small durable-execution prototype or compose Temporal directly.
