# Ordivon Recursive LEGO Calculus R1

Date: 2026-09-29
Status: FORMALIZED CANDIDATE / PROSPECTIVE EXTERNAL VALIDATION REQUIRED

## Purpose

This document consolidates the current Ordivon LEGO method into one typed, contract-preserving, evidence-driven problem-solving calculus.

It does **not** define intelligence, replace mature disciplines, or claim that the world is literally made of LEGO. LEGO is a task-conditioned operational representation used to make a problem composable, executable, verifiable, and revisable.

The calculus integrates the existing Ordivon LEGO lineages — systems engineering, DSM, compositional contracts, causal intervention, reliability analysis, feedback/control, information flow, exploration/search, C-K design, evolutionary search, and organizational cybernetics — without absorbing their specialist authority.

## 1. Scope and core stance

The object of this calculus is a problem-solving architecture:

`discover -> represent -> generate -> compose -> model -> systemize -> solve -> verify -> attribute -> optimize/repair`

This is a recursive graph, not a mandatory waterfall. Evidence may send work back to the earliest abstraction layer whose contract is invalid.

Core stance:

1. representation is not reality;
2. verifier output is not truth by definition;
3. LEGO composition is partial and contract-gated;
4. methods attach only when their assumptions fit the system;
5. verification must produce structured evidence sufficient for localization;
6. encapsulation is admitted by net benefit, not assumed complexity reduction;
7. architecture/configuration spaces are dependent, not Cartesian;
8. self-refinement requires an external anchor that the current optimizer cannot rewrite.

## 2. Problem and true specification

Use one symbol for one responsibility.

A problem instance is

`p = (w0, phi, Gamma)`

where:
- `w0` is the relevant initial world state;
- `phi` is the true target specification;
- `Gamma` is the hard constraint/authority/safety envelope.

The true solution set is

`X*_p = { x | phi(x; w0, Gamma) = 1 }`.

`phi` is independent of any verifier. A verifier measures or establishes evidence about `phi`; it does not define truth merely by returning PASS.

## 3. Discovery is a search problem with gates

The world does not normally arrive as a pre-scoped problem. Problem discovery searches candidate problem formulations `p in P(W)`.

Treat discovery as a multi-objective decision over at least:
- importance / expected value;
- tractability;
- verifiability;
- information gain;
- cost / opportunity cost.

Use a Pareto view unless a domain authority supplies a legitimate scalar objective.

Before expensive solving, the discovery gate should establish:
- evidence-grounded boundary;
- operationalizable goal/specification;
- explicit unknowns and assumptions;
- feasible verification path.

A discovery verifier `nu_D` checks the problem framing itself. It does not prove that the eventual answer is correct.

## 4. Representation as operationalization

A representation is not a label change. It turns a problem into a form on which valid operators become available.

Represent a transformation as

`rho = (alpha_rho, gamma_rho, phi_rho, epsilon_rho)`

where:
- `alpha_rho` is abstraction/encoding into a working representation;
- `gamma_rho` is concretization back to a set of compatible originals;
- `phi_rho` is the transformed specification;
- `epsilon_rho` records approximation / information-loss / leakage obligations.

Lossy representations need not have a single-valued inverse.

Minimum consistency is

`p in gamma_rho(alpha_rho(p))`

or an explicitly qualified approximate analogue.

A representation change is admissible only when the transformed solution/specification soundly refines the original. In the simplest single-valued recovery form:

`phi_rho(x') => phi(back(x'))`.

Representation search therefore optimizes estimated total solve cost, transform cost, and representation risk **subject to specification preservation**. It is legitimate to change representation instead of merely reasoning longer inside one representation.

## 5. Generator family, not an assumed basis

For a representation `rho`, choose a generator family

`G_rho = {g1, ..., gn}`

that provides the compositional vocabulary used to model the problem.

Do not call it a mathematical basis unless independence and completeness are actually established. Changing `G_rho` is changing the generative language used for the problem, not claiming a linear change of basis.

## 6. LEGO contract

A LEGO is a typed, contracted, encapsulatable, qualifiable, composable operational abstraction.

Use the conceptual schema

`ell = (I, O, S, pre, post, inv, eff, c, epsilon, prov, unfold)`

where:
- `I`: input type/interface;
- `O`: output type/interface;
- `S`: internal state type;
- `pre`: precondition / environmental assumption;
- `post`: postcondition / guarantee;
- `inv`: invariants to preserve;
- `eff`: external effects and authority-relevant effect semantics;
- `c`: cost/resource model;
- `epsilon`: abstraction/error/leakage envelope;
- `prov`: provenance and qualification;
- `unfold`: a route to reopen hidden structure when diagnosis requires it.

This schema is conceptual. Domain-native standards/contracts remain authoritative when they already provide a better representation.

## 7. Typed partial composition

Composition is a partial operation:

`o : L x L ->partial L`.

For `ell2 o ell1` to be defined, establish at least:
- output type of `ell1` is compatible with/refines the input type of `ell2`;
- `post1` discharges `pre2` or the equivalent assume-guarantee obligation;
- invariants are jointly satisfiable;
- effects, policy, identity and authority obligations do not conflict;
- any composition-specific seam contract is discharged.

If composition is defined, the composite must itself expose a valid LEGO contract. This is **type-level closure**, not proof that the implementation is correct in the world.

Operators are partial for the same reason. A legal operator program is not an arbitrary string from an operator alphabet. `Pi_legal(s)` contains only sequences whose preconditions hold at every intermediate state.

## 8. Recursive encapsulation

A valid composite may be encapsulated and reused as a higher-order LEGO when its internal complexity is hidden behind a sufficient contract and an `unfold` route remains available.

Encapsulation does not imply monotonic complexity reduction. Use a net-gain criterion such as

`G_enc = DeltaC_visible - C_glue - lambda * L_leak - mu * C_diagnose`.

Admit an encapsulation only when:
- `G_enc > 0` for the task;
- required specifications/invariants are preserved;
- leakage/error is inside its envelope;
- provenance and verification remain traceable;
- diagnosis can unfold the abstraction when necessary.

## 9. Model and system as LEGO refinements

A model is a LEGO refinement that adds inference/prediction/simulation semantics.

A system is a further refinement that adds state transition, effects, feedback and recovery semantics.

Use

`Primitive -> Composite -> Model -> System`

as a refinement relation, not as a claim of set inclusion or universal hierarchy.

## 10. Method LEGO as a higher-order operator

A method LEGO is not merely `State -> State`. It is a strategy that produces a legal operator program for a compatible system/problem/evidence context:

`mu : (s, p, e) ->partial Pi_legal(s)`.

Attach method `mu` only when `Req(mu)` is satisfied by `Cap(s)` and the relevant authority/safety conditions hold.

Examples of specialist method families include optimization, Bayesian inference, causal intervention, control, formal methods, statistical analysis, search, design theory, FMEA/FTA and STPA. Their canonical Skills/disciplines remain the natural owners of their own assumptions, procedures and stop conditions.

## 11. Solver semantics

Solving is the search for a legal program `pi in Pi_legal(s)` whose realized candidate satisfies the problem specification.

The abstract feasibility statement is

`exists pi in Pi_legal(s) : phi(pi(s))`.

In real systems, `phi` is often only partially observable, so solving must be paired with qualified verification rather than equating execution success with semantic success.

## 12. Verifier, evidence and UNKNOWN

A verifier is

`nu(x) = (v, e, q)`

where `v in {PASS, FAIL, UNKNOWN}`, `e` is structured evidence, and `q` is a qualification/uncertainty certificate.

For a deterministic formal verifier, soundness may be stated as

`PASS => phi(x)`.

For a statistical/empirical verifier, use a bounded false-acceptance statement such as

`Pr[nu(x)=PASS and not phi(x) | H_nu] <= delta_nu`.

Completeness can be separately bounded when meaningful.

Evidence should be rich enough for localization. A useful conceptual structure is:
- observations;
- claims;
- trace;
- locus `(component, port, contract, transition)`;
- counterexample/witness;
- provenance;
- uncertainty.

`UNKNOWN` is an epistemic state, not weak FAIL. Its valid continuations include:
- acquire more evidence;
- change/add an independent verifier;
- re-observe;
- re-represent if the current representation hides the needed variable;
- escalate to an external authority or human when required.

## 13. Attribution and earliest broken abstraction

Attribution consumes structured evidence, not only a PASS/FAIL label:

`Atr(e, s, pi) -> {(locus_i, weight_i, support_i)}`.

Use the evidence to identify the earliest abstraction layer whose contract or assumptions are invalid:

`L_fail* = earliest layer with a justified violation/currentness failure`.

Typical repair targets:
- problem definition/discovery;
- representation;
- generator/decomposition;
- composition/contracts;
- model;
- system;
- method/operator program;
- authority/binding/execution;
- evidence/verifier.

Repair from `L_fail*`; do not reflexively restart the entire pipeline or blindly retry execution.

## 14. Optimization after feasibility

`Solve != Optimize`.

First establish a feasible/qualified candidate. Then optimize over explicit objective(s), preferably as a Pareto problem when values conflict.

The architecture/configuration space is dependent. A suitable conceptual form is

`Xfrak_p = Sum_{rho in Rep(p)} Sum_{G in Gen(rho)} Sum_{Lambda in Comp(G)} Sum_{m in Model(Lambda)} Sum_{s in System(m)} (Theta_s x Pi_legal(s))`.

The dependent sums matter because parameter spaces, legal operators and available methods depend on earlier architectural choices.

Optimization may therefore change:
- representation;
- generator family;
- composition;
- model;
- system architecture;
- method;
- parameters.

## 15. Bounded self-reference

The framework itself can be represented as a problem object. This permits controlled process-level and representation-level refinement, but not unconstrained self-certification.

Let the current framework be `F_k` and a candidate refinement be

`F_{k+1} = Refine(F_k, e_k)`.

Evaluate meta-refinement against an external anchor envelope

`A* = (Phi*, B*, M*, H*)`

containing, as appropriate:
- frozen top-level specifications;
- holdout and/or real-world tasks;
- measurement pipelines outside the current mutable domain;
- human/external authority.

For the current refinement epoch require

`A* notin dom(Refine)`.

Accept only inside a bounded trust region with no material anchor regression beyond declared tolerance; otherwise rollback.

This does **not** prove global monotonic improvement, convergence, or existence of a fixed point. Meta-work requires stopping rules such as bounded meta depth, low expected marginal benefit, excessive meta cost, or explicit external stop.

## 16. Canonical recursive control flow

The conceptual control graph is:

`DISCOVER -> REPRESENT -> GENERATE -> COMPOSE -> MODEL -> SYSTEMIZE -> ATTACH METHOD / SEARCH LEGAL PROGRAM -> EXECUTE -> VERIFY -> ATTRIBUTE -> OPTIMIZE OR REPAIR`

Evidence may return to any earlier justified layer:

`VERIFY -> SOLVE | SYSTEM | MODEL | COMPOSE | REPRESENT | DISCOVER`.

The governing principle is:

**Evidence determines the earliest broken abstraction; repair from there.**

## 17. Relationship to existing Ordivon method Skills

This calculus is the cross-layer scaffold. It must not duplicate specialist method procedures.

Use existing Skills for their natural questions, including:
- `systems-engineering` for system boundary/context;
- `design-structure-matrix` for decomposition/coupling diagnostics;
- `compositional-contracts` for assume-guarantee composition/substitution;
- `causal-intervention` for causal claims;
- `fmea-fta` and `stpa` for failure/hazard structures;
- `feedback-control` for dynamic regulation;
- `information-flow-analysis` for information influence boundaries;
- `ck-design`, `evolutionary-search`, and `exploration-policy` for distinct generative/search regimes;
- `organizational-cybernetics` for viable organizational recursion;
- `project-kernel-decomposition` for project-native transferable kernels.

`method-router` remains a thin selector. It may route a cross-layer problem to this calculus, while this calculus may ask the router for a specialist method **only for a bounded subproblem**. Avoid recursive routing loops.

## 18. Non-claims

- LEGO is not an ontology of reality.
- A name, diagram or model is not evidence of correctness.
- A verifier is not truth merely because it emits PASS.
- A valid interface shape does not establish substitutability.
- Encapsulation does not necessarily reduce total complexity.
- Optimization against an internal evaluator does not establish real-world improvement.
- Self-reference does not imply autonomous or monotonic self-improvement.
- This calculus is not a definition of intelligence.

## 19. Prospective validation requirement

R1 is formalized but not yet externally validated as a superior workflow.

A valid prospective comparison should freeze a real task, source inputs, specification and external anchor, then compare the earlier workflow with this calculus on measures such as:
- semantic success / acceptance;
- invalid operator/composition rate;
- rework count;
- wall/tool/resource cost;
- earliest-failure localization accuracy;
- representation changes and their effect;
- verifier disagreement / UNKNOWN handling;
- regression against holdout or real-world anchor tasks.

Only after such evidence should stronger performance claims be promoted.

## Historical/local lineage

This R1 supersedes using the earlier LEGO documents as a complete cross-layer calculus, while preserving them as historical and specialist foundations:
- `catalogs/knowledge/lessons/lego-theory-foundations-r1.md`;
- `meta/next/docs/LEGO_THEORY_WAVE2_R1.md`;
- `meta/next/docs/LEGO_THEORY_WAVE3_R1.md`.

The `meta/next` documents are historical evidence and are not reactivated as an architecture owner by this synthesis.
