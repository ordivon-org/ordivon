# Meta-Thinking R1 — Counterexample-Guided Reform (CEGAR)

Status: Counterexample-guided reform ADOPTED AS COLLABORATION, NOT deployment or new authority. Minimum Sufficient Representation (MSR) as a **DEFAULT**: RETIRED (2026-10-25). MSR remains an **optional, consumer-scoped Skill LEGO**, not a general minimum/sufficiency/safety theorem. Preserve this source path for existing method-router consumers.
Date: 2026-10-24
Coordination: `space:ordivon-meta-thinking-r1:20261024`
Existing implementations: `meta/next/docs/COMPOSITION_SCIENCE_R1.md`, `.agents/skills/method-router/references/innovation-lens-routing.md`, `.agents/skills/method-router`, and each natural owner's tests and formal models.

## Why this exists

Ordivon's limiting factor is not primarily raw compute. It is the cost of distinguishing necessary states, relations, interactions, ambiguity, and evidence from incidental complexity. Make the *question* simpler before making its *execution* stronger.

For context X and a real consumer behavior B, start with a property-scoped coarse abstraction and existing Owner implementation. Check counterexamples before adding representation detail. Retire unconsumed responsibilities by consumer evidence. No global minimality or sufficiency certificate is required: proving universal minimality and sufficiency could cost more than solving the problem.

## Reform mandate and boundaries

Meta-Thinking can initiate cross-owner architecture challenges, propose and implement scoped candidate replacements and deletions through existing owner-approved execution paths, compare competing representations, and demand falsifiable consumer evidence. It does **not** unilaterally redefine Git/Runtime/Host/domain truth, override security approvals, publish proof claims from green CI, or become a duplicate orchestrator, LEGO registry, or perennial Agent staff.

The existing social Space is long-lived only as a discussion/navigation surface. A concrete reform is a short-lived Work/PR when genuinely necessary, with exact source cuts and owner-native gates. Historical knowledge is not current-state evidence.

## Diagnostic: separate three causes

- Essential: real domain variety, latency, failure, computation and risk that cannot be removed without changing B.
- Accidental: duplicated owners, redundant wrappers, implicit environment, inconsistent terminology, unneeded conditions and special-case implementations.
- Epistemic: missing consumer, unknown runtime context, weak observation or inability to tell competing explanations apart.

A failure may involve all three. Do not confuse a missing observation with hard intrinsic computational difficulty.

## Ten optional lenses, chosen by a falsifying question

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
| Compression-first | What source-and-context-bound knowledge predicts correct use? | Stale and repeated procedural knowledge |

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

## Counterexample-Guided Abstraction Refinement (CEGAR)

**No global minimality or sufficiency certificate.** Classical CEGAR is
property-scoped safety checking, not a universal optimizer, architecture
theorem or substitute for consumer acceptance.

1. Select one actual Owner, one consumer safety property and an exact
   SourceCut; start with an existing coarse abstraction.
2. Check it with a mature Owner-native model checker or contract verifier,
   where appropriate. A result proves only the encoded property and model.
3. For a reported trace, perform **abstract-to-concrete** feasibility:
   link the actions, guards, assumptions, identity and observable physical
   effects to real Owner transitions where evidence exists.
   - **REAL_COUNTEREXAMPLE**: a realizable concrete trace violates the
     consumer property. Repair Owner contract or implementation, preserve the
     counterexample, and check again.
   - **SPURIOUS_COUNTEREXAMPLE**: the abstract trace is impossible under
     the actual declared Owner assumptions. Refine only the missing
     predicate, guard, abstraction mapping or environment distinction.
   - **UNKNOWN**: missing evidence or unproved feasibility/refinement;
     neither promote PASS nor authorize deletion.
4. A model PASS supports concrete safety only with a justified
   over-approximation/simulation relation and correct property mapping.
   Bounded TLC alone does not prove Rust, Host, Harness, Network or goal
   acceptance. Liveness requires separate fairness/progress obligations.
5. For ordinary Git deletion, straightforward typed input checks or
   direct contract tests, do not force a CEGAR workflow; use the owner-native
   proof/consumer check directly.

Concrete motivation: the existing four-Owner
`packages/composition/formal/Lego21OwnerBoundary.tla` model had a
time-indexing issue when Network readiness could degrade after Runtime
admission. A failing bounded trace against a too-strong readiness invariant
requires refining *which moment* the property describes; it does not
prove that a physical Network or Runtime violated its contract. A scoped
candidate is https://github.com/ordivon-org/ordivon/pull/586 .
Do not introduce another model, solver, registry, Agent or authority.

Mature references: Clarke et al., CAV 2000,
https://doi.org/10.1007/10722167_15 ; Microsoft Research SLAM,
https://www.microsoft.com/en-us/research/project/slam/ .

## Operating loop

`GOAL -> SOURCE CUT / CONSUMER -> PROPERTY-SCOPED ABSTRACTION ->
CHECK -> CONCRETIZE COUNTEREXAMPLE -> [REPAIR / REFINE / UNKNOWN] ->
OWNER-NATIVE VERIFY -> CONSUMER ACCEPT -> KEEP / RETIRE`.

Record real counterexamples and only the abstraction distinction needed
to settle them. No proof of global representational minimality or
sufficiency is requested.

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
