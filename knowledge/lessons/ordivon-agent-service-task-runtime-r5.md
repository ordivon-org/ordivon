# Ordivon Agent Service — Task / Runtime Vertical Slice R5

Status: **IMPLEMENTED / LIVE LOCAL RUNTIME DOGFOOD / NOT YET CANONICAL-CUTOVER**
Date: 2026-09-18
Base implementation: `1744076b10616d74460c2bb51a428339c4dc2991`
Architecture delta: `knowledge/graphs/ordivon-agent-service-r5-task-runtime-delta.json`
Acceptance receipt: `evidence/acceptance/agent-service-task-runtime-r5.json`

## One-sentence result

**R5 proves that an Agent Service Task can be durably assigned to a READY Agent, admitted to the real Ordivon Runtime as one recoverable Runtime Job, and completed only after a separate Agent Service semantic verifier accepts Runtime evidence.**

## Implemented LEGO path

```text
TaskStore (N05)
   ↓
AssignmentPlanner (N11)
   ↓
AssignmentStore (N06)
   ↓
AssignmentActivator (N15)
   ↓
RuntimeMcpAdapter (N19)
   ↓
Ordivon Runtime Job / Attempt
   ↓
RuntimeJobObserver (N25 discovered in R5)
   ↓
SemanticVerifier (N13)
   ↓
TaskStore
```

## Core identity separation

R5 has three distinct identities:

```text
TaskId
  semantic work identity owned by Agent Service

AssignmentId
  binding of one Task to one AgentInstance

RuntimeJobId
  physical execution identity owned by Runtime
```

They are never aliased.

An Assignment also owns a stable Runtime request identity before any Runtime effect:

```text
agent-service:assignment:<assignmentId>:run:v1
```

That value is persisted together with the Assignment before Runtime submission.

## Response-loss law

The critical sequence is:

```text
persist Assignment + stable clientRequestId
             ↓
Runtime workspace.exec
             ↓
Runtime may commit Job
             ↓
Agent Service may crash before writing runtimeJobId
             ↓
restart
             ↓
workspace.exec with exact same clientRequestId + execution
             ↓
Runtime exact replay
             ↓
same Runtime Job
```

R5 live dogfood verified this behavior against the production Runtime.

## Semantic completion law

Runtime's public contract deliberately projects:

```text
semanticCompletionEvaluated = false
```

R5 treats any Runtime observation claiming otherwise as an authority violation.

The verifier evaluates terminal Runtime evidence in this order:

1. Runtime Job must be mechanically terminal.
2. Runtime `status` must be `succeeded`.
3. Runtime delivery must be `committed`.
4. Agent Service acceptance contract must be satisfied.
5. Only then may Task become `SUCCEEDED`.

Therefore:

```text
Runtime exit 0
      !=
Task success
```

and likewise:

```text
stdout looks correct + Runtime failed
      !=
Task success
```

## Minimal Task state machine

```text
PENDING
  ↓ planner
ASSIGNED
  ↓ Runtime Job bound
RUNNING
  ↓ terminal evidence + semantic verifier
SUCCEEDED | FAILED
```

R5 intentionally does not yet implement Task retry generations, cancellation semantics, deadlines, priorities, Goal ownership, or multi-assignment fan-out.

## Planner boundary

The R5 planner selects only a semantic AgentInstance that is:

```text
state == READY
revision_id == task.required_revision_id
```

No READY matching Agent means planning fails closed and Task stays `PENDING`.

This is intentionally a minimal deterministic planner rather than a scheduler policy engine.

## Runtime provider boundary

`RuntimeMcpAdapter` uses only the public Runtime MCP surface:

```text
workspace.exec
 task.observe
```

It does not read Runtime Registry SQLite, Attempt files, systemd units, or Runtime implementation state.

The local production client reads Runtime endpoint and bearer-token-file configuration from `/etc/ordivon/ordivon-runtime.env`; the bearer value remains in memory and is redacted from object representation.

## Hidden node discovered by LEGO decomposition

R2 used one broad `ProviderObserver` node for observations flowing from both carrier and Runtime adapters. R4/R5 implementation showed this is too coarse.

Carrier observation answers:

> Is the Agent carrier/provider binding present and ready?

Runtime observation answers:

> What mechanically happened to this exact Runtime Job?

They differ in identity, retry behavior, effect authority and evidence semantics. R5 therefore records a newly discovered architecture node:

```text
N25 RuntimeJobObserver
```

Its current realization is the observation half of `RuntimeMcpAdapter`. This may become a separate symbol later if independent replacement becomes useful.

## R5 acceptance kinds

The clean-room kernel currently supports only:

```text
stdout_contains
stdout_equals
```

This is deliberately narrow. It proves the authority split, not a complete scientific/artifact verification system.

A later LEGO should resolve durable Runtime Artifacts / external domain evidence instead of assuming a 64 KiB retained stdout tail is enough for all Tasks.

## Live dogfood

A separate Runtime target Workspace was used so the Agent Service test process and target execution did not share one Workspace reservation.

Four local execution cases were run through the production Runtime MCP:

### Semantic success

```text
Runtime: succeeded
stdout: R5_SEMANTIC_OK
acceptance: stdout_contains R5_SEMANTIC_OK
Task: SUCCEEDED
```

### Exit-zero semantic mismatch

```text
Runtime: succeeded
stdout: WRONG_OUTPUT
acceptance: stdout_contains EXPECTED_MARKER
Task: FAILED
reason: acceptance:stdout_contains:not_satisfied
```

### Mechanical failure despite matching output

```text
Runtime: failed (exit 7)
stdout contains EXPECTED_MARKER
Task: FAILED
reason: runtime:failed
```

### Response-loss replay

A Runtime Job was first admitted with the Assignment's stable clientRequestId without persisting the returned jobId into Agent Service. `AssignmentActivator` then replayed the same exact request and recovered the same Runtime Job identity.

```text
sameRuntimeJob = true
Task = SUCCEEDED
```

## R5 verdict

**TASK/RUNTIME AUTHORITY SPLIT HOLDS.** The real Runtime can be inserted behind N19 without changing Task identity or semantic completion ownership, and Runtime exact replay provides the mechanical recovery primitive required by the Assignment LEGO.
