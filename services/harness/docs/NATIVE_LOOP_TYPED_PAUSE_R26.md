# Harness R26 — Cause-specific pause transitions, not a generic UNKNOWN

2026-11-15. LOCAL private source candidate. R25 parent `39922e2a17731fd7c5ce0dec9fce298b262691de`.

## Hardest semantic issue discovered

Original `NativeAgentLoop::DurableJournal::record_pause(turn)` was invoked for three non-equivalent causes:

1. `ProviderResult::Unknown`: external model request may have reached provider; can persist only a Provider V4 UNKNOWN and must not blind resend.
2. `ModelDecision::RequestInput`: a valid model proposal asks the caller for more input; is NOT a failed/unknown Provider request.
3. `EffectResult::Unknown`: a physical Tool receiver may have executed a Tool; is NOT a Provider request status.

Treating these as one generic untyped `record_pause` risks a production Journal fabricating a Provider failure receipt for mere user input or a Tool outcome. This is a hard consumer/authority distinction, not an extra hash or metadata convenience.

## Implemented precise consumer change

- `PauseCause` is a typed enum `ProviderUnknown | NeedsInput | ToolUnknown`; `DurableJournal::record_pause(turn, cause)` is now explicit.
- Original `NativeAgentLoop` passes the correct cause from its three existing control paths; Run results retain `PausedUnknown` and `NeedsInput` distinction.
- All actual Rust consumer implementations in `native_loop.rs`, `native_pg_no_tool_http.rs`, `native_http_loop_e2e.rs`, and `pg_provider_head.rs` were migrated to the exact new trait.
- Existing Rust Loop source tests assert each of the three distinct causes, rather than only a common `paused` marker.
- The R25 true scratch PG18 `SourcePgUnknownJournal` explicitly rejects ToolUnknown or NeedsInput before any Provider V4 CAS or Journal write; only ProviderUnknown can author failure and PG V4 UNKNOWN.
- Existing R25 stale source Run TOCTOU falsifier remains: prior Contract snapshot cannot authorize another actual Provider send after the same PG Run revision advanced to Provider V4 UNKNOWN.

## Verified evidence

- Rust Cargo all-target workspace tests including 86/86 Loop, strict Clippy -D warnings, and original disposable PG18 with native V4/Failure CAS authorship/real HTTP loss/source Python+readonly Rust consumers: PASS Job `job-01a1dbda-aa1c-717e-8e2a-ad8cdb855387`.
- PG18 scratch stopped/removed; zero authenticated external Model calls and zero physical Tool calls.
- No installed production Gateway, Security credential materialization or production dispatch port modified.

## LEGO and remaining work

Thought: Design by Contract, Algebraic Data Types, causal event separation, independent falsification, UNKNOWN != FALSE; reuse PG original owner and Rust trait, no new Writer or database.
Logic: L4 NativeAgentLoop state representation; L8 fault and pause classification; L2 PG Journal causal admission; L6 Tool unknown belongs to Tool Owner, not Provider; L5 Provider response uncertainty.
Ability: exact typed Rust `PauseCause`, consumer trait update, existing native PG test double, source Python Oracle, live PG18 runner.

Open P0: full production Provider Journal positive `COMPLETED` with source AgentTurnResult/Usage, real authorized **free** API and security credential materialization, independent query/completion readback; current issuer at actual Tool spawn, Gateway installed `execution.harness`, Runtime OwnerReceipt and independently verified Coding domain success. Explicit user consent to local API use does not override tool security rejection; direct external keyed HTTP attempt was blocked and was not retried.
