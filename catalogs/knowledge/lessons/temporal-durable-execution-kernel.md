# Temporal Durable Execution Kernel — extracted design lessons

Status: **REGISTERED / PROTOTYPE-READY**
Registered: 2026-09-14

## One-sentence model

**Temporal makes application control flow durable by recording a Workflow Event History, replaying deterministic Workflow code to reconstruct state, and routing non-deterministic side effects through retryable Activities executed by Workers.**

## Mechanism 1: persist history, not a hand-maintained state machine

The key abstraction is an append-only Event History that records the durable decisions/results needed to reconstruct Workflow state.

A Worker can disappear. Another Worker can later replay the same Workflow Definition over the same History and rebuild the logical state.

General lesson:

**For long-lived deterministic orchestration, durable history + replay can replace custom checkpoint/state-machine plumbing.**

This is fundamentally different from keeping a process alive.

## Mechanism 2: deterministic control, non-deterministic effects

Workflow code must be replay-safe. External I/O must not execute as ordinary Workflow code because replay would repeat it.

Separate:

```text
Workflow
= deterministic durable decisions

Activity
= non-deterministic external work
```

This boundary is Temporal's most important programming-model rule.

It maps cleanly to Ordivon's execution philosophy:

`decision/orchestration state != physical/provider effect`

## Mechanism 3: Commands become Events

During normal execution, Workflow code emits Commands. The Temporal Service turns accepted outcomes into History Events.

During replay, the Worker re-runs code and matches would-be Commands against recorded Events rather than issuing old side effects again.

The history is therefore not merely logging. It is executable recovery state.

## Mechanism 4: durability is not exactly-once side effects

Activities may be retried after timeouts, Worker failure or transient errors.

Therefore:

```text
Workflow exactly remembers what it decided
!=
external effect ran exactly once
```

Activities that mutate external systems should use effect-owner semantics such as:

- idempotency keys;
- conditional writes;
- transactional uniqueness;
- receipts/state queries;
- explicit compensation where appropriate.

This strongly validates Ordivon's distinction:

`execution durability != external-effect idempotency != semantic completion`.

## Mechanism 5: retry belongs around effect contracts, not arbitrary opacity

Temporal makes retries cheap and durable, but automatic retry is only semantically safe when the Activity's effect contract tolerates it.

If an external call is opaque/non-idempotent, blindly retrying can duplicate the real-world effect.

This is exactly where Runtime's narrower Effect Commit Kernel remains different: arbitrary local execution is not automatically declared retry-safe.

General rule:

**Retry policy must follow effect semantics, not transport/process failure alone.**

## Mechanism 6: durable queues decouple scheduling from Workers

Workers are replaceable compute. Task Queues are stable routing names owned by Temporal.

This allows:

- Worker restart/scaling;
- language/service separation;
- rate/concurrency control;
- workload routing;
- rolling deployments/versioning.

Do not encode Worker machine identity into business Workflow state unless the workload truly requires it.

## Mechanism 7: sticky state is cache, not truth

Temporal Workers may cache reconstructed Workflow state via sticky execution for performance.

If that Worker disappears, Temporal falls back to History replay on another Worker.

This is a mature application of:

`cache may accelerate truth reconstruction; cache must not become truth`.

## Mechanism 8: timers should be durable logical time, not sleeping processes

Long waits belong in Workflow/timer state, not in a process/thread kept alive for days.

A Workflow can wait across Worker restarts without holding local process resources.

Use this for:

- scheduled follow-up;
- approval timeout;
- retry backoff;
- delayed escalation;
- long-running business lifecycle.

## Mechanism 9: interaction primitives should encode intent

Temporal distinguishes:

- **Signal** — asynchronous state-changing message;
- **Update** — synchronous tracked state-changing request;
- **Query** — read-only inspection.

Do not collapse these into one generic message if different acknowledgement/durability semantics matter.

## Mechanism 10: progress checkpointing belongs near long Activities

Activity Heartbeats do two useful things:

- liveness/progress detection;
- bounded progress state for retry/resume.

This is different from Workflow History: heartbeat details are Activity progress checkpoints, not the whole workflow control state.

The general lesson is to checkpoint at the natural recovery boundary rather than centralizing all progress into one global task object.

## Mechanism 11: history has cost, so roll it forward deliberately

Event History grows. `Continue-As-New` closes the current Run and starts another in the same Workflow chain with a fresh History while carrying forward relevant state.

This is useful both for scale and code-version hygiene.

General rule:

**Durable logs need explicit compaction/checkpoint boundaries; infinite append-only history is not free.**

## Mechanism 12: Visibility is an index, not business truth

Temporal Search Attributes and Visibility exist to find/inspect Workflow Executions.

They are not a substitute for a domain database or authoritative Workflow local state.

This is the same architectural rule already learned from Graphify and other derived indexes:

`derived searchable projection != source of truth`.

## Mechanism 13: replay creates code-evolution constraints

A Workflow Definition cannot be edited arbitrarily if existing Histories may replay through the new code.

This means durable replay trades operational resilience for a stronger code-compatibility discipline.

Keep unstable/rapidly changing implementation details in Activities where possible; keep Workflow code focused on stable orchestration semantics.

## Runtime comparison: what Temporal should replace

Current Runtime documentation itself states that traditional runtimes/workflow systems should own generic scheduling, durable workflow state and ordinary retries.

Temporal is the mature owner for those concerns.

Therefore Ordivon Runtime should not grow generic implementations of:

- workflow DAG/state-machine orchestration;
- durable business process state;
- timers/schedules;
- automatic Activity-style retry/backoff;
- distributed Worker routing/Task Queues;
- Signals/Updates/Queries;
- workflow search/visibility;
- Child Workflow / Continue-As-New semantics;
- workflow-level versioning/replay frameworks.

When such requirements appear, compose Temporal rather than extending Runtime.

## Runtime comparison: what remains distinct

Runtime's current irreducible problem is narrower:

> Convert one non-deterministic Agent proposal into an identifiable, bounded physical local commitment and preserve known/unknown execution truth across interruption.

Current distinctive Runtime semantics include:

- Workspace/source-state digest commitment;
- target executable/provider digest continuity;
- optional explicit Host Dependency commitments;
- immutable bound input materialization;
- at-most-once physical dispatch per Attempt;
- systemd/cgroup process-tree ownership;
- Windows/Linux authority-specific execution surfaces;
- terminal evidence/Artifact digest binding;
- uncertainty-preserving reconciliation for opaque commands;
- adapter-owned receipts for the small set of truly reconcilable effects.

Temporal does not natively promise these local physical/source-closure semantics.

## Recommended composition

The cleanest composition is:

```text
Agent / application
      ↓
Temporal Workflow
      ↓
Activity
      ├─ direct idempotent provider API
      ├─ n8n integration
      └─ Ordivon Runtime exact local effect
              ↓
           Reality
```

This makes Temporal the owner of **durable orchestration**, while the invoked provider remains owner of **effect semantics and physical evidence**.

## Relationship to MCP

MCP standardizes access/projection. Temporal owns durable workflow execution.

An MCP Tool can start/signal/query a Temporal Workflow, and the MCP Tasks extension can project a long-running operation, but MCP should not duplicate Event History, retries or Worker semantics.

## Relationship to n8n

Use n8n when integration graph/event automation is sufficient.

Use Temporal when the workflow itself must survive failures as a durable application object with code-level state, long waits, retries and messages.

Do not build a universal Ordivon workflow abstraction over both simply because both orchestrate steps.

## Relationship to Agent frameworks

Agent loops are often non-deterministic because model output changes. Do not place raw model calls directly in replay-sensitive Workflow code unless their outputs are recorded through an Activity/side-effect mechanism.

A useful pattern is:

```text
Temporal Workflow
  ↓ schedules
LLM/Agent Activity
  ↓ result recorded in History
Workflow uses recorded result
```

Replay should consume the historical model result rather than silently invoking the model again.

## What Ordivon should retain

1. Persist durable orchestration history rather than writing custom workflow-state tables when Temporal is justified.
2. Keep deterministic orchestration separate from non-deterministic physical/provider effects.
3. Treat Activity retry as effect-contract dependent, not inherently safe.
4. Use durable Task Queues to make Workers replaceable.
5. Keep cached Worker state reconstructible from History.
6. Use durable timers instead of long-sleeping processes.
7. Distinguish async writes, sync tracked writes and read-only queries.
8. Keep Activity progress checkpoints separate from Workflow state.
9. Compact/roll long histories with explicit continuation boundaries.
10. Keep Visibility/search as derived operational metadata.
11. Respect replay compatibility as a real maintenance cost.
12. Preserve Runtime only for its narrower exact physical/effect-commit boundary; do not turn it into Temporal-lite.

## What Ordivon should not copy

- another generic workflow state machine;
- private durable timers/retry scheduler;
- distributed task queues/worker router;
- Temporal-like Signal/Update/Query protocol;
- workflow Visibility/search database;
- Event History/replay implementation;
- a generic retrying Runtime Attempt model for opaque effects;
- a universal orchestration layer combining Temporal, n8n, ComfyUI and Agent graphs merely because all involve steps/graphs.

## Minimal prototype

A minimal architecture proof needs only:

```text
Workflow code
  ↓ deterministic commands
Event History DB
  ↓
Durable Task Queue
  ↓
Worker
  ├─ replay Workflow
  └─ execute Activity
        ↓
Activity result event
        ↓
Workflow continues
```

Test it by killing the Worker between Activity completion and subsequent Workflow progress, then prove recovery reconstructs state from History without rerunning an already-recorded completed Activity.

A second test should demonstrate an Activity retry against an idempotent fake external service so workflow durability is not confused with exactly-once side effects.

## Project-study acceptance

### One-sentence test

PASS: Temporal makes deterministic control flow durable through Event History replay while routing non-deterministic external work through retryable Activities.

### Prototype test

PASS: Event History, deterministic replay, Activity queue/worker execution, retry/heartbeat and message semantics are explicit enough to implement a small crash-recovery prototype.

## Verdict

**PASS — USE TEMPORAL FOR DURABLE WORKFLOWS; KEEP RUNTIME ONLY FOR ITS NARROWER PHYSICAL EFFECT-COMMIT BOUNDARY.**

Further study should be workload-driven around a real Temporal workflow, Worker versioning, multi-cluster/HA, Nexus or Temporal Cloud/self-host operations.
