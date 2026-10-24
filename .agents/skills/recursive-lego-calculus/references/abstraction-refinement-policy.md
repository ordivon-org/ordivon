# R2.1 representation selection: CEGAR and optional MSR

Status: current method decision, 2026-10-25. It supplements the immutable observed original R2.1 formal-model reference; no historical source digest is rewritten.

## Why Minimum Sufficient Representation is no longer the default

MSR is an OPTIONAL method/Skill LEGO, not a theorem, safety property, architecture mandate or standard release gate.

| Useful heuristic | Why it is not generally sufficient or minimal |
| --- | --- |
| Reduce unnecessary fields and mechanics | Abstraction can discard race conditions, attacks, error transitions, consumer effects and unknown requirements. |
| Lower routine Agent and tool costs | Proving all alternatives inferior, or proving the representation preserves its specification, can cost more than direct repair. |
| Reduce local interfaces | Glue and cross-Owner uncertainty may increase total complexity. |
| Speed exploration | Narrow acceptance tests are not proof against unseen future needs. |

For an explicit candidate set R and accepted property phi, a genuine claim requires Qualified(r,phi), a specified cost preorder and a lower-bound obligation: no qualified alternative is strictly cheaper. Neither exhaustive minimality nor qualified sufficiency comes free. Label unsupported proposals HEURISTIC or UNKNOWN, not MINIMUM, SUFFICIENT or SAFE. Use local, reversible compression only with consumer acceptance and rollback.

## Mature counterexample-guided abstraction refinement

Foundational source: Clarke, Grumberg, Jha, Lu and Veith, Counterexample-Guided Abstraction Refinement, CAV 2000; https://doi.org/10.1007/10722167_15.
Applied software model-checking source: Microsoft Research SLAM; https://www.microsoft.com/en-us/research/project/slam/.

For a concrete transition system C=(S,I,T) and safety property phi, choose an abstraction alpha:S->A and concretization gamma:A->2^S. Establish a sound overapproximation of initial states, transitions and the safety-predicate projection under an EXACT source-cut and declared assumptions.

1. Abstract model proves the safety property: the concrete MODEL inherits only that safety claim, conditional on the proved simulation and preserved property. This does not prove unmodelled real-world operations or liveness.
2. Abstract model provides trace t: check concrete path feasibility with actual initial and transition constraints using an admitted SMT/TLC/native verifier. SAT with a concrete witness means a REAL concrete-model counterexample; UNSAT means SPURIOUS and supports adding a predicate or state distinction that removes this trace without losing overapproximation; UNKNOWN means UNKNOWN.
3. After refinement: re-establish soundness, preserve property and source identity, and rerun. Never silently change assumptions, source, fairness conditions or ownership.
4. Stop on a proved scoped obligation, a realizable counterexample or bounded UNKNOWN due to time/iteration/state/resource/source drift. No general termination or completeness claim follows.

Per iteration preserve (sourceRevision, modelDigest, abstractionId, propertyId, assumptions, trace, concretizationResult, witnessOrUnsatEvidence). If these are not bound, never promote PASS or FAIL to the domain.

### Reuse, not a new framework

- Temporal and concurrency properties: existing digest-pinned TLA+/TLC and source-bound Runtime/Host/Harness/Network models.
- Finite predicate feasibility/trace replay: admitted local Z3/SMT.
- Actual compositional contracts: existing Owner-native assumptions/guarantees and optional Pacti where the interface supports it.
- JSON, identity and type constraints: mature strict parsers and JSON Schema, which do NOT independently prove runtime safety.

Abstract PASS is not implementation PASS; abstract FAIL is not real failure without concretization; verification is not domain completion. An omitted requirement remains UNKNOWN. Preserve the six-role LEGO responsibility interface and add only proof objects that change real consumer decisions.
