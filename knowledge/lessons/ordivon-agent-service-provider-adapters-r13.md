# Ordivon Agent Service — Provider / Effect Adapters R13

Status: **IMPLEMENTED / A2A + MCP TASK QUIESCENCE + EFFECT-LEDGER REPLAY SAFETY**
Date: 2026-09-18
Base implementation: `5915c494c8ecabd97fc9a5233e1d76a3a18fa44a`
Architecture delta: `knowledge/graphs/ordivon-agent-service-r13-provider-adapters-delta.json`
Acceptance: `evidence/acceptance/agent-service-provider-adapters-r13.json`

## One-sentence result

R13 keeps R12's failover protocol unchanged and supplies concrete A2A/MCP task-lifecycle adapters plus an external effect-ledger replay-safety adapter.

## Provider layer is not a new authority

R13 deliberately does not create another durable state machine.

It contains:

```text
protocol client
      ↓
provider adapter
      ↓
normalized R12 observation
```

R12 still owns:

```text
ExecutionQuiescenceRequest
ExecutionQuiescenceProof
ReplaySafetyDecision
ExecutionClaimTransfer
```

R11 still owns semantic completion.

## A2A adapter

`A2AQuiescenceAdapter` uses the current JSON-RPC operation names:

```text
CancelTask
GetTask
```

The remote Task identity must match the DeliveryReceipt/established correlation.

State mapping:

```text
TASK_STATE_CANCELED  -> quiescent
TASK_STATE_FAILED    -> quiescent
TASK_STATE_REJECTED  -> quiescent
TASK_STATE_COMPLETED -> RemoteExecutionCompleted
SUBMITTED/WORKING/INPUT_REQUIRED/AUTH_REQUIRED/UNSPECIFIED
                     -> QuiescencePending
```

A nonterminal CancelTask response is followed by GetTask.

The current A2A specification also allows CancelTask to return TaskNotCancelableError when the task is already terminal. JSON-RPC code -32002 is therefore recovered by GetTask. TaskNotFound is not promoted into quiescence because a purged task does not reveal its prior terminal outcome.

### A2A HTTP client

`A2AJsonRpcHttpClient`:

- uses the exact durable R12 sub-request identity as the JSON-RPC id;
- requires explicit protocol version configuration;
- emits `A2A-Version`;
- requires HTTPS for non-loopback providers;
- accepts credentials/other headers only from an out-of-band header provider;
- never includes header values in repr.

The Agent Service database does not store those header secrets.

## MCP Tasks adapter

MCP 2026-07-28 is stateless and the Tasks feature is the `io.modelcontextprotocol/tasks` extension.

`MCPTasksHttpClient` attaches to each task request:

```text
MCP-Protocol-Version: 2026-07-28
Mcp-Method: tasks/get | tasks/cancel
Mcp-Name: <taskId>

_meta.io.modelcontextprotocol/clientInfo
_meta.io.modelcontextprotocol/clientCapabilities.extensions.io.modelcontextprotocol/tasks
```

`MCPTaskQuiescenceAdapter` always performs:

```text
tasks/cancel
     ↓
ACK only
     ↓
tasks/get
     ↓
observable task status
```

Mapping:

```text
cancelled -> quiescent
failed    -> quiescent
completed -> RemoteExecutionCompleted
working   -> QuiescencePending
input_required -> QuiescencePending
```

Thus an MCP cancellation acknowledgement can never satisfy R12 by itself.

## Effect-ledger replay safety

`EffectLedgerReader` is intentionally external.

R13 does not infer effect truth from:

- provider Task status;
- HTTP success;
- absence of local rows;
- model claims;
- an empty unsealed list.

The reader returns an exact target-bound `EffectLedgerSnapshot`:

```text
Task id
source Binding id
target Binding id
complete coverage flag
effect records
evidence ref
```

Each effect can carry:

```text
effect_id
state
idempotency_key
replay_target_binding_id
evidence_ref
```

### Derived classifications

If `complete=false`:

```text
UNKNOWN / unsafe
```

If `complete=true` and there are zero effects:

```text
NO_EFFECTS / safe
```

If every effect is rolled back:

```text
ROLLED_BACK / safe
```

If remaining effects are rolled back or compensated and at least one is compensated:

```text
COMPENSATED / safe
```

If committed effects remain, every committed effect must have:

```text
non-empty idempotency_key
AND
replay_target_binding_id == exact fallback Binding
```

Only then:

```text
IDEMPOTENT_REPLAY / safe
```

Otherwise:

```text
PARTIAL_EFFECTS / unsafe
```

This is stronger than generic request idempotency because the evidence must bind the idempotency protection to the exact target Binding.

## No shadow effect authority

R13 adds no SQLite tables and no effect write API.

```text
external effect authority
        ↓
EffectLedgerReader
        ↓
EffectLedgerSnapshot
        ↓
EffectLedgerReplaySafetyAdapter
        ↓
R12 ReplaySafetyDecision
```

This preserves the earlier rule that Agent Service must not become a second execution/effect ledger.

## Credential boundary

A2A/MCP HTTP credentials are intentionally injected at the transport boundary through `header_provider(binding)`.

They are not fields on:

```text
Task
DelegationEnvelope
TransportBinding
ExecutionQuiescenceProof
ReplaySafetyDecision
```

The HTTP client reprs redact the entire header provider boundary.

## R13 composition

`AgentServiceR13.open(...)` wires:

```text
a2a-jsonrpc -> A2AQuiescenceAdapter
mcp         -> MCPTaskQuiescenceAdapter
effect ledger -> EffectLedgerReplaySafetyAdapter
```

and delegates all durable semantics to AgentServiceR12.

## Dogfood

A composed service run exercised:

```text
A2A primary delivery
  ↓
CancelTask -> TASK_STATE_CANCELED
  ↓
R12 quiescence proof
  ↓
complete external effect snapshot, zero effects
  ↓
NO_EFFECTS replay decision
  ↓
R12 CAS claim transfer
  ↓
MCP fallback delivery
```

Observed:

```text
sourceOwnerBefore = true
a2aCancelMethod = CancelTask
quiescent = true
quiescenceProviderStatus = TASK_STATE_CANCELED
replaySafe = true
replayClassification = NO_EFFECTS
claimOwnerAfter = true
fallbackReceiptMatches = true
effectLedgerReads = 1
taskState = RUNNING
```

The Task remains RUNNING, proving R13 did not bypass R11 acceptance.

## Explicitly not claimed

R13 does not claim:

- universal exactly-once business effects;
- that A2A/MCP cancellation undoes side effects;
- that provider task failure makes replay safe;
- that empty/absent effect data means no effects;
- that credentials belong in Agent Service state;
- that the built-in effect reader owns a ledger.

A production effect authority must implement `EffectLedgerReader` from a real execution/effect journal, transaction system, idempotency registry, or compensation ledger.
