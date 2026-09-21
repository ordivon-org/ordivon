# Capital protocol identity v2 convergence acceptance — 2026-09-21

Standing: ACCEPTED_SOURCE_ONLY

This acceptance records a versioned protocol-identity migration inside the existing Ordivon Capital owner. It does not grant production financial effect authority.

## Identity-preserving update

- previous qualified source: 808353c223c41ca370ee43911557dd65882561ae
- new qualified source: 2772faf183fe6c1ad94eef96cee777285d537eef
- update merge: d99f623045e396d100146a58005f0b175d074b4f
- previous tree: 061ea629d094dfe0e3e6d319a4f0e8cab7bfb32a
- new source/target tree: 377aedd5198a4390a74fbe0df6aa7f761c9efcae
- frozen source ref: refs/heads/migration/monorepo-qualified-source-r6-protocol-v2-20260921
- frozen bundle: /root/ordivon-migration-backups/2026-09-21-capital-protocol-v2-r6/capital.bundle
- bundle SHA-256: e041903f024e5cfcc52ff10fbcc455b1bb2e86f3895509ada48a4f1123eec98e

## Protocol decision

Current runtime documents use schemaVersion 2 and domain-correct namespaces aligned with Markets, Trading, Portfolio, Risk, Research, Governance, Accounting, plus Acceptance for cross-domain receipts.

The overloaded ordivon.capital.market.* family is no longer a current runtime identity.

There is no runtime v1 compatibility shim and no automatic v1-to-v2 conversion. Legacy protocol-v1 contracts/schemas are isolated under legacy_protocol_v1 directories. Frozen evidence and fixtures remain byte-identical and replay with the historical source revision or frozen bundle that owned v1.

## Qualification

Deterministic:

- 79 registered v1-to-v2 mappings
- Python 3.14.7 PASS
- Rust 1.98.1 PASS
- 288 tests / 53 test files PASS
- Ruff PASS
- dependency and lock consistency PASS
- R0-R5 bounded non-live closure PASS
- Trading full-effect closure PASS
- R0-R5 receipt schemaVersion 2 / acceptance namespace PASS
- Trading fullpath receipt schemaVersion 2 / acceptance namespace PASS
- external financial write attempted false
- real-money effect attempted false

Historical integrity:

- evidence manifest unchanged: sha256:c6a4f1293de042a5df2797afc8e49b90b736d704135ea4aad20914d7cb2e82be
- fixture manifest unchanged: sha256:69ca14c2747c05f4adbe08f178ebc4351d381283da0ef71ea5507af4819d5159

Operational public-network observation:

- Network transport config remained byte-identical: sha256:6be7389175a4c954f525ad9f43631bbfccbb515c9c2418f414e79f43470295d6
- protocol-v2 binding digest: sha256:d88a5ac5b2165dbb9829d0ea0352da1884a3fee6b5846f03f8929e9619f9f14e
- first v2 R2 one-shot sample: PARTIAL_STREAMING_PUBLIC_SHADOW, zero accepted snapshots over about 25 s; retained as a non-blocking operational sample failure
- v2 R3 reconnect diagnosis: PASS_DUAL_VENUE_PUBLIC_STREAM_RECONNECT_WITH_NETWORK_V2_FAILOVER
- OKX reconnect about 686 ms, generation 2, 3/3 measured
- Binance reconnect about 5676.5 ms, generation 2, 3/3 measured

The R2 PARTIAL sample is not erased by rerunning. R3 proves both venue paths operate under the same v2 build and unchanged Network transport.

## Production boundary

Production financial cutover: NOT PERFORMED.

Current external financial writes remain blocked by Capital policy and production authorization.
