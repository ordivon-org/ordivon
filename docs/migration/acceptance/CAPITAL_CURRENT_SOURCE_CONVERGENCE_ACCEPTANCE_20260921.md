# Capital current-source convergence acceptance — 2026-09-21

Standing: **ACCEPTED_SOURCE_ONLY**

Scope: current-source convergence of domains/capital onto the qualified Capital source lineage. This acceptance establishes the monorepo owner path as the current source-of-truth. It does not authorize production financial writes, live execution, credential expansion, provider-side effects, or deletion of recovery/provenance material.

## Source and history chain

Legacy first-generation import and current-source convergence were handled without pretending the old rewritten import was the original source identity.

- Legacy imported source revision: 918fd86a3ebe69bb0e05835d7e4c656731da0833
- Common pre-divergence base: 8590c3eeb7d2712a1f796a70c839a7d3cbda0ff8
- Legacy source-identity attachment: 7bf655654eb257a4489f3b01de0c52db3eb527d3
- First qualified source snapshot: 3344ed44d8dcf9392be5e876d443b659ee732660
- Identity-preserving supersession: c034974bf1aa517f17a55c03cc7f90fe2b38545c
- Supersession/identity receipt commit: 26661a4b0dfcf5d035a26eadcd659832e0989cbd
- Qualified source R2: c8999bd66f5470f6a46fad2fd4df4b0387f47259
- First identity-preserving update: 2a4df78a192f7d381540711ad90c5e787dea0a34
- First update-receipt commit: 95ba896e165759ab5cd2b677126fdecadaf46783
- Qualified source R3: abfa307d85a62debad7534b3726366d38d3b0bac
- R3 identity-preserving update: d0fc4c6b4fd4202504048177c4ec6cf80b1e3a12
- Final qualified source R4: 18ca785b7cb2b6de4e36a7d5f8db40232554c9a8
- Final source tree: fe63497446fab85d1e63bc0027ed6c470a4a787d
- Accepted domains/capital tree: fe63497446fab85d1e63bc0027ed6c470a4a787d
- Final source ref: refs/heads/migration/monorepo-qualified-source-r4-20260921
- Final frozen bundle: /root/ordivon-migration-backups/2026-09-21-capital-qualified-r4/capital.bundle
- Final bundle SHA-256: b9e6652ba1db19683b9c7219963b5b3a813d64a3d26d06b656d6e36279a641f7

All source updates after the supersession are linear descendants of their immediately previous qualified source revisions. Historical receipts remain append-only.

## Network owner convergence

The Capital source binds to the hardened Network v2 Finance transport authority.

- Network source commit carrying dual provider-DNS response race: 5044e714aa7886d612f9b664f1458bbc4b66d798
- Finance egress digest: sha256:6be7389175a4c954f525ad9f43631bbfccbb515c9c2418f414e79f43470295d6
- Capital transport binding digest: sha256:f7b0cea37460acc239df6ba11db3dab302a6ebc9449a58101d35c8accf9b5b02
- Provider-endpoint descriptor digest: sha256:c404749643723f4ec47143f9084c9feb20cb37ab071fcd2c2be0c5348bb16e74
- provider endpoint content disclosure: false
- DNS-1 isolated failure replay: PASS
- DNS-2 isolated failure replay: PASS
- monorepo Finance egress bytes == live /etc/network-v2/finance/egress.json: PASS at integration qualification

## Deterministic source acceptance

Executed from the canonical monorepo owner path domains/capital.

- Python latest-stable gate: 3.14.7 — PASS
- Rust latest-stable gate: 1.98.1 — PASS
- pytest: **276 collected tests / 51 test files — PASS**
- Ruff: PASS
- uv lock --check: PASS
- installed dependency consistency: PASS
- JSON parse/shape sweep: **70 files — PASS**
- R0–R5 bounded non-live composition closure: PASS_BOUNDED_NONLIVE_R0_R5_COMPOSITION_CLOSURE
- R0–R5 external financial write attempted: false
- owner-census no-unowned-active-Python-module invariant: PASS
- source/tree identity: PASS
- Git whitespace/diff gate: PASS
- acceptance replay leaves tracked source state unchanged: PASS

The accepted source includes the narrow NetworkV2ProxyClientConnection seam for python-websockets' HTTP-proxy/TLS pre-connection_made lifecycle hazard, uses the documented create_connection extension point, and leaves normal WebSocket protocol mechanics upstream-owned.

R2 now delegates opening-handshake retry/backoff to the external websockets async-iterator API before measurement starts. Once a venue connection is established, later stream loss is fatal for that R2 run; the samePersistentConnections=true claim therefore remains tied to one established connection per venue.

## Live operational evidence — separate from deterministic source acceptance

Public live transport samples are retained exactly as observed because provider/venue state is external to source bytes.

Positive R2 sample after opening-retry correction:

- standing: PASS_STREAMING_REPEATED_PUBLIC_SHADOW_WITH_NETWORK_V2_FAILOVER
- session duration: approximately 7.404 s
- accepted snapshots: 4
- measured snapshots: 3/3 qualified
- same persistent connections: true
- external financial writes attempted: false

Positive post-lifecycle-guard R3 sample:

- standing: PASS_DUAL_VENUE_PUBLIC_STREAM_RECONNECT_WITH_NETWORK_V2_FAILOVER
- OKX reconnect: approximately 0.674 s, generation 1 -> 2, 3/3 measured
- Binance reconnect: approximately 5.669 s, generation 1 -> 2, 3/3 measured
- callback AttributeError count: 0

Later R3 transport-tail sample, retained as PARTIAL rather than rewritten:

- overall: PARTIAL_DUAL_VENUE_PUBLIC_STREAM_RECONNECT
- OKX: PASS after approximately 20.726 s, generation 1 -> 4, 3/3 measured
- Binance: PARTIAL after approximately 20.058 s, generation 1 -> 4, 2/3 measured
- callback AttributeError count: 0
- R3 global deadline remained 35 s

The live PASS/PARTIAL distinction is operational evidence, not a deterministic source-migration gate. Deadlines were not relaxed.

## Effect boundary

The accepted line retains NON_LIVE / fail-closed financial-effect governance.

Previously requalified from the same implementation line:

- OKX authenticated provider audit: PASS_OKX_LIVE_PROVIDER_BOUND_CURRENT_NO_EFFECT_ADMISSION
- provider capability audit only: true
- private reality admission granted: false
- full local effect path: PASS
- external financial write attempted: false
- real-money effect attempted: false

No migration action in this acceptance authorizes production financial writes.

## Source-of-truth boundary

Current source-of-truth:

/root/projects/ordivon/domains/capital

The standalone repository /root/projects/ordivon-market-capital-next is retained only as provenance/recovery source carrier, including the frozen qualified refs and bundles. Its legacy main is not the current Capital source authority and must not be used as the default development source after this acceptance.

Deletion or archival of the standalone repository is a separate retirement action.

## Production boundary

**Production cutover: NOT PERFORMED.**

This acceptance covers source/history convergence and owner-path correctness only. Live execution, credentials, provider effects, capital deployment, and retirement of recovery authorities require separate explicit gates.
