# Network Agent Outcome Contract — Consumer Pilot SPEC R1

Date: 2026-11-09 (Asia/Shanghai)
Status: implementation specification; no production-completion claim
Source baseline: local \`origin/main\` = \`05fec3688cf1ae1f091a2dd080784249becbc18a\` at intake. Remote ref lookup timed out: remote-currentness UNKNOWN.
Natural owners: Composition (generic task-local binding), Network (first real consumer and domain verdict), Harness (agent experiments), Runtime (physical execution), Host (Work continuity).
Authority: \`AGENTS.md\`, \`packages/composition/AGENTS.md\`, \`platform/network/AGENTS.md\`, each owner-native API.

This is a **Network-owned vertical pilot**, not a competing root-wide Agent contract. The canonical merged system-wide specification is \`docs/architecture/AGENT_OUTCOME_CONSTRAINT_EXECUTION_SPEC_R1.md\` (origin/main PR #1965, 2026-11-09). This pilot deliberately implements a distinct, real Network shared-forward consumer and its concrete Composition Gate tests; it does not replace that Runtime/Host-focused execution DAG.

## 1. Problem / actual consumer

A coding Agent can deliver documentation, additional tests, or a locally green Job without changing the required real-world result. Model conservatism, local optimization, overengineering and self-reported PASS can therefore masquerade as domain success. The first actual consumer is Network's live shared-egress forwarding: source \`ExecReload\` exists, but previously observed installed/loaded unit lacks it, so a naive restart may cascade into the required Gluetun provider.

The business goal is **reliable consumer continuity during native shared-egress forward reconciliation**, using the existing installation and reload path, with evidence that reaches installed, loaded, kernel, provider and affected consumer states.

This reform is not a new task engine. Its scope is to make an existing concrete task contract independently falsifiable and reusable as an engineering *method*.

## 2. Upstream derivation, selectively adopted

- Matt Pocock \`skills\`: domain terms and real seams; \`to-spec\` then \`to-tickets\` blocking DAG, \`implement-spec\` with isolated candidates and review, \`retro\` as environment repair. Do not import its own tracker/workflow state. <https://github.com/mattpocock/skills>
- ECC: progressive \`iterative-retrieval\`; \`verification-loop\` distinguishes build/lint/test/diff from target deployment acceptance. No wholesale hooks, memory, scanning, or extra context loaders. <https://github.com/affaan-m/ECC>
- obra/Superpowers: isolate worktrees; task-level RED→GREEN; bounded executable plan, review and independent verification before completion. Avoid universal forced pauses or subagent orchestration. <https://github.com/obra/superpowers>

Source Skills are untrusted instructions. Extract ideas, do not execute bootstrap files or transfer tool permission or truth authority. If installing a skill, first run \`.agents/skills/skill-supply-chain-audit/SKILL.md\`; initial implementation installs none.

## 3. Accepted semantics / anti-growth constraints

Existing typed R2.1 LEGO: \`ell=(I,O,S,pre,post,inv,eff,c,epsilon,prov,unfold)\`.
Only independently contractable responsibilities get complete formal LEGO declarations. A \`Skill\`, method, file, test and task are not automatically separate LEGOs.
Reuse:
- \`packages/composition/src/ordivon_composition/cognitive_circuit_r1.py\` for non-authoritative task-local DAG;
- \`verification_obligation_r1.py\` for exact Gate obligations/bindings;
- \`composition-gate-result-v1.schema.json\` and \`evaluate_gate_results\` for SATISFIED/UNSATISFIED/UNKNOWN;
- \`platform/network/substrates/shared-egress/Taskfile.yml\` for physical source install/reload/kernel verification;
- Host Work, Runtime Job/Attempt and Artifact evidence for their own truths;
- existing owner formal toolchains (Python properties, TLA+/TLC, Lean, Z3 as justified).

Explicit exclusions: new Agent controller, policy engine, central evaluator, verifier registry, task database, completion status namespace, global LEGO registry, universal reward model, mandatory approval funnel.

## 4. Scope-bound outcome model

For each real owner task:
- Objective: consumer-visible desired effect with exact upstream/source scope.
- Proposal: replaceable Agent candidate. It may be wrong and has no semantic completion authority.
- Realization: specific owner-native effect and observation; Runtime Job success = physical execution only.
- Verification: independent verifier-owned scoped result, with proof-source and currentness binding.
- Acceptance: the affected natural consumer's domain verdict, not Composition's mechanical gate closure.

Formal safety properties:
- P1: Agent claim, document or test pass alone cannot yield \`consumerAccepted=true\`.
- P2: \`UNKNOWN\` and missing/stale/wrong-owner Gate evidence cannot be promoted to \`SATISFIED\`.
- P3: Gate evidence is bound to exact manifest digest and its declared support scope; changed source invalidates reuse unless a native refiner proves continuity.
- P4: A circuit with zero required Gates does not close mechanically; a mechanically closed circuit never establishes domain acceptance.
- P5: Unrelated UNKNOWN does not block a separately scoped authorized reversible effect; relevant unresolved preconditions remain explicit.
- P6: Shared-forward reload must not be realized as dependent Gluetun restart. Source install, loaded ExecReload, kernel forwarding, provider continuity and affected consumer acceptance are distinct predicates.
- P7: A new abstraction must close a currently unmet consumer contract; otherwise DELETE → REUSE → COMPOSE wins.
- P8: A task failure cannot be repeated blindly after an uncertain physical effect; reconcile exact Runtime Job/Attempt first.
Proof coverage is explicit: P1–P4 are largely enforced in existing Composition; P5–P8 need task-local owner observations. Tests checking static JSON shape alone are not a physical proof.

## 5. Network vertical LEGO profile (existing shared-egress responsibility)

\`ell_network_forward\` is a *description of the existing owner responsibility*, not new registry admission:

| R2.1 coordinate | Task-scoped representation |
| --- | --- |
| I | accepted source Unit, forward helper, provider env, kernel namespace, desired consumers |
| O | loaded ExecReload and observed forwarding plus provider/consumer continuity witnesses |
| S | source/installed/loaded/effect/provider/consumer generation with independent provenance |
| pre | exact Unit/helper SourceCut and active shared-forward service; affected provider defined |
| post | verified native reload preserves network path and targeted consumers |
| inv | no accidental provider restart during rule reload; no elevation from UNKNOWN to PASS |
| eff | install Unit, \`systemctl daemon-reload\`, \`systemctl reload\`, kernel rule reconciliation |
| c | caller's declared consumer boundary and expected native route behavior |
| epsilon | native effects can fail; Runtime execution truth and owner replay identity preserved |
| prov | exact Git cut, installed byte hashes, loaded systemd properties, provider/process/kernel and consumer witnesses |
| unfold | shared-egress rule → service → physical Gluetun dependency → concrete mobile/Codex/etc consumers |

Unproven runtime facts remain typed scoped UNKNOWN. No claim of full mathematical refinement is made by this table; later model/proof work must state its actual abstraction relation.

## 6. Minimal task-local Circuit, not a second model

Network owns a concrete \`shared-forward-reload-circuit-r1.json\` manifest and a Network-local consumer-contract test invoked through native \`mise run contract-agent-outcome\`, describing:
- source owner Network produces an accepted forward Unit realization;
- Network/Workstation installed+loaded stage consumes source and produces a reloadable service;
- native live reconciliation stage consumes loaded service and yields kernel/provider observations;
- Network consumer acceptance stage consumes verified effect and produces scoped verdict.

Each cross-owner seam has a required Gate with declared natural verifier owner and non-widenable support scope. The Network acceptance oracle independently freezes the concrete required Gate IDs and the original accepted SourceCut; generic Composition deliberately allows caller-selected partial Gate coverage. If an Agent removes a required Gate, generic mechanical closure may still succeed for the reduced set, but Network acceptance MUST NOT. A candidate must not choose its own obligatory acceptance baseline. A missing Gate, stale digest, wrong Owner or UNKNOWN **cannot** close the circuit. A SATISFIED complete circuit still says \`domainAcceptanceEstablished=false\`, because actual Network consumer acceptance is a separate owner-owned fact.

Manifests and tests are task-local source inputs; neither Composition nor Harness discovers/executes native verifiers. Do not add an unrelated capability provider or new LEGO solely to name stages.

## 7. Actual execution and verification contract

Read before any live mutation: current remote/local SourceCut (mark remote UNKNOWN if inaccessible), installed Unit/helper, systemd loaded properties, active target/provider MainPID, namespace and current consumers.
Source validation is NOT deployment acceptance:
1. \`task substrate:shared-egress:validate\` / owner-native source suite;
2. install only the source bytes from the accepted cut through existing \`substrate:shared-egress:materialize\`;
3. assert \`ExecReload\` is loaded, then invoke existing \`substrate:shared-egress:reload\` (not \`restart\`);
4. read back exact kernel rules, namespace, Provider PID + actual unit generation and physical carrier readiness;
5. verify a specified affected Network consumer path, using its native task and actual result.
Record \`SOURCE\`, \`INSTALLED\`, \`LOADED\`, \`EXECUTED\`, \`CONSUMED\` separately. If a live command fails or changes the provider, stop the current path, record the exact state and owner-native repair/recovery; don't claim success or blindly retry.

## 8. RED→GREEN adversarial tests

Task-local tests must directly invoke existing Composition operations and prove:
- manifest compiles deterministically with nonempty required Gates;
- missing evidence does not mechanically close;
- relevant UNKNOWN does not close but is not recast as UNSATISFIED;
- wrong source digest / wrong Gate owner / widened scope is rejected;
- result for a formerly accepted manifest does not apply after mutation;
- SATISFIED required Gates yield only mechanical closure, never domain acceptance;
- duplicated Gate ID or cycle is rejected;
- mutation control: removing a required cross-owner Gate reduces required set and cannot by itself be taken as sufficient domain acceptance.
Live semantic negatives: removing native ExecReload must fail loaded-service acceptance; using \`restart\` instead of \`reload\` violates no-disruption requirement; a source test PASS without consumer witness remains incomplete. Do not execute fault injection on shared production.

## 9. Deterministic task dependency graph / execution plan

| ID | Owner | Blocking dependencies | Deliverable | Native acceptance |
| --- | --- | --- | --- | --- |
| T0 | Architecture + Network | none | This SPEC with one bounded consumer, alternatives, truth boundaries | Explicit non-goals, precise owner responsibilities |
| T1 | Network + Composition consumer | T0 | Circuit JSON under Network and direct Network contract tests using Composition APIs | RED→GREEN + negative controls; no new controller |
| T2 | Network | T1 | Exact source/install/loaded drift closure through native materialize+reload | No Gluetun cascade; source/install/load/kernel checks |
| T3 | Network consumers | T2 | Real consumer acceptance and negative control, with UNKNOWN properly scoped | Consumer native check and current evidence |
| T4 | Harness eval | T1,T3 | Frozen task corpus: conservative/doc-only, overengineering, wrong-owner, stale evidence, actual repair | pre-registered outcome metrics; compare baseline vs task-local contract without leakage |
| T5 | Composition/formal | T1,T4 | Only the smallest verified missing property in existing formal model or owner native checker | bounded proof + falsifying control + distinct implementation witness |
| T6 | owner integration | T3,T4,T5 | no-new-registry rollout into current AGENTS/Skill entrypoints as needed; remove old duplicate instructions | cross-owner consumer uptake; no duplicated state |
| T7 | owner retrospective | T6 | evaluate real completion, elapsed work, unneeded code, consumer incidents and retire leftovers | before/after comparisons and deletions justified by current consumers |

No T2/T3 deployment evidence may be inferred from T1's source tests. No T4 generalization claim from a single-agent one-turn simulation. Run T5 only for property gaps demonstrated by T1–T4, not because a formal prover exists.

## 10. Frozen Agent experiment design

Treatments:
- A: current AGENTS/Owner guide/task + native tools (baseline).
- B: same exact task, tools, permissions and budget, plus a short task-local Circuit/required result contract and progressively exposed owner evidence.

Holdout failure modes: document-only completion, test-only completion, extra framework insertion, stale evidence reuse, wrong Owner, incorrect \`restart\`, unrelated UNKNOWN blocking authorized work.
Primary endpoint: proportion of tasks accepted by independent actual consumer oracle. Secondary: false success claims, external effect count/incident, time/token/cost, useless new bytes, reversibility and required UNKNOWN reporting.
Evaluate with frozen cases, randomized order and explicit denominator; non-discriminating test results remain inconclusive, never positive evidence. Use existing \`services/harness/evals\` designs and providers rather than a generic benchmark controller.

## 11. Rollout/stop/rollback

Ship one vertical slice before more process. No global activation or installation of 3 entire Skill libraries. Promote a reusable pattern only after at least one real consumer, a negative-control test, and a second independent owner showing the pattern resolves an otherwise repeated failure.
Retire proposals that add more code than demonstrable consumer value.
Rollback is Owner-native reverse of the actually applied change, not a new orchestrator.
Exact state is held by Git + Host Work + Runtime + native checks; no duplicate \`status.json\`.

## 12. Immediate execution ledger

- T0 Network pilot SPEC: source-authored in isolated Runtime workspace; does not claim release.
- T1: implemented and tested. Two frozen Network required-Gate identities were added to task-specific independent tests. Generic Composition's intentional partial coverage remains unchanged.
- T2: installed/loaded native Unit source reconciled; systemd reload executed and kernel/provider checks PASS with unchanged Gluetun PID.
- T3: Network Gluetun, Mobile Exit server and Codex scoped proxy checks passed on final samples; transient Codex CDN timeout observed on first native run, and iOS/client process egress remains UNKNOWN.
- T4–T7: pending; no cross-model generality or new formal theorem claim.
- Remote main freshness: UNKNOWN when \`git ls-remote\` times out.
- Production acceptance: proven only for the sampled listed native consumers and properties; not a universal no-bypass or mobile-client success proof.

## 13. References / source authority

- \`.agents/skills/recursive-lego-calculus/SKILL.md\`
- \`packages/composition/docs/COGNITIVE_CIRCUIT_R1.md\`
- \`packages/composition/docs/VERIFICATION_OBLIGATION_R1.md\`
- \`packages/composition/formal/Lego21OwnerBoundary.tla\`
- \`services/harness/evals/fresh_agent_ab/PREREGISTRATION-v2-currentness.md\`
- \`platform/network/substrates/shared-egress/Taskfile.yml\`
- <https://github.com/mattpocock/skills>
- <https://github.com/affaan-m/ECC>
- <https://github.com/obra/superpowers>
