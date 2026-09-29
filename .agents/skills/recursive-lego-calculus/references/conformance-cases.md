# Recursive LEGO Calculus — conformance cases R1

Use these cases to catch regressions in the method contract.

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
- search `Pi_legal(s)` only, where every intermediate precondition is satisfied.

## C4 Over-strong change-of-basis analogy

Bad:
- call a decomposition a basis without independence/completeness;
- assume a representation transform preserves solutions.

Required:
- call it a generator family unless basis properties are proved;
- require sound specification refinement across representation change.

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
- use structured evidence with a trace/locus/counterexample/provenance/uncertainty;
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
- infer monotonic global improvement from internal score gain.

Required:
- freeze an external anchor envelope outside the current mutable domain;
- use holdout/real-world outcomes and independent measurement where needed;
- trust-region, rollback and explicit non-convergence claims.

## C10 Method attachment

Bad:
- attach a discipline because its name sounds relevant.

Required:
- express method requirements and system capabilities/assumptions;
- attach only when the requirements are discharged;
- preserve the specialist method Skill's own stop conditions and non-claims.

## C11 Earliest-broken-abstraction repair

Bad:
- every verification failure restarts the whole project;
- every physical failure becomes a representation rewrite.

Required:
- locate the earliest layer actually invalidated by evidence;
- repair from that layer and preserve still-current layers.

## C12 Scope discipline

Bad:
- claim this calculus defines intelligence;
- create a new Representation Manager / LEGO Manager daemon because the method has a representation layer.

Required:
- keep the calculus as an advisory reasoning contract;
- natural owners remain authoritative for world state, execution, policy and evidence.
