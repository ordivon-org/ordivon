# ORDIVON BOARD PROJECTION RECEIPT STORE ELIMINATION R13

Date: 2026-09-19  
Status: TENTH_PRODUCTION_DELETION  
Parent: ORDIVON DELIVERY RECEIPT STORE ELIMINATION R12

## Result

R13 removes the specialized durable `BoardProjectionReceiptStore` and `board_projection_receipts` table while retaining `BoardProjectionReceipt` only as a read-only projection.

Deleted authority:

- `BoardProjectionReceiptStore`
- `board_projection_receipts`
- `service.board_receipts`
- all later façade forwarding of `board_receipts`
- foreign-key authority from the specialized table to `service_events` and `service_goals`

No replacement board receipt store, registry, or event-store class was introduced.

## Persistence after deletion

Board projection receipts now use the existing generic `ServiceEventStore.append_once(...)` primitive:

```text
aggregate_type = BoardProjection
aggregate_id   = source Goal service_event_id
sequence       = 1
event_type     = BoardProjectionCommitted
payload        = sourceEventId / goalId / clientMessageId / providerSequence
```

`BoardProjectionReceipt` is reconstructed as a projection from that event.

The Board remains projection-only. Goal/Task semantic truth remains owned by Agent Service.

## Response-loss semantics

The Board client message identity remains deterministic from the source Goal event id.

If the external Board commits and the response is lost before the local receipt event is appended:

1. no local BoardProjection receipt exists yet;
2. retry uses the same deterministic client message id;
3. provider-side idempotency returns/accepts the same message identity;
4. the generic immutable receipt is then appended exactly once.

This preserves the prior behavior without a specialized receipt table.

## Destructive migration

A database containing the obsolete `board_projection_receipts` table fails closed during R7 initialization.

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
cumulative retired top-level types: 12
```

`BoardProjectionReceipt` remains because it is a non-authoritative projection type.

Structural audit:

```text
observed top-level Agent Service classes = 159
legacy ceiling                           = 159
unexpected new classes                   = []
retired overlap                          = []
old BoardProjectionReceiptStore/table    = none
board_receipts façade refs               = none
replacement Board receipt stores         = none
```

## Validation

Board/Goal targeted regression:

```text
Ran 17 tests
OK
```

CORE_ZERO / deletion structural gate:

```text
Ran 23 tests
OK
```

Agent Service regression suite:

```text
Ran 216 tests
OK (skipped=5)
```

Full repository regression suite:

```text
Ran 315 tests
OK (skipped=5)
```

## Next deletion pressure

The next low-coupling candidate is `VerificationRecordStore`.

It must first be classified: if it owns durable semantic verification truth, it should remain or be mapped to a mature provenance/evidence owner; if it is merely a specialized projection/receipt table over already-authoritative evidence and task events, it can be removed.
