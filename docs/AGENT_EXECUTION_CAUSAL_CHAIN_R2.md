# Agent execution causal chain R2 — source-bound Golden Road

**Source baseline:** `710bd0619bf3633cb8fc5b68e95e9d04bef350a4` (2026-11-14). Status: bounded source implementation and Gateway/Composition contract checks, **not** a whole-system deployed end-to-end receipt. Built from established `recursive-lego-calculus`, `compositional-contracts`, `systems-engineering` and FMEA safety methods; native PG owners, not this document, authorize effects and own durable truth.

## The actual Agent consumer

An Agent calls a Tool. The Harness can lose the response after submission, Gateway can see an ambiguous Runtime dispatch or incomplete delivery, and Host might later re-enter a Work. The Agent must answer: *Did this exact operation happen? What should I read next? Am I permitted to retry?* The correct consumer outcome is **navigation to the original native owner and a clear uncertainty fence**, not replaying the command because a graph lacks a completion edge.

## Authoritative source / identity / edge inventory

| Owner | Native source and existing implementation | Typed outbound fact | What this does **not** establish |
| --- | --- | --- | --- |
| Harness | `services/harness/src/ordivon_harness/ordivon/{run_continuity,run_recovery,runtime_bridge}.py`, `plugin_gateway_effect.py` | `RunId → AttemptId → ProviderCallId / ToolCallId → clientRequestId` (where actually retained) | Agent step order or ToolCallId alone is not Runtime JobId or provider effect |
| Gateway | `services/gateway/src/ordivon_gateway/{execution_refs,execution_observations,contracts}.py` | `execution.resolve` binds submitted `clientRequestId` to native `operation_ref=ordivon-exec:v1:{owner_id}:{job_id}`; `execution.get` obtains Runtime `job.observe` | A route is not IAM; `absent` after lost response need not authorize another submit |
| Runtime | `services/runtime/crates/ordivon-runtime-core/src/runtime/engine/observation_projection.rs`; PG Job/Attempt + runner receipts | Job identity, Attempt/terminal state, delivery and recovery disposition, artifact refs | `starting` can be PG dispatch intent; exit 0 does not prove external provider effect |
| Composition | `packages/composition/src/ordivon_composition/{effect_reconciliation_r1,verification_impact}.py` | `operation_ref → effect_ref → dependent verification obligations`; next read `OBSERVE`, `RECONCILE`, or `VERIFY_DOMAIN_EFFECT` | Does not dispatch/retry/approve, authenticate caller-supplied Gateway-shaped JSON, or certify provider success |
| Host | `services/host/docs/SOCIAL_WORK_FABRIC_R2_SPEC.md`; PG Work/Topic/Message/Attention | `Work.get → attention.reentry → topic.resume → owner-native reference readback → WorkSnapshot commit → cursor acknowledgement` | Topic/Work snapshot is semantic continuity, **not** Runtime state, a restored side effect or automatic background action |
| External effect owner | Provider-specific original operation response or domain receipt | Actual provider effect after independent validation | Presence of an `operation_ref`, digest or status label is not exactly-once effect authority |

These are **typed, time/source-bound links**, not a new mandatory global graph database or a one-size-fits-all object/edge schema. A missing edge is UNKNOWN until owner readset/currentness is qualified; historical reference validity is not live authorization. Keep source authority and UI/agent projections separate.

## Cross-owner delivery vocabulary (this R2 refinement)

Gateway `ExecutionObservation.delivery_disposition` passes through the Runtime owner delivery, and Harness already recognizes four values. Composition's task-local `C06` now accepts all four *when the exact owner/ref is well-formed*:

| Delivery | Condition | Agent-readable next action | Effect/retry claim |
| --- | --- | --- | --- |
| `in_progress` | not terminal; no other recovery flag | `OBSERVE_ORIGINAL_OPERATION` | not established; no auto-retry |
| `unknown` | regardless of terminal | `RECONCILE_ORIGINAL_OPERATION` | unknown; no auto-retry |
| `reconciliation_required` | regardless of terminal or `recovery_required` flag | `RECONCILE_ORIGINAL_OPERATION` | unknown; no auto-retry |
| `committed` | terminal, conclusive resolution and verified Runner result | `VERIFY_DOMAIN_EFFECT_WITH_OWNER` | process/delivery result only; provider effect not established |

`recovery_required=true` and owner state `reconcile_required` separately force `RECONCILE_ORIGINAL_OPERATION`. Inconsistent/malformed or foreign operation identities fail closed, but a valid fourth delivery value must not become an unknown protocol failure. C06 still accepts a synthetic historical `external.pull` operation as caller-provided data; only `runtime.linux`, `runtime.windows`, and `runtime.harness` are recognized by Gateway's current native `execution_refs.py`. Keep those separate until actual legacy consumer retirement is proved.

## Source → formal model → implementation → real consumer

- **Specification:** `packages/composition/formal/EffectReplayFence.tla` models the four delivery states. TLC checks `NoBlindRetry`, `NoEffectEstablishedFromProcessExit`, exact recommendation, obligation influence and `ReconciliationDeliveryNeedsOriginalObservation` for all its reachable finite abstract states.
- **Independent negative controls:** the existing three counterexample probes and the new `ReconciliationDeliveryIsUnreachable` probe must each be falsified by pinned native TLC; the unsafe-retry mutation must violate `NoBlindRetry`.
- **Implementation correspondence:** `test_effect_reconciliation_r1.py` checks **288** representative combinations of nine declared source states (including actual `lost`, `orphaned` and `timed_out`), two terminal flags, two recovery flags, four deliveries and two indexed/unindexed scenarios. Six native Runtime owner×terminal cases test `reconciliation_required`, owner identity, scoped UNKNOWN propagation, and non-retry.
- **Actual owner transport:** `services/gateway/tests/test_gateway_service.py` uses `GatewayService.execution_get` to emit Pydantic `ExecutionObservation` for all three native owners and requires exact delivery, operation identity and no extra owner calls. A separately executed two-interpreter smoke test fed the real Gateway method output into Composition and obtained `RECONCILE_ORIGINAL_OPERATION` with no retry. Its Runtime `job.observe` was a test fake, **not a production PostgreSQL readback**.
- **Harness R4 refinement:** existing `services/harness/tests/test_gateway_execution_port.py` recognizes `reconciliation_required`; current R4 consumers also accept `lost + unknown + resultAvailable=false` as uncertain and refuse to invent a Runner result from mere Artifact inventory. The Harness native suite remains necessary even when abstract TLA proves the scoped decision model.
- **Host R3 observed:** actual Host Work `work:ordivon:agent-execution-causal-pg-e2e-r3:20261114` revision 2 was committed and reread through Gateway; Topic Message 27709 and this actor's cursor acknowledgement were reread. No independent second authenticated Agent has consumed it.

Do not remove real Gateway/Harness/Runtime/Host behavioral tests on the strength of a 577-state TLC model. A finite model has not proved JSON transport authenticity, installed Runtime source, crash recovery, provider idempotency, history completeness, actual external effects, or arbitrary implementation refinement.

## Ordered owner-to-agent read procedure

1. Obtain Harness's **exact durable ToolCall/operation intent** and current Run/Attempt/ProviderCall cursor; do not infer a Job by similar names.
2. For Gateway-routed execution, use the original `clientRequestId` and `execution.resolve`; treat absent/ambiguous response-loss results under the existing effect policy, not as an unconditional new-submission invitation.
3. If `operation_ref` is present, call Gateway `execution.get`; it performs owner-native Runtime observation. Require its exact `owner_id` + native Job identity, delivery, terminal and recovery fields.
4. Apply Composition `C06` only as **decision support**. `RECONCILE_ORIGINAL_OPERATION` → inspect the original Job/Attempt and original effect owner. `OBSERVE_ORIGINAL_OPERATION` → continue observing that same Job. `VERIFY_DOMAIN_EFFECT_WITH_OWNER` → get original authoritative provider receipt; an exit code is insufficient.
5. If the original native owner proves the domain outcome, let that natural owner update its real consumer. Host can **link** the resulting evidence and advance Work/Topic cursors, never manufacture or overwrite Runtime truth.
6. Classify all unindexed dynamic dependency/readset facts UNKNOWN; query the exact Owner rather than writing a global causal edge that pretends completeness.

## Remaining Q1 / Q2 obligations

- **Q1:** Run live owner-authorized PG Runtime/Gateway/Harness consumer test with an actual ambiguous launch or response loss, distinguish admission vs systemd start vs provider effect, verify no duplicate original operation.
- **Q1:** Validate a real Host work reentry and resulting Runtime/Gateway `operation_ref` readback in the same exact consumer and source cut. No Host snapshot was changed in this R2 source patch.
- **Q1:** Owner readset completeness and risk-tiered external-effect reconciliation for specific Agent tools before any claimed safe re-execution.
- **Q2:** Evaluate and refine model→Python equivalence beyond finite correspondence, including contradictory native observations, temporal owner currentness, negative dependency discovery, and authorization changes.
- **Q2:** Document and retire redundant historical SQLite/recovery shims only after actual consumer closure and verified replacement. **Do not** restore SQLite or add a new global graph/event/Hash service.
- **Q2:** Measure Agent resume time, unnecessary re-check count, duplicate effect attempts and missing-causal-edge rates against named real workloads; source-level PASS does not establish a productivity gain.

### LEGO responsibilities

Thinking LEGO: systems engineering, event-sourcing/temporal state, assume–guarantee composition, model checking, FMEA and conservative three-valued epistemics. Logic LEGO: exact causal identity binding; owner-source readback; status refinement; effect uncertainty propagation; history/attention reentry; model/code/consumer acceptance separation. Capability LEGO: existing Harness Runtime Bridge and Gateway execution APIs, Runtime PG Job/Attempt observation, Host PG Work/Topic/Attention, Composition C04/C06 selectors, native TLC + Ruff + pytest. **This R2 changes only Composition decision/model/verification and Gateway owner-facing contract tests**; the other existing capabilities are reused, not migrated or claimed installed.

## R3/R4 native PG counterexample — result delivery is not control commitment

Source candidate baseline: `f614cd50e93f00305009bb3bf5863b4d0ad1a021` (both prior PRs #2207 and #2210 merged). Exact production Runtime source for the live experiment was `d2ea2badbbf695ff00e55d99cefbb3bde3a2435f`, so patched Rust/Python sources are **not claimed deployed**.

Observed native operations in the R3 caller-owned test Workspace:

- A real Gateway Tool request `gpt6-causal-r3-at-most-once-marker-20261114-02` resolved back to PG Job `job-01a1d9fb-d07d-74d6-9257-f5694d0e0766` after the client deliberately discarded its received acknowledgement. Resubmission with exactly equal identity and arguments returned the same Job/Attempt, and `wc -l` via a second Gateway Job plus digest-bound Artifact reported **one** physical marker line. This is a caller-side response-loss simulation, not network severance.
- A real `timeoutMs=1100` command wrote `began` then slept. PG Job `job-01a1da01-6a4f-76e3-b6bf-4cf90a2bbc4a` became `timed_out`; independent Gateway `artifact.read` of a follow-up read-only `cat` Job returned only `began`. Process timeout did not undo a partial effect.
- A real `execution.cancel` of Job `job-01a1da03-59c8-741a-ba7d-44f187d39eff` generated `executionDisposition=lost`, `executionTerminal=true`, `deliveryDisposition=committed`, `recoveryRequired=false`, `resultAvailable=false`, with only `native_stop_evidence`. Native control/PG mechanics converged but **no Runner result existed**. This was a cross-owner counterexample, not a proof of an external effect. A later independently submitted read-only Gateway Job `job-01a1da1b-5ccf-7211-9d50-6f15e30124ee` read the actual cancelled Job's Workspace marker: `entered\n` was present, while `exited` was absent. The result was stored as the Runtime's native `stdout` Artifact with SHA-256 `46eb3d6b7c89c65df13fe70ea8feb5b9da22ff3c131aac57b36615a26d7577bd`, and the original marker's SHA-256 was `be91f7644f03cc4976431d2001387209fb097540e3c994bf3e8ba4a99efa1457`. This proves a **bounded local filesystem partial effect** on one LOST process, not the remote domain-effect outcome.

R4 source fix: in the existing PG Runtime owner, both `job.observe` and `job.list` use one conservative delivery projection function: `lost → unknown`, `orphaned → reconciliation_required`, conclusive terminal **with Runner result** → `committed`, missing execution result → `reconciliation_required`, nonterminal → `in_progress`. Harness accepts terminal lost+unknown even without a Runner result, and the Gateway adapter stops turning native-stop Artifact inventory into `resultAvailable=true`. Composition C06 now conservatively says `RECONCILE_ORIGINAL_OPERATION` for `lost/orphaned`, including contradictory old installed combinations with `committed`; no auto retry or effect certification.

Existing TLA+ C06 model was refined with explicit uncertain native resolution states and a reachable `lost+committed` negative probe. Its bounded model/code correspondence is not a PG-installed refinement or actual provider effect verification. Agent/Harness must never infer that committed **control resolution** equals complete physical/process **outcome delivery**.

### R4 cross-language Rust consumer refinement

The existing Harness Rust migration `services/harness/rust-migration/b-loop-probe/src/runtime_delivery.rs` independently interprets Runtime Owner delivery and is exercised by native GitHub owner-shard CI. The initial R4 candidate failed its own Python→Rust source oracle on the *real PG state* `lost + unknown + resultAvailable=false`; Rust had retained an obsolete requirement that an uncertain LOST must have a Runner result. The Rust consumer now classifies this state as `Unknown` (never `Terminal` or replay authority) while preserving its exact input validation. The current differential source test checks **1,362** Python-produced canonical Owner observations, including **215** valid inputs and **19** `unknown` cases, with Rust decisions matching the Python Owner classification. The amended candidate also adds an explicit Rust unit regression for the native-stop-without-result counterexample. Python/Rust source parity is not evidence that the Runtime process or external Provider effects are installed or correct.

## R5 source-qualified physical Runtime acceptance (2026-11-14)

After main integrated PR #2216 (`a31fe9e3882c6f912060954c0e9bc51c64fa5eb6`), the **existing** Rust `pg_vertical.rs` real PG/systemd tests were refined rather than creating another test framework. `failed_retained_pg_transient_auto_converges_to_lost_and_releases_capacity` now forces an exact disposable systemd Runner to lose its result, requires `job.observe` to produce `lost + unknown + resultAvailable=false + recoveryRequired=false`, and separately requires the existing `job.list` consumer to project the exact same original Job and unknown result. The real PG transaction must still release the reservation, retain native-stop evidence, and issue just one physical dispatch. `fresh_pg_mcp_native_runner_success_and_cancel` additionally checks `unknown` on its native-stop-only LOST branch while retaining successful/replay/cancel contract coverage.

**Actually executed** at integrated main source `a31fe9e3882c6f912060954c0e9bc51c64fa5eb6` with the native Runner prebuilt:

- `cargo test --locked -p ordivon-runtime-mcp --features postgres-runtime --test pg_vertical failed_retained_pg_transient_auto_converges_to_lost_and_releases_capacity -- --ignored --nocapture --test-threads=1` — **1 PASS/0 FAIL**, real disposable PG + systemd test.
- `cargo test --locked -p ordivon-runtime-mcp --features postgres-runtime --test pg_vertical fresh_pg_mcp_native_runner_success_and_cancel -- --ignored --nocapture --test-threads=1` — **1 PASS/0 FAIL**, real disposable PG + systemd test.

This is physical acceptance of the **tested candidate binaries**, not installation or source-currentness of the live `ordivon-runtime.service`. As of the R5 read-only inventory that service was still using `/usr/local/libexec/ordivon/ordivon-runtime-pg` SHA-256 `0ba685a55a5c9a3d7eaf7cb2da6f791a5cbb3aaf5a74e701ee0323e63e1faeae` with active entry time 2026-11-13 02:14 local. Connected Runtime provides `release.get` but not a qualified callable `release.apply`; the existing PG-native release operator requires a previously admitted durable release effect. Do not bypass that release/receipt boundary by manually swapping an active service executable. Production deployment, installed-state requalification, real Gateway/Harness *on the new installed binary*, and external provider effects remain UNKNOWN pending independent owner verification.
