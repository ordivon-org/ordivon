---
name: recursive-lego-calculus
description: "Apply the Ordivon Recursive LEGO Calculus when a problem must be operationalized across several abstraction layers: problem discovery, representation/re-representation, typed decomposition and composition, model/system construction, method attachment, legal operator-program search, verification, attribution, optimization, or bounded self-refinement. Use when the main difficulty may be the current representation or composition rather than a single specialist analysis method. Route specialist subquestions to their canonical method Skills; do not turn this Skill into a mega-method or execution authority."
compatibility: Cross-platform. Produces a typed problem-solving model and repair/optimization plan; it does not itself grant authority, execute effects, define domain truth, or replace specialist verification.
metadata:
  source-authority: Ordivon Recursive LEGO Calculus R1, grounded in systems engineering, assume-guarantee composition, formal refinement, verification, optimization and existing canonical Ordivon method Skills
---

# Recursive LEGO Calculus

Use this Skill when the problem spans several abstraction layers and solving harder inside the current representation may be the wrong move.

## Core rule

Treat LEGO as a **task-conditioned operational representation**, not an ontology of reality.

Separate:

`truth specification -> representation -> typed LEGO composition -> method/operator program -> execution -> verification/evidence -> attribution -> repair/optimization`.

Evidence decides which abstraction layer to revisit.

## Procedure

1. **Discover / bind the problem.** State `p=(w0, phi, Gamma)`: relevant initial world state, true target specification, and hard constraints/authority envelope. Keep `phi` separate from any verifier.
2. **Check problem admissibility.** Record importance/value, tractability, verifiability, information gain and cost. Do not promote an ungrounded or unverifiable framing into expensive solving without an explicit reason.
3. **Represent operationally.** Choose a representation `rho` that exposes the state/relations/operators needed by the task. Record loss/approximation and the obligation that transformed solutions soundly refine the original specification. If reasoning stalls, consider re-representation before merely adding reasoning depth.
4. **Choose a generator family.** Identify the compositional vocabulary `G_rho`. Do not call it a mathematical basis unless independence and completeness are established.
5. **Type the LEGO.** For each material LEGO expose enough of `(I,O,S,pre,post,inv,eff,c,epsilon,prov,unfold)` to judge compatibility, effects, cost, leakage and diagnosis.
6. **Compose only when defined.** Require type compatibility, assumption/guarantee discharge, jointly satisfiable invariants, and non-conflicting effect/authority obligations. Treat composition and operators as partial, not total.
7. **Encapsulate recursively only on net benefit.** A composite may become a higher-order LEGO when its interface is sufficient, specifications remain preserved, provenance remains traceable, and visible-complexity reduction exceeds glue/leakage/diagnostic cost. Retain `unfold`.
8. **Refine into model/system only when needed.** A model adds inference/prediction/simulation semantics; a system adds transition/effect/feedback/recovery semantics. These are LEGO refinements, not separate ontologies.
9. **Attach the smallest suitable method LEGO.** A method is a higher-order strategy `mu:(s,p,e)->partial Pi_legal(s)`. Its requirements must be satisfied by system capabilities/assumptions. Use `method-router` for a bounded specialist-method selection subproblem; then execute the selected method Skill rather than recursing through routers.
10. **Search only legal operator programs.** `Pi_legal(s)` contains programs whose preconditions hold at every intermediate state. Do not search arbitrary operator strings and call invalid sequences failed solutions.
11. **Verify independently of truth definition.** Use `nu(x)=(v,e,q)` with `v in {PASS,FAIL,UNKNOWN}`. PASS is qualified evidence, not truth by definition. Require deterministic soundness or an explicit probabilistic/empirical error envelope appropriate to the verifier.
12. **Require structured evidence.** Evidence should identify observations, claims, trace, provenance, uncertainty and, where possible, the failing `(component,port,contract,transition)` locus or a counterexample/witness.
13. **Attribute to the earliest broken abstraction.** Determine whether the first unjustified/violated layer is problem definition, representation, generator/decomposition, composition, model, system, method/operator program, authority/execution, or verifier/evidence. Repair from that layer instead of blindly restarting or retrying.
14. **Handle UNKNOWN epistemically.** Acquire evidence, change/add a verifier, re-observe, re-represent, or escalate to an external authority/human. Do not collapse UNKNOWN into FAIL or success.
15. **Optimize after feasibility.** Optimize explicit objectives over the dependent architecture/configuration space; representation, generator family, composition, model, system, method and parameters may all be variables. Prefer Pareto treatment when values conflict.
16. **Bound self-reference.** The framework/process itself may become a problem object, but current self-refinement must be judged by an external anchor envelope outside the mutable domain, within a trust region and with rollback. Make no general convergence or monotonic-improvement claim.

## Specialist routing

Use this Skill as the cross-layer scaffold, then delegate specialist questions to natural owners, for example:

- boundary/context -> `systems-engineering`;
- coupling/decomposition test -> `design-structure-matrix`;
- assumption/guarantee composition or substitution -> `compositional-contracts`;
- causal effect -> `causal-intervention`;
- failure propagation -> `fmea-fta`;
- unsafe interactions -> `stpa`;
- dynamics/control -> `feedback-control`;
- information influence -> `information-flow-analysis`;
- open-ended concept generation -> `ck-design`;
- candidate-population search -> `evolutionary-search`;
- sequential exploration allocation -> `exploration-policy`;
- organizational viability -> `organizational-cybernetics`;
- project-native transferable kernel -> `project-kernel-decomposition`.

Do not activate every lens. Choose only methods that can change the decision.

## Required distinctions

Keep these separate:

- `phi` / true specification != verifier result;
- representation != object;
- generator family != mathematical basis unless proven;
- interface shape != substitutability;
- composition legality != real-world correctness;
- execution success != semantic success;
- PASS != universal truth;
- UNKNOWN != FAIL;
- solve != optimize;
- model/system abstraction != natural authority;
- self-refinement != self-certification.

## Output

Produce the smallest useful set of:

- problem/specification/constraint tuple;
- current representation and preservation/loss obligations;
- generator family and typed LEGO/composition graph;
- model/system refinements only when they matter;
- selected method LEGO(s) and attachment assumptions;
- legal operator-program/search boundary;
- verifier + structured evidence contract;
- current verdict with UNKNOWN preserved explicitly;
- attribution to the earliest broken abstraction;
- repair/optimization action and external anchor when meta-refinement is involved.

Do not emit empty formalism merely to fill every field.

## Non-claims

- This Skill is not a definition of intelligence.
- It does not make a model, verifier, benchmark or fitness function authoritative.
- It does not prove that encapsulation lowers total complexity.
- It does not guarantee global improvement, convergence or a fixed point under self-reference.
- It does not create new Runtime/Host/Gateway owners or a Representation/LEGO mega-service.
- It does not replace domain standards or the specialist Skills it routes to.

## Stop condition

Stop when the current problem has a sound-enough operational representation, all proposed compositions/operator steps are contract-admissible, the next specialist method/execution is clear, and verification/repair paths are explicit. Re-enter only when new evidence invalidates an assumption, representation, composition, method, verifier or objective.

Canonical local reference:
- `catalogs/knowledge/lessons/lego-recursive-calculus-r1.md`

Formal details and conformance cases:
- `references/formal-model.md`
- `references/conformance-cases.md`
