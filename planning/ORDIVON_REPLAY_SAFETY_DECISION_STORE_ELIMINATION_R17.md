# ORDIVON REPLAY SAFETY DECISION STORE ELIMINATION R17

Date: 2026-09-19
Status: FOURTEENTH_PRODUCTION_DELETION
Parent: ORDIVON EXECUTION CLAIM TRANSFER STORE ELIMINATION R16

## Result

R17 removes the specialized durable `ReplaySafetyDecisionStore`, `replay_safety_decisions` table, and `service.replay_safety_decisions` surface.

`ReplaySafetyDecision` remains only as a projection over the existing generic immutable event journal.

Deleted authority:

- `ReplaySafetyDecisionStore`
- `replay_safety_decisions`
- `service.replay_safety_decisions`
- package export `agent_service.ReplaySafetyDecisionStore`
- foreign-key authority from the specialized table to Task, source/target TransportBinding, and ExecutionQuiescenceProof

No replacement replay-safety store, registry, or specialized event-store class was introduced.

## Durable replay-safety decision after deletion

```text
aggregate_type = ReplaySafetyDecision
aggregate_id   = client_replay_safety_request_id
sequence       = 1
event_type     = ReplaySafetyDecisionRecorded
payload        = clientReplaySafetyRequestId / taskId /
                 sourceBindingId / targetBindingId /
                 quiescenceProofId / safe /
                 classification / reason / evidenceRef
```

The generic event id is the durable `ReplaySafetyDecision.id`.

This supports both required access modes:

- exact replay by client replay-safety request id;
- transfer/failover validation by immutable decision event id.

## Safety classification rules retained

Deleting the Store does not delete the replay-safety policy.

The recognized positive classifications remain:

```text
NO_EFFECTS
ROLLED_BACK
COMPENSATED
IDEMPOTENT_REPLAY
```

A positive decision must use one of those classifications.

An unsafe decision cannot use one of those positive classifications.

The evidence reference remains mandatory.

## Transactional semantics

Replay-safety persistence remains in the same transaction as:

```text
ReplaySafetyDecisionRecorded
        +
REMOTE_REPLAY_SAFETY_EVALUATED
```

The downstream claim-transfer transaction consumes the immutable decision id through the generic journal.

R16's single-use decision-consumption receipt remains unchanged:

```text
ExecutionClaimTransferDecision/<replay_safety_decision_id>
    → ExecutionClaimTransferDecisionConsumed
```

Therefore retiring the specialized decision table does not weaken one-use authorization of a transfer.

## Destructive migration

A database containing the obsolete `replay_safety_decisions` table fails closed during R12 initialization.

No compatibility shim or silent migration is retained.

## CORE_ZERO ratchet

```text
R3 baseline: 171
R4:          170
R5:          169
R6:          168
R7:          167
R8:          165
R9:          164
R10:         162
R11:         161
R12:         160
R13:         159
R14:         158
R15:         157
R16:         156
R17:         155
cumulative retired top-level types: 16
```

`ReplaySafetyDecision` remains because it is now a non-authoritative projection type.

Structural audit:

```text
observed top-level Agent Service classes = 155
legacy ceiling                           = 155
unexpected new classes                   = []
retired overlap                          = []
old ReplaySafetyDecisionStore/table      = none
replay_safety_decisions façade refs      = none
replacement replay-safety stores         = none
```

## Validation

Replay-safety/failover/provider targeted regression:

```text
Ran 40 tests
OK
```

CORE_ZERO / structural deletion gate:

```text
Ran 46 tests
OK
```

Agent Service regression suite:

```text
Ran 228 tests
OK (skipped=5)
```

Full repository regression suite:

```text
Ran 327 tests
OK (skipped=5)
```

## Next deletion pressure

With both `execution_claim_transfers` and `replay_safety_decisions` removed, `ExecutionQuiescenceProofStore` no longer has a downstream specialized-table foreign key.

R18 should audit whether the immutable quiescence proof can be represented as a generic event projection while preserving:

- exact request replay;
- latest positive proof by Binding;
- source-Binding freeze semantics;
- proof identity consumed by replay-safety and claim transfer.
