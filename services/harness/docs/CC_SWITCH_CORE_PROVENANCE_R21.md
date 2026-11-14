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
