# TigerBeetle Capital Substrate R3.2 — Durable Restart / Reconciliation

## Standing

`PASS_DURABLE_RESTART_RECONCILIATION`

## Scope

R3.2 validates durable provider mechanics across ordinary TigerBeetle process restarts
while keeping Market Capital's semantic history authoritative. It does not claim
multi-replica disaster recovery graduation and does not activate external financial
writes.

## Durable account namespace

Market Capital no longer relies on caller-selected raw TigerBeetle account ids for the
capital substrate. Account identity is deterministically derived from:

```text
owner_root
+ resource_identity
+ ledger
+ account_code
+ role
```

The current mechanical roles are:

```text
AVAILABLE
ENCUMBRANCE
```

The role is part of the domain-separated hash input, so the two accounts cannot alias
while the same owner/resource namespace re-enters after restart.

This mapping proves identity continuity only. It does not make a TigerBeetle account
an owner, legal title, settled balance, or deployable-capital object.

## Restart law

For an intact replica data file:

```text
TigerBeetle stop
→ TigerBeetle start SAME DATA FILE
→ exact account/transfer history remains visible
```

No `format` occurs on restart. Re-formatting would create new provider history and is
not a recovery operation.

## Terminal-history reconciliation

R3.2 introduces a read-only reconciliation object between durable Market Capital
reservation history and exact TigerBeetle transfer history.

```text
semantic RESERVED + exact PENDING
→ MATCH

semantic RELEASED + exact VOID
→ MATCH

semantic CONSUMED + exact POST
→ MATCH

terminal semantic history + missing provider resolution
→ PROVIDER_INCOMPLETE_RETAIN

terminal semantic history + contradictory provider resolution
→ CONTRADICTION_RETAIN
```

Both mismatch states have:

```text
provider_repair_allowed = false
```

Thus provider state can never silently reopen:

```text
RELEASED → RESERVED
CONSUMED → RESERVED
```

and a stale provider projection cannot mint a replacement resolution.

## Qualification episode

The bounded R3.2 episode used one temporary TigerBeetle data file and restarted the
same replica twice.

1. Stable AVAILABLE and ENCUMBRANCE account ids were derived from one owner/resource namespace.
2. The AVAILABLE account was mechanically funded with 1000 units.
3. A 700-unit reservation was created as a PENDING transfer.
4. The TigerBeetle process was stopped and restarted using the same data file.
5. The exact pending transfer and 700 pending balances remained present.
6. The reservation was CONSUMED via POST_PENDING_TRANSFER.
7. The process was stopped and restarted again using the same data file.
8. Posted debit/credit balances remained 700/700 and pending balances remained zero.
9. Exact replay of the original reservation returned `EXISTS` and did not reopen pending state.
10. Exact semantic CONSUMED history reconciled to provider history as `MATCH`.
11. An intentionally incomplete provider observation with the semantic history still CONSUMED produced `PROVIDER_INCOMPLETE_RETAIN`, preserved terminal semantics, and prohibited provider repair.

The data file existed across process restarts inside the episode, then was deleted by
the harness. No long-running canonical TigerBeetle service was created.

## Data-loss recovery boundary

TigerBeetle distinguishes ordinary restart from permanent replica-data loss. If a
replica data file is lost, the provider's recovery protocol must be used; creating a
fresh formatted replica is not accepted as recovery. Market Capital therefore records
this rule explicitly and does not infer recovered financial truth from an empty or
reformatted provider state.

R3.2 does not claim that multi-replica `tigerbeetle recover` has been exercised. That
requires a healthy replicated cluster and is a separate Operations qualification, not
a prerequisite for the current bounded Market Capital composition.
