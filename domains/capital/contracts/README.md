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

Legacy protocol-v1 contracts are retained under contracts/legacy_protocol_v1/ for provenance only. Current runtime code does not load them or auto-upgrade v1 documents. Replaying v1 evidence uses the historical source revision or frozen bundle that owned those contracts.
