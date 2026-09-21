# Capital domain taxonomy convergence acceptance — 2026-09-21

Standing: ACCEPTED_SOURCE_ONLY

This acceptance records a source-owner decomposition inside the existing Ordivon Capital monorepo owner. It does not perform a production financial cutover and does not change external write authorization.

## Identity-preserving update

- previous qualified source: 18ca785b7cb2b6de4e36a7d5f8db40232554c9a8
- new qualified source: 808353c223c41ca370ee43911557dd65882561ae
- update merge: 1e7073a4fb6972162d83f9cf91791981d15b9562
- previous tree: fe63497446fab85d1e63bc0027ed6c470a4a787d
- new source/target tree: 061ea629d094dfe0e3e6d319a4f0e8cab7bfb32a
- frozen source ref: refs/heads/migration/monorepo-qualified-source-r5-domain-taxonomy-20260921
- frozen bundle: /root/ordivon-migration-backups/2026-09-21-capital-domain-taxonomy-r5/capital.bundle
- bundle SHA-256: e0d2ffe3681d8af177711de30a5e17487bc8a478b3a8a3769635442307f98a6f

## Current Capital source-owner taxonomy

- Markets: public market/reference data, microstructure, public streaming, market-transport qualification
- Trading: provider/private reality, orders, FIX projection, execution feasibility, execution reconciliation
- Portfolio: explicit portfolio counterfactual projection
- Risk: exposure and risk measurement
- Research: model/evidence validation and persistence
- Governance: authorization and policy gates
- Accounting: durable ledger mechanics

Execution is a capability under Trading.

The Python package ordivon_capital.market is retired with no compatibility shim.

## Compatibility boundary

This update does not silently rename the existing ordivon.capital.market.* JSON contract kind/schema family. Those identifiers are shared by active configs/schemas and frozen evidence and require a separate versioned contract migration.

The deployed ordivon_market_capital_* metric family, historical Market Capital evidence/fixture names, and the standalone repository path remain explicit compatibility/provenance identities.

## Acceptance evidence

The qualified source was accepted with:

- Python 3.14.7 and Rust 1.98.1 latest-stable gates
- 282 tests / 52 test files PASS
- Ruff PASS
- lock and dependency consistency PASS
- zero active old Python imports/path references
- Markets dependency-direction gate PASS
- R0-R5 bounded non-live closure PASS
- Trading full-effect closure PASS
- OKX authenticated GET-only audit PASS
- external financial write attempted false
- real-money effect attempted false
- source state unchanged by acceptance replay

Fresh live operational evidence from the same qualified source also passed R2 and R3 through Network v2. These live samples remain operational evidence rather than deterministic migration gates.

## Production boundary

Production financial cutover: NOT PERFORMED.

Current external financial writes remain separately blocked by Capital authorization and execution policy.
