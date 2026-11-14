# Harness R24 — NativeAgentLoop → original PG Provider V4 Journal, physical UNKNOWN

2026-11-15. PRIVATE SOURCE / TEST-CONSUMER ONLY. Not merged, pushed, installed or a production Provider.

## What changed (compared to R23)

The preexisting `crates/harness-loop/tests/pg_provider_head.rs` previously manually wrote the PG Claim and Dispatch, physically sent local HTTP, and manually wrote the UNKNOWN Event. That proved individual steps but not that the **actual NativeAgentLoop calls them in the right order**.

R24 replaces this hand sequencing in the same original ignored PG18 test with a narrow **test-only** `SourcePgUnknownJournal: DurableJournal` that consumes existing `harness-pg::lease::acquire_run_lease`, `harness-pg::journal_write::append_events` and *source-authored immutable original Python Provider V4 CAS objects*. There is no second Writer/SQL/Store/Coordinator or synthetic schema.

Real tested causal sequence:

1. Original Python PG18 Store creates source-valid Harness Run, Provider Transport Snapshot and immutable Provider V4 C/D/U CAS source records.
2. Rust source-PG read-only Contract/Transport verification selects exact endpoint/model/credentialRef (test only) and `HttpModelProvider::freeze_next_request_digest` fixes exact body bytes matching original Python V4 `providerRequestDigest`.
3. NativeAgentLoop::run invokes `DurableJournal::prepare_provider`. The adapter obtains the existing native PG Lease and commits source-authored `CLAIMED+DISPATCHING` transaction.
4. Actual local HTTP POST reaches PG-selected loopback server. **Inside the server thread, independent SELECT-only PostgreSQL connection verifies the DISPATCHING Event and Provider Head were durably committed before accepting the request bytes.** Server validates exact body SHA against source V4 CAS and closes without any response.
5. Rust Provider returns UNKNOWN. NativeAgentLoop invokes `record_pause`, which acquires another actual PG Lease and writes the original source-authored `UNKNOWN` Event.
6. NativeAgentLoop returns `RunResult::PausedUnknown` (NOT DomainSuccess); Rust SELECT-only Reader and original Python Store independently read the same Run/causal Provider V4 UNKNOWN head. Changed PG replay is rejected; no Tool may execute.
7. The current PG **Run status remains active**, while Provider V4 head is UNKNOWN. The `record_pause` adapter does not claim to write an official `harness.run-paused` Event. Recovery/continued cognition is unqualified until actual current-owned production Journal adapter and Run status semantics are implemented.

## Evidence

- True original PG18 runner `crates/harness-loop/tests/verify_pg_no_tool_http_r18.py --provider-v4`: PASS `job-01a1dbba-7f8d-778b-9237-fca0bdbf348d` (original Python Store + native Rust PG Writer/Reader + actual HTTP loopback + original Python readback).
- Full Rust Workspace `cargo fmt --check`, all-target tests and Clippy -D warnings + opt-in true PG18: PASS `job-01a1dbba-db99-7144-9d3d-c0a019ca4f4b`; Harness Loop 84/84, scratch PostgreSQL stopped/removed.
- No external Provider model API, billing, Security credential materialization, Runtime physical Tool, trusted Coding Oracle or DomainSuccess. Native Runner exit 0 proves only the test operation, not Agent business success.

## LEGO / consumer meaning

Thought: finite-state feedback control, Event Sourcing, causality, identity/lease fencing, Design by Contract, independent counterexample, UNKNOWN != FALSE, intent != effect != domain outcome, DELETE-CUSTOM→REUSE→COMPOSE.
Logic: L1 Run/Provider binding, L2 Journal state, L4 NativeAgentLoop, L5 frozen Provider bytes, L8 UNKNOWN pause & recovery. L6 Tool/current issuer, L7 Runtime Owner effect and L10 DomainSuccess stay open.
Ability: existing `NativeAgentLoop` `DurableJournal` trait, existing native PG Lease/Journal Writer and source Reader, exact Python Provider V4 source CAS fixtures, PG selected Provider Transport, reqwest local HTTP, original disposable PG18 runner. Only the consumer test adapter was created; no new production service.

## Next hard path

Implement source-owned *production* PG Provider V4 Writer/Journal for both positive and unknown outcomes (not test-only immutable preauthored records); bind live Security materialization/authorization and accurate billing, refuse any implicit retry after ambiguous network; then current Tool issuer + installed Gateway Harness route + Runtime OwnerReceipt + real Coding Domain verifier. Strong SQL/Quint/Runner schedule refinement should falsify actual time-of-check/time-of-use races, not substitute for genuine consumer evidence.
