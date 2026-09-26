# Oh My Pi Child Run + Agent Hub Kernel — extracted design and prototype specification

Status: **REGISTERED / PROTOTYPE-READY**  
Registered: 2026-09-14

## One-sentence model

**A parent Agent delegates one bounded unit of work into an independently identified child Run with its own context, Tool grant and optional isolated Workspace, then consumes a typed yield while retaining the ability to observe, steer, cancel, park and revive that child.**

## Problem

Parallel/subagent systems often degenerate into `spawn(prompt)` plus unstructured prose. That creates ambiguity around:

- child identity;
- Tool authority;
- output shape;
- workspace isolation;
- progress;
- cancellation;
- follow-up work;
- nested children;
- result provenance.

OMP's `task` + Agent Hub provides a much richer lifecycle: discoverable agent types, batch fan-out, concurrency bounds, optional isolated workspaces, background jobs, typed output schema, `agent://`/`history://` outputs, stable agent ids, parking/revival, messaging and cancellation.

## Ordivon translation

Do not create a new subagent ontology beside Harness.

```text
Parent Harness Run
   |
   +-- Child Harness Run A
   |      +-- child Run Contract
   |      +-- child cognition/session
   |      +-- child turn Tool surface
   |      `-- Runtime Workspace A (optional)
   |
   `-- Child Harness Run B
          `-- Runtime Workspace B
```

A child is a **Harness Run**, not a special process masquerading as an agent identity.

## Minimum data model

```ts
type ChildRunRequest = {
  spawnRequestId: string;
  parentRunId: string;
  name?: string;
  role?: string;
  task: string;
  sharedContext?: string;
  outputSchema?: object;
  schemaMode?: "permissive" | "strict";
  toolGrant: string[];
  isolation?: "none" | "workspace";
  async?: boolean;
};

type ChildRunRef = {
  childRunId: string;
  parentRunId: string;
  displayName: string;
  status: "queued" | "running" | "idle" | "parked" | "cancelled" | "failed" | "completed";
  workspaceId?: string;
};

type ChildYield = {
  childRunId: string;
  status: string;
  data?: unknown;
  summary?: string;
  artifactRefs: string[];
  runtimeRefs: string[];
  usage?: object;
  patchRef?: string;
};
```

## Spawn flow

```text
1. Parent authors ChildRunRequest.
2. Harness validates parent authority to spawn and requested Tool subset.
3. Allocate stable childRunId before physical execution.
4. Resolve child role/profile/model from caller policy; do not let existence imply authorization.
5. If isolated, open a fresh Runtime Workspace from an exact source revision.
6. Create child Harness Run Contract referencing parent and optional Workspace.
7. Start child Run synchronously or register as background work.
8. Child executes normal Harness model/Tool loop.
9. Child must terminate through one structured yield/completion proposal.
10. Parent receives bounded ChildYield + references; full transcript/output remains addressable separately.
```

## Tool-grant law

Child Tool availability is a subset selected explicitly from caller/parent authority.

```text
installed tools
   -> parent Run-admitted tools
      -> spawn-admitted child subset
         -> child turn-admitted tools
```

The child does not automatically inherit every Tool the parent can use.

For a first prototype, require exact Tool names and reject unknown tools before spawn.

## Structured yield

A child must not be required to encode its final result as prose only.

Minimum hidden/internal completion Tool:

```json
{
  "status": "completed",
  "data": {"...":"schema-bound result"},
  "summary": "short human/model projection",
  "artifactRefs": [],
  "runtimeRefs": []
}
```

Rules:

- `outputSchema` validates `data`;
- schema validation failure is distinct from child execution failure;
- full transcript/output is not injected into parent context by default;
- parent gets a bounded result and may fetch exact supporting evidence on demand.

## Isolation

OMP may use worktrees/other backends. Ordivon should use Runtime Workspace as the canonical isolation primitive when source mutation is involved.

Isolation flow:

```text
base source revision
  -> Runtime workspace.open
  -> child Run binds workspaceId
  -> child edits/executes there
  -> child yield references diff/commit/Artifacts
  -> caller/domain decides integration
  -> workspace.close
```

Do not let the child merge directly into canonical source merely because its Run succeeded.

Promotion/merge is a separate authority decision.

## Batch fan-out

Batching is interface sugar over multiple independent ChildRunRequests.

Required properties:

- stable child identity allocated per item;
- one concurrency semaphore/capacity policy;
- failure of one child does not erase other child identities/results;
- parent can consume partial settled results;
- each item may have different role/schema/tool subset if caller allows.

## Background jobs

A child may outlive the Tool call that spawned it.

The parent must receive immediately:

```ts
{
  childRunId,
  status: "running",
  continuationRef
}
```

Later result delivery is a projection convenience. Durable state belongs to the Child Harness Run, not the transient notification.

## Agent Hub kernel

The Hub is a **projection/control surface**, not a new state owner.

Minimum operations:

```ts
listChildren(parentRunId)
inspect(childRunId)
message(childRunId, text)
cancel(childRunId)
resume(childRunId, text?)
wait(childRunId | childRunId[])
```

### list

Return bounded rows:

- id/name/role;
- state;
- last activity;
- token/Tool usage summary;
- Workspace identity when relevant;
- unresolved effect/recovery signal.

### message / steer

A steer message is **new caller/parent ingress to the child Run**. It does not mutate hidden model state or rewrite prior messages.

### cancel

Persist child Run cancellation intent, then cancel active Runtime Jobs owned by that child where the exact effect semantics permit. Cancellation does not retroactively prove no external effect occurred.

### park / revive

A quiescent child may release model/process resources while retaining durable Run/session identity. Revival reconstructs the Run from durable state and fresh provider/runtime observations.

A parked child is not a new child.

## Nested children

Represent lineage explicitly:

```text
parentRunId -> childRunId -> grandchildRunId
```

Enforce a recursion-depth policy at spawn admission, not by hiding lineage.

Nested child outputs may use hierarchical resource names, but resource naming is convenience; Run IDs remain authoritative.

## Failure matrix

| Failure | Standing |
|---|---|
| invalid child schema/request | no child Run created |
| unknown Tool requested | reject before Run creation |
| Workspace open fails | child never starts; explicit failed admission |
| provider fails during child Run | child Run failure/recovery semantics |
| Runtime effect uncertain | child cannot claim clean completion until reconciled/declared unknown |
| child output violates schema | execution may have occurred; result standing = invalid structured yield |
| parent disappears | child durable identity remains; caller may reattach |
| notification lost | inspect Child Run; never respawn solely because notification was lost |

## Minimum prototype

Implement:

- `spawnChild()` over existing Harness create/run;
- exact parent/child Run linkage;
- explicit Tool subset;
- JSON Schema output;
- one isolated Runtime Workspace mode;
- concurrency semaphore;
- `list/inspect/message/cancel/wait` projection API;
- bounded child output Artifact.

Skip fancy TUI, role discovery and parking until the identity/lifecycle path passes.

## Acceptance tests

1. Parent spawns two children concurrently and receives two stable IDs.
2. Each child sees only its admitted Tool subset.
3. One child failure does not erase the other result.
4. Typed yield is schema-validated.
5. Full child transcript remains out of parent context until requested.
6. Isolated child source mutations do not modify parent's Workspace.
7. Lost spawn response is recovered by child/spawn identity without duplicate child execution.
8. Steer message becomes new child ingress and is visible after resume.
9. Cancel terminates live computation but preserves evidence of already-committed Runtime work.
10. Parent process restart can list/reconnect to durable child state.

## Project-study acceptance

### One-sentence test

PASS: OMP's subagent system is best understood as first-class child execution lifecycles with structured yield and supervision, not merely parallel prompts.

### Prototype test

PASS: the Run mapping, Tool-subset law, Workspace isolation and Hub controls are explicit enough to implement a child-Run prototype using current Harness/Runtime primitives.

## Verdict

**PASS — HIGH-VALUE; IMPLEMENT AS CHILD HARNESS RUNS, NOT A SECOND AGENT STATE MACHINE.**
