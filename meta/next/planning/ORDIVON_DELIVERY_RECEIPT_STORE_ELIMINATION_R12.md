# ORDIVON DELIVERY RECEIPT STORE ELIMINATION R12

Date: 2026-09-19  
Status: NINTH_PRODUCTION_DELETION  
Parent: ORDIVON EFFECT AUTHORIZATION COORDINATOR ELIMINATION R11

## Result

R12 removes the specialized durable `DeliveryReceiptStore` and `delivery_receipts` table while retaining `DeliveryReceipt` only as a read-only projection.

Deleted authority:

- `DeliveryReceiptStore`
- `delivery_receipts`
- `service.delivery_receipts`
- package export `agent_service.DeliveryReceiptStore`
- `delivery_receipts.binding_id -> transport_bindings.id` foreign-key authority

No replacement receipt store, registry, or table was introduced.

## Persistence after deletion

The existing generic `ServiceEventStore` is now the durable source for delivery receipts:

```text
aggregate_type = Delivery
aggregate_id   = binding_id
sequence       = 1
event_type     = DeliveryCommitted
payload        = bindingId / deliveryRequestId / admission / status /
                 providerRequestId / remoteTaskId / remoteContextId
```

`DeliveryReceipt` is reconstructed as a projection from that event.

## Exactly-once event receipt primitive

The generic journal now exposes `append_once(...)`.

It uses the existing unique event coordinate:

```text
(aggregate_type, aggregate_id, sequence)
```

with `sequence = 1` for single-receipt aggregate identities.

This preserves exact one-receipt semantics without adding a delivery-specific persistence surface. If an existing identity is bound to different event type/payload, the operation fails closed.

## Cross-layer migration

Receipt readers in these layers now project from the same event journal:

- delivery replay
- current-effect guard
- remote correlation / audit projection
- remote execution claim delivery
- remote completion verification
- quiescence checks
- replay-safety evaluation
- execution-claim transfer / failover

This preserves remote task/context correlation and pristine-target detection without a second receipt database.

## Destructive migration

A database containing the obsolete `delivery_receipts` table fails closed during R9 schema initialization.

No compatibility shim or silent data migration is retained.

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
cumulative retired top-level types: 11
```

`DeliveryReceipt` remains because it is now a non-authoritative projection type rather than a persistence owner.

Structural audit:

```text
observed top-level Agent Service classes = 160
legacy ceiling                           = 160
unexpected new classes                   = []
retired overlap                          = []
old DeliveryReceiptStore/table authority = none
replacement delivery receipt stores      = none
service.delivery_receipts refs           = none
```

## Validation

Cross-layer targeted regression:

```text
Ran 56 tests
OK
```

CORE_ZERO / public API / deletion gate:

```text
Ran 10 tests
OK
```

Agent Service regression suite:

```text
Ran 213 tests
OK (skipped=5)
```

Full repository regression suite:

```text
Ran 312 tests
OK (skipped=5)
```

## Next deletion pressure

The next authority audit should target other specialized receipt/evidence stores that duplicate the generic journal while distinguishing them from legitimate read-only projection types.
