# Ordivon Capital — Current State

Date: 2026-09-23
Truth role: human-readable projection of canonical Capital configs/contracts; when this page conflicts with those authorities, the machine-readable authorities win.

## Source and ownership

Canonical source owner is domains/capital in the Ordivon modular monorepo. The active source-owner domains are markets, trading, portfolio, risk, research, governance, and accounting. Execution is a capability inside Trading, not an eighth source-owner domain.

## Current authority standing

| Boundary | Current standing | Authority |
|---|---|---|
| Protocol identity | ACTIVE_V2_NO_RUNTIME_V1_SHIM / schema v2 | config/protocol_identity_migration_v2.json |
| Execution lane | NON_LIVE | config/execution_policy.json |
| Production external financial write | BLOCK_NOT_GRANTED; externalFinancialWriteAllowed=false | contracts/production-authorization.json |
| Portfolio risk budget | UNSET, owner OWNER_PRINCIPAL | config/portfolio_risk_budget.json |
| Private account data | NOT_ADMITTED; permission currentness pending | config/private_reality_policy.json |
| Local accounting mechanics | PASS_BOUNDED_SQLITE_WAL_ACCOUNTING | config/accounting_substrate.json |

## Current architecture laws

Provider/account/broker/custody reality remains authoritative for external financial facts. Engine-local fills, protocol acknowledgements, workflow success, tests, and local accounting state cannot independently establish an external effect.

The canonical composition remains:

Provider/Data Evidence -> Frozen Decision -> Standard Execution Intent -> Bounded Policy Decision -> Provider Effect -> Authoritative Venue Reality -> Reconciliation -> Accounting

Current Capital has no canonical production/live external-write implementation. Read-only and non-live qualification work remain independently usable.

## Current implementation ownership

Mature external mechanisms own only contracts they have actually won. Current narrow owners include websockets for bounded RFC 6455 client mechanics, PyArrow for typed Parquet materialization, DuckDB for independent Parquet readback, NumPy/SciPy/scikit-learn for their admitted numerical/statistical/estimator mechanics, and SQLite for the bounded single-host accounting primitive. LEAN, NautilusTrader, QuickFIX/n, OPA and TigerBeetle remain candidates/oracles/challengers for contracts they do not currently own.

## Current LEGO projection

planning/current-truth-r1.json is the rebuildable machine-readable current-state projection. planning/functional-lego-map-r1.json maps the seven source-owner domains onto the twelve functional composition roles. config/capital_lego_registry.json indexes registered implementations without becoming an authority source.

Historical operational progression is retained under docs/history/; it must not be used as current standing without re-entry through current authorities.
