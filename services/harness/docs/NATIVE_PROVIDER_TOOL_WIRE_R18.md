# R18 native Rust Provider Tool-wire consumer qualification (isolated source)

Status: PRIVATE SOURCE-CANDIDATE, not merged into main or installed Runtime/Gateway.
Source parent: 8a77e265e97b9068e1404fa9ecdbbb20183214c3 (existing Rust NativeAgentLoop branch).
This document does not grant Tool authority, credentials, or domain result admission.

## Exact user-facing consumer

The normal Agent workflow takes a model decision, distinguishes a suggestion
from an executable Tool call, checks one caller-bound Tool surface, records an
authenticated Tool Intent/Fence, delegates to the real Owner, and only after
an independent domain verifier may report success. Incomplete or malformed
Provider JSON is not Tool authority.

The Q1 fault reproduced in R18: the *existing* Rust OpenAI-style Provider
decoder accepted a tool_calls element whose type was not "function" solely
because it contained the usual id/function fields, permitting it to become a
ModelDecision::CallTools. The existing Tool preflight and Journal still stood
between it and effects, so this is NOT evidence of production authorization
bypass. R18 now requires the exact Provider type field before constructing any
Tool Call document; any unsupported/missing type returns ProviderResult::Unknown.

## Live consumer graph — distinct evidence and authority

HTTP response body (model-origin, untrusted)
→ native_provider_http.rs HttpModelProvider::query (type must be function)
→ native_loop.rs ModelDecision::CallTools / ProviderResult::Unknown
→ tool_call.rs inspect_model_tool_call
→ tool_surface.rs domain-granted Tool selection
→ tool_arguments.rs mature JSON Schema 2020-12 argument validation
→ native_loop.rs DurableJournal::admit_tool (natural PG/lease/Fence required,
  trait/test double is NOT an authorization proof)
→ EffectReceiver::execute (Runtime/Gateway Owner ONLY with independent current grant)
→ DurableJournal::record_effect (OwnerReceipt observed or UNKNOWN)
→ next Provider turn or PausedUnknown; CompletionProposal not DomainSuccess.

No new generic adapter, schema registry, PG writer or second Agent Loop was
implemented. Trust is maintained on the original natural module boundaries.

## Physical source evidence, 2026-11-14

1. RED: unknown Provider tool type mapped to Tool decision:
   job-01a1da90-e69d-733a-8a6e-3512bd61f78e, focused real cargo
   unit test exits 101 with 1/1 failure. This intentionally falsifies old code.
2. GREEN: exact same unit test passes after minimal check:
   job-01a1da92-5999-768d-8809-50413722c2de, 1/1 pass.
3. GREEN: existing native_http_loop_e2e.rs local HTTP server returns bad Tool
   type; unchanged NativeAgentLoop receives Unknown and pauses; test-only
   EffectReceiver receives ZERO calls; Journal has prepare/pause only:
   job-01a1da94-7ac9-7675-af48-ce8e058de57f, 1/1 pass.
   This is a *real loopback HTTP* integration test, not a real external model.
4. Original full Rust Harness workspace fmt, cargo test --all-targets, and
   strict Clippy all pass:
   job-01a1da95-8c7c-7389-a3b4-62a5eba0399f. Native loop unit 56 PASS,
   local HTTP integration 2 PASS; opt-in real-PG test targets remain ignored
   in the regular cargo test, not silently counted as successes.
5. The *existing ignored* native_pg_no_tool_http.rs test is now explicitly
   driven with an isolated new PostgreSQL 18 cluster and original Python
   PostgresHarnessStore, no alternative PG store.
   tests/verify_pg_no_tool_http_r18.py provisions a disposable cluster on a
   local Unix socket, creates exact no-Tool HarnessRunContract through the
   original Python owner, then invokes existing Rust
   native_pg_verifiable_provider_only_http_loop. Genuine PG source readback,
   accepted no-Tool answer and rejected model-fabricated exec Tool both pass:
   job-01a1da9a-b21a-727e-bfca-32b49b45e52f, 1/1. Private PG stopped,
   temporary data deleted. Provider HTTP is still loopback; Journal is a
   test double, NOT an external provider billing receipt or effectful Owner.

## What remains genuinely important + urgent

- Same natural single PG Harness Run: actual authorized/free external
  model → ModelDecision → live PG ToolGrant/Fence and spawn-time currentness
  → native Gateway and Runtime effect → signed/source-bound owner receipt
  → independently verified Coding domain result, with real token/cost/latency.
- Installed Gateway 0.10.8 lacks execution.harness, installed Runtime has no
  model credential materialization bindings in ChatGPT's connected surface.
  Do not pretend a local fake Provider satisfies this production consumer.
- Recent Runtime issue #2217 demonstrated source issuer-on revocation between
  dispatch and spawn could still produce physical effect; exact installed
  release/authority must be checked separately. The R18 code cannot repair
  Runtime's service lifecycle, and must not claim authorization from foreign
  reference metadata or a local Rust build.
- DurableJournal provider/Tool admission is currently a trait here; actual
  original PG Writer/Lease/Fence binding is an implementation obligation.
- Existing formal models are abstract/bounded. Real SQL/Runner/AgentLoop
  implementation refinement has not been discharged, so deterministic and
  physical tests cannot yet be deleted in favor of abstract model tests.

## LEGO ledger

Thought: Design by Contract, fail-closed Protocol parsing, real RED→GREEN TDD,
independent consumer falsification, evidence before success, DELETE-CUSTOM
→ REUSE(existing NativeAgentLoop/reqwest/serde/original PG writer)
→ COMPOSE rather than invent a new Owner.

Logic: L1 caller Run identity, L5 Provider wire negotiation, L7 model proposal,
L8/L9 granted tool and parameters, L10 physical Owner effect,
L11 observation/UNKNOWN, L14 independent DomainSuccess (still unsupported).

Ability:
- MINIMAL PATCH native_provider_http.rs supported Tool kind check
- NEW unit and existing native HTTP integration negative tests
- REUSED native_loop, tool_call, tool_surface, tool_arguments
- NEW opt-in disposable PG18 runner for already existing ignored
  native_pg_no_tool_http test, with original Python PG writer
- NO production installer, new PG schema owner, general validator, agent
  scheduler, paid model API call, or live Business DomainSuccess.

## Reproduction

Work in exact private candidate source layout, not production; no public push.

    cd services/harness
    cargo fmt --all -- --check
    cargo test --offline --locked --workspace --all-targets
    cargo clippy --offline --locked --workspace --all-targets -- -D warnings
    python3 -B crates/harness-loop/tests/verify_pg_no_tool_http_r18.py

Only the last command runs the ignored PG18 test against a temporary real
Postgres cluster; it is not included automatically in cargo test. It cleans
the test cluster even if the consumer assertion fails.
