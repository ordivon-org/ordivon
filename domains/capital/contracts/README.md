# Capital contracts

Current protocol contracts use schemaVersion 2 and domain-correct identities.

- external-boundary-v2.json — current component-responsibility map.
- external-write-policy-input-v2.json — current external-effect admission input.
- nonlive-effect-admission-v2.json — current bounded non-live effect admission contract.
- portfolio-risk-budget-v2.schema.json — current Risk portfolio budget schema.

**Durable reservation standing (type/state contract).** A
`DurableReservationHistory` accepts only the three explicit
`ReservationStanding` enum states. Strings, unknown labels and untyped values
must not be interpreted as a terminal `CONSUMED` state: a historical
`RELEASED` value cannot justify a ledger `POST_PENDING_TRANSFER`.
The natural owner contract lives in
`src/ordivon_capital/accounting/durable.py`; negative controls and
valid-transition consumers live in `tests/test_accounting_durable.py`.
The acceptance boundary is `mise run verify` (non-provider owner tests),
not a new state registry or cross-domain authority.

**Trading/Accounting amount boundary.** A complete exact-quantity provider
fill and a positive partial fill are not interchangeable. The current
order-wide reservation mapping permits POST_PENDING_TRANSFER only for a
fully filled, quantity-consistent order with matching trade evidence;
order-only fill claims and partial execution (even if canceled
later) returns PARTIAL_EXECUTION_UNSETTLED / NO_MUTATION. This preserves
the original reservation pending while the authoritative executed quantity,
per-trade identities, fees and final unfilled quantity are independently
reconciled. Do not automatically VOID a partially filled order or invent
per-fill ledger transfers. See trading/execution_reconciliation.py,
its negative tests and the separately qualified Accounting state machine.
NO_MUTATION is an unresolved state, not evidence that no external economic
effect occurred.

**One-time partial terminal settlement.** accounting/substrate.py now allows
an explicit integer posted_amount for POST_PENDING_TRANSFER, with
0 < posted_amount <= reserved. The PostgreSQL ledger subtracts the complete
original reserved amount from both pending sides, posts only posted_amount
on both booked sides and atomically releases reserved - posted_amount.
This matches TigerBeetle's two-phase transfer semantics:
https://docs.tigerbeetle.com/coding/two-phase-transfers/ .
A pending transfer is resolved **once**, not once per exchange fill. An exact
replay returns EXISTS; conflicting amount / second terminal resolution must
not mutate balances. DurableReservationHistory(CONSUMED, posted_amount=...)
carries the terminal amount and independently compares it to the
ledger transfer observation; None preserves historical full-post semantics.
An isolated PostgreSQL test cluster and the Accounting Z3 integer model
verify the bounded local accounting properties.

**PG state-refinement witness.** A durable reservation comparison now requires
both the pending transfer's actual PostgreSQL status and the terminal transfer
status. RESERVED must observe PENDING; RELEASED requires VOIDED; CONSUMED
requires POSTED. A missing status is INCOMPLETE_NO_REPAIR, not a certified
MATCH; contradictory status is CONTRADICTION_NO_REPAIR. Native PG consumers
must pass the status returned by ledger.transfer() into
LedgerTransferObservation rather than inventing a local terminal outcome.

This capability is **not** a Trading authorization or automatic per-fill
settlement. With missing provider-certified final state, denomination,
fee treatment or original reservation identity, retain
PARTIAL_EXECUTION_UNSETTLED / NO_MUTATION rather than invent the spend value.

Legacy protocol-v1 contracts are retained under contracts/legacy_protocol_v1/ for provenance only. Current runtime code does not load them or auto-upgrade v1 documents. Replaying v1 evidence uses the historical source revision or frozen bundle that owned those contracts.
