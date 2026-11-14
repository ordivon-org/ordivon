# Harness R19 — native Provider completion boundary, consumer-qualified

Status: **isolated Rust source candidate only**. Not installed, not an externally
billed Provider qualification, not a physical Runtime Tool authorization, and
not DomainSuccess. Parent SourceCut:
`62791866ac4266f0ff773f360d3ea253e87d45af` (R18).
Date: 2026-11-14 (Asia/Shanghai).

## Real business question and standard

Coding and Research Agents routinely ask a model to finish a response or
choose a Tool. They may hit output truncation, content filtering, a backend
protocol discrepancy, or an ambiguous/partial response even when HTTP=200 and
the body *looks* plausible. Sending that partial response to Tool admission,
or reporting it as a completed repair, is the wrong business outcome.

The supported wire family is non-streaming OpenAI-compatible Chat Completions.
Official source: https://developers.openai.com/api/reference/resources/chat/subresources/completions/methods/create

Per that contract a successful **natural answer** has `finish_reason=stop`;
a completed **Tool proposal** has `finish_reason=tool_calls`; `length`,
`content_filter` and legacy `function_call` are different outcomes.
For this explicitly function-Tool-only Rust adapter, no undocumented
or legacy fallback may become executable authority.

## Actual source diagnosis

Existing source `crates/harness-loop/src/native_provider_http.rs` read only
`choices[0].message`. It projected any well-shaped, nonempty message text as
`ModelDecision::ProposeCompletion`, and any superficially valid function Tool
array as `ModelDecision::CallTools`, regardless of whether the Provider
declared its output finished, truncated, filtered or unknown.

R19 adds **no new Router, Provider Registry, Tool admission or PG writer**.
It checks the standard source-owned `choices[0].finish_reason` on the same
original JSON response:

| Model message | Required `finish_reason` | Harness Result |
| --- | --- | --- |
| nonempty text, no nonempty Tool calls | `stop` | `ProposeCompletion` (never DomainSuccess) |
| nonempty function-Tool calls, no conflicting text | `tool_calls` | `CallTools`, still requiring native Contract+Journal+Owner admission |
| truncated text or Tool proposal | `length` | `Unknown`, then native Loop `PausedUnknown` |
| filtered text or Tool proposal | `content_filter` | `Unknown`, then `PausedUnknown` |
| missing, null, deprecated or mismatched finish reason | none accepted | `Unknown`, then `PausedUnknown` |
| malformed Tool variant/parameters | no authority | `Unknown`/preflight refusal as appropriate |

This is **transport semantic correctness, not entitlement or effect authority**.
It deliberately refuses nonstandard Provider responses until an actual
Provider-specific contract is independently qualified. The recognized
`function_call` legacy finish code is not an automatic adaptation.

## Consumer and effect authority map

```
L1 Caller HarnessRunContract / source + model identity
  -> L5 reqwest HTTP Provider (untrusted response; source finish_reason)
  -> L7 NativeAgentLoop::ModelDecision (Unknown is not false/success)
  -> L8 ToolCall decoder / local JSON Schema 2020-12
  -> L9 DurableJournal::admit_tool (PG source authority; test port NOT proof)
  -> L10 natural Gateway/Runtime Owner admission + physical effect
  -> L11 owner receipt / journal release / UNKNOWN reconciliation
  -> L14 independent caller/domain semantic verifier
```

For a `length` or `content_filter` wire, this R19 change stops at L5→L7:
there is **no Tool preflight, no ToolAdmission, no Tool effect, no CompletionProposal**.
An external Provider may still have been billed, so `Unknown` **does not**
authorize a blind new Provider request.

## Evidence ledger (scoped and executable)

* Genuine RED in original branch before the fix:
  * `job-01a1dab3-0dfc-7528-9ec4-89f490f304b8` — two `length` cases
    accepted, 2/2 expected negative tests failed (exit 101).
  * `job-01a1dab3-4240-718f-9a0c-17b97a84be15` — missing finish reason
    accepted, expected negative test failed (exit 101).
* Fixed Provider local HTTP unit tests:
  * `job-01a1dab4-b5eb-72d3-bd32-c5a01bb4ea25` — 11/11 pass,
    including R18 non-function Tool type guard and R19 RED cases.
* Same existing Rust NativeAgentLoop with **real loopback HTTP**, not a
  synthetic `Provider` trait stub:
  * `job-01a1dab6-8155-7003-913e-eaf566fb0293` — 2/2 integration
    tests pass. One suite runs 5 bad-wire situations; each yields
    `PausedUnknown`, zero receiver invocations, no completion admission.
    The Owner/Journal in this test is explicitly **test-only**.
* **Actual PostgreSQL 18** natural source consumer:
  * Reused R18 `crates/harness-loop/tests/verify_pg_no_tool_http_r18.py`
    without inventing another PG Store or runner. The original Python
    `PostgresHarnessStore` creates an exact no-Tool Run; the Rust
    `inspect_pg_no_tool_run` checks Contract/Model/Grant in the same isolated
    PG; the original ignored `native_pg_no_tool_http.rs` now exercises five
    real loopback-HTTP outcomes, including truncation and absence of finish
    reason. `job-01a1dab6-bd9a-73aa-b910-7bda6a7259f7`: 1/1 pass, PG
    stopped and removed; `externalProviderCalls=0`, `physicalToolCalls=0`,
    test-only Journal.
* Full existing Rust Harness workspace:
  * `job-01a1dab8-d3db-7093-ab94-122d511db31d`: fmt check,
    `cargo test --offline --locked --workspace --all-targets`, strict Clippy
    `-D warnings`, all return exit 0. 59 Loop unit tests; other
    ordinary tests pass; opt-in PG targets still show `ignored` in this
    command. **Only the explicit PG18 runner** above exercised the relevant
    ignored PG test.

## What this does NOT close

1. Installed Gateway 0.10.8 has zero `execution.harness` route matches.
2. Installed Runtime model credential materialization bindings are empty.
   No true external free model → physical Tool → owner receipt → domain
   verdict was executed here.
3. The native Rust Loop's `DurableJournal` Port remains test-only in R19
   consumers; no genuine ProviderCall v4 claimed/dispatching/result chain
   was proved in the SAME real Run as a physical Owner Job.
4. Runtime/Harness issuer currentness at spawn, late revocation, real
   network crashes/partitions, exact reuse after ambiguous billing, and
   independently measured AgentSolved/Cost/Latency remain separate Q1
   acceptance obligations.
5. Historical Quint contracts, PG SQL tests and this real HTTP regression
   cover different slices; a sampled abstract model is NOT an
   implementation refinement proof. In particular the outstanding
   safety obligation is
   `finish not recognized -> NOT (tool_effect OR terminal_proposal)`;
   implementation mapping is now tested locally but not formally
   discharged for all Provider/PG/Runtime schedules.

## Mature LEGO ledger

* **思想型**: Design by Contract, protocol/variant refinement,
  capability-security (proposal != grant), TDD RED→GREEN, negative-control
  falsification, UNKNOWN as a third state, evidence before status claims,
  DELETE-CUSTOM→REUSE→COMPOSE.
* **逻辑型**: L1 Run/Contract, L5 Provider wire normalization,
  L7 Model action categorization, L8–L9 Tool admission,
  L10 physical Owner effect (unqualified), L11 observation/UNKNOWN,
  L14 independent domain verification (unqualified).
* **能力型**: patched existing Rust `HttpModelProvider`; reused existing
  `NativeAgentLoop`, `reqwest`, `serde_json`, `DomainToolSurface`,
  existing Rust native local HTTP integration tests, original Python
  PG Store, original Rust PG Reader and R18 disposable PG18 runner.
  No custom parser, second PG authority, duplicate scheduler or
  security-bypassing test proxy.

## Installed Gateway/Runtime consumer qualification (same source, scoped)

This is a *separate installed infrastructure check*, NOT proof that the
`execution.harness` capability itself exists or grants model/Tool authority.

* Installed Gateway version `0.10.8`, route digest
  `sha256:809352746859c38759a8c05c1e138241dceb1ea6a08dc71ef1e14a0492727d7e`.
  `execution.linux` resolves to natural `runtime.linux`, `linux-pg`.
  Search for `execution.harness` still returned zero matches.
* Actual installed Gateway `execution.linux` → native PG Runtime Job
  `job-01a1dabf-e226-7417-93c9-fbc4904cd628`:
  `cargo test --test native_http_loop_e2e`; Gateway terminal
  `succeeded` and Runtime direct Owner observed exit 0 with 2/2 tests.
* Actual installed Gateway `execution.linux` → native PG Runtime Job
  `job-01a1dac0-91bc-77ba-a3c9-fd699ab2b728`:
  original Python Store real PG18 → Rust verified no-Tool Run → local
  HTTP Loop consumer 1/1 PASS, original disposable PG removed. Gateway and
  Runtime independently observed terminal succeeded/exit0.
* Negative missing-route request using `execution.harness` was rejected
  (Gateway surfaced `INVALID_ARGUMENT`); Runtime
  `job_list(clientRequestId=exact_missing_route_request)` returned
  `jobs=[]`. This proves **no fallback to generic Linux execution was
  observed for that one exact request**, not universal enforcement against
  a future different install or actor.
* These are tests on **the same private local Git SourceCut**. No paid/free
  remote model was called, no natural ToolGrant→Owner effect was issued,
  no true domain semantic verdict or production Harness release occurred.

## Workspace lifecycle and naturally owned debt

The native Runtime `workspace.close` refused cleanup with
`WORKSPACE_DIRTY` despite Git status clean because existing Cargo/Python
source-parity tests generated Git-ignored `.venv`, `__pycache__`, and
`ordivon_harness.egg-info` in this isolated Workspace. The Runtime refusal
is correct under its current lifecycle contract; it protects untracked data.
The test cache comes from original Python parity tests invoking `uv run`
and other Python source invocations. Do not globally force-delete arbitrary
ignored files, erase shared Cargo targets or mutate other Agent worktrees.
Only source-confirmed ephemeral paths with no active Job are eligible for
explicit consumer release. Longer-term retention/ignored-artifact lifecycle
belongs to the natural Runtime/Workstation owner, not a new Harness GC daemon.

## R19 Q2 local logic extraction and bounded model matrix

One actual consumer justified a narrow decoupling: `HttpModelProvider::query`
continues to own `reqwest` transport, bounded HTTP response bytes and
single-call no-blind-retry semantics, while a new **private pure function**
`decode_chat_completion(&serde_json::Value)` in the same Rust source file
interprets untrusted wire JSON as a model Proposal. It returns `None` for
incomplete/unrecognized responses; this becomes the original
`ProviderResult::Unknown` and then `NativeAgentLoop::PausedUnknown`.
It is **not** a Provider gateway, semantic policy owner, Tool authority,
independent codec, PG writer or new transport abstraction. This removes
one previously coupled responsibility at the smallest existing seam.

The ordinary Rust tests and original Python/PG18 live consumer were rerun
after extraction; strict Clippy initially rejected the new Option-returning
function's let-else form (`job-01a1daca-62a2-74b1-be1e-b828b829e0b3`,
exit 101). Replacing those expressions with standard Rust Option `?`
eliminated the errors: fmt/check, strict Clippy and all native loop tests
passed `job-01a1dacb-9873-702d-95b2-58afc9c3b6ca`; the actual
isolated original Python PG Store → Rust no-Tool → loopback HTTP consumer
passed `job-01a1daca-27fc-74e3-adc2-77c197d9d136` and removed its PG.

A new **source-owning decision matrix** covers 10 `finish_reason`
classes (including `null`, non-string and missing) × 6 model-message
shapes = **60 finite combinations**. Only `stop + valid text` and
`tool_calls + valid function ToolCall` are allowed as *proposals*;
all 58 other combinations must yield `None`/UNKNOWN. Actual matrix
positive: `job-01a1dace-fd22-71a5-adbe-8c895c49389c` PASS.
An independent *mutation negative-control* deliberately permitted
`length + text`; `job-01a1dacf-7966-71c6-94c3-1f6ff52c0c6e`
failed as expected, pinpointing that exact unauthorized promotion.
The safe exact rule was restored **before further validation**;
the restored matrix PASS is
`job-01a1dacf-fe32-76e6-8a7f-fea83d1ba0f0`.

This is finite model-based testing of a **bounded source-visible
classifier**, not a whole-system Quint/TLA+ proof or a tested SQL
refinement of the Provider/Tool Journal/physical Runtime race. Since the
new decoder is pure and returns only proposals, future genuinely
justified formal refinement can express the 60-case safety predicate
without replacing independent physical, cancellation and
domain-verifier tests.

## Next gate

The natural full-path consumer remains:
authorized actual model + caller WorkingSet -> same PG Run/Provider V4
records -> native PG ToolGrant/Intent/Fence -> current issuer+spawn checks
-> Gateway+Runtime actual owner effect -> PG OwnerReceipt with UNKNOWN
reconciliation -> original Coding domain hidden verification and an
independent TaskSuccess/cost/latency result. Promote this source only
through exact-source integration/CI/installed release qualification,
not by interpreting this local candidate's GREEN tests as a deployment.
