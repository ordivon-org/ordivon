# Oh My Pi Branchable Session + Context Projection Kernel — extracted design and prototype specification

Status: **REGISTERED / PROTOTYPE-READY**  
Registered: 2026-09-14

## One-sentence model

**Persist an append-only tree of what happened, keep a movable current leaf, and reconstruct only the branch-local context needed by the model instead of treating the entire transcript as current cognition.**

## Problem

Long-running agents need all of the following at once:

- durable history;
- branching/forking;
- compaction;
- resume;
- provider/model state changes;
- current-context reconstruction;
- transcript inspection;
- protection against dangling or invalid Tool-call state.

A flat mutable `messages[]` cannot represent these cleanly without conflating history, cognition and UI transcript.

OMP uses append-only session entries linked by `id` / `parentId`, plus a current leaf. Context is reconstructed by walking one path to the root and applying reset/compaction/state rules.

This independently aligns with Ordivon Harness's stronger law:

```text
Canonical History != Durable Cognition != Interaction Cognition != Attempt Cognition
```

OMP's storage model is a useful implementation donor; Ordivon's cognition ownership remains canonical.

## Minimum data model

```ts
type SessionId = string;
type EntryId = string;

type SessionHeader = {
  sessionId: SessionId;
  version: number;
  createdAt: string;
  workspaceRef?: string;
  parentSession?: string;
};

type EntryBase = {
  id: EntryId;
  parentId: EntryId | null;
  timestamp: string;
};

type SessionEntry =
  | (EntryBase & { type:"message"; message: AgentMessage })
  | (EntryBase & { type:"model_change"; model:string })
  | (EntryBase & { type:"compaction"; summary:string; firstKeptEntryId?:EntryId })
  | (EntryBase & { type:"branch_summary"; summary:string; fromId:EntryId })
  | (EntryBase & { type:"reset_boundary" })
  | (EntryBase & { type:"control_state"; key:string; value:unknown })
  | (EntryBase & { type:"custom"; kind:string; payload:unknown });

type SessionState = {
  header: SessionHeader;
  leafId: EntryId | null;
  entriesById: Map<EntryId, SessionEntry>;
};
```

For a first prototype, an append-only JSONL file is enough. A database is not required to prove the semantics.

## Core operations

```ts
append(entryWithoutIdParent): EntryId
branch(entryId): void
resetLeaf(): void
buildContext(leafId?): ModelContext
buildTranscript(leafId?): Transcript
compact(request): CompactionEntry
fork(entryId): NewSession
```

### Append

- new entry receives `parentId=currentLeaf`;
- entry is persisted before becoming the durable leaf;
- existing entries are never mutated for ordinary branch navigation.

### Branch

- verify target entry exists;
- move only the current leaf pointer;
- next append creates a new child from the selected target.

### Reset

- append an explicit reset boundary or set leaf to null depending on desired semantics;
- do not delete history merely to hide it from current model context.

## Context reconstruction algorithm

Minimum deterministic algorithm:

```text
1. Resolve selected leaf.
2. Walk parentId to root.
3. Detect repeated id; stop/fail on corrupt cycle.
4. Reverse into root -> leaf order.
5. Derive latest control state (model, mode, injected rules, etc.).
6. Find latest reset boundary.
7. Within visible suffix, find latest applicable compaction.
8. Emit summary + kept/post-compaction semantic messages.
9. Remove/neutralize dangling Tool calls or invalid aborted assistant turns.
10. Return model context separately from display transcript.
```

The prototype must have **two projections**:

- `buildModelContext()` — bounded current decision context;
- `buildTranscript()` — human/audit history projection.

They must not be aliases.

## Ordivon-specific composition

OMP session entries must not absorb Runtime truth.

Instead use references:

```ts
type ToolEvidenceRef = {
  runtimeJobId?: string;
  runtimeArtifactId?: string;
  operationDigest?: string;
  deliveryDisposition?: string;
};
```

A Harness history event may record that the Agent observed or requested an effect, but the Runtime Job/Artifact remains the physical authority.

Likewise Host Task completion remains outside the Session.

## Cognition integration

The OMP tree is primarily **canonical Run history + reconstruction mechanics**. Ordivon should preserve a separate explicit WorkingSet / cognition selection layer.

Recommended compilation:

```text
branch path from Session Graph
      +
Agent-selected Durable Cognition
      +
current caller ingress
      +
current Tool observations
      +
current Execution Control
      |
      v
Effective Model View
```

Thus branching history does not implicitly decide long-lived cognition.

## Compaction

A minimal compaction entry contains:

```ts
{
  type: "compaction",
  summary,
  firstKeptEntryId,
  sourceLeafId,
  sourceDigest,
  tokensBefore
}
```

Rules:

1. compaction is an append-only derived projection, not destructive history rewrite;
2. its source branch identity is explicit;
3. a later branch before the compaction naturally excludes it;
4. the exact pre-compaction history remains inspectable;
5. summary semantic quality is not silently equated with source truth.

## Branch summary

When abandoning one path and returning to an earlier point, an optional `branch_summary` may carry useful findings from the discarded path into the new branch.

It should be treated as **new cognition/history content**, not as mutation of the prior branch.

## Persistence and large content

Follow a split similar to OMP but map onto existing owners:

- compact entries/events remain in Harness Journal/session storage;
- large/binary content belongs in CAS/Artifact storage;
- history references blobs by digest/URI;
- model view fetches only the bounded representation required now.

Do not duplicate Runtime Artifacts into Harness session JSONL.

## Recovery

On reopen:

1. load header/version;
2. validate entries and ids;
3. rebuild index;
4. verify current leaf or deterministically choose last valid entry;
5. reconstruct branch-local control/cognition projection;
6. reconcile unresolved Provider/Tool effects through their actual authority before allowing unsafe continuation.

A loaded transcript does not prove an uncertain physical Tool result.

## Failure modes

| Failure | Required behavior |
|---|---|
| malformed entry | fail/skip according to explicit compatibility policy; never reinterpret silently |
| parent missing | mark history damaged; do not invent parent |
| parent cycle | stop/fail boundedly |
| leaf missing | explicit recovery path |
| compaction source invalid | ignore/fail compaction, retain source history |
| dangling Tool call | remove from model projection or reconcile; retain canonical evidence |
| branch switch during active effect | preserve effect identity; branch movement must not authorize duplicate dispatch |

## Minimal prototype

Implement in ~one package with:

- JSONL append store;
- in-memory id index;
- `leafId` metadata;
- 6 entry variants;
- `append/branch/buildContext/buildTranscript/compact`;
- one fake Provider Tool call pair;
- one Runtime-reference entry.

No TUI is necessary.

## Acceptance tests

1. Linear session reconstructs exactly.
2. Branching from an old entry leaves original future history untouched.
3. New branch context excludes sibling future messages.
4. Full transcript can still show both branches/history.
5. Compaction reduces model context without deleting old entries.
6. Branching before compaction excludes that compaction.
7. Reset hides prior model context but retains audit history.
8. Corrupt parent cycle cannot loop forever.
9. Dangling Tool call is not emitted as if completed.
10. Runtime evidence reference survives resume without becoming copied Runtime truth.

## Project-study acceptance

### One-sentence test

PASS: OMP sessions are an append-only branch graph plus deterministic context projection, not a mutable transcript list.

### Prototype test

PASS: the entry taxonomy, leaf semantics and reconstruction algorithm are explicit enough to implement a functioning branch/compact/resume prototype while preserving Ordivon cognition boundaries.

## Verdict

**PASS — ADOPT STORAGE/RECONSTRUCTION PATTERN; KEEP ORDIVON HISTORY/COGNITION/EFFECT OWNERSHIP.**
