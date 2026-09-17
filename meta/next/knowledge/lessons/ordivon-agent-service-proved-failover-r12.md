# Ordivon Agent Service — Proved-safe Remote Failover R12

Status: **IMPLEMENTED / QUIESCENCE + REPLAY SAFETY + CAS CLAIM TRANSFER / LIVE PROVIDER ADAPTERS DEFERRED**
Date: 2026-09-18
Base implementation: `595dfcbc50e82a7280025461f6db2ae8592f465c`
Architecture delta: `knowledge/graphs/ordivon-agent-service-r12-proved-failover-delta.json`
Acceptance: `evidence/acceptance/agent-service-proved-failover-r12.json`

## One-sentence result

**R12 makes remote failover a three-proof protocol: persist and prove the old execution is quiescent, independently prove re-execution is effect-safe, then atomically transfer the Task's REMOTE_BINDING claim to a pristine fallback Binding.**

## Why R11's fail-closed owner needed another slice

R11 deliberately refused automatic fallback once a remote Binding owned a Task. That prevented double execution, but it also meant fallback could never occur safely.

The naive next step would have been:

```text
cancel source
    ↓
move claim to fallback
```

That is insufficient for two independent reasons:

1. A cancellation request/acknowledgement does not prove the old executor stopped.
2. Even if it stopped, it may already have produced irreversible or partial side effects.

R12 therefore separates:

```text
ExecutionQuiescenceProof
        ≠
ReplaySafetyDecision
```

Both are required before ownership can move.

## Current protocol basis

The current A2A specification states that Cancel Task asks the server to attempt cancellation and success is not guaranteed. A returned/terminal task lifecycle describes provider work state, but A2A operation idempotency does not promise rollback of arbitrary business effects.

The MCP 2026-07-28 Tasks extension is even more explicit: `tasks/cancel` is cooperative intent. A successful cancellation request is an acknowledgement; the task may remain `working`, and may ultimately reach a terminal state other than `cancelled`, including completion.

Therefore R12 never interprets a cancel ACK as quiescence.

## LEGO 1 — ExecutionQuiescenceRequestStore

Before invoking any external quiescence/cancel provider, R12 persists:

```text
ExecutionQuiescenceRequest
├── client exact request id
├── Task id
├── source Binding id
└── state
    ├── REQUESTED
    ├── PROVED
    └── NOT_PROVED
```

This closes the response-loss window.

The order is:

```text
pure failover preflight
        ↓
REQUESTED persisted
        ↓
REMOTE_EXECUTION_QUIESCENCE_REQUESTED event
        ↓
provider effect
```

If the provider accepts cancellation/quiescence and the response is lost, the local row remains `REQUESTED`.

`TransferAwareDeliveryCoordinator` treats any quiescence-attempt history as a freeze:

```text
REQUESTED / PROVED / NOT_PROVED
        ↓
old Binding cannot be delivered again
```

The source Task claim remains unchanged until all failover proof gates pass.

## LEGO 2 — ExecutionQuiescenceProof

`ExecutionQuiescenceCoordinator` answers only:

```text
Can the previous remote owner still execute?
```

It does not answer whether replay is safe.

A provider observation may directly establish quiescence only when:

```text
terminal = true
successful = false
```

This covers normalized failed/cancelled/rejected-style terminal outcomes.

The following is deliberately insufficient:

```text
terminal = true
successful = null
```

That requires an explicit provider-specific `ExecutionQuiescenceAdapter` proof.

Any historical observation with:

```text
terminal = true
successful = true
```

blocks failover, even if a later provider status appears to regress. Completed work belongs in R11 evidence/semantic verification, not retry/failover.

Remote task/context correlation in a quiescence proof must remain consistent with the DeliveryReceipt or latest established observation.

## LEGO 3 — ReplaySafetyDecision

Quiescence does not answer:

```text
Did the old attempt already charge money?
Did it publish a message?
Did it write half a transaction?
Did it perform an irreversible operation?
Can the fallback safely repeat the work?
```

Those are effect-domain questions.

R12 therefore delegates them to a separate `ReplaySafetyAdapter` and persists a target-bound decision:

```text
ReplaySafetyDecision
├── Task
├── source Binding
├── target Binding
├── quiescence proof
├── safe boolean
├── classification
├── reason
└── evidence reference
```

Recognized positive classifications are:

```text
NO_EFFECTS
ROLLED_BACK
COMPENSATED
IDEMPOTENT_REPLAY
```

Examples that block transfer include:

```text
PARTIAL_EFFECTS
UNKNOWN
UNSAFE
```

These classification names are Ordivon effect-domain contracts. They are not inferred merely from A2A/MCP task status.

## Pure preflight before external effects

R12 validates the failover structure before invoking a provider:

```text
source != target
same DelegationEnvelope
Task = RUNNING
source owns current REMOTE_BINDING claim
target is pristine
Task has no verification verdict
```

A pristine fallback currently means:

```text
no DeliveryReceipt
no remote observation history
no quiescence-attempt history
no prior execution-claim transfer history
```

If the target is dirty or cross-Delegation, failover rejects before calling the quiescence adapter or replay-safety adapter.

This avoids freezing a healthy source only to discover later that the proposed fallback was invalid.

## LEGO 4 — CAS ExecutionClaimTransfer

Only after both positive gates exist:

```text
quiescence_proof.quiescent = true
replay_safety_decision.safe = true
```

may `ExecutionClaimTransferCoordinator` perform:

```text
UPDATE task_execution_claims
SET owner_id = fallback
WHERE task_id = T
  AND mode = REMOTE_BINDING
  AND owner_id = source
```

Exactly one row must change.

If another actor changed ownership first, transfer fails closed.

The durable transfer record binds:

```text
Task
source Binding
target Binding
quiescence proof
replay-safety decision
ordered transfer sequence
exact client transfer identity
```

A quiescence proof can be consumed by at most one transfer.

## Fallback does not complete the Task

After successful transfer:

```text
Task = RUNNING
claim = REMOTE_BINDING(fallback)
```

Fallback delivery may now occur.

Even if the fallback eventually reports completion, semantic completion remains R11's responsibility:

```text
remote provider result
        ↓
remote evidence/artifact
        ↓
digest verification
        ↓
EvidenceSemanticVerifier
        ↓
Task verdict
```

R12 therefore changes execution ownership, not acceptance authority.

## Late old-owner results

A source provider can theoretically emit a late message after local claim transfer.

That late observation may be stored for audit/correlation, but the old Binding can no longer complete the Task through R11 because `RemoteTaskCompletionReconciler` checks that the Binding still owns the Task execution claim.

This is the final defense against stale-owner semantic takeover.

## Response-loss semantics

### Quiescence provider response loss

```text
quiescence REQUESTED persisted
provider commits/acts
response lost
```

Result:

```text
Task claim stays on source
source Binding remains frozen
no fallback transfer yet
```

Exact retry uses the same quiescence request identity and reconciles the provider result.

### Replay-safety response loss

The source is already frozen by quiescence. Exact replay uses the same replay-safety request identity. Ownership does not move until the durable positive decision exists.

### Transfer replay

Once the local CAS transfer is committed, exact failover replay returns the historical transfer record before attempting new provider effects.

## What R12 does NOT claim

R12 does not claim universal exactly-once business effects.

It also does not yet provide concrete live implementations for:

```text
A2A CancelTask / status quiescence adapter
MCP tasks/cancel + tasks/get quiescence adapter
application/database effect journal replay-safety adapter
compensation engine
business transaction rollback engine
```

Those are replaceable adapters that must satisfy the R12 contracts.

## Composition dogfood

A composed SQLite/service run exercised:

```text
primary delivery
  ↓
REMOTE_BINDING(primary)
  ↓
quiescence request/proof
  ↓
ReplaySafety = COMPENSATED
  ↓
CAS primary -> fallback
  ↓
old primary delivery blocked
  ↓
fallback delivery
```

Observed:

```text
sourceOwnerBeforeTransfer = true
quiescenceRequestState = PROVED
quiescent = true
replaySafe = true
replayClassification = COMPENSATED
claimOwnerAfterTransfer = true
oldBindingFrozen = true
fallbackReceiptBindingMatches = true
sourceSendCount = 1
fallbackSendCount = 1
taskState = RUNNING
```

The Task remained RUNNING exactly as required.

## Next boundary

R13 should not invent another failover abstraction. The useful next work is concrete adapter realization and effect-ledger integration:

```text
A2AQuiescenceAdapter
MCPTaskQuiescenceAdapter
ReplaySafetyAdapter backed by effect/idempotency/compensation evidence
```

The semantic failover protocol is now independent of those providers.
