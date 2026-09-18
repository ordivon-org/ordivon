# ORDIVON VERIFICATION RECORD STORE ELIMINATION R14

Date: 2026-09-19
Status: ELEVENTH_PRODUCTION_DELETION
Parent: ORDIVON BOARD PROJECTION RECEIPT STORE ELIMINATION R13

## Result

R14 removes the specialized durable `VerificationRecordStore`, `task_verifications` table, and `service.verifications` façade.

`VerificationRecord` remains only as a projection over the generic immutable event journal.

Deleted authority:

- `VerificationRecordStore`
- `task_verifications`
- `service.verifications`
- all later façade forwarding of `verifications`
- foreign-key authority from `task_verifications.task_id` and `task_verifications.assignment_id`

No replacement verification store, registry, or specialized event-store class was introduced.

## Durable verification receipt after deletion

```text
aggregate_type = Verification
aggregate_id   = assignment_id
sequence       = 1
event_type     = VerificationRecorded
payload        = taskId / assignmentId / runtimeJobId / stage /
                 accepted / reason / evidence
```

`TASK_VERIFIED` still carries `verificationId`, which is now the generic event id.

Task semantic truth remains in the authoritative Task state and Task event stream.

## Transactional safety

R14 extends the generic journal with:

```text
ServiceEventStore.append_once_in_transaction(...)
```

This is the transaction-scoped counterpart of `append_once(...)`.

The completion transaction remains:

```text
VerificationRecorded receipt
        +
TASK_VERIFIED
        +
Task terminal state
        +
Assignment terminal state
        +
TASK_SUCCEEDED / TASK_FAILED
```

all under one SQLite transaction.

Fault injection confirms that if verification receipt persistence fails, Task remains RUNNING, Assignment remains ACTIVE, and no terminal Task event is committed.

## Replay semantics

The immutable receipt identity is assignment-scoped.

A replayed completion reconciliation first queries the exact `Verification/<assignment_id>` receipt. If present, it returns without creating a second verification or terminal event.

## Destructive migration

A database containing the obsolete `task_verifications` table fails closed during R6 initialization.

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
cumulative retired top-level types: 13
```

`VerificationRecord` remains because it is now a non-authoritative projection type.

Structural audit:

```text
observed top-level Agent Service classes = 158
legacy ceiling                           = 158
unexpected new classes                   = []
retired overlap                          = []
old VerificationRecordStore/table        = none
service.verifications façade refs        = none
replacement verification stores          = none
```

## Validation

Evidence/verification targeted regression:

```text
Ran 13 tests
OK
```

CORE_ZERO / structural deletion gate:

```text
Ran 19 tests
OK
```

Agent Service regression suite:

```text
Ran 219 tests
OK (skipped=5)
```

Full repository regression suite:

```text
Ran 318 tests
OK (skipped=5)
```

## Next deletion pressure

Re-run the authority inventory and prioritize specialized stores that have no downstream foreign-key authority and whose durable truth is already represented by the generic journal or another mature owner.

Security credential/identity proof surfaces should not be deleted merely because they are low-reference; their authority boundary must be proven first.
