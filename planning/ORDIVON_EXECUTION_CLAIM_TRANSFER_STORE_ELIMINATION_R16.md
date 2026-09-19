# ORDIVON EXECUTION CLAIM TRANSFER STORE ELIMINATION R16

Date: 2026-09-19
Status: THIRTEENTH_PRODUCTION_DELETION
Parent: ORDIVON REMOTE TASK VERIFICATION STORE ELIMINATION R15

## Result

R16 removes the specialized durable `ExecutionClaimTransferStore`, `execution_claim_transfers` table, and `service.claim_transfer_records` surface.

`ExecutionClaimTransferRecord` remains only as a projection over the existing generic immutable event journal.

Deleted authority:

- `ExecutionClaimTransferStore`
- `execution_claim_transfers`
- `service.claim_transfer_records`
- package export `agent_service.ExecutionClaimTransferStore`
- foreign-key authority from the specialized table to Task, source/target TransportBinding, ExecutionQuiescenceProof, and ReplaySafetyDecision

No replacement transfer store, registry, or specialized event-store class was introduced.

## Durable transfer receipt after deletion

```text
aggregate_type = ExecutionClaimTransfer
aggregate_id   = client_transfer_request_id
sequence       = 1
event_type     = ExecutionClaimTransferred
payload        = clientTransferRequestId / taskId /
                 fromBindingId / toBindingId /
                 quiescenceProofId / replaySafetyDecisionId /
                 sequence
```

`REMOTE_EXECUTION_CLAIM_TRANSFERRED` still carries `claimTransferId`, which is now the generic event id.

## Unique safety-token consumption

The retired table previously enforced:

```text
UNIQUE(quiescence_proof_id)
UNIQUE(replay_safety_decision_id)
```

R16 preserves those constraints explicitly with two generic single-use receipt identities:

```text
ExecutionClaimTransferProof/<quiescence_proof_id>
    → ExecutionClaimTransferProofConsumed

ExecutionClaimTransferDecision/<replay_safety_decision_id>
    → ExecutionClaimTransferDecisionConsumed
```

Each is written with `append_once_in_transaction(...)`.

A different transfer attempting to consume the same proof or replay-safety decision therefore conflicts and the whole transaction rolls back.

## Atomicity

The transfer commit remains one SQLite transaction:

```text
CAS TaskExecutionClaim owner source → target
        +
ExecutionClaimTransfer receipt
        +
quiescence-proof consumption receipt
        +
replay-safety-decision consumption receipt
        +
REMOTE_EXECUTION_CLAIM_TRANSFERRED Task event
```

A conflict in any generic receipt aborts the CAS transaction.

## Historical queries

The old store queries are now reconstructed from Task transfer events plus immutable transfer receipts:

- exact replay by client transfer request id;
- proof-consumption lookup;
- source/target Binding history;
- per-Task transfer sequence.

No direct specialized transfer table remains.

## Destructive migration

A database containing the obsolete `execution_claim_transfers` table fails closed during R12 initialization.

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
cumulative retired top-level types: 15
```

`ExecutionClaimTransferRecord` remains because it is now a non-authoritative projection type.

Structural audit:

```text
observed top-level Agent Service classes = 156
legacy ceiling                           = 156
unexpected new classes                   = []
retired overlap                          = []
old ExecutionClaimTransferStore/table    = none
claim_transfer_records façade refs       = none
replacement transfer stores              = none
```

## Validation

Claim-transfer/failover targeted regression:

```text
Ran 20 tests
OK
```

CORE_ZERO / structural deletion gate:

```text
Ran 26 tests
OK
```

Agent Service regression suite:

```text
Ran 225 tests
OK (skipped=5)
```

Full repository regression suite:

```text
Ran 324 tests
OK (skipped=5)
```

## Next deletion pressure

With `execution_claim_transfers` gone, `ReplaySafetyDecisionStore` no longer has a downstream specialized-table foreign key from claim transfers.

R17 should re-audit ReplaySafetyDecisionStore and ExecutionQuiescenceProofStore independently.

Do not delete `ExecutionQuiescenceRequestStore` merely for structural reduction: it is a mutable request state machine and requires a different ownership argument.
