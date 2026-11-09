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
- [x] Declare bounded Network dependency edges and independent acceptance.

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

## N2 — Source-frozen obligation refinement and native SMT law (T1 completed)

- [x] Name original required Network Gate identities, owners, scopes and guarantees from exact published pilot Git cut b7d64d103cf6; no candidate text is accepted as original authority.
- [x] Add source-refinement verifier in platform/network/formal/agent_outcome_refinement.py; candidate must retain exact original duty fields, and source mutation negative controls must fail.
- [x] Use the **existing centrally pinned Z3 5.3.2 CLI** through tools/formal and standard SMT-LIB, not a second Python library download.
- [x] Prove bounded safety with an independent-consumer predicate, show candidate-only acceptance after a missing Gate is satisfiable (negative control), and prove UNKNOWN, wrong-owner, stale, widened-scope cannot yield independent acceptance in this finite abstraction.
- [ ] Observe final CI results and protected merge from the actual candidate branch; a local SMT PASS does not authorize release.

## N3 — Real Composition implementation refinement (blocked on N2)

- [x] Extend the Network-native contract suite to compare actual candidate source against the original immutable Git blob and reject six relevant mutations.
- [x] Exhaust SATISFIED, UNSATISFIED, UNKNOWN and MISSING for the two current Gate IDs: 4×4=16 concrete Composition evaluator combinations.
- [x] Keep mechanical closure distinct from Network domain acceptance.
- [x] Run both native commands and retain actual output: mise run contract-agent-outcome, mise run formal-agent-outcome.
- Expected: independent original requirements cannot be dropped by an implementation candidate; the abstract proof is distinctly scoped from the real code and installed effects.

## N4/N5 — Native physical and consumer readback

- [x] Original Forward Unit materialize/reload completed without Gluetun restart; kernel/source/loaded readback and final sampled Gluetun/Mobile Exit service/Codex proxy READY were observed earlier on the production Linux node.
- [ ] Requalify only changed physical assumptions or consumer state; don't repeat a live mutation when only formal source or documentation changes.
- [ ] Keep iOS client exit and Windows application process egress as explicit UNKNOWN until their own native consumers verify them.

## N6 — Protected GitHub delivery (blocked on N2,N3,N5)

- [ ] Preserve original PR #1982; do not create a second global SPEC PR.
- [x] Merge/fetch current main at a7d70e83945b7418f41b9636f0803d1544e84355 into the isolated pilot branch without resetting another Agent's work; the observed source overlap did not conflict. Recheck remote head at release.
- [ ] Run root owner boundary and architecture checks, Network CI/formal, focused Composition, style and negative controls. Check current CodeQL and GitHub checks.
- [ ] Push a fast-forward update and integrate through protected GitHub main; obtain exact merged SHA and current consumer readback. Do not infer release from source tests.

## N7 — Propagate only real contract demand and retire duplication

- [ ] Reuse existing Host/Runtime/Harness specs and native formal methods; avoid another global Agent-governance Skill, controller or verifier registry.
- [ ] Require a concrete second Owner consumer before promoting a generalized new method. Delete duplicate/stale explanatory artifacts when no real consumer depends on them.
- [ ] Final report distinguishes source/merged/installed/executed/consumed and exact remaining UNKNOWN.

No weak-model A/B runs, artificial model-rank comparisons, cross-model generality claims or blanket all-Skills activation are part of this programme.

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
- Historical initial scope T4–T7 was not executed. The weak-model A/B proposal is retired and replaced with bounded SMT proof and implementation refinement N2/N3; no iOS/Windows end-to-end application exit certification.

- Owner-boundary refinement: root \`check_owner_boundaries.py\` rejected the initial Composition-test→Network source-path dependency. Moved the consumer test under Network \`acceptance/lifecycle/\`, retaining only the public \`ordivon_composition\` API, and added \`platform/network/mise.toml:contract-agent-outcome\` to Network native \`ci\` dependencies. The original wrong-direction path was removed.

- Public inter-owner integration: the repository boundary check correctly identified Network's source-task reference to the public Composition environment. Added one exact \`network → composition\` public task-local consumer seam in \`tools/repo/dependency_contracts.toml\`. This is a documented source dependency, not a truth or execution-authority transfer.

- Integration coexistence: \`origin/main\` PR #1965 separately merged a **root Runtime/Host Agent outcome** SPEC while this Network pilot was in progress. To avoid duplicated root authority, both pilot documents moved under \`platform/network/docs/\`; root \`docs/architecture/AGENT_OUTCOME_CONSTRAINT_EXECUTION_SPEC_R1.md\` remains canonical for the cross-system task graph. The Network pilot is a concrete consumer implementation, not a second global governance plan.

## Theory and formal follow-up — 2026-11-09

Current source follow-up reconciles with remote main a7d70e83945b7418f41b9636f0803d1544e84355 by a normal merge. The Network pilot remains a PR candidate pending protected integration. The detailed derivation is in the pilot SPEC section 2A, with Hoare, assume–guarantee refinement, temporal safety/liveness, abstract interpretation, separation-logic footprints, hermetic source identity, STPA, SMT negative controls and source-to-code-to-consumer refinement. This replaces the old planned weak-model trial rather than adding one.

## Current formal-source verification receipt (follow-up)

- Exact first published pilot Git baseline: b7d64d103cf67242cbd1609e5c7df729fc187d45; **immutable candidate**, not independent acceptance. Current follow-up source merged main a7d70e83945b7418f41b9636f0803d1544e84355 into the pilot branch without modifying the shared primary checkout.
- Native formal Task **formal-agent-outcome** returned 0 with standing BOUNDED_ABSTRACT_SAFETY_PROVED, two original required Gates, and a reachable false-acceptance counterexample for an intentionally weakened candidate-only checker. Missing Gate, UNKNOWN, wrong owner, stale source and wrong scope cannot pass the independent abstract predicate. Not an installed or full implementation proof.
- Network-local **contract-agent-outcome** returned 12 passed, including 16 exhaustive concrete Gate observation combinations, exact Git source Gate preservation and explicit no-domain-acceptance results.
- The existing pinned Z3 5.3.2 from tools/formal was used through native mise/SMT-LIB. Initial Python z3-solver wheel download timed out; no extra solver was installed or given new authority.
- No deliberately weak model experiment was performed, scheduled or needed.
