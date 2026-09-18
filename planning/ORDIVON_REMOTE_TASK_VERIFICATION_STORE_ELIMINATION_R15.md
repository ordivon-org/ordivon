# ORDIVON REMOTE TASK VERIFICATION STORE ELIMINATION R15

Date: 2026-09-19
Status: TWELFTH_PRODUCTION_DELETION
Parent: ORDIVON VERIFICATION RECORD STORE ELIMINATION R14

## Result

R15 removes the specialized durable `RemoteTaskVerificationStore`, `remote_task_verifications` table, and `service.remote_verifications` façade.

`RemoteTaskVerificationRecord` remains only as a projection over the existing generic immutable event journal.

Deleted authority:

- `RemoteTaskVerificationStore`
- `remote_task_verifications`
- `service.remote_verifications`
- package export `agent_service.RemoteTaskVerificationStore`
- later façade forwarding of `remote_verifications`
- foreign-key authority from the specialized table to Task, TransportBinding, and RemoteDeliveryObservation

No replacement remote-verification store, registry, or specialized event-store class was introduced.

## Durable remote verification receipt after deletion

```text
aggregate_type = RemoteVerification
aggregate_id   = task_id
sequence       = 1
event_type     = RemoteVerificationRecorded
payload        = taskId / bindingId / remoteObservationId /
                 stage / accepted / reason / evidence
```

`TASK_VERIFIED_REMOTE` still carries `remoteVerificationId`, which is now the generic event id.

Task semantic truth remains the Task state plus Task event stream.

## Transactional safety

R15 reuses `ServiceEventStore.append_once_in_transaction(...)`.

The remote completion transaction remains:

```text
RemoteVerificationRecorded receipt
        +
TASK_VERIFIED_REMOTE
        +
Task terminal state
        +
TASK_SUCCEEDED / TASK_FAILED
```

under one SQLite transaction.

## Failover safety

Failover previously queried `RemoteTaskVerificationStore.get_by_task(...)` to prevent execution-claim transfer after verification.

It now queries the exact immutable `RemoteVerification/<task_id>` receipt from `ServiceEventStore`.

Therefore:

- a verified Task still cannot transfer its execution claim;
- a replay of the same remote completion reuses the same verification receipt;
- successful terminal remote work still requires verification instead of replay/failover.

## Destructive migration

A database containing the obsolete `remote_task_verifications` table fails closed during R11 initialization.

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
cumulative retired top-level types: 14
```

`RemoteTaskVerificationRecord` remains because it is now a non-authoritative projection type.

Structural audit:

```text
observed top-level Agent Service classes = 157
legacy ceiling                           = 157
unexpected new classes                   = []
retired overlap                          = []
old RemoteTaskVerificationStore/table    = none
remote_verifications façade refs         = none
replacement remote verification stores   = none
```

## Validation

Remote verification + failover targeted regression:

```text
Ran 31 tests
OK
```

CORE_ZERO / structural deletion gate:

```text
Ran 37 tests
OK
```

Agent Service regression suite:

```text
Ran 222 tests
OK (skipped=5)
```

Full repository regression suite:

```text
Ran 321 tests
OK (skipped=5)
```

## Next deletion pressure

Re-run the low-coupling store inventory.

Credential and identity-proof stores remain security-boundary candidates and require a separate authority analysis rather than deletion by reference count alone.

Failover proof/decision stores should be assessed individually for whether they are authoritative safety evidence or specialized persistence that can be represented by the generic journal without weakening replay/quiescence semantics.
