# TigerBeetle Capital Substrate R3.1 — Reservation / Resolution Composition

## Standing

`PASS_RESERVATION_RESOLUTION_MECHANICAL_COMPOSITION`

## Purpose

R3.1 composes the existing Market Capital reservation/effect semantics onto
TigerBeetle's mature pending-transfer mechanics without transferring semantic
authority to the provider.

## Exact mapping

```text
Market Capital Reservation
        ↓ exact binding
TigerBeetle PENDING transfer

EffectDisposition.RETAIN
        ↓
NO TigerBeetle mutation

EffectDisposition.RELEASE
        ↓
TigerBeetle VOID_PENDING_TRANSFER

EffectDisposition.CONSUME
        ↓
TigerBeetle POST_PENDING_TRANSFER
```

The provider operation is downstream of a Market Capital disposition. TigerBeetle is
not permitted to infer `RETAIN`, `RELEASE`, or `CONSUME` from its own balance or
transfer state.

## Exact identity binding

`reservation_ref + resource_identity` is domain-separated and deterministically
mapped to a non-zero TigerBeetle `u128` pending-transfer id. A resolution uses its own
independent `resolution_ref` plus the exact reservation/resource/disposition binding
to derive a distinct provider transfer id. This prevents caller-selected provider ids
from becoming an alternate authority path while preserving exact replay identity.

## Mechanical scarcity

A source account configured with TigerBeetle `DEBITS_MUST_NOT_EXCEED_CREDITS` can use
pending debits to prevent mechanical over-reservation. This is only a conservation
mechanism:

```text
TigerBeetle EXCEEDS_CREDITS
!= ScarcityAuthority

TigerBeetle available balance
!= CapitalTruth
```

Market Capital still decides what resource the account represents and whether a
reservation is institutionally valid.

## Ephemeral qualification episode

The R3.1 smoke created a temporary single-replica development database and funded a
mechanical source account with 1000 units.

1. A 700-unit reservation became a pending transfer.
2. A second 400-unit reservation failed with `EXCEEDS_CREDITS`.
3. `RETAIN` emitted no provider mutation and the 700-unit pending balance remained.
4. `RELEASE` voided the first pending transfer.
5. A new 600-unit reservation was created and `CONSUME` posted it.
6. Exact replay of the consume resolution returned `EXISTS`, not a second posting.
7. A later RELEASE attempt after consume failed with `PENDING_TRANSFER_ALREADY_POSTED`.
8. The canonical false-green law continued to reject
   `TigerBeetle balance -> deployable capital`.

The temporary database was destroyed after the episode. No external venue, broker,
custodian, account credential, or financial write was touched.

## Remaining R3 work

R3.1 proves the reservation/resolution mechanical composition only. It does not yet
make a persistent TigerBeetle ledger canonical. Before doing so, the next slice must
specify account namespaces and restart/recovery reconciliation so provider state cannot
silently outrank Market Capital's durable semantic history.
