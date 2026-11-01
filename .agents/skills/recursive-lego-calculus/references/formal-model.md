# Recursive LEGO Calculus — formal model R2.1

This reference gives the compact formal contract behind `recursive-lego-calculus`. Symbols are deliberately single-purpose. R2.1 separates truth/specification from verification, system specification from runtime state, representation validity from vacuous refinement, and linear repair from the more general minimal broken frontier of a recursive dependency graph.

## Symbols

- `W`: world / environment space.
- `Pfrak`: problem-instance space.
- `p=(w0,phi,Gamma) in Pfrak`: one admitted problem instance.
- `X_p`: candidate solution/outcome space for `p`.
- `X*_p subseteq X_p`: true/specification-satisfying solution set induced by `phi`.
- `rho`: representation contract.
- `R_rho`: working-representation space for `rho`.
- `X_{rho,p}`: candidate solution space under representation `rho` for problem `p`.
- `G_rho`: generator family for `rho`.
- `ell`: LEGO contract.
- `m`: model LEGO.
- `Sigma`: system LEGO / system specification.
- `theta in Theta_Sigma`: one concrete parameter/configuration choice for `Sigma`.
- `sigma_t in State(Sigma,theta)`: one runtime/system state under that instantiated system.
- `kappa`: partial operator over states admitted by the instantiated system.
- `mu`: method LEGO / higher-order strategy.
- `Pi_legal(Sigma,theta,sigma0)`: legal operator programs from one initial state.
- `pi`: one legal operator program.
- `nu`: verifier.
- `psi_nu`: exact predicate/obligation encoded for verifier `nu`; it may equal `phi` but need not.
- `e`: structured evidence.
- `Ffrak`: the recursive problem-solving framework.
- `A*`: external anchor envelope for meta-refinement.

## Discovery and problem admission

The world does not normally arrive as one already-correct problem statement. Discovery searches candidate framings `Cand(W) subseteq Pfrak` and MUST keep framing evidence separate from later solution evidence.

A framing may be compared by a multi-objective vector such as

`J_D(p)=(Importance(p),Tractability(p),Verifiability(p),InformationGain(p),-Cost(p))`.

Unless a domain authority provides a legitimate scalar utility, use a Pareto/policy selection rather than inventing hidden weights. A discovery gate `nu_D` should at least check that the boundary is evidence-grounded, the goal/specification is operationalizable, important unknowns/assumptions are explicit, and a feasible verification path exists. Discovery acceptance makes `p` admissible for solving; it does not establish that `phi` is satisfied.

## Problem and truth/specification semantics

`X*_p = {x in X_p | phi(x;w0,Gamma)=1}`.

The target predicate `phi` is logically prior to the verifier result. Here "true/specification-satisfying" means true relative to the admitted normative/domain specification `phi`; the calculus does not claim metaphysical access to truth.

A verifier may operate on an encoded predicate `psi_nu`. If it directly checks `phi`, take `psi_nu = phi`. Otherwise its qualification/evidence MUST include a bridge/refinement obligation sufficient for the intended claim.

Verifier: `nu(x)=(v,e,q)`, with `v in {PASS,FAIL,UNKNOWN}`. The qualification object `q` MUST identify the actual target predicate, guarantee kind, assumptions, model/representation identity and any bridge used to relate `psi_nu` to `phi`.

### Deterministic soundness and bridge

Local checker soundness is

`nu(x).v = PASS => psi_nu(x)`.

An end-to-end claim about the problem specification additionally requires a justified bridge

`B_nu : psi_nu(x) => phi(x)`

for the accepted scope. Without `B_nu`, a formal-tool PASS supports `psi_nu`, not automatically `phi`.

### Procedure-level false-acceptance control

For a randomized/statistical procedure and declared target predicate `T_nu` (either `phi` or an explicitly bridged `psi_nu`), one possible guarantee is

`sup_{x : not T_nu(x)} Pr_nu[nu(x).v = PASS | x,H_nu] <= alpha_nu`.

This is a property of the verification procedure under assumptions `H_nu`.

### Conditional reliability of PASS

A different guarantee is conditional false-discovery/reliability:

`Pr[not T_nu(x) | nu(x).v = PASS,H_nu,D_nu] <= delta_nu`,

where `D_nu` denotes the calibrated population/base-rate model needed to make that conditional probability meaningful.

Do **not** infer conditional reliability from a joint bound such as

`Pr[nu(x)=PASS and not T_nu(x)] <= delta`.

Do not infer either probabilistic guarantee from the other without the additional assumptions required by probability theory.

### Optional completeness / false-rejection control

When meaningful, record separately, for example:

`sup_{x : T_nu(x)} Pr_nu[nu(x).v = FAIL | x,H_nu] <= beta_nu`.

## Representation and specification preservation

`rho=(alpha_rho,gamma_rho,phi_rho,epsilon_rho,beta_rho)`.

- `alpha_rho : Pfrak -> R_rho` is abstraction/encoding.
- `gamma_rho : R_rho -> 2^Pfrak` is concretization of compatible problem instances.
- `phi_rho` is the transformed specification over `X_{rho,p}`.
- `epsilon_rho` is the approximation/loss/leakage envelope.
- `beta_rho subseteq X_{rho,p} x X_p` relates transformed candidates to admissible original-space candidates.

Minimum problem-level consistency is

`p in gamma_rho(alpha_rho(p))`

or an explicitly qualified approximate analogue.

For `x' in X_{rho,p}`, let

`Related_rho(x') = {x in X_p | beta_rho(x',x)}`.

Representation change MUST declare the refinement mode used for candidate solutions. Two common sound modes are:

1. **universal-safe refinement**:
   `phi_rho(x') => (Related_rho(x') != empty and forall x in Related_rho(x'). phi(x))`;
2. **witness-preserving refinement**:
   `phi_rho(x') => exists x in Related_rho(x'). phi(x)`, with the realized concrete witness and its evidence carried into acceptance.

The explicit non-emptiness clause prevents a universal condition from becoming vacuously true when `x'` has no concrete realization. Do not silently switch refinement modes. A single-valued `back` is only the special case in which `beta_rho` is total and functional on accepted transformed candidates.

Representation selection may minimize

`E[C_solve(p_rho)] + C_transform(rho) + lambda*Risk(rho)`

subject to specification preservation, realizability, authority constraints and evidence/reconstruction obligations.

## Counterexample-guided abstraction refinement (CEGAR)

**Method LEGO, not a universal schema or guaranteed terminating optimizer.**
The task's normative predicate `phi` remains prior to both an abstraction and
its verifier. Let `C` be a concrete transition system, `A_i` the current
abstract transition system, `alpha_i` a state/trace abstraction, and
`gamma_i` its concretization. For safety model checking require an admitted
**over-approximation simulation**, e.g. `Traces(C) subseteq gamma_i(Traces(A_i))`
under the *same* declared environment/initial-state assumptions. This is a
nontrivial obligation, not a consequence of the word "abstraction".

For a scoped safety property `Safe` preserved by concretization:

1. **ABSTRACT:** choose an existing Owner model / representation `A_i`
   with explicit source cut, assumptions, interface and simulation relation;
   coarse does not mean globally minimal or sufficient for every use.
2. **CHECK:** run the *existing* qualified checker on `A_i`. An abstract
   safety PASS transfers to `C` **only** with the established over-approximation,
   property mapping, checker soundness and relevant model-to-code bridge.
   Finite TLC success alone proves bounded-model invariants, not Rust code.
3. **COUNTEREXAMPLE:** if the checker returns an abstract violating trace
   `tau_i`, invoke a **concrete feasibility checker/replay** for the relevant
   Owner and environment, retaining source/configuration/identity. A real,
   reproducible violating concrete trace is `FAIL` for the specified scope;
   it is not a pretext to edit the abstract model until the failure disappears.
4. **REFINE:** if and only if the trace is *proved infeasible* (spurious),
   refine the abstraction's predicates/state partitions or transition
   precision to exclude it, while maintaining the concrete simulation.
   An unknown feasibility result remains `UNKNOWN`, **not** spurious.
5. **RECHECK:** repeat with a changed abstract-model digest and scoped proof.
   Bound time/memory/refinement attempts; return `UNKNOWN` if exhausted or
   if environmental/realization equivalence cannot be established.

Typed result:

`CEGAR(C,phi,A0,budget) in {SAFE(model_scope,evidence), UNSAFE(concrete_trace,evidence), UNKNOWN(reason)}`.

A valid refinement must exclude the *spurious trace* while retaining every
admitted concrete behavior. Blindly deleting a failing transition is unsound.
State explosion, undecidability, coarse-to-fine divergence, spurious replay,
coverage omissions, and time-varying environment may preclude convergence.
CEGAR is most naturally applied to safety; liveness/fairness, probabilistic
and hyperproperties need separately qualified abstractions and checkers.

**Ordivon four-Owner example:** the abstract invariant "dispatch implies
Network is currently READY" is too strong when Network can degrade *after*
Runtime's justified admission. The candidate trace
`NetworkObserve -> HarnessPropose -> RuntimeAdmit -> NetworkDegrade -> RuntimeDispatch`
requires feasibility inspection. If it is a real permitted execution, fix the
misstated specification/temporal observation by distinguishing immutable
`admissionInputsWitness` from current Network readiness. Do **not** label
this real trace "spurious" merely to satisfy TLC. If no concrete feasibility
bridge exists, mark `UNKNOWN`. Preserve the original safety objective:
no dispatch without correctly witnessed admission.

**Mature foundation:** Clarke, Grumberg, Jha, Lu, Veith, *Counterexample-
Guided Abstraction Refinement*, CAV 2000, DOI 10.1007/10722167_15;
JACM 2003 symbolic-model-checking extension. Reuse the natural Owner's TLC,
SMT, Rust/Host/Harness CDC, or transport replay; do not create a proprietary
CEGAR runtime, global counterexample registry, or new acceptance authority.

**MSR distinction:** no `Minimal(rho)`, `Sufficient(rho)`, or their conjunction
is a default Ordivon proof obligation. Global optimality may be unprovable
or more expensive to establish than solving the actual task. A compact
representation is an optional engineering hypothesis; when it removes
behavior, the soundness/consumer contract and concrete trace determine its
acceptance, not its apparent size.

## Generator family

`G_rho={g1,...,gn}` is a compositional vocabulary. It is not called a mathematical basis without independent proofs of independence and completeness.

## LEGO contract — adopted component semantics

Treat R2.1 as an application profile of established module/interface and
contract theories, not a new universal calculus. Preserve the six practical
roles (identity, responsibility, inputs, outputs, behavioral contract,
acceptance); these are engineering descriptors, not six mathematical axioms.

### Semantic mapping

| Existing R2.1 coordinate | Adopted interpretation | Required distinction |
| --- | --- | --- |
| identity / responsibility | scoped component identity and requirement allocation | identity is not semantic equivalence |
| I, O | typed signatures / ports with declared direction and visibility | shape compatibility is not behavioral substitutability |
| S, pre, post, inv | transition systems and Hoare-style obligations | invariant satisfiability is not invariant preservation |
| behavioral contract | assume–guarantee contract with explicit behavior universe | a specification is distinct from its implementations |
| compose / unfold | theory-specific composition and hiding / architectural decomposition | hiding is not generally invertible |
| replacement | contract refinement or contextual/observational relation | declare the relation and its direction |
| rho, alpha, gamma, beta | abstraction and property-preserving realization relations | arbitrary encoding is not automatically a Galois connection |
| eff | observable effects and environment/authority assumptions | a proof never grants execution permission |
| c, epsilon | measured cost / explicitly defined approximation bounds | neither is a universal truth or compatibility metric |
| prov, acceptance | source-bound evidence and requirement-specific acceptance | metadata and test outcomes are not component semantics |

The R2.1 formal admission tuple

`ell=(I,O,S,pre,post,inv,eff,c,epsilon,prov,unfold)`

is **mandatory, in full, for every independent formally DECLARED or ADMITTED LEGO**, whether method, capability, composite or ordinary domain responsibility, including when no property has yet been proved. DECLARATION_COMPLETE is not MODEL_PROVED. Raw source, exploratory evidence and incomplete candidates are not independently admitted LEGOs.
Its six practical identity/responsibility/interface/contract/acceptance roles
remain mandatory too. Do not omit a coordinate because it is awkward; give it
an exact typed interpretation and a relevant checked obligation. For genuinely
stateless, effect-free or exact components use `S=Unit`, empty effects or
`epsilon=0` **only with a justified semantic argument**. `c` needs a named
unit and scope; `prov` binds the exact implementation/model and evidence;
`unfold` identifies the actual connected/hidden children (possibly an
explicitly justified atomic leaf). If a coordinate's value or evidence is unknown, declare a typed UNKNOWN(reason,
unit/scope where relevant, unfulfilled obligation); this is a present field,
not a numeric 0 or a proof. UNKNOWN blocks only propositions relying on it.
Proof standing for an unrelated verified property may still be MODEL_PROVED,
but CODE_REFINED or INSTALLED_CURRENT requires its own qualified bridge.
The existing Lean fields c : Nat and epsilon : Nat are a scoped numeric
model, not a general representation of unknown empirical cost or error. The tuple is a typed declaration with separate mathematical obligations, not
an automatic theorem, new runtime object, metadata registry, invented
universal calculus or proof that every repository file is a LEGO. Acceptance
also declares the consumer/goal and observation or Boolean theorem, a
comparable baseline or fixed specification, instrument, decision predicate,
guardrails and evidence/UNKNOWN; cost c and error epsilon do not substitute
for domain outcome. An explicitly requested verified architecture theorem can
be a scoped architecture milestone, never by itself a deployed product claim.
Keep existing names and natural consumer APIs; check each applicable coordinate
in the existing mature Lean/Pacti/TLA+/SMT/implementation proof carrier.

### Behavioral assume–guarantee profile

For this profile fix a behavior universe `B`, port alignment, and observation
semantics before comparing contracts. A behavior can be an input/output
valuation or a trace; do not silently identify the two. Let an implementation
denote `Beh(M) subseteq B`, and let `C=(A,G)` with `A,G subseteq B`.
Here `C` is a local contract symbol (not the concrete transition system in
the CEGAR section).

Satisfaction is the standard behavioral relation:

`M |= C iff Beh(M) intersection A subseteq G`.

Equivalently use the saturated guarantee
`Ghat = (B minus A) union G`; then
`M |= C iff Beh(M) subseteq Ghat`.

For contracts on this same universe, use the saturated refinement preorder:

`C_new <=ref C_old iff A_old subseteq A_new and Ghat_new subseteq Ghat_old`.

This admits every previously legal environment and restricts permitted
implementation behavior. It yields the satisfaction-preservation implication
`M |= C_new and C_new <=ref C_old => M |= C_old`.
This statement is about the adopted behavioral contract semantics. Substitution
inside a system additionally requires the chosen composition's monotonicity,
port/authority compatibility and the property's preservation hypotheses.

Do not infer realizability from a nonempty `A intersection G`: a component
may have to choose outputs causally against all legal environment choices.
Declare input/output control, initial states, time and strategy requirements
when asking for a realizable reactive implementation. Check non-vacuity
separately: empty assumptions or absent relevant behaviors can make
satisfaction vacuous without solving the intended architectural obligation.

### Stateful observable-step refinement: safety AND enabled progress

Existing native Lean owner: tools/formal/RecursiveLegoRefinement.lean.
This is a restricted semantic **profile of the same canonical R2.1 11-tuple**,
not an alternate LEGO definition. ObservableStep instantiates the typed
input I, output O, state S, enabled pre, transition post and one visible
effect label from eff. The inv, full eff/authority policy, c, epsilon, prov
and unfold coordinates retain their separate typed declarations and qualified
proof obligations. They are not defaulted to empty or zero.

Fix a relation R between NEW concrete and OLD abstract states (not
necessarily a function), identical consumer input alphabet, and an explicit
consumer-observable (output, effect) alphabet. For every related pair and
input accepted by the OLD component, require simultaneously:

1. Input receptiveness: the NEW component accepts the old legal input.
2. Enabled progress: there EXISTS an actual new transition. Otherwise the
   empty transition relation satisfies ordinary safety simulation vacuously.
3. Step matching: EVERY new visible output/effect transition has an OLD
   transition with the same observed output/effect and a related successor.

StepRefines is the exact Lean predicate combining these conditions.
Theorems step_refinement_has_real_progress and
step_refinement_preserves_two_visible_effects show a one-step non-vacuity
and two-step trace matching consequence. The theorem
vacuous_effect_safety_cannot_prove_step_refinement supplies a concrete
safety-only false-green model; this is a kernel proof, not an AST check.
A substitution may be rejected even if its successful outputs happen to
match the old outputs: dropping required old commands or returning no
output breaks the consumer.

This is the strict one-step observable profile, not a theorem about
invisible transitions, stuttering, arbitrary fairness, asynchronous
timeouts, cancellation, divergence, effect authority, probabilistic
approximation or cost. For those, adopt the appropriate simulation/temporal
theory with explicit side conditions, state mapping, initialization and
fairness/ranking obligations. Lean makes initial-state nonvacuity explicit:
empty_relation_satisfies_step_refinement shows StepRefines is vacuous
when state relation R is empty. InitialCoverage is a derived predicate
on existing typed initial-state sets and R; for a nonempty OLD initial
set, initial_coverage_supplies_related_state produces a related start,
and empty_relation_fails_real_initial_coverage rejects the false-green.
This is neither an installed initialization proof nor a new R2.1 field.

Initial states must be related separately;
no real Rust or installed PG backend is verified merely by this Lean proof.

Mature roots: Abadi and Lamport, The Existence of Refinement Mappings;
de Alfaro and Henzinger, Interface Automata; Chilton, Jonsson and
Kwiatkowska, An Algebraic Theory of Interface Automata. Use the existing
pinned Lean owner (mise run formal:verify), not a new registry or verifier.

### Composition is theory-specific

Use separate, declared operators for sequential, parallel, feedback and hiding
composition; the old `compose : L x L ->partial L` is only generic notation.
Compatibility is not a preorder in general. Keep port compatibility,
contract refinement and observational equivalence as different relations.

For **sequential commands**, under a shared state interpretation and the
usual Hoare-logic side conditions, use the composition rule
`{P} f {Q}, {Q} g {R} => {P} f;g {R}`.
Account for parameter substitution, framing and effects. Partial-correctness
triples do not establish termination. The old `post1 => pre2` check is a
sequential seam obligation, not a theorem for arbitrary interacting services.

**R2.1 sequential substitution rule (mechanically checked, bounded ports).**
The existing Lean OrdivonR21.IOContract projection has assumptions A
and guarantees G over the same observable I/O port universe. For
F_new <=ref F_old and H_new <=ref H_old, local refinement does *not* alone
authorize replacing F_old;H_old by F_new;H_new. A sufficient middle-wire
obligation is:

    forall x y, A_F_old(x) and G_F_new(x,y) -> A_H_old(y)

Under this condition the original sequentialContract (existential
relational composition) satisfies
(F_new;H_new) <=ref (F_old;H_old). The checked Lean proof is
OrdivonR21.sequential_refines_if_intermediate_admissible, with reflexive
and transitive refinement lemmas in the same existing formal source.
The local_refinements_do_not_imply_unconditional_sequential_refinement
countermodel uses Bool intermediate values: F guarantees true,
H_old admits only false, and H_new allows both. Each local
refinement holds but global refinement fails. Thus replacing a
contract/LEGO merely because both parts passed is unsound.

This side condition is sufficient, not claimed necessary. The theorem
concerns the restricted input/output contract projection **only**; when
instantiating the full unique 11-coordinate R2.1 LEGO, the S, inv,
eff, c, epsilon, prov and unfold coordinates retain independent
typed obligations (in particular a hidden effect or installed authority
cannot be erased by this projection). Implementation-to-model refinement,
evidence readset closure and deployment currentness require separate
consumer verification. To recheck, run Lean from tools/formal/ with
mise exec -- lean RecursiveLegoRefinement.lean and inspect the
#print axioms reports on positive and counterexample theorems.

For the **saturated behavioral contract algebra**, after lifting both
contracts to a common behavior universe, the parallel contract operation is:

`Ghat_12 = Ghat_1 intersection Ghat_2`
`A_12 = (A_1 intersection A_2) union (B minus Ghat_12)`
`C_1 tensor C_2 = (A_12,Ghat_12)`.

This is the standard algebraic operation, not an executable network connector.
Use its implementation-composition theorem only when concrete wiring,
synchronization, shared variables and hiding realize the adopted semantics.
Do not replace it with naive `(A1 and A2, G1 and G2)`, or infer liveness,
schedulability, causal realizability or permission from this equation.

The existing Lean OrdivonR21.IOContract has **input-only** assumptions.
To check the standard full-behavior tensor without another contract schema,
instantiate its input type as the whole behavior universe B and output type
as Unit: IOContract B Unit. Unit is a representation carrier, **not** an
assertion that an executable component produces no output. The Lean kernel
checks tensor_saturation_exact (exact saturated guarantee intersection),
tensor_refinement_monotone (local refinement monotonicity within that SAME
behavior universe) and naive_parallel_conjunction_is_not_tensor (a finite
countermodel to naive conjunction). These do **not** prove executable
concurrency, effect interleavings, reactive realizability, an installed
component, or hidden-port refinement. Each still needs its own qualified
bridge and current SourceCut. Inspect their existing #print axioms reports.

**Critical representation boundary (kernel checked):** B is the WHOLE
BEHAVIOR in this tensor encoding, while the existing Implements predicate
treats its input coordinate as an environment-provided INPUT.
The theorem tensor_io_implementation_iff_universal_saturation proves that
the tensor, when incorrectly fed into that I/O-totality predicate, admits
an implementation only if EVERY behavior in B satisfies its saturated
conjunction. The finite theorem
algebraic_tensor_does_not_imply_io_implementation shows a well-defined
algebraic tensor with no such I/O-total implementation. This is a
PROJECTION MISMATCH, not a proof that standard saturated contracts are
intrinsically unrealizable. Do not promote tensor_refinement_monotone into
CODE_REFINED, INSTALLED_CURRENT, or DOMAIN_ACCEPTED. A concrete
input/output/trace simulation bridge needs its own behavior, effect,
consumer and installed-currentness evidence.

**Native execution identity (H04):** a Gateway recovery/submit binding
is one abstract triple (nativeId, operationRef, requestId). The existing
Lean source checks the conditional induction rule
admitted_binding_preserves_coherence on a finite history, with pairwise
identity equivalences in ALL three directions, and a finite bad replay
unguarded_native_request_rebinding_breaks_coherence countermodel. The
corresponding real Harness consumer is GatewayMcpRuntimeAdapter:
retain exactly one binding, allow exact replay, reject native/operation/
request rebindings before mutating its two existing maps. This is only
an abstract identity-state law + native Python/fixture tests: not a proof
that the entire Python implementation or installed Gateway/Runtime
refines the abstract model under all possible concurrency or crashes.

For **protocol interaction**, an interface-automata profile may express
input/output/internal actions and use alternating simulation for refinement.
Its original optimistic compatibility means that a suitable environment
exists, not that every environment is safe. A translation between interface
automata and assume–guarantee contracts must identify which operators and
relations it preserves; naming both theories does not supply that proof.

For **concurrency/feedback**, use a valid assume–guarantee, rely–guarantee or
temporal composition rule with its side conditions. Circular promises are
not self-justifying. Invariant checking requires admissible initialization
and preservation by every admitted transition, including interference.
Deadlock freedom, fairness and liveness are separate obligations.

### Recursive closure, refinement and realization

A composite may expose a component contract using the selected theory's
composition/hiding operators. Schema closure alone is not semantic closure.
`unfold` records the architectural decomposition and its provenance; it is
not an inverse to information-hiding semantics. Associativity, identity,
monotonicity and congruence are inherited only where established by that
theory under its side conditions, never from the LEGO name.

Keep three judgments separate:
1. the abstract component/architecture satisfies its formal specification;
2. the implementation refines that abstract specification;
3. the installed artifact/configuration is the implementation just verified.

For a temporal profile, provide an explicit state/trace mapping and show
initialization and step correspondence (with stuttering where appropriate).
Trace inclusion preserves only properties covered by that semantics; fairness,
liveness and information-flow hyperproperties need their own preservation
arguments. A sampled execution trace is conformance evidence, not a universal
implementation-refinement theorem.

### Architectural acceptance and incremental evidence

Architectural requirements are legitimate current goals. Accept an abstract
design against its declared composition/realizability/refinement obligations;
record implementation and downstream domain obligations separately. Do not
block architecture reform on every terminal business outcome, and do not
present architectural acceptance as completed deployment/domain acceptance.

Bind a verification claim to the property, semantic profile, assumptions,
model/implementation/configuration identities, checker and evidence used.
When an input changes, revalidate dependent claims or provide a proved reuse
argument. Historical proofs remain proofs about their original objects.
Unknown dependencies require conservative revalidation; digest equality
alone does not prove dependency completeness.

The existing Interface Contract R2's compatibility, currentness and evidence
admissibility remain distinct engineering judgments. `EXACT_MATCH` or
`COMPATIBLE_BY_DECLARATION` is not automatically a behavioral-refinement
certificate. No new schema, gate per edge, registry or solver is required.

### Mature sources and scope

- Parnas, *On the Criteria To Be Used in Decomposing Systems into Modules*
  (1972), https://doi.org/10.1145/361598.361623 — decomposition/information hiding.
- Paulson, *ML for the Working Programmer*, chapter 7,
  https://www.cl.cam.ac.uk/~lp15/MLbook/PDF/chapter7.pdf — signatures,
  structures, abstract types and functors; not a distributed-protocol proof.
- Benveniste et al., *Contracts for System Design* (2018),
  https://doi.org/10.1561/1000000053 — contract meta-theory and behavioral
  assume–guarantee algebra; use the selected theory's hypotheses.
- de Alfaro and Henzinger, *Interface Automata* (2001),
  https://doi.org/10.1145/503209.503226 — protocol compatibility and
  alternating refinement with optimistic environment semantics.
- Abadi and Lamport, *The Existence of Refinement Mappings* (1991),
  https://doi.org/10.1016/0304-3975(91)90224-P — refinement mappings;
  mappings and hypotheses must be established for the actual system.
- Pacti, https://www.pacti.org/docs/getting_started/ — existing tooling
  for supported contract theories, not an implementation of every theory above.

This reference adopts definitions and specifies proof obligations. Editing it
does not machine-check these mappings or certify the existing Ordivon code.

### Scoped evidence is not global graph coverage

A Gate verifier for an existing composite may check one consumer-level
predicate even when the explicit dataflow has several cross-Owner edges.
Let `G_req` denote caller-declared required Gates and `E_cross` the
cross-Owner edges in a representation. Their sets are NOT the same
mathematical object, and requiring a separate Gate for every `e in
E_cross` is not a general LEGO axiom. One verifier may legitimately
discharge a composite end-to-end assumption, provided its scope and
bridge are independently justified.

A scoped gate closure establishes only `forall g in G_req: psi_g` under
each verifier's assumptions. It does not imply
`forall e in E_cross: ContractValid(e)` without independently established
coverage/refinement relations linking the Gates to those edges. If a
consumer actually requires whole-graph assurance, that additional
coverage is a separate task-local obligation; without an express bridge,
its standing is UNKNOWN. Never upgrade a passed bounded Gate into domain
acceptance or add redundant Gates merely to match graph cardinality.

## Encapsulation

As an optional engineering heuristic, compare measured encapsulation costs using

`G_enc = DeltaC_visible - C_glue - lambda*L_leak - mu*C_diagnose > 0`

Treat the score as a task-local decision aid only: units, weights and measurements must be declared. It is neither a formal admission law nor a necessary condition for encapsulation. Establish specification preservation separately and retain traceability and `unfold`. No monotonic total-complexity claim follows merely from encapsulation.

## Model and system refinement

`m = Refine_model(ell)` denotes a proposed modeling transformation adding inference/prediction/simulation semantics; the name alone proves no refinement relation.

`Sigma = Refine_system(m)` denotes a proposed system-description transformation adding state space, transition/effect semantics, feedback and recovery contracts. Qualify either transformation by an explicit relation and preservation argument before calling it a proved refinement.

A concrete configuration `theta in Theta_Sigma` instantiates the system. Keep that system specification/configuration distinct from mutable runtime state:

`sigma_t in State(Sigma,theta)`.

This prevents a system architecture object from being silently substituted for the state being operated on.

## Partial operators and legal programs

An operator is partial relative to an instantiated system:

`kappa_(Sigma,theta) : State(Sigma,theta) ->partial State(Sigma,theta)`

with explicit `pre_kappa(Sigma,theta,sigma)` and transition/post obligations. This partial-function notation is the deterministic operator profile. Nondeterministic or concurrent operators require a transition relation (or set-valued semantics), explicit environment/strategy quantification, and legality obligations over the relevant possible successors; the single reached-state rule below does not certify those profiles.

`Pi_legal(Sigma,theta,sigma0)` is defined recursively:

- the empty program is legal at an admissible `sigma0 in Init(Sigma,theta)`;
- if `pi` is legal from `sigma0`, its reached state is `sigma`, and `pre_kappa(Sigma,theta,sigma)` holds, then `pi;kappa` is legal.

No claim is made about arbitrary strings from an operator alphabet.

Abstract execution/realization is explicit:

`Exec(Sigma,theta,sigma0,pi) = (tau,x,e_exec)`

where `tau` is a state/effect trajectory, `x in X_p` is the candidate artifact/outcome presented to `phi`, and `e_exec` is execution evidence. A successful process exit is not itself `phi(x)`.

## Method LEGO

`mu : (Sigma,theta,sigma0,p,e) ->partial Pi_legal(Sigma,theta,sigma0)`.

Attachment is legal only when method requirements are discharged by system capabilities/assumptions and authority/safety prerequisites hold:

`Req(mu) <= Cap(Sigma,theta)`.

## Feasibility and dependent configuration space

Abstract feasibility is

`exists pi in Pi_legal(Sigma,theta,sigma0), tau,x,e_exec : Exec(Sigma,theta,sigma0,pi)=(tau,x,e_exec) and phi(x)`.

The dependent configuration space is conceptually

`Xfrak_p = Sum_{rho in Rep(p)} Sum_{G in Gen(rho)} Sum_{Lambda in Comp(G)} Sum_{m in Model(Lambda)} Sum_{Sigma in System(m)} Sum_{theta in Theta_Sigma} Sum_{sigma0 in Init(Sigma,theta)} Pi_legal(Sigma,theta,sigma0)`.

Every variable is bound before dependent terms refer to it. Parameter spaces, admissible initial states and legal programs depend on earlier architecture choices.

## Optimization after feasibility

`Solve != Optimize`.

Let `Q_p` denote the currently qualified feasible set under hard constraints and acceptance evidence. Optimization searches **within** that set (or a conservative admissible approximation):

`Q_p = {z in Xfrak_p | Hard_p(z) and Qualified_p(z)}`.

For objective vector `J(z)`, optimize over `z in Q_p`. If an architecture/representation/method change invalidates the evidence establishing `Qualified_p(z)`, that candidate returns to verification before acceptance. Finding one feasible baseline never authorizes later optimizer steps to violate `Gamma` or silently leave the feasible set.

Use a Pareto set when objectives are not legitimately reducible to one scalar.

## Evidence and attribution

Evidence should support observations, claims, trace, provenance, uncertainty, counterexample/witness and one or more loci such as `(component,port,contract,transition)`.

`Atr(e,Sigma,theta,pi) -> {(locus_i,weight_i,support_i)}`.

The proof/abstraction dependency structure may be a DAG, not a total order. Runtime interaction graphs can contain cycles; do not assume they are DAGs. For cyclic dependencies, establish a valid joint/fixed-point argument or treat a strongly connected component as one analysis unit before using the DAG frontier below. Define `a prec b` to mean that `a` is an upstream prerequisite/refinement dependency of `b`. Let `Broken(e)` be loci whose contracts or assumptions are justified as invalid by current evidence. The repair frontier is

`B_min(e) = Min_prec(Broken(e))`.

`B_min(e)` may contain multiple incomparable loci. The older "earliest broken abstraction" rule is the special case in which the relevant dependency path is linear and `B_min(e)` is a singleton. Preserve unaffected/current subgraphs rather than restarting the whole problem.

## UNKNOWN

`UNKNOWN` means available evidence establishes neither sufficient support for `phi` nor sufficient support for its negation under the declared verifier target/guarantee and bridge obligations. Report checker-local status for `psi_nu` separately from end-to-end status for `phi`: local PASS can coexist with end-to-end UNKNOWN when the representation, implementation or evidence bridge is unestablished.

Allowed continuations include evidence acquisition, verifier change/independent verifier, re-observation, re-representation and external escalation. UNKNOWN is not weak FAIL and does not authorize blind retry.

## Bounded self-reference

Meta-refinement:

`Ffrak_{k+1}=Refine(Ffrak_k,e_k)`.

External anchor envelope:

`A*=(Phi*,B*,M*,H*,C*)`,

where `Phi*` is frozen top-level specification, `B*` holdout/real-world tasks, `M*` measurement pipeline, `H*` external/human authority where needed, and `C*` commitment/isolation metadata such as immutable digests, hidden labels or externally controlled benchmark selection.

For the current refinement epoch:

`A* notin dom(Refine)`.

That immutability condition is necessary but not sufficient. The candidate framework must also be unable to choose, rewrite, leak hidden labels into itself, or materially influence the anchor measurement/acceptance path outside the declared protocol. Where material, treat evaluator isolation as an information-flow/noninterference obligation and use independent execution/measurement.

Accept a candidate refinement only inside a declared trust region with no material anchor regression beyond tolerance; otherwise rollback.

No general theorem of global monotonic improvement, convergence or fixed-point existence is asserted.

## Machine-checkable obligation routing

Do not hand-roll a universal prover. Route a bounded obligation to the mature owner matching its semantics:

- finite first-order/arithmetic consistency, counterexamples and bounded logical obligations -> local Z3 reasoning-waist provider;
- legal action/operator programs and precondition-valid plans -> local Unified Planning provider;
- algebraic assume/guarantee composition, quotient or refinement -> Pacti when the seam is explicitly formalizable and that optional provider is admitted for the task;
- concurrent/temporal state-machine safety/liveness -> existing digest-pinned TLA+/TLC owner;
- RDF evidence/shape conformance -> pySHACL when RDF is the natural carrier;
- discrete objective/configuration search -> OR-Tools, while keeping its objective separate from truth/acceptance;
- evaluator/anchor leakage or prohibited influence -> information-flow/noninterference analysis, with stronger formalization only when warranted by the risk.

A solver/model-checker PASS establishes only the encoded obligation under its model and assumptions. It does not by itself validate the representation, prove implementation refinement, establish domain truth, or qualify the full Recursive LEGO Calculus.
