# ORDIVON EXECUTION QUIESCENCE PROOF STORE ELIMINATION R18

Date: 2026-09-19
Status: FIFTEENTH_PRODUCTION_DELETION
Parent: ORDIVON REPLAY SAFETY DECISION STORE ELIMINATION R17

## Result

R18 removes the specialized durable `ExecutionQuiescenceProofStore`, `execution_quiescence_proofs` table, and `service.quiescence_proof_records` surface.

`ExecutionQuiescenceProofRecord` remains only as a projection over the existing generic immutable event journal.

Crucially, R18 does **not** remove `ExecutionQuiescenceRequestStore` or `execution_quiescence_requests`.

The request is mutable control state:

```text
REQUESTED -> PROVED | NOT_PROVED
```

The proof is immutable evidence. Only the latter is eliminated as a specialized persistence authority.

## Durable proof after deletion

```text
aggregate_type = ExecutionQuiescenceProof
aggregate_id   = client_quiescence_request_id
sequence       = 1
event_type     = ExecutionQuiescenceProofRecorded
payload        = clientQuiescenceRequestId / taskId / bindingId /
                 quiescent / method / providerStatus /
                 remoteTaskId / remoteContextId /
                 basisRemoteObservationId / evidenceRef
```

The generic event id is the durable proof id.

## Historical query semantics

The deleted Store previously supported:

- get by proof id;
- exact replay by client quiescence request id;
- latest proof for a Binding;
- latest positive proof for a Binding.

R18 reconstructs the Binding-history query through the authoritative Task event stream:

```text
Task
 ├─ REMOTE_EXECUTION_QUIESCENCE_PROVED
 └─ REMOTE_EXECUTION_QUIESCENCE_NOT_PROVED
           |
           v
  quiescenceProofId
           |
           v
ExecutionQuiescenceProof generic event
```

No hidden replacement SQL store is introduced.

## Transactional semantics

Proof persistence remains in the same transaction as:

```text
ExecutionQuiescenceProofRecorded
        +
ExecutionQuiescenceRequest state transition
        +
REMOTE_EXECUTION_QUIESCENCE_PROVED
or
REMOTE_EXECUTION_QUIESCENCE_NOT_PROVED
```

Thus an immutable proof cannot become durable without the corresponding request terminal state and Task evidence event.

## Downstream safety

Replay-safety and claim-transfer consumers now resolve proof ids through the generic journal.

The positive-proof checks remain unchanged:

- replay safety requires a positive quiescence proof;
- transfer requires a positive proof for the current source Binding;
- a target Binding with prior positive quiescence history is not pristine;
- failover replay validates the historical proof identity.

R16's proof-consumption receipt remains the one-use transfer guard:

```text
ExecutionClaimTransferProof/<quiescence_proof_id>
    -> ExecutionClaimTransferProofConsumed
```

## Destructive migration

A database containing the obsolete `execution_quiescence_proofs` table fails closed during R12 initialization.

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
R18:         154
cumulative retired top-level types: 17
```

Structural audit:

```text
observed top-level Agent Service classes = 154
legacy ceiling                           = 154
unexpected new classes                   = []
retired overlap                          = []
old ExecutionQuiescenceProofStore/table  = none
quiescence_proof_records façade refs     = none
replacement proof stores                 = none
ExecutionQuiescenceRequestStore          = retained
execution_quiescence_requests            = retained
```

## Validation

Quiescence/failover/provider targeted regression:

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
Ran 231 tests
OK (skipped=5)
```

Full repository regression suite:

```text
Ran 330 tests
OK (skipped=5)
```

## Next deletion pressure

Do not automatically delete `ExecutionQuiescenceRequestStore`.

R19 should re-run the authority inventory and compare mutable request/control stores with immutable observation/evidence stores. Prefer the next immutable duplicated authority before attempting to event-source a live control state machine.
