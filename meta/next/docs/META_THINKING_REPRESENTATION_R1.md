# Meta-Thinking R1 — Minimum Sufficient Representation

Status: ADOPTED AS COLLABORATION / PROPOSED AS REPO METHOD, **NOT** DEPLOYMENT OR NEW AUTHORITY
Date: 2026-10-24
Coordination: `space:ordivon-meta-thinking-r1:20261024`
Existing implementations: `meta/next/docs/COMPOSITION_SCIENCE_R1.md`, `meta/next/docs/INNOVATION_LENS_ROUTING_R1.md`, `.agents/skills/method-router`, and each natural owner's tests and formal models.

## Why this exists

Ordivon's limiting factor is not primarily raw compute. It is the cost of distinguishing necessary states, relations, interactions, ambiguity, and evidence from incidental complexity. Make the *question* simpler before making its *execution* stronger.

For context X and accepted observable behavior B, choose representation R and implementation A to reduce the measured cost of comprehension, state, coupling, operation, verification and maintenance, **subject to** preserving B for X. No universal scalar complexity score or context-free best architecture is asserted.

## Reform mandate and boundaries

Meta-Thinking can initiate cross-owner architecture challenges, propose and implement scoped candidate replacements and deletions through existing owner-approved execution paths, compare competing representations, and demand falsifiable consumer evidence. It does **not** unilaterally redefine Git/Runtime/Host/domain truth, override security approvals, publish proof claims from green CI, or become a duplicate orchestrator, LEGO registry, or perennial Agent staff.

The existing social Space is long-lived only as a discussion/navigation surface. A concrete reform is a short-lived Work/PR when genuinely necessary, with exact source cuts and owner-native gates. Historical knowledge is not current-state evidence.

## Diagnostic: separate three causes

- Essential: real domain variety, latency, failure, computation and risk that cannot be removed without changing B.
- Accidental: duplicated owners, redundant wrappers, implicit environment, inconsistent terminology, unneeded conditions and special-case implementations.
- Epistemic: missing consumer, unknown runtime context, weak observation or inability to tell competing explanations apart.

A failure may involve all three. Do not confuse a missing observation with hard intrinsic computational difficulty.

## Ten lenses, one minimum method

See `.agents/skills/method-router/references/representation-first.md` for practical routing and negative checks.

| Lens | Key question about a LEGO | Complexity that may disappear |
| --- | --- | --- |
| Type-driven | Can illegal input or state be made unconstructible? | Dynamic guards and invalid variants |
| Constraint-first | What must components assume and guarantee? | Ad hoc compatibility branches |
| Graph-first | Who really consumes or depends on this? | Blind cleanups and implicit coupling |
| State-machine-first | Which transitions and interleavings are permitted? | Hidden temporal behavior |
| Algebra-first | Which lawful generic operators generate families? | Handwritten variants |
| Equivalence-first | Which implementations are substitutable in context? | Duplicate implementations and branches |
| Declarative-first | Are dependencies, versions and environment explicit? | Implicit machine-specific behavior |
| Abstraction-first | Can hierarchical summaries preserve required behavior? | Global reasoning across every combination |
| Causal-first | What controlled intervention distinguishes root causes? | Symptom-driven retry/patch cycles |
| Compression-first | What minimum source-and-context-bound knowledge predicts correct use? | Stale and repeated procedural knowledge |

Two cross-cutting obligations: **LEGO-first** fixes the replaceable consumer-conditioned unit; **Formal-first** fixes the acceptance predicate, assumptions, guarantees, transitions, and evidence. Neither one is an extra universal truth database.

## Typed problem representation (conceptual, not a new shared runtime schema)

`Problem_X = (Goal, Owner, Consumers, Evidence, Unknowns, Constraints, ObservableBehavior)`

`LEGO_X = (Input, Output, Assumptions, Guarantees, Effects, StateTransitions, Dependencies, ProofObligations)`

`Reform = (sourceCut, problem_X, candidateReduction, selectedNativeMethod, counterexample, ownerVerification, consumerAcceptance, disposition)`

Only carry fields that actually change the decision. Missing fact = `UNKNOWN` rather than `PASS` or `NO_CONSUMER`.

## Invariants for candidate reform

1. **Required behavior preserved:** consumer-observable requirements remain true for the declared context, including side effects, ownership and environment assumptions.
2. **No invented authority:** a Meta-Thinking proposal cannot commit an effect; owner-native tools perform any changes under their existing authority.
3. **No unproved deletion:** static absence of a reference is not complete proof that no runtime/external consumer exists; check declared dynamic boundaries or explicitly mark unknown.
4. **State correctness:** the model distinguishes admissible transitions and tests counterexamples, including cancellation, retry and out-of-order events where applicable.
5. **Composition correctness:** individually passing LEGO checks are not sufficient to show assumptions are discharged at the composition boundary.
6. **Claim/evidence alignment:** process exit, test PASS, bounded formal model, measured cause and real consumer acceptance have different claim scopes.
7. **No new framework without residual:** prefer native type checker, owner tests, TLA+ model, CUE/JSON Schema, DSM/Datalog, or causal test as justified by actual scale.
8. **Self-subtraction:** remove this meta mechanism if it adds a second source of truth, requires universal manual metadata, or fails to change outcomes.

## Minimal operating loop

`GOAL -> OBSERVE -> IDENTIFY COMPLEXITY SOURCE -> ELIMINATE/QUOTIENT/CONSTRAIN/DECOUPLE/RESOLVE -> SELECT MATURE LEGO -> OWNER-NATIVE VERIFY -> CONSUMER ACCEPT -> EVOLVE OR RETIRE`.

Record only actual gaps and counterexamples, not generic reports. Begin with one primary method; use a second only if it supplies independently necessary evidence.

## First executable reform candidates

1. Improve existing `method-router` to ask complexity-removal questions before selecting a method; use native `meta/next/tests/test_method_router_skill.py` to check navigation integrity (not semantic proof).
2. Select one Runtime Workspace lifecycle invariant; relate its finite formal model to the actual code and a failing/negative regression case.
3. Select one Git/LEGO deletion candidate; gather static **and** dynamic consumers, distinguish `used` / `unused with bounded proof` / `unknown`, and qualify deletion through native tests.
4. Select one Golden Path traversing real owner boundaries; bind CDC, telemetry, replay, fault injection and consumer acceptance to the **same** obligation.

These are candidates, not claims of completion. A completed work must have specific owner-native test output and a source/PR commit; a Space post is only a proposal.

## Mature methods, not Ordivon-owned theories

- CUE constraint/unification specification: https://cuelang.org/docs/reference/spec/
- Soufflé typed Datalog and reachability/static analysis: https://souffle-lang.org/docs/home/
- Alloy relational/model exploration: https://alloytools.org/about
- TLA+ proof/model work for state and concurrency: https://proofs.tlapl.us/doc/web/content/Home.html

Adopt incrementally at the demonstrated seam. Do not install a new tool merely to satisfy this list.
