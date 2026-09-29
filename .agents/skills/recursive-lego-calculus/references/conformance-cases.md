# Recursive LEGO Calculus — conformance cases R2

Use these cases to catch regressions in the method contract. A prose case may be paired with a machine-checkable obligation when a mature provider matches the semantics; not every case should be forced into SMT/model checking.

## C1 Truth/verifier separation

Bad:
- define the solution set as `{x | verifier(x)=PASS}`;
- later claim PASS may be wrong.

Required:
- define `phi` and `X*_p` independently;
- give the verifier a soundness/error envelope relative to `phi`.

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
- search `Pi_legal(Sigma,sigma0)` only, where every intermediate precondition is satisfied.

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
- write one Cartesian product `Theta x LEGO x Relation x Representation x Operator` when parameter/operator spaces depend on architecture choices.

Required:
- use a dependent sum/family or an equivalent typed configuration structure.

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
- attach only when the requirements are discharged;
- preserve the specialist method Skill's own stop conditions and non-claims.

## C11 Minimal broken frontier repair

Bad:
- every verification failure restarts the whole project;
- every physical failure becomes a representation rewrite;
- force a single "earliest" broken layer when evidence points to two incomparable branches.

Required:
- compute/argue the minimal evidence-supported broken frontier in the abstraction dependency graph;
- repair from each minimal locus that is actually invalidated;
- preserve still-current subgraphs.

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
- declare the guarantee kind in `q`;
- keep procedure-level false acceptance, conditional reliability and false rejection separate;
- state the assumptions/population under which each bound holds.

Machine probe:
- there MUST exist a probability assignment satisfying a small joint false-acceptance bound while violating an equally small conditional false-discovery bound;
- adding the conditional bound MUST eliminate that counterexample.

## C14 System specification versus runtime state

Bad:
- use one symbol/object both for the system architecture/transition contract and the current mutable state;
- write `pi(system)` when the operator program actually acts on a state admitted by the system specification.

Required:
- use `Sigma` for the system LEGO/specification and `sigma_t in State(Sigma)` for runtime state;
- define operators and legal programs relative to both.

## C15 Representation refinement mode

Bad:
- require all concretizations to satisfy the original specification when the transform only promises to reconstruct one certified witness;
- accept one witness when the representation claims universal safety over all concretizations.

Required:
- declare universal-safe or witness-preserving refinement (or another explicit sound mode);
- carry the required concrete witness/evidence when using witness-preserving refinement.

## C16 Formal-provider scope

Bad:
- translate every prose claim into SMT because Z3 is available;
- infer full implementation/domain correctness from a bounded TLA+/SMT/planning PASS;
- add optional providers to the core dependency graph without repeated real pressure.

Required:
- route only bounded obligations whose semantics match the provider;
- preserve model assumptions and non-claims;
- keep Pacti/TLA+/Z3/Unified Planning/pySHACL/OR-Tools as natural specialized owners rather than a new universal formalism.
