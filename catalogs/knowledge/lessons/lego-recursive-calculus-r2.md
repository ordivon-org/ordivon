# Ordivon Recursive LEGO Calculus R2.1

Date: 2026-09-29
Status: FORMALIZED CANDIDATE / LOCAL BOUNDED FORMAL CONFORMANCE PASS / PROSPECTIVE EXTERNAL VALIDATION REQUIRED

## Purpose

R2.1 is the current formal synthesis of the Ordivon LEGO method. It treats LEGO as a task-conditioned operational representation and organizes problem solving as a recursive, typed, evidence-driven graph:

`discover -> admit problem -> represent -> generate -> compose -> model -> systemize -> attach method -> search legal program -> execute -> verify encoded obligation + bridge -> attribute -> repair/optimize`.

The graph is recursive rather than a mandatory waterfall. Any composite, model, system, method or even the framework itself may become a later problem object, subject to bounded self-reference and an external acceptance anchor.

R2.1 does **not** define intelligence, claim that reality is literally made of LEGO, replace mature disciplines, or infer domain truth from a formal-tool PASS.

## 1. Discovery is itself a gated search problem

The world does not arrive already scoped. Candidate framings are compared on at least importance/value, tractability, verifiability, information gain and cost. Use Pareto/policy selection unless a legitimate scalar utility is supplied by an external/domain authority. Before expensive solving, a discovery gate checks that the boundary is evidence-grounded, the target is operationalizable, unknowns/assumptions are explicit and a verification path exists.

## 2. Problem specification is prior to verification

For admitted `p=(w0,phi,Gamma)`, candidate solution space is `X_p` and `X*_p={x in X_p | phi(x;w0,Gamma)=1}`. Here `phi` is the admitted normative/domain specification, not a claim of metaphysical omniscience.

A verifier usually checks an encoded predicate `psi_nu`. Local soundness is `PASS=>psi_nu`; a claim about `phi` additionally requires a justified bridge `psi_nu=>phi`, unless the two predicates are exactly identical by construction.

R2.1 also distinguishes deterministic soundness, procedure-level false-acceptance/type-I control, conditional reliability of PASS (which requires a calibrated population/base-rate model), and optional false-rejection/completeness guarantees. A small joint probability `P(PASS and false)` is not a substitute for `P(false | PASS)`.

## 3. Representation is operationalization with realizability and refinement obligations

A representation `rho` supplies abstraction/encoding, concretization, transformed specification, approximation/loss envelope and a candidate-refinement relation from transformed candidates `X_{rho,p}` to original candidates `X_p`.

R2.1 distinguishes universal-safe refinement from witness-preserving refinement. Universal-safe refinement explicitly requires at least one concrete realization; otherwise `forall related x` can become vacuously true on an empty relation. A single-valued `back` function is only the total-functional special case.

## 4. Generator family, typed LEGO and partial composition

The compositional vocabulary is a generator family `G_rho`, not a mathematical basis unless independence and completeness are proved. A LEGO is a typed, contracted, encapsulatable, qualifiable and composable operational abstraction. Domain compatibility/refinement relations must be declared. Composition is partial and requires type, assume/guarantee, invariant, effect/authority and seam compatibility. Schema closure does not establish real-world correctness.

## 5. Recursive encapsulation does not imply monotonic complexity reduction

A composite may be lifted only when its visible-complexity gain exceeds glue, leakage and diagnosis costs for the task while preserving specification, provenance and `unfold`. A representative criterion is `G_enc = DeltaC_visible - C_glue - lambda*L_leak - mu*C_diagnose`.

## 6. Model/system refinement and state separation

A model LEGO adds inference/prediction/simulation semantics. A system LEGO `Sigma` adds state space, transitions/effects, feedback and recovery contracts. Configuration `theta` instantiates it; runtime state is `sigma_t in State(Sigma,theta)`.

A legal operator program preserves every intermediate precondition. Abstract execution is `Exec(Sigma,theta,sigma0,pi)=(trajectory,candidate,execution-evidence)`, keeping architecture, configuration, mutable state, process exit and semantic solution separate.

## 7. Methods are higher-order LEGO

A method LEGO is `mu:(Sigma,theta,sigma0,p,e)->partial Pi_legal(Sigma,theta,sigma0)`. It generates/selects legal operator programs only when its assumptions are discharged. Specialist disciplines remain natural owners rather than being copied into this calculus.

## 8. Verification, evidence and minimal broken frontier

Evidence must support observations, trace, provenance, uncertainty, witness/counterexample and loci such as `(component,port,contract,transition)`. Because abstraction dependencies form a graph, R2.1 uses the **minimal broken frontier**: all minimal evidence-supported invalid loci under an explicitly directed prerequisite/refinement relation. A singleton earliest layer is only the linear special case.

UNKNOWN is epistemic, not weak FAIL.

## 9. Optimization is constrained dependent architecture search

Solve and optimize are distinct. The search space is a dependent family over representation, generator family, composition, model, system, configuration, admissible initial state and legal program; every dependent variable is bound before use.

Optimization occurs inside a qualified feasible region. Finding one feasible baseline never authorizes later optimizer steps to violate hard constraints. If a change invalidates prior acceptance evidence, it returns to verification before acceptance. Use Pareto treatment when objectives cannot legitimately be scalarized.

## 10. Bounded self-reference requires an external anchor and influence control

The external anchor contains frozen specifications, holdout/real-world tasks, measurement pipeline, external/human authority where needed, and commitment/isolation metadata. It must be outside the current mutable domain, and the candidate must not choose/rewrite hidden labels, benchmark selection, measurement implementation or acceptance thresholds used to judge that same refinement. Anchor immutability alone is therefore insufficient; material leakage is an information-flow/noninterference problem. Use trust regions and rollback. No general convergence/fixed-point theorem is claimed.

## 11. Mature formal providers, not a private formal universe

Route bounded obligations to natural owners: Z3 for bounded logical/arithmetic consistency and counterexamples; Unified Planning/Pyperplan for legal action programs; Pacti for explicitly algebraic assume/guarantee seams when task-admitted; TLA+/TLC for concurrent temporal/state-machine properties; pySHACL for RDF shapes; OR-Tools for discrete optimization without confusing objective value with truth.

Current local standing: the reasoning-waist provides Z3 5.1.0, Unified Planning 1.3.0, OR-Tools 9.15.6755, RDFLib 7.6.0 and pySHACL 0.40.1. Pacti 0.3.1 has a prior isolated pilot but is deliberately not a core dependency. Runtime has a digest-pinned TLA+/TLC 1.7.4 owner and a previously accepted bounded concurrency model; the current detached workspace lacked its ignored JAR cache, so no fresh TLC rerun is claimed.

A formal-provider PASS is bounded evidence about the encoded model. It does not prove representation adequacy, implementation refinement, real-world domain truth or superiority of this whole workflow.

## 12. Local executable conformance

The adjacent `references/formal-conformance-r2.py` tests only narrow obligations. R2.1 adds probes for verifier encoding bridges, non-vacuous representation realizability, composition seams and feasibility-preserving optimization in addition to the existing probability and legal-program probes.

The harness must be rerun after this R2.1 revision; only its exact result may change this document's local-conformance status to PASS.

## 13. Prospective validation remains required

Local formal conformance is not the external anchor experiment. A real comparison must freeze task, inputs, problem specification and anchor, then compare the earlier workflow with R2.1 on semantic acceptance, invalid composition/operator rate, rework, resource cost, failure-localization accuracy, representation changes, UNKNOWN/verifier disagreement and holdout/real-world regression.

Only such evidence can support a stronger claim that R2.1 improves real problem solving.

## Historical lineage

R2.1 supersedes R2/R1 as the current candidate synthesis while preserving earlier artifacts as historical evidence. Specialist method Skills and natural external owners retain their authority.
