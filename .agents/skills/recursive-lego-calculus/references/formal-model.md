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

## Generator family

`G_rho={g1,...,gn}` is a compositional vocabulary. It is not called a mathematical basis without independent proofs of independence and completeness.

## LEGO contract

`ell=(I,O,S,pre,post,inv,eff,c,epsilon,prov,unfold)`.

All domain-specific compatibility/refinement relations used below MUST be declared; where written `<=`, it denotes the domain's declared refinement/compatibility preorder rather than numeric order.

Composition is partial:

`compose : L x L ->partial L`.

A candidate `compose(ell2,ell1)` is defined only when:

1. `O1 <= I2` under the declared compatibility/refinement relation;
2. `post1 => pre2` or the corresponding environmental assumption is otherwise discharged;
3. `inv1 and inv2` are jointly satisfiable;
4. effect/policy/identity/authority obligations are compatible;
5. composition-specific seam obligations are discharged.

If defined, the composite must itself expose the LEGO schema. This is type/schema closure only; it is not proof that the realization is correct in the world.

## Encapsulation

A recursive composite may be encapsulated when

`G_enc = DeltaC_visible - C_glue - lambda*L_leak - mu*C_diagnose > 0`

and specification preservation, traceability and `unfold` remain available. No monotonic total-complexity claim follows merely from encapsulation.

## Model and system refinement

`m = Refine_model(ell)` adds inference/prediction/simulation semantics.

`Sigma = Refine_system(m)` adds state space, transition/effect semantics, feedback and recovery contracts.

A concrete configuration `theta in Theta_Sigma` instantiates the system. Keep that system specification/configuration distinct from mutable runtime state:

`sigma_t in State(Sigma,theta)`.

This prevents a system architecture object from being silently substituted for the state being operated on.

## Partial operators and legal programs

An operator is partial relative to an instantiated system:

`kappa_(Sigma,theta) : State(Sigma,theta) ->partial State(Sigma,theta)`

with explicit `pre_kappa(Sigma,theta,sigma)` and transition/post obligations.

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

The abstraction structure is generally a dependency DAG, not a total order. Define `a prec b` to mean that `a` is an upstream prerequisite/refinement dependency of `b`. Let `Broken(e)` be loci whose contracts or assumptions are justified as invalid by current evidence. The repair frontier is

`B_min(e) = Min_prec(Broken(e))`.

`B_min(e)` may contain multiple incomparable loci. The older "earliest broken abstraction" rule is the special case in which the relevant dependency path is linear and `B_min(e)` is a singleton. Preserve unaffected/current subgraphs rather than restarting the whole problem.

## UNKNOWN

`UNKNOWN` means available evidence establishes neither sufficient support for `phi` nor sufficient support for its negation under the declared verifier target/guarantee and bridge obligations.

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
