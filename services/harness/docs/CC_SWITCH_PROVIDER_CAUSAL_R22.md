# Harness R22 — Provider usage observation and causal physical-UNKNOWN

2026-11-15. Status: **PRIVATE SOURCE CANDIDATE ONLY**, not merged, installed, or publicly published.

## Source, consumers, and why it matters

- Base: Harness R21 local commit `f8e09a85235dcaa0120e4847105f4cd442f03473`.
- Upstream examined: `saladday/cc-switch-cli` v5.11.1, SHA `7a8605108b5f1e97ca2daa6ab8dea3cb2707ee0d` (MIT), including `proxy/usage/parser.rs`, `provider_router.rs`, `http_client.rs`, `model_mapper.rs`, `providers/transform.rs`, `circuit_breaker.rs`.
- Upstream `ProviderRouter` owns `Arc<Database>`; `http_client.rs` uses global OnceCell proxy/client state; copying the whole implementations would add another authority and violate current Harness single PG Writer and external Network ownership. The routing/transport modules were NOT brought into production code.
- The legacy `HttpModelProvider::new_provider_only(endpoint,bearer,...)` accepts an arbitrary endpoint even when the PG Contract proves a model identity; it is NOT production-qualified. R22 adds a new **sourceRefs-bound immutable Provider Transport Snapshot** for no-Tool PG Runs. Its read-only CAS identity binds endpoint/provider/adapter/model and opaque credentialRef without a new database. Security credential materialization and a current PG dispatch permit are still P0; a bound snapshot alone authorizes no model send.

### Implementation and exact typed boundaries

1. `cc_usage.rs` implements a *source-derived, adapted subset* of CC-Switch `TokenUsage::from_openai_response` and cache helper semantics. This is NOT an exact copy of the full upstream parser. It retains `u64` and rejects invalid token fields instead of CC-Switch `as u32` narrowing.
2. `native_provider_sse.rs` retains the single final usage-only SSE frame on completed `[DONE]` streams; missing, premature, duplicated or malformed frames fail conservatively. The existing R19 `finish_reason` and function-Tool gate remain sole decision authority.
3. `native_provider_http.rs` now exposes `last_usage() -> Option<&ProviderUsageObservation>`, which is **ephemeral observation**, not a PG record, settled invoice, billing authorization, or evidence of no charge. Missing usage is `None`, not zero.
4. The HTTP Provider enters an instance-local **unknown_requires_reconciliation** posture before attempting a send; any uncertain outcome blocks all further sends on that instance. A successful validated model decision clears it. An independent PG-authoritative reconciliation must precede authorizing any newly constructed call.
5. The existing PG18 V4 test `pg_provider_head.rs` now commits source-authored CLAIMED+DISPATCHING into a real scratch PG18 Run before one real local HTTP request. The local server accepts that request and closes without a result, yielding physical `Unknown`. A second native PG Lease/Journal commit records UNKNOWN after the loss. SELECT-only Rust Reader and original Python Store verify the same Run; PG exact replay is idempotent, while a changed replay is rejected. No external provider/model or charged call was made. The source-generated `providerRequestDigest` for this test is still a synthetic fixture identity and **is not yet an exact hash binding to physical outbound HTTP bytes**.

6. `harness-pg::read_cas_object_readonly` reuses the existing PostgreSQL CAS Reader and enforces exact digest/kind/immutable bytes. `pg_provider_config::inspect_pg_provider_transport` consumes one exact original RunContract.sourceRefs binding, rejects drift, extra/mismatched fields, embedded secrets, unsafe URL forms and missing CAS. `HttpModelProvider::new_provider_only_pg_bound` takes its endpoint from the PG source (not a caller-supplied URL). The original PG18 Python Store creates this CAS/Contract and the actual Rust no-Tool consumer sends a local HTTP request to the **PG-selected** loopback port. This is source-bound local transport only; bearer is test-only and not Security materialization.

## Evidence

- Rust Harness Loop all-target tests, CC usage/SSE negative tests and strict Clippy: PASS, `job-01a1db9c-9d00-751d-89e9-8855cecda40a` (80 Loop tests at that point).
- Real PG18 + local socket loss and original Python/Rust independent PG V4 consumer: PASS, `job-01a1db9f-904c-762c-bd59-8a4a5fcaf15c`. Scratch PG stopped/deleted, externalProviderCalls=0, physicalToolCalls=0.
- After instance quarantine change: final complete Rust Workspace tests/Clippy + original live PG18 runner: PASS, `job-01a1dba1-ba4b-77e2-8383-860623663c07`; Harness Loop 81/81. No production release, no actual domain acceptance. Default ignored PG tests were separately exercised through the original opt-in PG18 runner.

- Provider transport binding source/PG/local HTTP consumer: PASS, `job-01a1dba9-84e2-7151-93a1-f6abec9294cf`. Original disposable PG18 Store+CAS+Rust Reader+HTTP reached exact PG-selected port; no external model, billing or Tool.
- The immediately prior full Rust Workspace tests/Clippy and PG18 run after sourceRef validation passed: `job-01a1dba7-e6f0-7304-95e3-38ff6194947c`; Rust Loop 82/82. After later endpoint-bound local HTTP test, format/Clippy/real PG18 repeated PASS.

## LEGO

- Thought: DELETE-CUSTOM -> REUSE -> COMPOSE, Event Sourcing, transaction ordering, failure semantics, least duplication, independent falsification, UNKNOWN != FALSE, ModelProposal != Effect, SourceCut.
- Logic: L1 immutable Provider configuration binding (PARTIAL), L2 durable state, L5 Provider/Transport, L8 causal recovery, L9 token usage observation. L6/L7 physical Tool and Security credential authority remain unresolved.
- Ability: existing PG CAS+Lease+Journal Writer/Reader, actual native Linux Runtime, exact CC SSE subset from R21, adapted CC Usage subset, Rust HTTP Provider, original PG18 fixture runner and original Python Store readback.

## Unresolved P0 hard kernel

- ProviderConfig endpoint/model CAS binding is SOURCE-QUALIFIED for no-Tool PG Run, but Security credential materialization, actual live Run/Lease dispatch authority and full Provider/pricing configuration are still OPEN. Do not reuse CC SQLite/AppState/global HTTP client as a second control plane.
- Immutable pre-dispatch request body/endpoint/model digest bound to source ProviderCall V4. Current real HTTP loss test uses a synthetic fixture request digest and must NOT be presented as complete physical source binding.
- One authorized external model: PG V4 Claim -> Dispatch -> actual external API -> Outcome/UNKNOWN with true Usage and late charge reconciliation, no blind retry/failover.
- Current Tool issuer-at-spawn, qualified installed Gateway `execution.harness`, exact OwnerReceipt -> independent Coding DomainSuccess.
- Formal source/SQL/Runtime refinement and unused duplicate removal only after consumer qualification.

### Independent invalid-but-CAS-authentic negative

The original Python PostgreSQL Store now creates a second source-valid Run with a CAS-authentic Provider Transport Snapshot whose `providerId` belongs to a different Provider. Rust validates both RunContracts and both CAS objects; only the matching Run/Provider may construct `ObservedProviderTransport`. The foreign object is rejected at the Provider semantic boundary, despite valid CAS bytes. Original PG18 runner returned PASS (`job-01a1dbac-375e-7419-9e9f-b6e1dae41685`), disposable PostgreSQL stopped/removed. This is a negative for semantic misbinding, not a proof of endpoint safety policy or credential ownership.
