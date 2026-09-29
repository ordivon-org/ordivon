# Recursive LEGO Calculus — conformance cases R2.1

Use these cases to catch regressions in the method contract. Pair a prose case with a machine-checkable obligation only when a mature provider matches the semantics; do not force every claim into SMT/model checking.

## C1 Truth/verifier separation

Bad:
- define the solution set as `{x | verifier(x)=PASS}`;
- later claim PASS may be wrong.

Required:
- define `phi` and `X*_p` independently;
- give the verifier a declared target predicate and soundness/error envelope relative to that target.

## C2 Illegal composition

Bad:
- concatenate two LEGO because output and input names look similar.

Required:
- check type/refinement compatibility;
- discharge `post1 => pre2` or equivalent assumptions;
- check invariant and effect/authority compatibility.

## C3 Arbitrary operator strings

Bad:
- search every sequence in an operator alphabet and count precondition violations as ordinary failed solutions.

Required:
- search `Pi_legal(Sigma,theta,sigma0)` only, where every intermediate precondition is satisfied.

Machine probe:
- an `execute` action requiring prior authorization MUST be rejected from an unauthorized state;
- `authorize;execute` MAY be accepted when all preconditions/goals hold.

## C4 Over-strong change-of-basis analogy

Bad:
- call a decomposition a basis without independence/completeness;
- assume a representation transform preserves solutions.

Required:
- call it a generator family unless basis properties are proved;
- require explicit specification refinement across representation change.

## C5 Encapsulation monotonicity

Bad:
- assert every abstraction strictly reduces complexity.

Required:
- account for glue, leakage and diagnostic costs;
- preserve `unfold`;
- encapsulate only when net gain is positive for the task.

## C6 Unstructured attribution

Bad:
- feed only PASS/FAIL into attribution and invent a responsible module.

Required:
- use structured evidence with trace/locus/counterexample/provenance/uncertainty;
- return unresolved attribution when evidence is insufficient.

## C7 UNKNOWN handling

Bad:
- convert UNKNOWN to FAIL;
- blind retry the same execution.

Required:
- acquire evidence, change/add verifier, re-observe, re-represent, or escalate.

## C8 Dependent configuration space

Bad:
- write one Cartesian product when parameter/state/operator spaces depend on architecture choices;
- refer to `sigma0` in a legal-program family before `sigma0` has been bound.

Required:
- use a dependent sum/family or equivalent typed configuration structure;
- bind `theta` and `sigma0` before `Pi_legal(Sigma,theta,sigma0)`.

## C9 Self-certification / Goodhart

Bad:
- allow a self-optimizing framework to rewrite the benchmark/verifier that judges the same refinement;
- let the candidate choose hidden labels, benchmark selection, acceptance threshold or measurement implementation for its own acceptance;
- infer monotonic global improvement from internal score gain.

Required:
- freeze an external anchor envelope outside the current mutable domain;
- isolate hidden/holdout evaluation information and measurement control where needed;
- use holdout/real-world outcomes and independent measurement where needed;
- trust-region, rollback and explicit non-convergence claims.

## C10 Method attachment

Bad:
- attach a discipline because its name sounds relevant.

Required:
- express method requirements and system capabilities/assumptions;
- attach only when requirements are discharged;
- preserve the specialist method's own stop conditions and non-claims.

## C11 Minimal broken frontier repair

Bad:
- every verification failure restarts the whole project;
- every physical failure becomes a representation rewrite;
- force a single "earliest" broken layer when evidence points to two incomparable branches.

Required:
- define the dependency direction;
- compute/argue the minimal evidence-supported broken frontier;
- repair each minimal invalid locus while preserving current subgraphs.

## C12 Scope discipline

Bad:
- claim this calculus defines intelligence;
- create a new Representation Manager / LEGO Manager daemon because the method has a representation layer.

Required:
- keep the calculus as an advisory reasoning contract;
- natural owners remain authoritative for world state, execution, policy and evidence.

## C13 Probabilistic verifier guarantee kinds

Bad:
- use `Pr[PASS and false] <= delta` as if it implied `Pr[false | PASS] <= delta`;
- report a posterior reliability number without the calibration/base-rate model needed to define it;
- confuse procedure-level type-I error with conditional false-discovery probability.

Required:
- declare the guarantee kind and target predicate in `q`;
- keep procedure-level false acceptance, conditional reliability and false rejection separate;
- state the assumptions/population under which each bound holds.

Machine probe:
- there MUST exist a probability assignment satisfying a small joint false-acceptance bound while violating an equally small conditional false-discovery bound;
- adding the conditional bound MUST eliminate that counterexample.

## C14 System specification versus runtime state

Bad:
- use one symbol/object both for system architecture/transition contract and current mutable state;
- write `pi(system)` when the program acts on a state admitted by an instantiated system.

Required:
- use `Sigma` for system LEGO/specification, `theta` for configuration, and `sigma_t in State(Sigma,theta)` for runtime state;
- define operators and legal programs relative to all required bindings.

## C15 Representation refinement mode and realizability

Bad:
- accept `forall related concrete x: phi(x)` when there are zero related concrete realizations;
- require all concretizations to satisfy the original specification when the transform only promises one certified witness;
- accept one witness when the representation claims universal safety.

Required:
- require non-empty realization for accepted transformed candidates;
- declare universal-safe, witness-preserving, or another explicit sound mode;
- carry the concrete witness/evidence when using witness-preserving refinement.

Machine probe:
- the naive universal implication MUST admit a vacuous no-realization model;
- adding the non-empty realization obligation MUST reject that model.

## C16 Formal-provider scope

Bad:
- translate every prose claim into SMT because Z3 is available;
- infer full implementation/domain correctness from bounded TLA+/SMT/planning PASS;
- add optional providers to core dependencies without repeated real pressure.

Required:
- route only bounded obligations whose semantics match the provider;
- preserve model assumptions and non-claims;
- keep formal providers as specialized owners rather than a universal formalism.

## C17 Verifier encoding bridge

Bad:
- let a formal checker prove encoded predicate `psi_nu` and report PASS as direct evidence of `phi` without proving the encoding/refinement bridge.

Required:
- local checker soundness establishes `PASS => psi_nu`;
- an end-to-end claim about `phi` additionally requires a justified `psi_nu => phi` bridge, or `psi_nu=phi` by exact construction.

Machine probe:
- `PASS=>psi_nu` alone MUST allow a model with `PASS and not phi`;
- adding `psi_nu=>phi` MUST eliminate it.

## C18 Discovery admissibility

Bad:
- treat any noticed anomaly as a fully scoped problem;
- rank candidate problems with hidden arbitrary weights while claiming objectivity;
- spend heavily on a framing with no plausible verification path.

Required:
- keep framing candidates/evidence explicit;
- consider importance, tractability, verifiability, information gain and cost;
- use Pareto/policy selection unless a legitimate scalar utility is externally supplied;
- run a discovery gate before expensive solving.

## C19 Optimization feasibility preservation

Bad:
- find one feasible baseline and then let optimization violate hard constraints or invalidate acceptance evidence without re-verification.

Required:
- optimize inside a qualified feasible set or conservative admissible approximation;
- reverify after changes that invalidate the evidence establishing qualification;
- preserve `Gamma` throughout accepted optimization.

## C20 External-anchor influence boundary

Bad:
- declare the anchor immutable while allowing the candidate to see hidden labels, choose test instances, influence measurement, or select its own acceptance threshold.

Required:
- treat anchor isolation as both a mutation-control and information/influence-control problem;
- apply information-flow/noninterference analysis or independent execution/measurement when material.
