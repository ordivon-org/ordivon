# Ordivon Recursive LEGO Calculus R2

Date: 2026-09-29
Status: FORMALIZED CANDIDATE / LOCAL BOUNDED FORMAL CONFORMANCE PASS / PROSPECTIVE EXTERNAL VALIDATION REQUIRED

## Purpose

R2 is the current formal synthesis of the Ordivon LEGO method. It treats LEGO as a task-conditioned operational representation and organizes problem solving as a recursive, typed, evidence-driven graph:

`discover -> represent -> generate -> compose -> model -> systemize -> attach method -> search legal program -> execute -> verify -> attribute -> repair/optimize`.

The graph is recursive rather than a mandatory waterfall. Any composite, model, system, method or even the framework itself may become a later problem object, subject to bounded self-reference and an external acceptance anchor.

R2 does **not** define intelligence, claim that reality is literally made of LEGO, replace mature disciplines, or infer domain truth from a formal-tool PASS.

## 1. Problem truth is prior to verification

A problem is `p=(w0,phi,Gamma)` in a declared problem-instance space. The true solution set is `X*_p={x | phi(x;w0,Gamma)=1}`. `phi` is not defined by a verifier.

R2 distinguishes deterministic soundness, procedure-level false-acceptance/type-I control, conditional reliability of PASS (which additionally needs a calibrated population/base-rate model), and optional false-rejection/completeness guarantees. A small joint probability `P(PASS and false)` is not a substitute for `P(false | PASS)`.

## 2. Representation is operationalization with a refinement obligation

A representation `rho` supplies abstraction/encoding, concretization, transformed specification, approximation/loss envelope and a candidate-refinement relation. It is useful only when it makes valid operators cheaper/clearer and preserves the original specification under an explicit refinement mode.

R2 distinguishes universal-safe refinement from witness-preserving refinement. A single-valued `back` function is only one special case.

## 3. Generator family, typed LEGO and partial composition

The compositional vocabulary is a generator family `G_rho`, not a mathematical basis unless independence and completeness are proved. A LEGO is a typed, contracted, encapsulatable, qualifiable and composable operational abstraction. Composition is partial and requires type, assume/guarantee, invariant, effect/authority and seam compatibility. Schema closure does not establish real-world correctness.

## 4. Recursive encapsulation does not imply monotonic complexity reduction

A composite may be lifted only when its visible-complexity gain exceeds glue, leakage and diagnosis costs for the task while preserving specification, provenance and `unfold`. A representative criterion is `G_enc = DeltaC_visible - C_glue - lambda*L_leak - mu*C_diagnose`.

## 5. Model/system refinement and state separation

A model LEGO adds inference/prediction/simulation semantics. A system LEGO `Sigma` adds state space, transitions/effects, feedback and recovery contracts. `Sigma` is not the current state: runtime state is `sigma_t in State(Sigma)`.

A legal operator program preserves every intermediate precondition. Abstract execution is `Exec(Sigma,sigma0,pi)=(trajectory,candidate,execution-evidence)`, keeping architecture, mutable state, process exit and semantic solution separate.

## 6. Methods are higher-order LEGO

A method LEGO is `mu:(Sigma,sigma0,p,e)->partial Pi_legal(Sigma,sigma0)`. It generates/selects legal operator programs only when its assumptions are discharged. Specialist disciplines remain natural owners rather than being copied into this calculus.

## 7. Verification, evidence and minimal broken frontier

Evidence must support observations, trace, provenance, uncertainty, witness/counterexample and loci such as `(component,port,contract,transition)`. Because abstraction dependencies form a graph, R2 replaces an always-singular "earliest broken layer" with the **minimal broken frontier**: all minimal evidence-supported invalid loci. The singleton earliest layer is only the linear special case.

UNKNOWN is epistemic, not weak FAIL.

## 8. Optimization is dependent architecture search

Solve and optimize are distinct. The search space is a dependent family over representation, generator family, composition, model, system and then system-dependent parameters/initial states/legal programs. Use Pareto treatment when objectives cannot legitimately be scalarized.

## 9. Bounded self-reference requires an external anchor and influence control

The external anchor contains frozen specifications, holdout/real-world tasks, measurement pipeline, external/human authority where needed, and commitment/isolation metadata. It must be outside the current mutable domain, and the candidate must not choose/rewrite hidden labels, benchmark selection, measurement implementation or acceptance thresholds used to judge that same refinement. Use trust regions and rollback. No general convergence/fixed-point theorem is claimed.

## 10. Mature formal providers, not a private formal universe

Route bounded obligations to natural owners: Z3 for bounded logical/arithmetic consistency and counterexamples; Unified Planning/Pyperplan for legal action programs; Pacti for explicitly algebraic assume/guarantee seams when task-admitted; TLA+/TLC for concurrent temporal/state-machine properties; pySHACL for RDF shapes; OR-Tools for discrete optimization without confusing objective value with truth.

Current local standing before the R2 test: the reasoning-waist acceptance record contains OR-Tools 9.15.6755, z3-solver 5.1.0.0, Unified Planning 1.3.0 + Pyperplan 1.1.0, RDFLib 7.6.0 and pySHACL 0.40.1; Pacti 0.3.1 has a prior isolated pilot but is deliberately not a core dependency; Runtime has a digest-pinned TLA+/TLC 1.7.4 owner and an accepted bounded concurrency model from 2026-09-19.

A formal-provider PASS is bounded evidence about the encoded model. It does not prove representation adequacy, implementation refinement, real-world domain truth or superiority of this whole workflow.

## 11. R2 local executable conformance

`references/formal-conformance-r2.py` checks only narrow obligations: deterministic soundness rejects `PASS and not phi`; a joint false-acceptance bound does not imply the corresponding conditional bound; an explicit conditional bound eliminates that counterexample; compatible and incompatible composition seams are distinguished; witness-preserving and universal-safe refinement are distinguished; Unified Planning rejects `execute` before authorization and accepts `authorize;execute` when legal. Optional Pacti availability is reported but is not required.

## 12. Prospective validation remains required

Local formal conformance is not the external anchor experiment. A real comparison must freeze task, inputs, true specification and anchor, then compare the earlier workflow with R2 on semantic acceptance, invalid composition/operator rate, rework, resource cost, failure-localization accuracy, representation changes, UNKNOWN/verifier disagreement and holdout/real-world regression.

Only such evidence can support a stronger claim that R2 improves real problem solving.

## 13. Local R2 conformance result — 2026-09-29

The bounded local harness passed under the existing reasoning-waist interpreter.

Observed live providers:
- Z3 `5.1.0`;
- Unified Planning `1.3.0`;
- OR-Tools `9.15.6755`;
- RDFLib `7.6.0`;
- pySHACL `0.40.1`;
- Pacti: optional provider not present in the current reasoning-waist environment; prior isolated 0.3.1 pilot remains historical evidence only.

Machine-checked R2 obligations passed:
- deterministic soundness rejects a false PASS;
- a joint false-acceptance bound admits a counterexample to the corresponding conditional reliability claim;
- the explicit conditional bound eliminates that counterexample;
- a compatible post/pre composition seam has no encoded counterexample while an incompatible seam does;
- witness-preserving refinement can hold while universal-safe refinement fails, confirming that the refinement mode must be explicit;
- an unauthorized operator program is invalid while the authorized sequence is valid.

The current detached workspace did not contain the ignored TLA+/TLC JAR cache, so `services/runtime/scripts/tla-formal check` returned the expected cache-missing gate rather than a model verdict. The digest-pinned TLA+/TLC 1.7.4 owner and the previously accepted Runtime bounded model remain separate evidence; no temporal claim in R2 depends on pretending that this rerun occurred.

This local PASS qualifies only the encoded conformance obligations. Prospective real-task validation remains open.

## Historical lineage

R2 supersedes `catalogs/knowledge/lessons/lego-recursive-calculus-r1.md` as the current synthesis while preserving R1 and earlier LEGO documents as historical evidence. Specialist method Skills and natural external owners retain their own authority.
