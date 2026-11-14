# Harness R21 — CC-Switch pinned Rust-source adoption

- Upstream: SaladDay/cc-switch-cli, tag v5.11.1, commit `7a8605108b5f1e97ca2daa6ab8dea3cb2707ee0d`.
- License: MIT, full upstream license in `docs/CC_SWITCH_CORE_LICENSE_R21.txt`.
- Vendored **verbatim**: `crates/harness-loop/src/cc_sse.rs`, from `src-tauri/src/proxy/sse.rs`.
- Harness-specific narrow adapter: `crates/harness-loop/src/native_provider_sse.rs`; the original strict `decode_chat_completion` remains the proposal gate.
- Rationale: upstream `default-features=false` still compiles unconditional `rusqlite` and imports private AppState/proxy modules; direct full dependency would violate the Harness-only PostgreSQL/no-second-proxy boundary. Do not vend entire upstream repo.
- No CC-Switch SQLite, credential file, AppState, daemon or model proxy is launched. No Provider dispatch authority is created by SSE decoding. Until the real ProviderV4 PG call and actual ToolOwner consumer are proven, this is source-implementation only.
- R20 baseline: `31cabdc47a1663cf0527d71d50f0b1835dbaf601`.

## Future boundary

Do not attach CC upstream circuit breaker to physical retries. Pre-dispatch route selection can be gated by PG currentness; post-dispatch UNKNOWN must not automatically cause another send or failover. Resume the specific existing PG ProviderCall first.

## Actual consumer graph and evidence (R21)

1. CC source proxy/sse.rs -> exact Harness cc_sse.rs (three pure helpers).
2. native_provider_sse.rs uses all three helpers, validates complete Chat Completions SSE and synthesizes a candidate model response only.
3. Existing native_provider_http.rs (non-stream default) offers with_streaming(), applies unchanged R19 strict finish/tool semantics, and preserves UNKNOWN on truncated/malformed/wrong-content-type/missing-DONE streams.
4. Existing NativeAgentLoop and ToolGrant decide whether any Tool proposal is admissible. This patch creates NO new physical permit.
5. The original Python PostgresHarnessStore supplies a real PG18 no-Tool Run/Contract for the opt-in native PG consumer; its Rust DurableJournal is TEST-ONLY.
6. Original real PG18 Provider V4 source objects, native single PG Writer and SELECT-only Rust recovery reader remain unchanged.

Initial R21 gates: cargo fmt, full Cargo workspace all-target tests and strict Clippy PASS (job-01a1db7f-331e-73e1-ab3e-3c08fe83b0b4). Native Harness Loop 70/70 at that point. Opt-in live-PG tests were ignored in this default suite.

Original opt-in genuine PG18 consumer: the existing crates/harness-loop/tests/verify_pg_no_tool_http_r18.py --provider-v4 with two new SSE cases (job-01a1db82-f311-7435-bd7c-b153c947c8a7) returned status=PASS, realPostgres18=true, rustVerifiedContractHttpLoop=true, nativeProviderV4Suite=PASS, originalPythonStoreReadback=true, postgresStopped=true and isolatedClusterRemoved=true. External model calls=0, physical Tool calls=0, test-only Journal=true.

### Source first, installed last

This private source branch is NOT merged or deployed. Installed Gateway v0.10.8 lacks execution.harness; generic execution.linux does not substitute for a qualified Harness Tool Owner. No credential, billed Provider call, issuer-at-spawn or AgentSolved/DomainSuccess proof follows from this SSE/PG test.

### Remaining higher-value frontier

- CC routing, wire transforms, Provider config, Usage and circuit-breaker are UNCONSUMED, not integrated. Do not import upstream AppState or unconditional SQLite.
- Next consumer: actual model request in same original PG Provider V4 Claim/Dispatch/Result/Unknown with current issuer + exact ToolGrant/Fence to native Owner effect and independent Coding verifier.
- CC breaker may block pre-dispatch new requests; it must never automatically replay an ambiguous send or switch Provider after possible dispatch.
