# Recursive LEGO Calculus — formal model R2

This reference gives the compact formal contract behind `recursive-lego-calculus`. Symbols are deliberately single-purpose. R2 separates verifier guarantee kinds, system specification from runtime state, and a linear "earliest broken layer" from the more general minimal broken frontier of a recursive dependency graph.

## Symbols

- `W`: world / environment space.
- `Pfrak`: problem-instance space.
- `p=(w0,phi,Gamma) in Pfrak`: one problem instance.
- `X*_p`: true solution set induced by `phi`.
- `rho`: representation contract.
- `R_rho`: working-representation space for `rho`.
- `G_rho`: generator family for `rho`.
- `ell`: LEGO contract.
- `m`: model LEGO.
- `Sigma`: system LEGO / system specification.
- `sigma_t in State(Sigma)`: one runtime/system state under `Sigma`.
- `kappa`: partial operator over states admitted by `Sigma`.
- `mu`: method LEGO / higher-order strategy.
- `Pi_legal(Sigma,sigma0)`: legal operator programs from one initial state.
- `pi`: one legal operator program.
- `nu`: verifier.
- `e`: structured evidence.
- `Ffrak`: the recursive problem-solving framework.
- `A*`: external anchor envelope for meta-refinement.

## Problem and truth specification

`X*_p = {x | phi(x;w0,Gamma)=1}`.

The target predicate `phi` is logically prior to verification. A verifier may establish qualified evidence about `phi`; it does not define `phi` by returning PASS.

Verifier: `nu(x)=(v,e,q)`, with `v in {PASS,FAIL,UNKNOWN}`. The qualification object `q` MUST identify which guarantee kind is actually justified and its assumptions.

### Deterministic soundness

When the verifier is a sound deductive checker for the modeled semantics:

`nu(x).v = PASS => phi(x)`.

### Procedure-level false-acceptance control

For a randomized/statistical procedure, one possible guarantee is a type-I/false-acceptance bound:

`sup_{x : not phi(x)} Pr_nu[nu(x).v = PASS | x,H_nu] <= alpha_nu`.

This is a property of the verification procedure under assumptions `H_nu`.

### Conditional reliability of PASS

A different guarantee is conditional false-discovery/reliability:

`Pr[not phi(x) | nu(x).v = PASS,H_nu,D_nu] <= delta_nu`,

where `D_nu` denotes the calibrated population/base-rate model needed to make that conditional probability meaningful.

Do **not** infer conditional reliability from a joint bound such as

`Pr[nu(x)=PASS and not phi(x)] <= delta`.

Do not infer either probabilistic guarantee from the other without the additional assumptions required by probability theory.

### Optional completeness / false-rejection control

When meaningful, record separately, for example:

`sup_{x : phi(x)} Pr_nu[nu(x).v = FAIL | x,H_nu] <= beta_nu`.

## Representation and specification preservation

`rho=(alpha_rho,gamma_rho,phi_rho,epsilon_rho,beta_rho)`.

- `alpha_rho : Pfrak -> R_rho` is abstraction/encoding.
- `gamma_rho : R_rho -> 2^Pfrak` is concretization of compatible problem instances.
- `phi_rho` is the transformed specification.
- `epsilon_rho` is the approximation/loss/leakage envelope.
- `beta_rho subseteq X_{rho,p} x X_p` is a candidate-refinement relation between transformed and original solution spaces.

Minimum problem-level consistency is

`p in gamma_rho(alpha_rho(p))`

or an explicitly qualified approximate analogue.

Representation change MUST declare the refinement mode used for candidate solutions. Two common sound modes are:

1. **universal-safe refinement**: `phi_rho(x') => forall x.(beta_rho(x',x) => phi(x))`;
2. **witness-preserving refinement**: `phi_rho(x') => exists x.(beta_rho(x',x) and phi(x))`, with the realized concrete witness and its evidence carried into acceptance.

Do not silently switch between these modes. A single-valued `back` is only the special case in which `beta_rho` is functional.

Representation selection may minimize

`E[C_solve(p_rho)] + C_transform(rho) + lambda*Risk(rho)`

subject to specification preservation, authority constraints and evidence/reconstruction obligations.

## Generator family

`G_rho={g1,...,gn}` is a compositional vocabulary. It is not called a mathematical basis without independent proofs of independence and completeness.

## LEGO contract

`ell=(I,O,S,pre,post,inv,eff,c,epsilon,prov,unfold)`.

Composition is partial:

`compose : L x L ->partial L`.

A candidate `compose(ell2,ell1)` is defined only when:

1. `O1 <= I2` under the domain's compatibility/refinement relation;
2. `post1 => pre2` or the corresponding environmental assumption is otherwise discharged;
3. `inv1 and inv2` are jointly satisfiable;
4. effect/policy/identity/authority obligations are compatible;
5. composition-specific seam obligations are discharged.

If defined, the composite must itself expose the LEGO schema. This is type-level/schema closure only; it is not proof that the realization is correct in the world.

## Encapsulation

A recursive composite may be encapsulated when

`G_enc = DeltaC_visible - C_glue - lambda*L_leak - mu*C_diagnose > 0`

and specification preservation, traceability and `unfold` remain available. No monotonic total-complexity claim follows merely from encapsulation.

## Model and system refinement

`m = Refine_model(ell)` adds inference/prediction/simulation semantics.

`Sigma = Refine_system(m)` adds the state space, transition/effect semantics, feedback and recovery contracts.

Keep `Sigma` distinct from its mutable runtime state:

`sigma_t in State(Sigma)`.

This prevents a system specification/architecture object from being silently substituted for the state being operated on.

## Partial operators and legal programs

An operator is partial relative to a system specification:

`kappa_Sigma : State(Sigma) ->partial State(Sigma)`

with explicit `pre_kappa(Sigma,sigma)` and transition/post obligations.

`Pi_legal(Sigma,sigma0)` is defined recursively:

- the empty program is legal at an admissible `sigma0`;
- if `pi` is legal from `sigma0`, its reached state is `sigma`, and `pre_kappa(Sigma,sigma)` holds, then `pi;kappa` is legal.

No claim is made about arbitrary strings from an operator alphabet.

Abstract execution/realization is explicit:

`Exec(Sigma,sigma0,pi) = (tau,x,e_exec)`

where `tau` is a state/effect trajectory, `x` is the candidate solution artifact/outcome presented to `phi`, and `e_exec` is execution evidence. A successful process exit is not itself `phi(x)`.

## Method LEGO

`mu : (Sigma,sigma0,p,e) ->partial Pi_legal(Sigma,sigma0)`.

Attachment is legal only when method requirements are discharged by system capabilities/assumptions and authority/safety prerequisites hold:

`Req(mu) <= Cap(Sigma)`.

## Feasibility and optimization

Abstract feasibility is

`exists pi in Pi_legal(Sigma,sigma0), tau,x,e_exec : Exec(Sigma,sigma0,pi)=(tau,x,e_exec) and phi(x)`.

Optimization starts only after a feasible/qualified candidate exists.

The dependent configuration space is conceptually

`Xfrak_p = Sum_{rho in Rep(p)} Sum_{G in Gen(rho)} Sum_{Lambda in Comp(G)} Sum_{m in Model(Lambda)} Sum_{Sigma in System(m)} (Theta_Sigma x State0(Sigma) x Pi_legal(Sigma,sigma0))`.

This is a dependent family: parameter spaces, admissible initial states and legal programs depend on earlier architecture choices. Use a Pareto set when objectives are not legitimately reducible to one scalar.

## Evidence and attribution

Evidence should support observations, claims, trace, provenance, uncertainty, counterexample/witness and one or more loci such as `(component,port,contract,transition)`.

`Atr(e,Sigma,pi) -> {(locus_i,weight_i,support_i)}`.

The abstraction structure is generally a dependency DAG, not a total order. Let `Broken(e)` be layers/loci whose contracts or assumptions are justified as invalid by current evidence, and let `prec` be the dependency/refinement order. The repair frontier is

`B_min(e) = Min_prec(Broken(e))`.

`B_min(e)` may contain multiple incomparable loci. The older "earliest broken abstraction" rule is the special case in which the relevant dependency path is linear and `B_min(e)` is a singleton. Preserve unaffected/current subgraphs rather than restarting the whole problem.

## UNKNOWN

`UNKNOWN` means available evidence establishes neither sufficient support for `phi` nor sufficient support for its negation under the declared verifier guarantee.

Allowed continuations include evidence acquisition, verifier change/independent verifier, re-observation, re-representation and external escalation. UNKNOWN is not weak FAIL and does not authorize blind retry.

## Bounded self-reference

Meta-refinement:

`Ffrak_{k+1}=Refine(Ffrak_k,e_k)`.

External anchor envelope:

`A*=(Phi*,B*,M*,H*,C*)`,

where `Phi*` is frozen top-level specification, `B*` holdout/real-world tasks, `M*` measurement pipeline, `H*` external/human authority where needed, and `C*` commitment/isolation metadata such as immutable digests, hidden labels or externally controlled benchmark selection.

For the current refinement epoch:

`A* notin dom(Refine)`.

That immutability condition is necessary but not sufficient. The candidate framework must also be unable to choose, rewrite, leak hidden labels into itself, or materially influence the anchor measurement/acceptance path in ways outside the declared test protocol. Use independent execution/measurement where the blast radius warrants it.

Accept a candidate refinement only inside a declared trust region with no material anchor regression beyond tolerance; otherwise rollback.

No general theorem of global monotonic improvement, convergence or fixed-point existence is asserted.

## Machine-checkable obligation routing

Do not hand-roll a new universal prover. Route a bounded obligation to the mature owner that matches its semantics:

- finite first-order/arithmetic consistency, counterexamples and bounded logical obligations -> local Z3 reasoning-waist provider;
- legal action/operator programs and precondition-valid plans -> local Unified Planning provider;
- algebraic assume/guarantee composition, quotient or refinement -> Pacti when the seam is explicitly formalizable and that optional provider is admitted for the task;
- concurrent/temporal state-machine safety/liveness -> existing digest-pinned TLA+/TLC owner;
- RDF evidence/shape conformance -> pySHACL when RDF is the natural carrier;
- discrete objective/configuration search -> OR-Tools, while keeping its objective separate from truth/acceptance.

A solver/model-checker PASS establishes only the encoded obligation under its model and assumptions. It does not by itself validate the representation, prove implementation refinement, establish domain truth, or qualify the full Recursive LEGO Calculus.
