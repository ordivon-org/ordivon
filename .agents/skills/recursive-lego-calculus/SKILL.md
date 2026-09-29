---
name: recursive-lego-calculus
description: "Apply the Ordivon Recursive LEGO Calculus when a problem must be operationalized across several abstraction layers: problem discovery, representation/re-representation, typed decomposition and composition, model/system construction, method attachment, legal operator-program search, verification, attribution, optimization, or bounded self-refinement. Use when the main difficulty may be the current representation or composition rather than a single specialist analysis method. Route specialist subquestions to their canonical method Skills; do not turn this Skill into a mega-method or execution authority."
compatibility: Cross-platform. Produces a typed problem-solving model and repair/optimization plan; it does not itself grant authority, execute effects, define domain truth, or replace specialist verification.
metadata:
  source-authority: Ordivon Recursive LEGO Calculus R2, grounded in systems engineering, assume-guarantee composition, formal refinement, verification, optimization and existing canonical Ordivon method Skills
---

# Recursive LEGO Calculus

Use this Skill when the problem spans several abstraction layers and solving harder inside the current representation may be the wrong move.

## Core rule

Treat LEGO as a **task-conditioned operational representation**, not an ontology of reality.

Separate:

`truth specification -> representation -> typed LEGO composition -> method/operator program -> execution -> verification/evidence -> attribution -> repair/optimization`.

Evidence determines the minimal broken frontier to revisit; a single earliest broken layer is only the linear special case.

## Procedure

1. **Discover / bind the problem.** State `p=(w0, phi, Gamma)`: relevant initial world state, true target specification, and hard constraints/authority envelope. Keep `phi` separate from any verifier.
2. **Check problem admissibility.** Record importance/value, tractability, verifiability, information gain and cost. Do not promote an ungrounded or unverifiable framing into expensive solving without an explicit reason.
3. **Represent operationally.** Choose a representation `rho` that exposes the state/relations/operators needed by the task. Record loss/approximation and the exact refinement mode by which transformed solutions preserve the original specification. If reasoning stalls, consider re-representation before merely adding reasoning depth.
4. **Choose a generator family.** Identify the compositional vocabulary `G_rho`. Do not call it a mathematical basis unless independence and completeness are established.
5. **Type the LEGO.** For each material LEGO expose enough of `(I,O,S,pre,post,inv,eff,c,epsilon,prov,unfold)` to judge compatibility, effects, cost, leakage and diagnosis.
6. **Compose only when defined.** Require type compatibility, assumption/guarantee discharge, jointly satisfiable invariants, and non-conflicting effect/authority obligations. Treat composition and operators as partial, not total.
7. **Encapsulate recursively only on net benefit.** A composite may become a higher-order LEGO when its interface is sufficient, specifications remain preserved, provenance remains traceable, and visible-complexity reduction exceeds glue/leakage/diagnostic cost. Retain `unfold`.
8. **Refine into model/system only when needed.** A model adds inference/prediction/simulation semantics; a system LEGO `Sigma` adds state-space, transition/effect/feedback/recovery semantics. Keep `Sigma` distinct from mutable runtime state `sigma_t in State(Sigma)`.
9. **Attach the smallest suitable method LEGO.** A method is a higher-order strategy `mu:(Sigma,sigma0,p,e)->partial Pi_legal(Sigma,sigma0)`. Its requirements must be satisfied by system capabilities/assumptions. Use `method-router` for a bounded specialist-method selection subproblem; then execute the selected method Skill rather than recursing through routers.
10. **Search only legal operator programs.** `Pi_legal(Sigma,sigma0)` contains programs whose preconditions hold at every intermediate state. Do not search arbitrary operator strings and call invalid sequences failed solutions.
11. **Verify independently of truth definition.** Use `nu(x)=(v,e,q)` with `v in {PASS,FAIL,UNKNOWN}`. PASS is qualified evidence, not truth by definition. `q` must state the actual guarantee kind: deterministic soundness, procedure-level false-acceptance control, conditional PASS reliability, completeness/false-rejection control, or another explicit domain-native contract. Do not substitute a joint `P(PASS and false)` bound for `P(false | PASS)`.
12. **Use mature formal owners for bounded obligations.** Prefer the smallest natural provider that matches the semantics (for example Z3 for bounded logical obligations/counterexamples, Unified Planning for legal action programs, Pacti for explicitly algebraic contracts when admitted, TLA+/TLC for concurrent temporal/state-machine properties, pySHACL for RDF shapes). A tool PASS proves only the encoded obligation under its assumptions.
13. **Require structured evidence.** Evidence should identify observations, claims, trace, provenance, uncertainty and, where possible, failing `(component,port,contract,transition)` loci or a counterexample/witness.
14. **Attribute to the minimal broken frontier.** Model abstraction dependencies as a graph when needed. Identify all minimal evidence-supported invalid loci; there may be several incomparable ones. Repair from that frontier and preserve unaffected/current subgraphs instead of blindly restarting or retrying.
15. **Handle UNKNOWN epistemically.** Acquire evidence, change/add a verifier, re-observe, re-represent, or escalate to an external authority/human. Do not collapse UNKNOWN into FAIL or success.
16. **Optimize after feasibility.** Optimize explicit objectives over the dependent architecture/configuration space; representation, generator family, composition, model, system, method and parameters may all be variables. Prefer Pareto treatment when values conflict.
17. **Bound self-reference.** The framework/process itself may become a problem object, but current self-refinement must be judged by an external anchor envelope outside the mutable domain, within a trust region and with rollback. The candidate must not control hidden labels, benchmark selection, measurement implementation or acceptance thresholds used to certify that same refinement. Make no general convergence or monotonic-improvement claim.

## Specialist routing

Use this Skill as the cross-layer scaffold, then delegate specialist questions to natural owners, for example:

- boundary/context -> `systems-engineering`;
- coupling/decomposition test -> `design-structure-matrix`;
- causal effect -> `causal-intervention`;
- failure propagation -> `fmea-fta`;
- unsafe interactions -> `stpa`;
- dynamics/control -> `feedback-control`;
- information influence / evaluator-anchor leakage -> `information-flow-analysis`;
- open-ended concept generation -> `ck-design`;
- candidate-population search -> `evolutionary-search`;
- sequential exploration allocation -> `exploration-policy`;
- organizational viability -> `organizational-cybernetics`;
- project-native transferable kernel -> `project-kernel-decomposition`.

For algebraic assume/guarantee composition or substitution, prefer the admitted formal-contract provider when the seam is actually formalized; do not create a proprietary universal contract language merely to satisfy this Skill.

Do not activate every lens. Choose only methods/providers that can change the decision.

## Required distinctions

Keep these separate:

- `phi` / true specification != verifier result;
- procedure-level false-acceptance control != conditional PASS reliability;
- representation != object;
- universal-safe refinement != witness-preserving refinement;
- generator family != mathematical basis unless proven;
- system specification `Sigma` != runtime state `sigma_t`;
- interface shape != substitutability;
- composition legality != real-world correctness;
- execution success != semantic success;
- formal-tool PASS != whole-system/domain truth;
- PASS != universal truth;
- UNKNOWN != FAIL;
- solve != optimize;
- model/system abstraction != natural authority;
- self-refinement != self-certification.

## Output

Produce the smallest useful set of:

- problem/specification/constraint tuple;
- current representation, refinement mode and preservation/loss obligations;
- generator family and typed LEGO/composition graph;
- model/system refinements and `Sigma`/`sigma` separation only when they matter;
- selected method LEGO(s), formal providers if applicable, and attachment assumptions;
- legal operator-program/search boundary;
- verifier guarantee kind + structured evidence contract;
- current verdict with UNKNOWN preserved explicitly;
- minimal broken frontier (or singleton earliest layer on a linear path);
- repair/optimization action and external anchor when meta-refinement is involved.

Do not emit empty formalism merely to fill every field.

## Non-claims

- This Skill is not a definition of intelligence.
- It does not make a model, verifier, solver, benchmark or fitness function authoritative.
- It does not prove that encapsulation lowers total complexity.
- It does not guarantee global improvement, convergence or a fixed point under self-reference.
- It does not create new Runtime/Host/Gateway owners or a Representation/LEGO mega-service.
- It does not replace domain standards or the specialist Skills/tools it routes to.

## Stop condition

Stop when the current problem has a sound-enough operational representation, proposed compositions/operator steps are contract-admissible, applicable narrow formal obligations have either been checked by their natural provider or explicitly left UNKNOWN/unsupported, the next specialist method/execution is clear, and verification/repair paths are explicit. Re-enter only when new evidence invalidates an assumption, representation, composition, method, verifier, objective or external anchor.

Canonical local reference:
- `catalogs/knowledge/lessons/lego-recursive-calculus-r2.md`

Formal details, cases and local conformance harness:
- `references/formal-model.md`
- `references/conformance-cases.md`
- `references/formal-conformance-r2.py`
