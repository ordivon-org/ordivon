# Agent Outcome Contract — Implementation Plan R1

> Execution: existing detached Runtime Workspace, then owner-native test/review. The SPEC remains binding; no second task status store.

**Goal:** Prevent Agent prose, local test passes and biased proposals from being accepted as the final Network consumer outcome.
**Architecture:** Reuse existing R2.1, Cognitive Circuit, native Network Task and verifier-owned Gate. One vertical consumer test before expansion.
**Tech Stack:** Python, JSON Schema, pytest, Git, Task/systemd; existing Composition TLA+/TLC only when a demonstrated property gap requires it.
**Spec:** \`platform/network/docs/AGENT_OUTCOME_NETWORK_PILOT_SPEC_R1.md\`

## Global constraints
- No new controller, completion registry, policy engine or automatic verifier discovery.
- Model output is not evidence of owner effects. Mechanical Gate closure is not consumer acceptance.
- UNKNOWN remains scoped, not FALSE or PASS.
- Source vs installed vs loaded vs executed vs consumed are separate observations.
- Current natural Owner retains effect/acceptance authority.

## Preflight
- [x] Confirm exact local SourceCut and read AGENTS/Composition/Network boundaries; remote ref currentness UNKNOWN on timed-out query.
- [x] Reuse existing Circuit, Gate and task-local obligation APIs.
- [x] Verify upstream Skill mechanisms by reading public original SKILL.md. No installation.

## T0 — Bind SPEC to real consumer
- [x] Record problem, Network Forward drift, existing task entrypoints and owner separation.
- [x] Specify all 11 existing responsibility coordinates, nonclaims and final consumer.
- [x] Declare T1→T7 blocking edges and independent acceptance.

## T1 — Native Circuit integration and mutation gates
- [x] Write RED tests in \`platform/network/tests/test_shared_forward_contract_circuit.py\` proving: positive compile; missing/UNKNOWN; stale/foreign/widened result; no domain verdict; wrong scope and zero gate.
- [x] Execute RED test, read failure (missing concrete Network circuit).
- [x] Add \`platform/network/acceptance/lifecycle/shared-forward-reload-circuit-r1.json\` with existing Cognitive Circuit schema and gate obligations; no new library or registry.
- [x] Execute GREEN targeted pytest with Composition module accessible; lint files and run Network tests.
- [x] Run existing Composition verification subset / independent negative control where available.
- Expected: all specified tests pass, and altered sources/unknown never silently yield accepted domain effect.

## T2 — Apply owner-native live repair (blocked on T1)
- [x] Capture current service/provider PID and SourceCut; verify installed/loaded drift.
- [x] Run existing Network materialize task (not a provider restart); confirm installed bytes and loaded ExecReload.
- [x] Run existing shared-egress reload; verify kernel forwarding; confirm no provider restart/identity reset.
- Expected: source/installed/loaded/current kernel align, provider stable. If failure, report exact blocker and effect recovery; do not label success.

## T3 — Consumer closure (blocked on T2)
- [x] Run Network's native affected consumer readiness/probe and exact provider continuity checks.
- [ ] Attach provenance/currentness in existing owner evidence/Host Work; keep untested iOS client exit usage UNKNOWN.
- Expected: specified consumer path independently accepted; source test and process UP alone insufficient.

## T4 — Agent evaluation (blocked on T1, T3)
- [ ] Pre-register A/B tasks, holdout failures and denominators in Harness existing Evals folder.
- [ ] Test different Agent/harness configurations with equal tools/authority/budget; collect real effect evidence.
- Expected: distinguish false-success rate from source correctness and model-only scores; no generalization without replication.

## T5 — Formal gap (blocked on T1, T4)
- [ ] Identify minimal property not already proved by existing gate machinery.
- [ ] Add one native formal lemma/model-checker property and falsifying control *only if justified*; otherwise record no missing formal gap.
- [ ] Verify concrete implementation refinement separately.
- Expected: theorem/model scope and independent runtime consumer checks clearly distinguished.

## T6 — Integrate and prune (blocked on T3,T4,T5)
- [ ] Review diff, consumers, and current main; update only relevant AGENT/Skills entrypoints.
- [ ] Delete any now-redundant local process text/custom glue, not proven necessary recovered data.
- [ ] Integrate through documented serialized repo helper/normal PR; do not push unreviewed shared main.
- Expected: no extra owner lifecycle or duplicate task state.

## T7 — Retro and rollout decision (blocked on T6)
- [ ] Compare measured consumer outcomes and unnecessary changes before/after.
- [ ] Promote narrow reusable method only if a second Owner benefits; otherwise keep local.
- Expected: improvement evidence or explicit rejection, not a ceremonial "global rollout".

## Review focus
- Unproven source-installed relationship
- Wrong Gate Owner or widened support scope
- Stale manifest/source acceptance
- False completion from tests or provider active
- Provider restart triggered by a supposedly harmless reload

## Execution observations — 2026-11-09 (not a new task state database)

- Exact Linux Runtime workspace: \`ws-gpt6-lego-agent-contract-spec-20261109\`, intake local origin/main \`05fec3688cf1ae1f091a2dd080784249becbc18a\`; fresh remote ref query timed out, remote currentness UNKNOWN.
- T1 RED: before source manifest existed, 10 case setup errors. T1 GREEN: 10/10 target tests; Ruff check/format PASS. An intermediate 9/10 result exposed the real counterexample that generic Composition permits partial cross-owner Gate coverage; the Network consumer test now freezes both required Gate identities outside candidate declarations and demonstrates reduced-gate mechanical closure does not confer domain acceptance.
- Composition owner native pytest: exit 0, with pre-existing skip cases. Initial wrong-cwd combined collection failed on missing \`scripts\` import; rerun from \`packages/composition\` was green. Network owner native pytest: 384 passed in 36.01 seconds.
- T2: native \`substrate:shared-egress:validate\`, \`materialize\`, \`reload\` and \`verify\` all succeeded. Source-installed Forward Unit bytes equal, loaded ExecReload exists, kernel FORWARD/namespace checks PASS. Provider MainPID 2780666 and NRestarts 0 remained unchanged after reload; Gluetun carrier readiness READY.
- T3: \`provider:gluetun:verify\` succeeded; \`consumer:mobile-tailnet-exit:verify\` succeeded (server READY; \`clientPublicExit=NOT_EVALUATED\`). First \`consumer:codex:verify\` hit a 5-second CDN timeout. Independent direct/codex proxy checks then returned ChatGPT HTTP 200 and CDN HTTP 404 with CONNECT=200/TLS complete; repeated native Codex verification returned READY and unknown-destination REJECTED. This does not prove zero intermittent failures or actual Windows Codex application-process egress: \`applicationProcessEgress=UNKNOWN\`.
- Native Runtime Job references: materialize \`job-01a1c099-4452-7027-a85b-d969ba05e41a\`, combined owner readback \`job-01a1c09b-559b-7308-9d33-5796f7bea55b\` (wrapper exit 1 due transient Codex check), second Codex verify \`job-01a1c09d-23fe-7434-8a15-85728ec69738\`. Runtime execution receipt is not semantic completion.
- T4–T7 remain not executed; no cross-model improvement claim, no new formal theorem, and no iOS/Windows end-to-end application exit certification.

- Owner-boundary refinement: root \`check_owner_boundaries.py\` rejected the initial Composition-test→Network source-path dependency. Moved the consumer test under Network \`acceptance/lifecycle/\`, retaining only the public \`ordivon_composition\` API, and added \`platform/network/mise.toml:contract-agent-outcome\` to Network native \`ci\` dependencies. The original wrong-direction path was removed.

- Public inter-owner integration: the repository boundary check correctly identified Network's source-task reference to the public Composition environment. Added one exact \`network → composition\` public task-local consumer seam in \`tools/repo/dependency_contracts.toml\`. This is a documented source dependency, not a truth or execution-authority transfer.

- Integration coexistence: \`origin/main\` PR #1965 separately merged a **root Runtime/Host Agent outcome** SPEC while this Network pilot was in progress. To avoid duplicated root authority, both pilot documents moved under \`platform/network/docs/\`; root \`docs/architecture/AGENT_OUTCOME_CONSTRAINT_EXECUTION_SPEC_R1.md\` remains canonical for the cross-system task graph. The Network pilot is a concrete consumer implementation, not a second global governance plan.
