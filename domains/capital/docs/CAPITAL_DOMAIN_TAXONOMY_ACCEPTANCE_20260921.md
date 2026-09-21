# Capital domain taxonomy acceptance — 2026-09-21

Standing: ACCEPTED_SOURCE_TAXONOMY

## Decision

Ordivon Capital is the umbrella. The active Python source-owner taxonomy is:

- Markets — public market/reference facts, microstructure, public streaming and transport qualification.
- Trading — provider/private reality, order intent, FIX projection, execution feasibility and execution reconciliation.
- Portfolio — explicit portfolio counterfactual projection.
- Risk — exposure, factor/dependence statistics, expected shortfall and risk-budget measurement.
- Research — model monitoring, prospective validation, evidence persistence and standards inventory.
- Governance — execution/live-test/risk-budget/pre-trade policy gates.
- Accounting — durable reservation/post/void/idempotency and ledger bindings.

Execution is a capability inside Trading.

The former Python package ordivon_capital.market is retired with no compatibility shim.

## Physical source result

The old overloaded package was decomposed into:

- src/ordivon_capital/markets/
- src/ordivon_capital/trading/
- src/ordivon_capital/portfolio/
- src/ordivon_capital/risk/
- src/ordivon_capital/research/
- src/ordivon_capital/governance/
- existing src/ordivon_capital/accounting/

The public Binance USD-M reference-data normalizer was extracted from the Trading provider module into markets/binance_usdm_reference.py, preventing Markets from depending on Trading.

The active full-effect runner is now scripts/run-capital-trading-fullpath-closure.

## Deterministic acceptance

- Python latest-stable: 3.14.7 — PASS
- Rust latest-stable: 1.98.1 — PASS
- pytest: 282 tests / 52 test files — PASS
- Ruff over src/tests/scripts/tools — PASS
- lock and installed dependency consistency — PASS
- active ordivon_capital.market.* Python imports — zero
- active src/ordivon_capital/market/ path references — zero
- Markets dependency rule — PASS; Markets imports no Trading/Portfolio/Risk/Research/Governance/Accounting module
- R0–R5 bounded non-live closure — PASS
- renamed Trading full-effect path — PASS
- OKX authenticated GET-only provider audit — PASS
- external financial write attempted — false
- real-money effect attempted — false
- worktree stable across effect-path acceptance — true

## Fresh operational evidence

Live public-network qualification remains separate from deterministic source acceptance.

R2 after package decomposition:

- standing: PASS_STREAMING_REPEATED_PUBLIC_SHADOW_WITH_NETWORK_V2_FAILOVER
- elapsed: approximately 7.01 s
- accepted snapshots: 4
- measured rounds: 3/3 qualified
- same persistent connections: true
- transport binding: sha256:f7b0cea37460acc239df6ba11db3dab302a6ebc9449a58101d35c8accf9b5b02
- external financial writes attempted: false

R3 after package decomposition:

- standing: PASS_DUAL_VENUE_PUBLIC_STREAM_RECONNECT_WITH_NETWORK_V2_FAILOVER
- OKX reconnect: approximately 0.662 s, generation 2, 3/3 measured
- Binance reconnect: approximately 5.628 s, generation 2, 3/3 measured
- external financial writes attempted: false

These observations prove the new package paths execute through the existing live Network v2 transport. They are not converted into deterministic source guarantees.

## Compatibility boundary

This migration changes source ownership, not protocol versions.

Existing ordivon.capital.market.* JSON kind/schema identifiers are deliberately not silently renamed because active configs/schemas and frozen historical evidence share those identities. Their v2 replacements are registered in config/protocol_identity_migration_v2.json; frozen v1 evidence is replayed with its historical source revision rather than auto-upgraded by current runtime code.

The old Market-Capital Prometheus family was later retired after live census proved it had no active consumer. Historical Market Capital evidence/fixture names and the standalone repository path used by research provenance remain explicit provenance identities.

## External vocabulary

The taxonomy follows established industry semantics: FIX separates Market Data from Trade and Post-Trade; CFA material distinguishes research/portfolio management, trading, risk management and accounting functions; OpenGamma Strata separates market data from trade/position models and risk calculations.

These references define vocabulary only; they do not imply certification or regulatory compliance.
