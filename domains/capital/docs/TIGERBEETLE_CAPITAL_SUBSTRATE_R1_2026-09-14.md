# TigerBeetle Capital Substrate R1 — 2026-09-14

## Decision

TigerBeetle is composed as the mature provider for double-entry accounting mechanics,
accounting conservation, atomic transfer mechanics, and transfer identity. It is not a
Market Capital truth source.

The installed server binary and official Python client are both pinned to `0.17.9`.
The client lives in an isolated provider environment instead of expanding Market
Capital's own dependency stack.

## Ownership boundary

TigerBeetle may own:

- account and transfer mechanics;
- debit/credit conservation enforced by the provider;
- atomic transfer application;
- provider transfer identity/idempotency mechanics.

Market Capital continues to own:

- `CapitalTruth`, `ClaimRoot` and `Parcel` identity;
- Treasury standing and scarcity semantics;
- Reservation and domain admission semantics;
- `ExternalFinancialWriteAdmission`;
- `EffectAuthority` and reconciliation disposition;
- settlement, legal ownership, encumbrance, withdrawability and deployability claims.

## Composition law

```text
TigerBeetle account/transfer state
!= settled capital
!= legally owned capital
!= deployable capital
!= external financial write admission
!= EffectAuthority
```

This is already backed by the canonical false-green law
`tigerbeetle_balance -> ledger balance is not deployable capital` in `semantic.py`.

## Provider shape

The local adapter mirrors only the stable mechanical fields required to construct
TigerBeetle `Account` and `Transfer` objects. Provider-specific flag values are not
copied into the semantic core; the official client environment resolves those values.
TigerBeetle 0.17.x permits zero-amount transfers, so the adapter deliberately does not
invent a stricter local rule.

## Current standing

`PASS_EPHEMERAL_MECHANICAL_ONLY`

A development-only one-replica TigerBeetle cluster was formatted in a temporary
directory and exercised with the official `0.17.9` Python client. Two accounts were
created, a 500-unit transfer posted, lookup showed exactly 500 posted debits and 500
posted credits, and exact replay of the same transfer identity returned the provider's
`EXISTS` standing rather than applying a second transfer. The temporary database was
removed after the run.

No persistent TigerBeetle database or long-running replica is created by this slice.
External financial writes remain `NOT_ADMITTED`. The smoke proves provider mechanics
only; it does not establish settlement, ownership, deployability or EffectAuthority.
