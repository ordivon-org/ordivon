# Agent-native Formal Delivery Contract — Spec R1

Date: 2026-11-09
Status: DECIDED SPEC; phased implementation, not a live deployment or completed domain outcome.
Initial SourceCut: 3b43977e682d8c7668f6371ffd998c7821e4312a
Natural owners: repository mechanics (source policy), Composition (contract/gate), Host (Work semantics), Harness (Run), Runtime (effects), Gateway (routing), domain owners (outcome).
Consumer: every consequential Ordivon change delivered by a human or Agent through current source, GitHub CI, installed Owner tools and the relevant domain acceptance.

## 1. Purpose and non-goals

Make Agent proposals replaceable. A less capable or overly conservative model may explore poor options, but it must not convert its own preference into Ordivon authority, reduce or invent acceptance obligations, infer success from planning/testing alone, or bypass a natural Owner. The system should allow real authorized work to proceed, including deletion and substitution, rather than demanding additional review rituals for harmless steps.

Do not: install Matt/ECC/Superpowers as duplicate global frameworks; create an Agent Service, task database, verifier registry, global LEGO service, extra control broker, universal planner, or new approval process; impose a property proof on each file; conflate all formal tasks with real-world acceptance; require an experiment comparing model abilities. Do not rewrite existing language-native tests or change production permissions as part of this architecture wave.

## 2. Source and adopted mechanisms

1. Current Ordivon: root AGENTS.md, tools/repo/owners.toml and dependency_contracts.toml, tools/repo/check_architecture_docs.py and test_lego_graph_laws.py; packages/composition existing Cognitive Circuit, Verification Obligation, Successor Contract and TLA+ Owner boundary; domain Owner-native consumers. Structure R2 remains only partially deployed.
2. Matt Pocock Skills (https://github.com/mattpocock/skills): to-spec captures decided domain language, to-tickets builds blocking-edge tracer bullets, implement-spec executes ready tasks, domain-modeling keeps concepts precise, and code-review independently checks standards and spec fidelity. Use existing Host Work/GitHub issues rather than a second tracker.
3. ECC (https://github.com/affaan-m/ECC): contract-first boundaries, delivery-gate acceptance criteria, selective instructions and compact context/decision handoff. Import method, not its full plugin, hooks, agents, or redundant memory.
4. Superpowers (https://github.com/obra/superpowers): writing-plans with exact paths/commands/expected results, red-green TDD, systematic-debugging, verification-before-completion, and one final review. Use Ordivon Runtime/Git native isolated worktrees.
5. Formal foundations: R2.1 full typed ell = (I,O,S,pre,post,inv,eff,c,epsilon,prov,unfold); assume-guarantee refinement, non-vacuity, scoped three-valued evidence; native Lean/Z3/TLA+/Hypothesis or compiler tests selected per property, never all for every change.

All external Skills are advisory. Existing Owner interfaces, checked-in source, CI and real consumer outputs remain authoritative for their own scopes. Source code and documentation are not themselves production currentness.

## 3. Typed semantic projection, not a new persistent object

A task-local view T consists of:
- Goal/phi: the user or domain's observable desired result, plus negative criteria.
- Owner and Consumer: who owns the effect/fact, who independently observes whether it is useful.
- SourceCut: exact relevant Git/package/provider revision; current installed generation is a separate observation.
- ExistingContract: one existing Owner-native type or public contract, or an explicitly open gap.
- Obligations: property-scoped composition gates and independent falsifiers as existing Owner/Composition inputs.
- EffectAuthority: current natural Owner's grant, resource scope and executable operation; no inherited Skill authority.
- Witness: exact consumer-produced observation/readback, with source, environment, identity and time.
- Standing: SPECIFIED, MODEL_VERIFIED, CODE_REFINED, INSTALLED, EXECUTED and CONSUMED are independent facets. PASS/FAIL/UNKNOWN is per obligation, never an unqualified global completion flag.
- NextAction: immediate safe executable step if permitted, or one precise missing premise and how to establish it.

These are projections over Host Work/Topic, Composition gate inputs, Runtime receipts, Git and Owner-native domain facts. They do NOT require another JSON file, SQL table or registry per task. A declared independent LEGO uses all 11 R2.1 coordinates in its natural Owner's existing contract carrier.

## 4. Formal obligations and prohibited inferences

F1 — Source plans have no authority:
  For every source-only LEGO graph node or slice x,
  SourceProjection(x) implies not EffectAuthority(x), not DeletionAuthority(x),
  not PromotionAuthority(x), not DomainAccepted(x), not ProofReuseAuthority(x).
  Existing explicit false fields remain legal. Missing fields mean no claim.
  A future Agent cannot manufacture authorization by adding a true flag to a plan.

F2 — Verification is scoped:
  ModelPASS(x, psi) does not imply DomainPASS(x, phi) unless an owner-qualified
  bridge B proves psi -> phi over the required environment/readset. Code refinement
  and physical consumer acceptance are distinct obligations. UNKNOWN is never
  silently promoted to PASS or converted to FALSE.

F3 — Task completion is consumer-rooted:
  AcceptDomain(x) requires at least one applicable current independent consumer
  witness, all required consumer obligations discharged and the natural Owner's
  acceptance rule. Successful Tool/Job/Run/CI/proof is neither sufficient nor an
  automatic failure if another evidence dimension remains open.

F4 — Replacement preserves obligations:
  Substitution B for A may not strengthen any consumed precondition or weaken any
  required guarantee; it must preserve identity, state, effect and provenance
  obligations and requalify changed SourceCut/readsets. Mechanically closed gates
  cannot grant promotion or external effects.

F5 — Progress is enabled by evidence:
  If a task has an allowed safe native operation and an unsatisfied goal, an
  Actionable next step is the default. Missing facts trigger observation, bounded
  source/consumer inspection, or an isolated experiment — not a blanket refusal.
  Unknown effect authority does not block read-only investigation but does block
  the effect requiring that authority.

F6 — No self-certifying evidence:
  The candidate Agent cannot change the independent consumer oracle merely by
  changing its own implementation. A self-declared evidenceRef or schema-valid
  receipt is at most DECLARED; its source, Owner, currentness and consumer readback
  must be established at the appropriate acceptance boundary.

This R1 reform does not promise a formal proof that arbitrary open-ended software
implements phi. The machine guard in T1 establishes F1 at the current source-graph
boundary; later tickets carry F2-F6 to existing real consumers.

## 5. Acceptance criteria (contract, scenario, oracle)

AC-01 SOURCE AUTHORITY: Given an Owner LEGO R1 planning graph, inserting
  deletionAuthorized=true, effectAuthorized=true, promotionAuthorized=true,
  domainAccepted=true, proofReuseAdmissible=true or deploymentAuthorized=true
  into a node or slice must make the existing architecture checker reject it.
  An explicit false must remain admissible; an unknown or source-only status
  cannot be made a positive authority. Verify with test_lego_graph_laws.py and
  the native checker. No new schema/registry.

AC-02 NON-VACUOUS CONTRACTS: An optional-only or UNKNOWN required composition
  gate cannot produce required mechanical completion; candidate-created
  evidence does not establish domain outcome. Preserve existing successor
  contract + gate tests, native Composition verification and negative controls.
  Do not turn source plans into consumer proof.

AC-03 OWNER BOUNDARY: A new cross-Owner effect/import must go through the
  producing Owner public contract or fail the native check. Reuse the active
  dependency checker and PR #1963 when qualified; do not fork that code.

AC-04 EFFECT IDENTITY: A Runtime Job's success, a Harness Run's proposal
  and a Host Work's completion text do not substitute for external effect
  readback or domain acceptance. Qualification is Owner-native, source-bound
  and requires an actual negative/failure control where material.

AC-05 REPRESENTATION: Every independently DECLARED/ADMITTED R2.1 LEGO has the
  complete typed 11-tuple in its natural Owner/source-backed contract, or
  explicit scoped UNKNOWN. No mandatory contract record for each file/Tool.

AC-06 PROGRESS: Legitimate isolated inspection, testing, local refactoring and
  source retirement remain feasible without central approvals. Only the actual
  effect authority and irreversible transitions require owner-specific fencing.

AC-07 NO NEW SHADOW SERVICES: No independent Agent Task database, verifier
  registry, autonomous source of truth, new system-wide scheduler or duplicated
  Skill installation is introduced. Existing Host/Runtime/Git/Composition
  remain source owners for their specific obligations.

AC-08 DELIVERY: Every landed change has exact base/head SHA, native test
  results and reviewer/consumer standing. NOT_RUN/TIMED_OUT/ENV_BLOCKED are not
  PASS. Only verified GitHub PR/merge/deployment can be claimed as such.

## 6. Implementation task graph

T0 SPEC AND SOURCECUT (repo; no dependencies)
  Files: docs/architecture/AGENT_FORMAL_DELIVERY_SPEC_R1.md, current root
  AGENTS.md and native R2.1 contract reference.
  Output: this decided specification, exact prohibitions, task owners,
  negative controls and no duplicate authority. Verify exact main, source
  paths and existing Composition contracts. Retain as one specification,
  not a second knowledge catalog.

T1 SOURCE-ONLY LEGO AUTHORITY FITNESS (repo; depends T0)
  Files: tools/repo/check_architecture_docs.py,
  tools/repo/test_lego_graph_laws.py.
  Interface: existing validate_owner_lego_graph(plan).
  RED: falsifying tests inject forbidden positive authority booleans into
  real current node and slice, without changing their other valid fields;
  check currently accepts them. GREEN: reject those claims through this
  single native validator, preserve false/absent and all actual plans.
  Expected: pytest affected tests PASS, check_architecture_docs.py PASS.
  No new model registry or per-node schema.

T2 EXISTING COMPOSITION FORMAL/CONSUMER BRIDGE (Composition; depends T1)
  Files to inspect: packages/composition/src/ordivon_composition/
  successor_contract_r1.py, verification_obligation_r1.py,
  formal/Lego21OwnerBoundary.tla, tests/test_successor_contract_r1.py,
  tests/test_verification_obligation_r1.py.
  Do not reimplement gates already present. Demonstrate current exact
  assumptions, non-vacuity counterexamples and owner-native results.
  Add implementation refinement / negative test only for a discovered
  falsifiable gap. Verification: Composition native verify plus current TLC
  owner-boundary model when materialized. Expected: qualified model and
  source claims separated from installed/domain claims.

T3 TASK HANDOFF WITHOUT NEW WORKFLOW ENGINE (Host/Harness; depends T0,T2)
  Existing carriers: services/host Work Snapshot/Topic/Message, Harness
  RunContract and task-space-reentry Skill.
  Define at the existing caller seam when goal, source, active consumer,
  actual effect identity, next action and evidence status are projected.
  No new Task table; use existing Host CAS and Run continuity.
  Acceptance: plan-only message does not count as evidence of completed
  external effect; a valid read-only next action is not blocked by missing
  effect credentials. Verify with real disposable PostgreSQL and caller tests.

T4 EXECUTION AND CURRENTNESS (Runtime/Gateway; depends T2,T3)
  Bind current SourceCut and operation ID to Runtime Job/Attempt/result,
  Gateway owner route and real provider effect. Preserve response-loss
  reconciliation, no blind retry, UNKNOWN on ambiguous effects.
  Acceptance: real bounded native recovery/readback and counterexample
  against stale/foreign owner receipt, selected existing native tests.

T5 DOMAIN ACCEPTANCE (Game/Capital/Media/Artifact etc.; depends T2,T4)
  Each domain names one genuine final consumer predicate and returns
  precise standing. Adopt upstream-native consumer tests (e.g. Godot/Bevy
  gameplay; Finance PG Paper accounting; native media export).
  Do not impose one cross-domain business definition. A fake Agent SUCCESS,
  empty report, or test-only loop must not establish domain completion.

T6 RETIREMENT AND EVOLUTION (repo + natural Owners; depends T1-T5)
  Cross-check typed SourceCut, consumer graph, unique unpublished value,
  active effect/recovery and retention obligations; perform justified
  subtraction using Git, Runtime and Owner-native deletion APIs.
  No per-document classification bureaucracy. Current evidence and
  actual consumer determine retention.

## 7. Execution discipline adopted from upstream Skills

- Before implementation: source truth, natural owner, spec, test seam, known
  counterexample, exact source cut. Use Matt to-spec/to-tickets as mental
  discipline; existing Host/Git tracks work, not a parallel ticket system.
- Per task: reproduce RED at actual public/native seam, minimal GREEN,
  re-run affected Owner tests, inspect diff. For formal claims, report
  specification/model/source refinement/real consumer as separate results.
- For architecture-changing work: Matt two-axis review (Standards and Spec),
  ECC contract-first + delivery acceptance, Superpowers verification-before-
  completion. Automated machine checks run in existing CI, not extra hooks.
- On a blocker: take an allowed next observation/execution; if the spec is
  contradicted, record a bounded ruling in existing Work/PR, preserve the
  consumer outcome, then continue. No mandatory human intervention for a
  reversible, already authorized step.
- Release: commit isolated worktree, run native and repo checks, open PR;
  keep merge, installed and domain outcomes distinct. Do not hide skipped
  or timed-out checks.
- No weaker-model experiments: rely on upstream proven methodology and
  deterministic contract/negative tests of the actual code.

## 8. Rollback, failure, and definition of done

T1 is accepted only when its RED case was witnessed, GREEN source guard passes,
existing Owner graph cases remain admissible, and native repo verification
executes on a clean committed SourceCut. If current protected CI has a
pre-existing unrelated failure, report its exact stage; no false PASS.

Later T2-T6 have independent PR/Owner acceptance. The cross-system program
is not DONE until at least one source-to-installed-to-consumer end-to-end
path has independently established the required result and remaining
obligations are explicit. Root source governance cannot declare domain DONE.

Rollback of each isolated change uses normal Git revert; do not reset
protected main, drop live Work/Workspace, or alter production authority.
