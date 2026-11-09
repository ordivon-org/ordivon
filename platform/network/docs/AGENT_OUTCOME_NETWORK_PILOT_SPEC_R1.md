# Network Agent Outcome Contract — Consumer Pilot SPEC R1

Date: 2026-11-09 (Asia/Shanghai)
Status: implementation specification; no production-completion claim
Source baseline: local \`origin/main\` = \`05fec3688cf1ae1f091a2dd080784249becbc18a\` at intake. Historical original intake; remotely fetched main source cut for this follow-up is a7d70e83945b7418f41b9636f0803d1544e84355; re-check main at actual merge.
Natural owners: Composition (task-local APIs), Network (physical network and final consumer), Workstation (systemd installation), Runtime (physical Job facts), GitHub protected main (source merge).
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

## 2A. Mathematical foundations — adopted semantics, not a new calculus

The domain language stays Recursive LEGO R2.1 and the already owned Composition
API. The theories below supply *precisely scoped proof rules*. No choice of
formal notation creates correctness without explicit assumptions, genuine
refinement to implementation and natural-consumer evidence.

### A. Design by Contract, Hoare logic and weakest preconditions

For an owner-native effect command \`C\` and a required postcondition \`Q\`,
a Hoare triple \`{P} C {Q}\` establishes only partial correctness when \`P\`
holds and \`C\` terminates. For termination/progress, prove additional
conditions, rather than silently turning a safety proof into liveness.

The engineering approach is *backward*: start with a real consumer property
\`Q\` and calculate/check the necessary \`P\` by weakest-precondition reasoning.
For Forward reload:

- \`Q\`: loaded native ExecReload, same provider generation, correct forwarding
  rules, and a specified real consumer path functioning.
- \`C\`: native materialize → daemon-reload → systemctl reload → owner readback.
- \`P\`: accepted regular source Unit/helper, active target, namespace/provider
  identities, and correctly scoped effect rights.

A green source unit test does not discharge the runtime premises of \`P\`.

Reference: Cambridge Hoare Logic lectures and Dijkstra's predicate transformers:
https://www.cl.cam.ac.uk/archive/mjcg/HoareLogic/

### B. Assume–guarantee contracts and interface refinement

Treat a LEGO interface as an explicit pair \`K=(A,G)\` of admitted environment
behaviors and produced guarantees; this is a *semantic view* of R2.1
\`pre/post/inv/eff\`, not a replacement representation.

Under a fixed trace/interface model and compatible environment, an acceptable
successor \`K1\` for \`K0\` must accept at least the old environmental behavior
and produce no behavior forbidden by the old guarantees:

\`A0 ⊆ A1\` and \`G1 ⊆ G0\`.

This subset relationship needs the relevant contract semantics and port
compatibility, not only matching JSON fields. Exact original Gate fields are
currently preserved rather than claiming to solve unrestricted semantic
implication. In the current Network pilot, a Gate may only change through an
explicit successor-contract/consumer authority decision; a candidate may add
separate independent duties but cannot delete or silently weaken original ones.

Use Pacti for tractable affine/linear contract questions, and proven local
interface methods for general temporal protocols. Do not introduce a universal
contract-algebra service.

References:
- de Alfaro/Henzinger, Interface Automata: https://doi.org/10.1145/503209.503226
- Pacti: https://arxiv.org/abs/2303.17751

### C. Temporal logic: independent safety and conditional liveness

Safety is a property of all finite prefixes, such as:

\`□(DomainAccepted → CurrentRequiredConsumerEvidence)\`

and \`□(ReloadForward → NotRestartProvider)\` within the stated owner model.

Liveness is conditional, not an unconditional promise:

\`□((actionable ∧ availableOwner ∧ fairScheduler) → ◇(effectObserved ∨ concreteBlocker))\`

The latter only follows under a maintained enabling condition and an
explicitly fair scheduler; a one-shot source test cannot prove it.

Use existing TLA+/TLC for genuinely concurrent Job/Workspace recovery, native
systemd/Quadlet dependency transitions and other temporal state machines.
Do not model a deterministic JSON list as a new distributed system.

References:
- Leslie Lamport, Specifying Systems: https://lamport.azurewebsites.net/tla/book.html
- Abadi/Lamport, existence of refinement mappings:
  https://research.google/pubs/the-existence-of-refinement-mappings-2/

### D. Abstract interpretation, partial knowledge and typed UNKNOWN

A faithful abstraction \`α\` must over-approximate the concrete behavior in
its stated scope. Its conclusion cannot simply be extended to the rest of the
system. The useful result form is scoped
\`SATISFIED(evidence)\` | \`UNSATISFIED(counterexample)\` |
\`UNKNOWN(reason,scope,missingWitness)\`, not one global boolean.

For the current circuit, Network distinguishes UNKNOWN and MISSING from
UNSATISFIED, and a stale Gate witness cannot be reclassified as fresh. An
unrelated UNKNOWN never prevents an independently authorized, reversible
action unless it is part of that action's precondition.

Reference: Patrick Cousot, abstract interpretation:
https://www.di.ens.fr/~cousot/

### E. Separation logic and locality of effects

The frame-rule intuition says that a locally verified change may preserve
disjoint unaffected resources *when its true footprint is known*. Network's
Forward helper, systemd reload and Gluetun dependency are not automatically
disjoint just because they belong to different files or Owners.

Instead of an abstract "no collateral damage" promise, bind the exact
effect footprint: installed Unit identity, native reload versus restart,
kernel rule set, provider MainPID/generation, and named consumer probes.
Where dependencies may cross the footprint, discharge that dependency
with actual readback. No claim is made to a mechanized separation-logic
proof of systemd's real dependency graph.

Reference: O'Hearn/Reynolds frame rule and local reasoning:
https://web.tecnico.ulisboa.pt/~joaofernandoferreira/2021/SoftSpec/09-separation.html

### F. Hermetic builds, immutable inputs and provenance

A reproducible source proof must bind exact candidate bytes, toolchain,
assumptions and verifier source; cached PASS is reusable only when its
dependency read-set is adequately qualified.

For the first pilot a published immutable Git commit
\`b7d64d103cf67242cbd1609e5c7df729fc187d45\` supplies an exact original
**candidate** Gate baseline. It is immutable but not, by that fact, independent
consumer approval. The Network proof reads that original regular Git blob;
the candidate cannot silently remove/optionalize/reassign/widen either
required Gate relative to this baseline. The protected Git main and the
actual consumer's review/admission must still establish baseline authority.

Use existing Git, pinned mise toolchains, Cargo/uv lockfiles and the Artifact
owner. Do not create a second immutable blob registry.

References:
- Bazel hermeticity: https://docs.bazel.build/versions/main/hermeticity.html
- Nix reproducibility: https://reproducible.nixos.org/

### G. Feedback control, STPA and failure propagation

The "Agent is overly conservative" symptom is not solved by moral
instructions: it is a mismatch between objective, sensor, controller and
actuator. Construct an STPA control structure around the *actual* Owner
boundary: Agent proposal → Owner-native effect → physical state → consumer
feedback. Identify unsafe actions caused by omission, commission, timing
and duration. Relevant Network counterexamples include:
- omitting the live reload and ending with source-only evidence;
- restarting Forward and cascading into an otherwise healthy VPN provider;
- deciding that \`active\` or \`job succeeded\` proves the affected consumer;
- retrying an uncertain external side effect without checking exact receipt.

The intervention is bounded native action and current feedback, not a new
control-plane service. Reliability budgets and observed consumer impact
decide the appropriate risk posture.

References:
- MIT STPA Handbook: https://www.mit.stamp-institute.com/handbooks
- Google SRE Workbook: https://sre.google/workbook/index/

### H. CEGAR, adversarial controls, and model-to-code refinement

Counterexample-guided abstraction refinement provides a useful development
method: express a small property; find a reachable violating state; repair the
contract/checker; repeat only until the real obligation is settled.

For the Network pilot:
1. A caller-selected Gate set can shrink and still give mechanical
   \`COMPOSITION_GATES_SATISFIED\`.
2. An independently frozen required-Gate set rejects that candidate.
3. Pinned native Z3 proves that \`independentAccept\` cannot coexist with
   missing, UNKNOWN, wrong-owner, stale or wrong-scope required obligations
   in its bounded Boolean/finite-status abstraction.
4. The same Z3 job must find the *counterexample* where the weaker
   candidate-only evaluator accepts after one original Gate is removed.
5. A source-level test exhausts 16 status/missing combinations of the
   actual Composition evaluator and asserts mechanical closure never equals
   domain acceptance.

The model is deliberately **not** a general AI-alignment or complete
systemd proof. The exact checked source, installed Unit, running provider
and real consumer still require independent verification. Do not introduce
a "formal" label that hides missing implementation refinement.

References:
- Lamport refinement and TLC: https://github.com/tlaplus/vscode-tlaplus/blob/master/resources/knowledgebase/tla-refinement.md
- CompCert implementation-level refinement: https://compcert.org/doc/

### I. Executable method borrowing — one procedure, not three frameworks

- Matt Pocock \`to-spec\`: start from consumer-facing domain vocabulary and
  existing stable test seams; \`to-tickets\` generates a dependency frontier,
  not an additional workflow database; \`implement-spec\` builds actual
  tracers on an isolated branch. Official source: https://github.com/mattpocock/skills
- ECC \`iterative-retrieval\` and \`verification-loop\`: load only relevant
  Owner evidence, reuse failing information and rerun the affected native
  acceptance. Do not install all ECC hooks or transfer automatic permissions.
  Official source: https://github.com/affaan-m/ECC
- Superpowers \`writing-plans\`, \`test-driven-development\`,
  \`systematic-debugging\`, \`verification-before-completion\`: explicit
  paths and failure conditions, RED→GREEN at each meaningful seam, then
  independently verify exact effects. Avoid mandatory user interviews,
  extra review services and per-step paperwork.
  Official source: https://github.com/obra/superpowers

**No weak-model A/B or synthetic model ranking is needed.** The system is
improved by adopting independently verified contract laws and native
consumer tests, not by asking a deliberately weaker model to repeat them.

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

## 9. Executable dependency DAG — formal-first and consumer-first

The existing GitHub PR, Network task files and current Owner APIs are the task
graph. No second task database, verifier registry or Agent orchestrator.

| ID | Natural owner | Dependencies | Deliverable and independent acceptance |
| --- | --- | --- | --- |
| N0 | Network/architecture | none | Exact remote/source, original consumer duties, upstream theory and existing method Skills; avoid duplicates |
| N1 | Network consuming Composition | N0 | Current Cognitive Circuit + obligation tests; stale/foreign/UNKNOWN/missing controls via the existing Composition API |
| N2 | Network formal | N1 | Frozen original Gate SourceCut and pinned Z3 bounded safety property with reachable candidate-only false-acceptance counterexample |
| N3 | Network code consumer | N1,N2 | Exhaust all 16 states of the two-Gate real Composition evaluator; no domain acceptance from mechanical closure |
| N4 | Network + Workstation | N1 | Real source-to-installed-to-loaded, systemd reload, kernel and provider continuity; use existing native Task |
| N5 | affected Network consumers | N3,N4 | Gluetun/CodeX proxy/Mobile Exit server readiness; keep iOS and Windows application-level exit UNKNOWN if not observed |
| N6 | protected GitHub main + consumer Owner | N2,N3,N5 | Normal protected integration of existing PR #1982, code analysis, exact merge SHA and current scoped consumer acceptance |
| N7 | actual affected Owners | N6 | Reuse only demonstrated missing contract seams; delete superseded instructions or adapters instead of global rollout |

Source proofs N1–N3 cannot substitute for physical effects N4–N5.
N4–N5 are stateful observations and must be rechecked when the live system
changes. N6 remains open while PR is OPEN regardless of how many CI jobs pass.

### File-exact implementation steps (Matt/Superpowers/ECC)

1. N2 source and SMT: modify
   **platform/network/formal/agent_outcome_refinement.py**; use
   **mise run formal-agent-outcome**. Start with a false-acceptance
   counterexample from a removed required Gate and reject missing, optional,
   wrong Owner, widened scope, weakened guarantee and wrong circuit identity.
   Use the pinned Z3 5.3.2 in tools/formal, not a downloaded second solver.
2. N3 code refinement: in
   **platform/network/acceptance/lifecycle/test_shared_forward_contract_circuit.py**
   compare the candidate with the immutable published pilot Git blob, then
   exhaust SATISFIED, UNSATISFIED, UNKNOWN and MISSING for both Gates using
   actual Composition code. Run **mise run contract-agent-outcome**.
3. N2+N3 CI: in **platform/network/mise.toml** reuse the existing Network
   CI dependency list. Do not add a provider, runner, global check registry,
   or new correctness-status vocabulary.
4. N4 live effect: use the existing shared-egress validate, materialize,
   reload and verify tasks, then actual loaded ExecReload, kernel and
   Gluetun MainPID readback. The initial production correction already
   occurred: don't repeat a mutation merely because an algorithm says so.
5. N5 consumers: native Gluetun, Mobile Tailnet Exit and Codex scoped
   proxy verification with honest scope. Service-side READY is not proof
   the mobile/iOS public exit or every Windows desktop process used it.
6. N6 branch/release: update existing PR #1982, use protected GitHub
   checks and independent consumer/source review, then read back the actual
   merged SHA and deployed SourceCut where applicable. Candidate content
   cannot approve its own original contract merely by quoting an older SHA.
7. N7: consult existing Host, Runtime and Harness Owner specs; adopt the
   method only at independently demonstrated gaps. Do not run weak-model
   comparisons, A/B rankings, or an unrestricted multi-Agent evaluation.

## 10. Formal obligations and explicit non-claims

**O1 — Source contract preservation.** All original independently required
Gate IDs remain required, with identical producer/consumer, assumptions,
guarantees, verifier Owner and support scope. Additional independent obligations
may be proposed; inherited semantics can change only by an accepted
successor-contract decision of the natural consumer.

**O2 — Consumer authority.** In the bounded Z3 abstraction, independent
acceptance needs every original Gate to be present, SATISFIED, fresh,
correct-owner and correct-scope, *plus* an independently observed consumer
outcome. The candidate cannot select a smaller required set to satisfy it.

**O3 — Non-vacuous falsification.** A weakened candidate-only rule must admit
the removed-Gate counterexample; the independent rule rejects it. A model
where the failure state is unreachable by definition alone is insufficient.

**O4 — Implementation refinement.** Compare the abstract closure law to the
16 actual code combinations of two Gates with four observations each.
Generic mechanical closure stays separate from domain completion. This is
finite code-path qualification, not proof over all circuits or networks.

**O5 — Physical effect.** Source, installed, loaded, executed and consumed
are separate coordinates. Native reload must preserve actual provider
identity and satisfy named consumer probes, not just return process exit 0.

**O6 — Epistemic correctness.** UNKNOWN has a reason, proposition and missing
witness; it is never silently promoted to PASS or FALSE. Unknown external
effects require reconciliation before replay; unrelated UNKNOWN cannot
become a universal execution freeze.

**O7 — Conditional liveness.** Under actual available Owner interfaces and
appropriate fairness, executable work should produce an observed effect
or an observed concrete blocker. This is a conditional system property,
not a guarantee that every proposed task has a solution.

**O8 — Trusted boundary.** The published pilot cut is an immutable original
source witness, **not** an automatically authorized/approved consumer baseline.
An Agent able to edit its own CI and test files could still weaken checks;
protected main/required checks, independent natural Owner verification and
current installed readback are required. Formal syntax itself supplies no
security authority.

**Stop rule:** finish at exact consumer acceptance or actionable scoped
UNKNOWN. Never replace a real delivery with a new architecture report,
or a model check with a statement about live Gluetun traffic.

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
- N2/N3: pinned native Z3 finite safety proof, non-vacuity counterexample and 16-state real-code refinement are implemented in this follow-up; reverify against the final PR head.
- N6/N7: protected integration and cross-Owner re-use/retirement remain separate actions. No weak-model rankings, universal theorem or end-user client egress claim.
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
