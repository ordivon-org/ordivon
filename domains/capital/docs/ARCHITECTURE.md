# Architecture

## Core rule

Use mature external methods, standards and components. Ordivon-owned code is limited to mandate content, source-specific semantic mapping, strategy/economic logic, thin authority bindings and reconciliation rules.

The canonical flow is:

`Evidence -> Decision -> ExecutionIntent -> Authority -> External Effect -> Reality -> Reconciliation -> Evidence`

An engine-local fill, protocol acknowledgement, workflow success or passing test is never promoted to capital truth or production authority by itself.

## Layer 1 — Mandate and research

- CFA-informed machine-readable IPS and constraints.
- GLEIF for legal-entity identity.
- SEC Company Facts / XBRL for issuer fundamentals.
- Research Capability for dataframe validation, Parquet, DuckDB and MLflow lineage.
- Output: immutable research evidence and target-portfolio decision artifacts.

Research infrastructure remains external to Market Capital.

## Layer 2 — Decision and trading intent

QuantConnect LEAN owns trading-engine mechanics such as buying-power modeling, order sizing, calendars and bounded execution simulation. FIX 4.4 / QuickFIX/n provides standard order-intent semantics where useful. Market Capital owns only the domain mapping from an admitted target portfolio to an execution intent.

Decision time and execution time are causally separated. A frozen decision/precommit may not be silently resized or rewritten after future market data is observed.

## Layer 3 — Thin authority waist

`ordivon-market-capital-v2` is an external semantic provider, not a second application stack. `config/authority_waist.json` binds Market Capital to one exact provider revision and exact semantic/contract digests.

The retained semantics are deliberately narrow:

- observation/same-cut;
- proof binding and currentness;
- Scientific Truth != Economic Truth != Capital Truth;
- Reservation != Grant;
- EffectAuthority disposition;
- revocation/recovery boundaries;
- ProductionAuthorization.

All current trading runners cross the non-live authority preflight. Production authorization is `BLOCK_NOT_GRANTED`; external financial writes are not admitted.

## Layer 4 — External financial infrastructure

Future broker/custodian/venue integration should use mature broker APIs, LEAN brokerage adapters or FIX sessions only where required. External infrastructure remains authoritative for account, cash, positions, order lifecycle, executions and custody/settlement evidence.

Read-only account reality precedes write authority.

## Layer 5 — Reality and reconciliation

Future completion is not `send()` or HTTP/FIX acknowledgement. The boundary is:

`intent -> authorized effect -> broker receipt/execution -> authoritative account reality -> reconciliation`.

Expected and authoritative state must reconcile, otherwise the effect remains pending/retained and recovery is required.

PFMI and ISO 20022 are reference semantics for external post-trade infrastructure; Market Capital does not implement a private clearing or settlement system unless a concrete substitution failure requires it.

## Current progression

- Wave A: investment/research loop closed.
- Wave B M1-M4: LEAN execution mechanics, feasibility, provider-origin historical data and FIX order semantics admitted in bounded non-live lanes.
- Wave B M5: causal post-decision gate implemented.
- Wave B M6: pre-decision shadow order precommit frozen.
- Wave B M6.1: external semantic authority waist is now bound into the trading runners.
- Next: M7 must execute the exact M6 frozen quantities against the first admitted post-decision session without rescaling from future prices.
- Paper brokerage, real account reality, reconciliation and live authorization remain future admissions.
