# Provider: LangGraph

Status: **PROTOTYPE-READY / ON-DEMAND STATEFUL AGENT-ORCHESTRATION FRAMEWORK / NOT LOCALLY INSTALLED**
Role: low-level programmable runtime for checkpointed, cyclic, stateful Agent applications with explicit human-in-the-loop control.

## One-sentence understanding

**LangGraph models an Agent application as explicit mutable State plus Nodes and Edges, checkpoints state at super-step boundaries, and supports cyclic routing, interrupt/resume, thread-scoped persistence and state forking so custom long-running Agent behavior can be inspected and controlled.**

## Current upstream observation — 2026-09-14

- repository: `langchain-ai/langgraph`;
- about 40k GitHub stars observed during this study;
- MIT license;
- current stable Python release observed: `langgraph==1.2.11` (2026-08-11);
- project describes itself as a low-level orchestration framework/runtime for long-running, stateful Agents rather than a prompt/model abstraction.

## Current local observation

No importable `langgraph` package, uv tool or local LangGraph project was observed during the 2026-09-14 census.

Ordivon already has:

- Codex as a mature engineering Agent/harness;
- Microsoft Agent Framework as an installed multi-agent orchestration provider;
- Temporal as the selected generic durable-workflow provider;
- MCP as the capability interface.

Therefore LangGraph should remain workload-gated rather than becoming another base orchestration dependency.

## Core primitive: StateGraph

A LangGraph application is built from:

```text
State
+ Nodes
+ Edges
```

### State

State is an application-defined schema shared across graph execution. Nodes return partial updates rather than replacing the entire state.

Each state field can define a reducer controlling how concurrent/sequential updates are combined.

Example conceptual state:

```text
messages: append reducer
plan: replace
artifacts: merge
approval: replace
```

This is useful when Agent control flow depends on a structured working state rather than only a conversation transcript.

### Nodes

Nodes are ordinary functions/callables. They can contain:

- LLM calls;
- tool calls;
- deterministic code;
- subgraphs;
- human-interaction logic;
- external operations.

A node should remain one inspectable state transition/computation boundary.

### Edges

Edges determine routing between nodes.

They can be:

- fixed;
- conditional;
- parallel fan-out;
- cyclic/looping;
- dynamically selected through `Command`.

This makes cycles a first-class application structure, which is particularly useful for Agent loops such as:

```text
plan
 ↓
act
 ↓
observe
 ↓
critic
 ├─ done -> END
 └─ revise -> plan
```

## Super-step execution

LangGraph's runtime is inspired by Pregel-style message passing. Nodes activated in the same logical round form a **super-step** and may execute in parallel.

Checkpoint boundaries are aligned with these state-transition rounds rather than arbitrary individual source-code lines.

This matters for durability/time travel: the inspectable recovery units are graph-state transitions.

## Checkpointers and Threads

A checkpointer persists graph-state checkpoints under a `thread_id`.

A checkpoint records enough state to inspect/resume the graph, including state values, next nodes/tasks and metadata.

Current documented production choices include persistent PostgreSQL/SQLite checkpointers, while in-memory savers do not survive restart.

A **thread** is a LangGraph execution/state-continuity namespace, not automatically:

- a user identity;
- an Ordivon task;
- a business process;
- a Temporal Workflow;
- global Agent memory.

Keep thread identity scoped to the application that owns the graph.

## Short-term and long-term memory distinction

LangGraph distinguishes:

```text
checkpointer
= thread-scoped graph/working state

store
= application-defined information across threads
```

This is useful separation but neither should automatically become Ordivon's user-memory or knowledge authority.

Long-term facts/preferences/knowledge should remain in the natural owning system; a LangGraph Store is only one possible application persistence implementation.

## Interrupt / Human-in-the-loop

`interrupt()` dynamically pauses execution from inside a node and surfaces a JSON-serializable payload to the caller.

The graph is resumed later with `Command(resume=...)`, which becomes the interrupt's return value.

Conceptually:

```text
Agent node
  ↓
interrupt("Approve deployment?")
  ↓ checkpoint
PAUSED
  ↓ human/system response
Command(resume=approval)
  ↓
continue node/graph
```

This is stronger than a static breakpoint because the pause condition can depend on runtime state.

Useful cases:

- approval before consequential tool action;
- human correction of an Agent draft;
- requesting missing data;
- escalation from autonomous to supervised mode.

Human-in-the-loop pause/resume is an orchestration capability. The resumed value does not itself prove the human had domain/legal authority; authorization remains external.

## Time travel / fork

Persisted checkpoints can be inspected and previous state can be forked/updated to explore an alternate trajectory.

This is highly useful for Agent debugging:

```text
checkpoint N
  ├─ original continuation
  └─ modified state -> alternative continuation
```

Treat this as debugging/experimentation over Agent state, not mutation of historical external reality. Replaying/forking graph state must not silently repeat irreversible side effects.

## Durable execution semantics

With persistence enabled, LangGraph supports pause/resume and recovery from a prior checkpoint.

Current guidance requires non-deterministic/side-effecting operations to be wrapped in tasks so their results can be persisted and reused during resume rather than repeated blindly.

Durability modes trade overhead for checkpoint guarantees:

- `exit` — persist when execution exits/interruption/error;
- `async` — checkpoint asynchronously while next work proceeds;
- `sync` — persist synchronously before continuing.

This is useful for Agent application continuity, but it is not equivalent to Temporal's full durable-workflow model or Runtime's physical-effect commitment semantics.

## Functional API

LangGraph also offers a Functional API with `@entrypoint` and `@task`, allowing durable/checkpointed workflows to be written with ordinary Python control flow instead of explicit graph construction.

This demonstrates an important point:

**The graph visualization is not the essential primitive; checkpointed state transitions and task-result persistence are.**

Use the Graph API when explicit state/routing visualization helps; use ordinary code when it is clearer.

## Subgraphs

Subgraphs allow reusable nested Agent/workflow components.

Persistence can be configured per-invocation, per-thread or disabled depending on whether the sub-agent/subgraph needs:

- interrupt support;
- multi-turn state;
- inspectable checkpoints;
- independent invocation isolation.

Do not make every sub-agent stateful across calls. Per-invocation isolation is the better default for one-off delegated subagents.

## Boundary with Codex

Codex is already a complete engineering Agent/harness:

```text
thread/turn
+ model/tool loop
+ tool registry
+ permissions/sandbox
+ execution environment
```

Use Codex directly for ordinary engineering work.

LangGraph is appropriate only when building a **custom Agent application** whose explicit state machine, cyclic routing, checkpoint inspection or human-interrupt semantics are themselves product requirements.

Do not reimplement Codex as a LangGraph graph for architectural uniformity.

## Boundary with Microsoft Agent Framework

Microsoft Agent Framework provides higher-level multi-agent orchestration patterns such as sequential/concurrent execution, handoff and group collaboration.

LangGraph is lower-level and gives more explicit control over application state transitions, reducers, loops and checkpoints.

Routing heuristic:

```text
standard multi-agent collaboration pattern
  -> MAF first candidate

custom cyclic/stateful Agent protocol needing explicit graph state,
checkpoint inspection/forking or custom HITL points
  -> LangGraph candidate
```

Do not run both for the same agentic stage unless one is clearly wrapping a bounded capability of the other.

## Boundary with Temporal

There is real overlap: both provide durable state, recovery and human interaction.

Use **Temporal** when the semantic center is a general application/business process with:

- long timers/waits;
- external events;
- strongly durable Activities;
- service/workflow lifecycle independent of any LLM;
- distributed Worker/task-queue semantics;
- durable process state that must survive Agent/framework replacement.

Use **LangGraph** when the semantic center is the Agent's own evolving working state and control policy:

- iterative reasoning loops;
- tool/critic/replan cycles;
- inspectable message/plan state;
- human intervention into the Agent trajectory;
- checkpoint fork/time-travel for Agent debugging.

For important long-lived business processes, a clean composition is:

```text
Temporal Workflow
   ↓ Activity / agentic stage
LangGraph Agent
   ↓ tools/providers
Reality
```

Do not encode the same durable macro process independently in both.

## Boundary with MCP

MCP supplies tools/resources/prompts to the Agent application. LangGraph decides when/how its custom Agent state reaches a node that calls those capabilities.

MCP does not own LangGraph state; LangGraph does not need to wrap every tool in a custom tool protocol when MCP/native tools already exist.

## Side-effect boundary

Checkpoint replay/resume makes side-effect discipline essential.

A node may run again from its beginning after interruption/failure. Therefore:

- put non-deterministic or effecting operations in framework tasks/explicit provider calls whose results are persisted;
- use idempotency keys/reconciliation for external effects;
- use Runtime where exact local physical commitment/evidence matters;
- do not assume checkpointing makes arbitrary external effects exactly-once.

## Observability boundary

LangGraph state/checkpoint history is application execution state.

Tracing should still use standards-native OpenTelemetry/OTel GenAI/OpenInference where practical. LangSmith may be useful as a product, but LangGraph adoption does not require making LangSmith Ordivon's observability authority.

## Adoption threshold

Use LangGraph when several of these are truly needed:

- custom Agent control graph rather than standard tool loop;
- cycles/iterative state-machine logic;
- structured shared Agent state with reducers;
- dynamic HITL interrupts inside arbitrary nodes;
- persistent Agent threads/checkpoints;
- checkpoint inspection/fork/time-travel;
- resumable multi-stage Agent application;
- reusable nested subgraphs with scoped persistence.

Do not use LangGraph just because an Agent has multiple steps.

## Prototype recipe

A minimal LangGraph-like prototype needs only:

1. define a typed state dictionary;
2. define field reducers;
3. register node functions;
4. connect fixed/conditional/cyclic edges;
5. execute nodes in super-steps and merge state updates;
6. persist a checkpoint after each super-step;
7. address checkpoints by `thread_id`;
8. implement `interrupt(payload)` and `resume(value)`;
9. support state inspection and fork from an old checkpoint;
10. persist results of side-effecting/non-deterministic tasks so resume does not blindly repeat them.

This proves the architectural kernel without requiring model-provider integration.

## Prototype readiness gate

**PASS.** State/reducer/node/edge semantics, checkpoint/thread persistence, interrupts, subgraphs and side-effect boundaries are explicit enough to build a small checkpointed Agent state machine or use LangGraph directly.
