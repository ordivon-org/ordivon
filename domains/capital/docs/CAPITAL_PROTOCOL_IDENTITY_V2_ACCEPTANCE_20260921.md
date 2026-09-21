# Capital protocol identity v2 acceptance — 2026-09-21

Standing: ACCEPTED_V2_NO_RUNTIME_V1_SHIM

## Decision

The current Ordivon Capital protocol surface no longer uses the overloaded ordivon.capital.market.* identity family.

Current protocol documents use schemaVersion 2 and semantic namespaces aligned with the source-owner taxonomy:

- ordivon.capital.markets.*
- ordivon.capital.trading.*
- ordivon.capital.portfolio.*
- ordivon.capital.risk.*
- ordivon.capital.research.*
- ordivon.capital.governance.*
- ordivon.capital.accounting.*
- ordivon.capital.acceptance.* for cross-domain acceptance receipts

The machine-readable mapping authority is config/protocol_identity_migration_v2.json and contains 79 v1-to-v2 identity mappings.

## Compatibility rule

There is no current-runtime v1 compatibility shim and no automatic v1-to-v2 conversion.

Legacy protocol-v1 contract/schema definitions are isolated under:

- contracts/legacy_protocol_v1/
- schema/legacy_protocol_v1/

Frozen evidence and fixtures remain byte-identical. Replaying old protocol-v1 evidence uses the historical source revision or frozen bundle that owned v1.

This deliberately chooses source/history reproducibility over permanent runtime compatibility debt.

## Versioned contracts

Current contract/schema files are:

- contracts/nonlive-effect-admission-v2.json
- contracts/external-write-policy-input-v2.json
- contracts/external-boundary-v2.json
- contracts/portfolio-risk-budget-v2.schema.json
- schema/private-reality-snapshot-v2.schema.json

Current writers and readers require the domain-correct v2 identity.

## Deterministic acceptance

- protocol mappings: 79
- Python: 3.14.7 — PASS
- Rust: 1.98.1 — PASS
- pytest: 288 tests / 53 test files — PASS
- Ruff: PASS
- dependency/lock consistency: PASS
- R0–R5 bounded non-live closure: PASS
- Trading full-effect closure: PASS
- current runtime v1 market identity outside migration metadata: zero
- external financial write attempted: false
- real-money effect attempted: false
- source state stable across deterministic acceptance: true

Historical integrity:

- evidence: 54 files, manifest sha256:c6a4f1293de042a5df2797afc8e49b90b736d704135ea4aad20914d7cb2e82be
- fixtures: 4 files, manifest sha256:69ca14c2747c05f4adbe08f178ebc4351d381283da0ef71ea5507af4819d5159

Both exactly match the pre-migration baseline.

## Live public-network observation

The Network v2 transport configuration remains unchanged:

sha256:6be7389175a4c954f525ad9f43631bbfccbb515c9c2418f414e79f43470295d6

The protocol-v2 binding digest is:

sha256:d88a5ac5b2165dbb9829d0ea0352da1884a3fee6b5846f03f8929e9619f9f14e

The binding digest changed because the binding document itself now has schemaVersion 2 and a markets.* identity; it does not indicate a transport configuration change.

### R2 sample

The first protocol-v2 R2 one-shot sample was PARTIAL_STREAMING_PUBLIC_SHADOW:

- accepted snapshots: 0
- duration: about 25.0 s
- no Python/parser error
- no credential use
- no private account data
- no execution

This sample is retained and is not rerun merely to obtain a green observation.

### R3 diagnosis

The independent per-venue reconnect qualification passed:

- top-level kind: ordivon.capital.markets.crypto-stream-resilience-r3-result
- session kind: ordivon.capital.markets.crypto-stream-resilience-r3-session
- schemaVersion: 2
- OKX: generation 2, 3/3 measured rounds, reconnect about 686 ms
- Binance: generation 2, 3/3 measured rounds, reconnect about 5676.5 ms
- overall: PASS_DUAL_VENUE_PUBLIC_STREAM_RECONNECT_WITH_NETWORK_V2_FAILOVER

Because both venue paths passed under the same v2 build and unchanged Network transport, the R2 result is treated as an operational dual-stream startup sample failure rather than a protocol migration failure.

## Financial-effect boundary

This migration changes document identity only. It grants no new execution authority.

Production authorization remains fail closed and external financial writes remain separately governed.
