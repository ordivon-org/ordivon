# Architecture

## Core rule

Market Capital is one canonical composition, not a federation of Ordivon finance subsystems. Use mature external financial/research infrastructure wherever it already exists; keep only the irreducible Market Capital domain semantics, mappings, decisions, authority rules and reconciliation logic in this repository.

Canonical flow:

`Evidence -> Decision -> ExecutionIntent -> Authority -> External Effect -> Reality -> Reconciliation -> Evidence`

Engine-local fills, protocol acknowledgements, workflow success and passing tests never establish capital truth or production authority by themselves.

## 1. Evidence and research

External mature sources/capabilities provide most evidence mechanics:

- CFA-informed IPS/mandate structure;
- GLEIF legal-entity identity;
- SEC/XBRL issuer disclosure;
- Research Capability for dataframe validation, Parquet, DuckDB and MLflow lineage;
- market-data providers for historical and future market reality.

Market Capital owns the mappings from admitted evidence into its domain decisions, not duplicate research infrastructure.

## 2. Decision

Portfolio construction produces an immutable decision artifact with a causal decision boundary. Decision-time inputs and future execution-time observations are kept distinct. Future market data must not silently rewrite a frozen decision or precommit.

## 3. Execution intent

QuantConnect LEAN owns mature trading-engine mechanics such as buying-power modeling, sizing, calendars and bounded execution simulation. FIX 4.4 / QuickFIX/n supplies standard order-intent semantics where appropriate. Market Capital owns the mapping from an admitted decision into an `ExecutionIntent`.

## 4. Canonical semantic and authority core

The semantic core is now implemented directly in this repository under `src/market_capital/semantic.py`; there is no active `market-capital-v2` dependency.

Canonical retained semantics are:

- observation/same-cut;
- proof binding/currentness;
- Scientific Truth != Economic Truth != Capital Truth;
- registry/parcel/scarcity identity;
- Reservation != Grant;
- EffectAuthority RETAIN/RELEASE/CONSUME;
- revocation/recovery boundaries;
- ProductionAuthorization.

The execution gate is `src/market_capital/authority.py` plus `config/execution_authority.json` and the contracts under `contracts/`.

All current runners must pass this in-repository gate before LEAN starts. Production authorization is `BLOCK_NOT_GRANTED`; external financial writes are not admitted and the live verifier is not implemented.

## 5. External financial infrastructure

Future broker/custodian/venue integration should use mature broker APIs, LEAN brokerage adapters or FIX sessions only where they are actually required. External systems remain authoritative for account, cash, positions, order lifecycle, executions, custody and settlement evidence.

Read-only account reality precedes write authority.

## 6. Reality and reconciliation

Completion is not `send()` or an HTTP/FIX acknowledgement. The operational boundary is:

`intent -> authorized effect -> broker receipt/execution -> authoritative account reality -> reconciliation`.

Expected and authoritative state must reconcile; otherwise the effect remains pending/retained and recovery is required.

PFMI and ISO 20022 remain reference semantics for external post-trade infrastructure. Market Capital does not implement a private clearing or settlement system absent a demonstrated substitution failure.

## Current progression

- Wave A: investment/research loop closed.
- Wave B M1-M4: LEAN mechanics, feasibility, provider-origin historical data and FIX semantics admitted in bounded non-live lanes.
- Wave B M5: causal post-decision gate implemented.
- Wave B M6: pre-decision shadow order precommit frozen.
- Wave B M6.1: semantic/authority core migrated directly into the canonical repository; temporary cross-repo architecture removed.
- Next: M7 must execute the exact M6 frozen quantities against the first admitted post-decision session without future-price rescaling.
- Paper brokerage, real account reality, reconciliation and live authorization remain future admissions.
