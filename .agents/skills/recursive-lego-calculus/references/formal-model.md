# Recursive LEGO Calculus — formal model R1

This reference gives the compact formal contract behind `recursive-lego-calculus`. Symbols are deliberately single-purpose.

## Symbols

- `W`: world / environment space.
- `p=(w0,phi,Gamma)`: one problem instance.
- `X*_p`: true solution set induced by `phi`.
- `rho`: representation.
- `G_rho`: generator family for `rho`.
- `ell`: LEGO.
- `m`: model LEGO.
- `s`: system LEGO.
- `kappa`: partial operator.
- `mu`: method LEGO / higher-order strategy.
- `Pi_legal(s)`: legal operator programs for `s`.
- `nu`: verifier.
- `e`: structured evidence.
- `F`: the recursive problem-solving framework.
- `A*`: external anchor envelope for meta-refinement.

## Truth specification

`X*_p = {x | phi(x;w0,Gamma)=1}`.

The target predicate `phi` is logically prior to verification.

Verifier: `nu(x)=(v,e,q)`, with `v in {PASS,FAIL,UNKNOWN}`.

Deterministic soundness when applicable:

`nu(x).v = PASS => phi(x)`.

Statistical/empirical soundness envelope when applicable:

`Pr[nu(x)=PASS and not phi(x) | H_nu] <= delta_nu`.

Optional completeness envelope:

`Pr[nu(x)=FAIL and phi(x) | H_nu] <= beta_nu`.

## Representation

`rho=(alpha_rho,gamma_rho,phi_rho,epsilon_rho)`.

- `alpha_rho : P -> R_rho` is abstraction/encoding.
- `gamma_rho : R_rho -> 2^P` is concretization.
- `phi_rho` is the transformed specification.
- `epsilon_rho` is the approximation/loss/leakage envelope.

Consistency: `p in gamma_rho(alpha_rho(p))`, or a declared approximate variant.

A transformed solution must soundly refine the original specification. For a single-valued recovery map `back`:

`phi_rho(x') => phi(back(x'))`.

Representation selection may minimize

`E[C_solve(p_rho)] + C_transform(rho) + lambda * Risk(rho)`

subject to specification preservation and authority/evidence constraints.

## Generator family

`G_rho={g1,...,gn}` is a compositional vocabulary. It is not called a basis without independent proofs of independence and completeness.

## LEGO

`ell=(I,O,S,pre,post,inv,eff,c,epsilon,prov,unfold)`.

Composition is partial: `o : L x L ->partial L`.

A candidate `ell2 o ell1` is defined only when:

1. `O1 <= I2` under the domain's compatibility/refinement relation;
2. `post1 => pre2` or the corresponding environmental assumption is otherwise discharged;
3. `inv1 and inv2` are jointly satisfiable;
4. effect/policy/identity/authority obligations are compatible;
5. composition-specific seam obligations are discharged.

If defined, the composite must itself expose the LEGO schema. This is type-level closure only.

## Encapsulation

A recursive composite may be encapsulated when:

`G_enc = DeltaC_visible - C_glue - lambda*L_leak - mu*C_diagnose > 0`

and specification preservation, traceability and `unfold` remain available.

## Model/system refinement

`m = Refine_model(ell)` adds inference/prediction/simulation semantics.

`s = Refine_system(m)` adds transitions, effects, feedback and recovery semantics.

These are typed contract refinements, not ontology claims.

## Partial operators and legal programs

Each operator is partial: `kappa : X ->partial X`, with explicit precondition `pre_kappa`.

`Pi_legal(s)` is defined recursively:

- empty program is legal at an admissible initial state;
- if `pi` is legal and `pre_kappa(pi(s))` holds, then `pi;kappa` is legal.

No claim is made about arbitrary strings from an operator alphabet.

## Method LEGO

`mu : (s,p,e) ->partial Pi_legal(s)`.

Attachment is legal only when method requirements are discharged by system capabilities/assumptions and authority/safety prerequisites hold:

`Req(mu) <= Cap(s)`.

## Feasibility and optimization

Abstract feasibility:

`exists pi in Pi_legal(s) : phi(pi(s))`.

Optimization starts only after a feasible/qualified candidate exists.

The dependent configuration space is conceptually:

`Xfrak_p = Sum_{rho in Rep(p)} Sum_{G in Gen(rho)} Sum_{Lambda in Comp(G)} Sum_{m in Model(Lambda)} Sum_{s in System(m)} (Theta_s x Pi_legal(s))`.

Use a Pareto set when objectives are not legitimately reducible to one scalar.

## Evidence and attribution

Evidence should support a locus such as `(component,port,contract,transition)` in addition to observations, trace, provenance, counterexample/witness and uncertainty.

`Atr(e,s,pi) -> {(locus_i, weight_i, support_i)}`.

The repair target is the earliest abstraction layer whose assumptions/contracts are invalidated by evidence.

## UNKNOWN

`UNKNOWN` means available evidence establishes neither sufficient support for `phi` nor sufficient support for its negation under the current verifier envelope.

Allowed continuations include evidence acquisition, verifier change/independent verifier, re-observation, re-representation and external escalation.

## Bounded self-reference

Meta-refinement: `F_{k+1}=Refine(F_k,e_k)`.

External anchor envelope: `A*=(Phi*,B*,M*,H*)`.

For the current refinement epoch: `A* notin dom(Refine)`.

Accept a candidate refinement only inside a declared trust region and with no material anchor regression beyond tolerance; otherwise rollback.

No general theorem of global monotonic improvement, convergence or fixed-point existence is asserted.
