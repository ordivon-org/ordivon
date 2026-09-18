# Ordivon Agent Service — Execution Ownership / Remote Evidence R11

Status: **IMPLEMENTED / REMOTE EVIDENCE ENTERS LOCAL SEMANTIC VERIFIER / CLAIM TRANSFER DEFERRED**
Date: 2026-09-18
Base implementation: `80234d0aadf151225aaa1854920a43c8a4008788`
Architecture delta: `knowledge/graphs/ordivon-agent-service-r11-remote-evidence-delta.json`
Acceptance: `evidence/acceptance/agent-service-remote-evidence-r11.json`

## Result

R11 closes the gap between remote provider completion and local semantic Task truth without allowing double execution.

The two key changes are:

```text
TaskExecutionClaim
  ├── LOCAL_ASSIGNMENT
  └── REMOTE_BINDING
```

and:

```text
RemoteDeliveryObservation
        ↓
RemoteArtifactReader
        ↓
digest / identity / kind checks
        ↓
EvidenceBundle
        ↓
existing EvidenceSemanticVerifier
        ↓
RemoteTaskVerificationRecord
        ↓
local Task verdict
```

## Why execution ownership had to come first

Before R11, one Task could theoretically acquire a local Assignment while also having a remote Delegation/TransportBinding. Both paths were individually valid but there was no shared owner primitive preventing both from executing.

R11 adds `TaskExecutionClaimStore` as the single execution-owner authority.

A claim is immutable and has exactly one mode:

```text
LOCAL_ASSIGNMENT -> owner is Assignment.id
REMOTE_BINDING   -> owner is TransportBinding.id
```

The Task id is unique in the claim table.

## Local Assignment path

`ClaimAwareAssignmentPlanner` replaces the R11-visible planner.

Assignment creation and execution ownership happen in the same database transaction:

```text
choose READY AgentInstance
      ↓
create Assignment
      ↓
claim Task as LOCAL_ASSIGNMENT
      ↓
Task -> ASSIGNED
      ↓
TASK_ASSIGNED event
```

If a remote Binding already owns the Task, local planning fails closed.

Historical Assignments created before R11 are lazily adopted as LOCAL_ASSIGNMENT claims when re-entered through the R11 planner.

## Remote delivery path

A DelegationEnvelope does not own execution. A TransportBinding does not own execution merely because it exists.

Execution ownership begins only when a specific Binding is about to perform the external delivery effect.

`ClaimAwareDeliveryCoordinator` does:

```text
resolve Binding / Delegation / Task
      ↓
check adapter exists
      ↓
check Goal readiness when Goal-managed
      ↓
claim Task as REMOTE_BINDING
      ↓
Task -> RUNNING
      ↓
REMOTE_EXECUTION_CLAIMED
      ↓
external DeliveryAdapter.send
```

The claim is committed **before** the external send.

Therefore if the remote provider commits but the response is lost:

```text
Task remains RUNNING
REMOTE_BINDING claim remains durable
no local Assignment can start
no alternate Binding can start
retry reuses the same delivery_request_id
```

This is fail-closed rather than guessing whether the remote side executed.

## Route candidates are not execution candidates

R9 intentionally allowed multiple immutable route Bindings for one Delegation:

```text
A2A primary
MCP fallback
```

R11 preserves that design but allows only one Binding to execute.

Once A2A primary claims the Task, MCP fallback cannot send the same Task.

Safe fallback now requires a future explicit **execution claim transfer/release protocol** that proves the old owner can no longer execute. R11 does not fake such a proof.

## DAG readiness applies to remote work

Remote delivery cannot bypass R7 dependencies.

For Goal-managed Tasks, the delivery coordinator requires the same derived readiness condition before acquiring a remote claim.

A blocked Task remains:

```text
Task = PENDING
execution claim = none
remote send = not performed
```

## Remote terminal is still not semantic completion

R10 established this law; R11 makes the next step explicit.

After delivery:

```text
Task = RUNNING
Goal = RUNNING after Goal reconciliation
```

After the provider reports:

```text
TASK_STATE_COMPLETED
terminal = true
successful = true
```

the Task is **still RUNNING**.

Only `RemoteTaskCompletionReconciler` may create a local verdict.

## Remote artifact evidence

For a successful remote execution, R11 requires evidence.

`RemoteArtifactReader` is a provider/transport seam returning:

```text
artifact_ref
kind
digest
content
```

`RemoteArtifactEvidenceResolver` verifies:

- the returned artifact ref exactly matches the requested ref;
- artifact kind is valid;
- content is text for the current text acceptance family;
- SHA-256 of content equals the supplied digest;
- exactly one artifact matches the acceptance artifact kind.

Only then is the content exposed in-memory as normalized EvidenceBundle facts.

Durable receipt stores provenance such as:

```text
bindingId
deliveryRequestId
remoteObservationId
remoteTaskId
remoteContextId
artifactRef
artifactKind
digest
byteLength
providerEvidenceRef
```

It does **not** persist raw remote artifact text.

## One semantic verifier

R11 deliberately uses the existing `EvidenceSemanticVerifier` from the local Runtime evidence path.

The semantic question remains:

```text
Does normalized evidence satisfy Task.acceptance?
```

It does not become:

```text
Does A2A say success?
Does MCP say success?
Does the remote agent say success?
```

Provider success only opens the evidence-verification path.

## Mechanical remote failure

A terminal remote provider failure can produce a local FAILED Task, but only through `RemoteTaskCompletionReconciler` and a durable `RemoteTaskVerificationRecord` with:

```text
stage = mechanical
resolver = remote_mechanical_gate
```

The RemoteDeliveryObserver itself never mutates Task terminal state.

## Digest mismatch behavior

If a remote artifact's claimed digest does not match its content:

```text
ArtifactDigestMismatch
Task remains RUNNING
no RemoteTaskVerificationRecord is created
```

This avoids turning corrupted/unverified evidence into a negative semantic verdict.

## R10 -> R11 migration

R10 could already have durable DeliveryReceipts but no execution-claim table.

R11 supports safe adoption:

```text
existing R10 DeliveryReceipt
      ↓
R11 delivery exact replay
      ↓
NO remote resend
      ↓
create REMOTE_BINDING claim
Task PENDING -> RUNNING
return historical receipt
```

If a historical local Assignment exists instead, R11 adopts the local claim and blocks remote delivery.

## Goal-level dogfood

The composed R11 path was exercised end-to-end:

```text
remote delivery
  -> Task RUNNING
  -> Goal RUNNING
remote terminal success
  -> Task still RUNNING
remote artifact digest + acceptance pass
  -> RemoteTaskVerificationRecord semantic/accepted
  -> Task SUCCEEDED
Goal reconcile
  -> Goal SUCCEEDED
```

Observed:

```text
claimMode = REMOTE_BINDING
claimOwnerMatchesBinding = true
taskAfterDelivery = RUNNING
goalAfterDelivery = RUNNING
remoteTerminal = true
taskAfterRemoteTerminal = RUNNING
verificationStage = semantic
verificationAccepted = true
finalTask = SUCCEEDED
finalGoal = SUCCEEDED
evidenceResolver = remote_artifact_text
evidenceContainsDigest = true
evidenceContainsRawAcceptedText = false
```

## Compatibility debt

The existing frozen acceptance schema calls the artifact-text rule:

```text
runtime_artifact_text_contains
```

R11 reuses its semantic contract for remote evidence so local and remote verification do not fork.

The **resolver** is correctly remote-specific (`remote_artifact_text`), but the acceptance-kind name is now legacy wording. Renaming it to a transport-neutral name should be a dedicated schema migration rather than an incidental R11 change.

## Explicitly deferred

R11 does not implement:

```text
execution claim release
execution claim transfer
proved-safe route failover
remote cancellation proof
transport-neutral acceptance-schema rename
live A2A/MCP artifact readers
```

These are now isolated follow-up capabilities rather than hidden ambiguity in Task execution semantics.
