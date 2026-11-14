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
| `committed` | terminal and no recovery requirement | `VERIFY_DOMAIN_EFFECT_WITH_OWNER` | process/delivery result only; provider effect not established |

`recovery_required=true` and owner state `reconcile_required` separately force `RECONCILE_ORIGINAL_OPERATION`. Inconsistent/malformed or foreign operation identities fail closed, but a valid fourth delivery value must not become an unknown protocol failure. C06 still accepts a synthetic historical `external.pull` operation as caller-provided data; only `runtime.linux`, `runtime.windows`, and `runtime.harness` are recognized by Gateway's current native `execution_refs.py`. Keep those separate until actual legacy consumer retirement is proved.

## Source → formal model → implementation → real consumer

- **Specification:** `packages/composition/formal/EffectReplayFence.tla` models the four delivery states. TLC checks `NoBlindRetry`, `NoEffectEstablishedFromProcessExit`, exact recommendation, obligation influence and `ReconciliationDeliveryNeedsOriginalObservation` for all its reachable finite abstract states.
- **Independent negative controls:** the existing three counterexample probes and the new `ReconciliationDeliveryIsUnreachable` probe must each be falsified by pinned native TLC; the unsafe-retry mutation must violate `NoBlindRetry`.
- **Implementation correspondence:** `test_effect_reconciliation_r1.py` checks **96** representative combinations of three source states, two terminal flags, two recovery flags, four deliveries and two indexed/unindexed scenarios. Six native Runtime owner×terminal cases test `reconciliation_required`, owner identity, scoped UNKNOWN propagation, and non-retry.
- **Actual owner transport:** `services/gateway/tests/test_gateway_service.py` uses `GatewayService.execution_get` to emit Pydantic `ExecutionObservation` for all three native owners and requires exact delivery, operation identity and no extra owner calls. A separately executed two-interpreter smoke test fed the real Gateway method output into Composition and obtained `RECONCILE_ORIGINAL_OPERATION` with no retry. Its Runtime `job.observe` was a test fake, **not a production PostgreSQL readback**.
- **Harness unchanged:** existing `services/harness/tests/test_gateway_execution_port.py` recognizes `reconciliation_required` and does not promote an ambiguous process to a consumer terminal result. The Harness native suite remains necessary even when abstract TLA proves the scoped decision model.
- **Host unchanged:** the existing PG Work and MessageRelation/Attention cursor reentry flow remains the source of semantic continuity. No new WorkSnapshot or Topic history was written to assert an operation happened.

Do not remove real Gateway/Harness/Runtime/Host behavioral tests on the strength of a 193-state TLC model. A finite model has not proved JSON transport authenticity, installed Runtime source, crash recovery, provider idempotency, history completeness, actual external effects, or arbitrary implementation refinement.

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
