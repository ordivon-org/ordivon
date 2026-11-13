# Rust-native Harness Loop

This crate implements Rust-native decision mechanics and a bounded in-process
Agent Loop, with the following independently testable responsibilities:

- `native_loop.rs`: Provider turn state, ordered Tool batch preflight, bounded
  turns/Tool calls, Journal admission before effects, response-UNKNOWN stop,
  owner receipt observation, privacy-bounded Provider-visible Tool results,
  and bounded CompletionProposal. `new_provider_only` consumes a real PG-verified
  zero-Tool Run identity, never a synthetic empty Tool Grant.
- `native_provider_http.rs`: direct mature `reqwest` HTTPS model transport,
  fixed endpoint, model-visible granted Tool schemas, strict bounded JSON,
  no automatic uncertain retry, and a local TCP HTTP test harness. `reqwest`
  honors configured HTTPS proxy routes; local loopback tests bypass proxy.
- `tool_selection.rs`, `progress.rs`, `evidence.rs`: pure turn/evidence laws.
- `tool_arguments.rs`: reuse mature offline JSON Schema Draft 2020-12
  for *whole-batch* argument validation before admitting ANY Tool effect.
- `tool_call.rs`, `tool_surface.rs`, `provider_head.rs`,
  `runtime_delivery.rs`: typed validation and narrow owner observations.

The native `DurableJournal` and `EffectReceiver` traits are *authority
boundaries*, not a proof that a given implementation is durable or authorized.
Current Loop tests use explicit test doubles. The HTTP loop E2E runs real local
HTTP requests but not an installed external Provider, production PG admission,
or real Runtime Tool effect. The PG18 verified no-Tool consumer test proves
real source Contract + HTTP + Rust decision flow, but its Journal is a test
double and does NOT prove durable Provider dispatch or production readiness.
A Tool result reaches the next model turn only after the Journal returns a
bounded, digest-verified privacy release; absent release, the model receives
receipt metadata only, not invented domain knowledge. Both backend-specific implementations remain P0
before this Rust Loop can replace production Python.

`harness-pg` owns the Run PG authority and `harness-core` the canonical
representation. Python oracle fixtures are historical tests, never a runtime
compatibility bridge or writer fallback.

Verification:
```bash
cargo test --locked --offline --workspace --all-targets
cargo clippy --locked --offline --workspace --all-targets -- -D warnings
cargo fmt --all -- --check
```

No production dual writer, Python bridge or new global scheduler is introduced.
