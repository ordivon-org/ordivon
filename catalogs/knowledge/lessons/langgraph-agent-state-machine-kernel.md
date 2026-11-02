# LangGraph Agent State-Machine Kernel

Status: **REGISTERED / PROTOTYPE-READY**
Registered: 2026-09-14

## One-sentence model

**LangGraph's durable value is a checkpointed Agent state machine: explicit mutable state plus reducers, cyclic/dynamic transitions, resumable human interrupts and inspectable/forkable checkpoints around a custom Agent application.**

## Mechanism 1: Agent state can be more explicit than conversation history

A mature custom Agent often needs working state such as:

```text
messages
plan
current objective
tool observations
candidate artifacts
review status
approval
retry/replan count
```

Representing this as typed fields can be clearer than encoding everything into one transcript.

General rule:

**Use explicit application state for facts/control variables that the program must reason about deterministically; use messages for conversational evidence, not as a universal state database.**

## Mechanism 2: reducers make concurrent state updates explicit

When multiple nodes update the same state field, the framework needs a combination rule.

Examples:

```text
messages -> append
results  -> merge/deduplicate
status   -> replace
score    -> max/min/custom
```

This is especially important under parallel graph steps.

Do not let implicit last-writer-wins behavior decide multi-agent state semantics accidentally.

## Mechanism 3: cycles are a legitimate Agent primitive

Ordinary DAG thinking is insufficient for many Agent protocols:

```text
plan -> act -> observe -> critique
                 ^          |
                 |----------|
```

The loop ends according to state/decision criteria rather than because the graph has no more nodes.

This is one of LangGraph's genuinely natural Agent-oriented abstractions.

However, a cycle must have:

- termination/limit conditions;
- bounded costs/time;
- observable state;
- failure/escalation rules.

Do not build unbounded self-reflection loops.

## Mechanism 4: checkpoint is the recovery/debug unit

A checkpoint stores the logical graph state and continuation point at a super-step boundary.

This enables:

- resume after failure;
- inspect past state;
- human modification;
- fork alternative continuations;
- avoid rerunning completed graph steps when supported by persistence semantics.

A checkpoint is not external-world truth. It is a snapshot of the Agent application's logical state.

## Mechanism 5: thread is an application continuity namespace

`thread_id` identifies one sequence of checkpoints.

Do not overload it as:

- global user identity;
- business task ID;
- source-document ID;
- Temporal Workflow identity;
- Ordivon universal conversation state.

Map across systems explicitly only when a workload requires correlation.

## Mechanism 6: HITL should be an explicit control transition

Dynamic `interrupt()` is more precise than a generic "ask human" convention because it creates an explicit paused state and continuation value.

Useful pattern:

```text
Agent proposes consequential action
      ↓
interrupt(proposal + evidence)
      ↓
human/provider decision
      ↓
resume(approved/rejected/edited)
      ↓
continue state machine
```

The orchestration framework records where execution paused. External identity/authorization systems still decide whether the approving actor is allowed to approve.

## Mechanism 7: time travel is for counterfactual execution, not rewriting reality

Forking a checkpoint is powerful for:

- debugging;
- prompt/model comparison;
- alternate planning experiments;
- regression analysis.

But if the original path performed irreversible external effects, the fork does not erase them.

General rule:

`fork logical Agent state != fork external world`.

Side effects must remain independently reconciled/identified.

## Mechanism 8: task-result persistence contains non-determinism

LangGraph's durable execution guidance mirrors a broader mature pattern:

```text
pure/control logic
  -> replay/re-execute safely

non-deterministic / effecting operation
  -> isolate behind task/provider boundary
  -> persist result
```

This avoids silently re-sampling a model, random number or external API during resume.

The principle matches Temporal's Workflow/Activity split, though the frameworks differ in durability scope and execution model.

## Mechanism 9: durability has levels, not one magical guarantee

Current LangGraph durability modes trade performance against checkpoint persistence timing:

```text
exit  < async < sync
performance       durability
```

This reinforces:

**"durable" must always be unpacked into the exact failure boundary and persistence guarantee.**

Do not compare frameworks only by whether they advertise durable execution.

## Mechanism 10: subgraph persistence should be scoped narrowly

A delegated sub-agent often needs persistence only during one invocation so it can interrupt/resume, not permanent state across every future call.

Use per-thread persistent subgraphs only when cross-invocation memory is genuinely required.

This prevents hidden state coupling and namespace conflicts.

## Mechanism 11: Graph API and Functional API expose the same deeper primitive

Explicit graph notation is helpful when control topology matters.

Ordinary Python is often clearer for straightforward flows.

The durable architectural primitive is not "draw everything as nodes" but:

- controlled state transitions;
- persisted task/checkpoint results;
- resumability;
- explicit side-effect boundaries.

Do not force visual graphs onto code that is simpler as structured control flow.

## Relationship to Codex

Codex already gives Ordivon a mature packaged Agent loop for engineering.

LangGraph's advantage appears only when **we are developing the Agent application itself** and need custom state/control semantics.

```text
use agent
 -> Codex

build a bespoke stateful agent protocol/application
 -> LangGraph candidate
```

This prevents framework-building from replacing productive Agent use.

## Relationship to Microsoft Agent Framework

MAF is stronger as a higher-level provider of common multi-agent collaboration patterns.

LangGraph is stronger when the interaction protocol must be represented as an explicit custom state machine with cycles/checkpoints/interrupts.

Do not maintain equivalent multi-agent workflows in both.

## Relationship to Temporal

There is overlap, but natural authority differs.

```text
Agent cognitive/control state
 -> LangGraph

business/system process state independent of agent implementation
 -> Temporal
```

A valuable composition is Temporal around LangGraph, not a duplicated process encoded twice.

Example:

```text
Temporal Paper lifecycle
  ↓
Agentic review Activity
  ↓
LangGraph review Agent
  ├─ gather
  ├─ critique
  ├─ revise loop
  └─ human interrupt
```

Temporal remains free to replace LangGraph with another Agent provider later.

## Relationship to Runtime

LangGraph task/checkpoint durability does not provide exact local physical-effect evidence.

If a graph node invokes a consequential local command:

```text
LangGraph node/task
   ↓
Runtime
```

may still be appropriate where source/executable/input binding and ambiguity-preserving physical dispatch evidence matter.

## Relationship to MCP

MCP is the preferred interoperable capability surface where available. LangGraph nodes may call MCP tools/resources without creating a new Ordivon tool protocol.

## Current Ordivon assessment

No local LangGraph installation exists.

Existing capabilities already cover most common needs:

- Codex -> packaged engineering Agent loop;
- MAF -> multi-agent orchestration patterns;
- Temporal -> generic durable workflow;
- MCP -> capabilities;
- Runtime -> exact physical execution boundary.

Therefore LangGraph is a **real but narrow on-demand capability**, useful specifically when a bespoke Agent application's state machine is itself the thing being engineered.

## Adoption triggers

Install/use LangGraph when several are true:

- explicit custom Agent state schema is useful;
- graph contains meaningful cycles/replanning loops;
- Agent state must pause/resume across human interventions;
- checkpoint inspection/forking materially improves development or operation;
- the same Agent application must survive process interruption;
- standard Codex/MAF orchestration does not express the desired protocol cleanly.

Otherwise stay with the simpler existing provider.

## What Ordivon should retain

1. Use explicit state rather than conversation-only state when program logic needs it.
2. Define reducers for concurrent/shared-state updates.
3. Treat cycles as first-class but bounded Agent control structures.
4. Persist checkpoints at meaningful logical transition boundaries.
5. Keep thread IDs application-scoped.
6. Model human intervention as an explicit pause/resume transition.
7. Use checkpoint forks for debugging/counterfactuals without pretending external effects were undone.
8. Isolate/persist non-deterministic operations behind task/provider boundaries.
9. Choose durability level according to the real failure contract.
10. Scope subgraph persistence narrowly.
11. Prefer ordinary code over graph notation when graph structure adds no clarity.

## What Ordivon should not copy

- universal Ordivon `StateGraph`;
- global thread/checkpoint database;
- another generic durable workflow engine;
- another universal Agent memory store;
- private tool protocol around graph nodes;
- LangGraph state as business/domain truth;
- duplicate MAF/Codex workflows reimplemented in LangGraph;
- time-travel semantics applied to irreversible external effects.

## Minimal prototype

```text
Typed State
   ↓
Node Registry
   ↓
Edges / conditional routing / cycle
   ↓
Super-step executor
   ↓
Reducer-based state merge
   ↓
Checkpoint(thread_id)
```

Add:

```text
interrupt -> paused checkpoint
resume(value) -> continue
old checkpoint -> fork alternate state/path
side-effect task -> persisted result
```

A four-node `plan -> act -> critique -> plan|end` graph with one interrupt is sufficient to demonstrate the kernel.

## Project-study acceptance

### One-sentence test

PASS: LangGraph is a checkpointed programmable Agent state machine, not a general replacement for packaged Agents or durable business workflows.

### Prototype test

PASS: typed state/reducers, cyclic graph execution, checkpoint/thread persistence, interrupt/resume and state forking are explicit enough to build a minimal working clone.

## Verdict

**PASS — KEEP LANGGRAPH ON-DEMAND FOR BESPOKE STATEFUL AGENT APPLICATIONS; PREFER CODEX/MAF FOR EXISTING AGENT WORK AND TEMPORAL FOR MACRO DURABLE PROCESS STATE.**
