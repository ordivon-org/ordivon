# Successor Contract R1 — Verified Recursive Succession

Date: 2026-09-22
Status: **R1 CANDIDATE / GENERIC MECHANICAL SUCCESSION ONLY**

## Decision

Ordivon already has bounded evidence for Agent-owned multi-attempt adaptation, source
self-modification, improvement-of-improvement, autonomous discovery, lawful abstention, and
higher-information repository search. The missing generic representation is the transition:

```text
exact predecessor S_t
        +
exact candidate S*
        +
exact improvement process
        +
frozen evaluation anchors
        +
verifier-owned succession gates
        ↓
Successor Contract R1
        ↓
mechanical succession projection
```

R1 does **not** create an RSI Controller, search service, evaluator service, scheduler,
promotion service, or new source-of-truth database.

## Formal object

Let the system state be:

```text
S_t = (M_t, K_t, C_t, T_t, V_t, A_t, L_t)
```

where the tuple may include model/cognition, knowledge/memory, cognitive circuits,
tools/capabilities, evaluators, authority/policy, and lineage.

An improvement process `I_t` may produce a candidate:

```text
S* = I_t(S_t, evidence, objective)
```

A persistent self-change is present when `S* != S_t` under exact bound identity. A
recursive-mechanism change is present when the declared change set includes the mechanism
that produces future improvements:

```text
improvement-mechanism ∈ Δ(S_t -> S*)
```

That condition is descriptive only. It does not prove that the mechanism became better.

## Why "successor" is stricter than "candidate"

A candidate is generated. A successor is lineage-bound and evidence-bound.

R1 therefore binds:

- one exact self boundary;
- one exact predecessor;
- one exact candidate;
- one exact improvement-process identity;
- one exact objective;
- one exact promotion-policy identity;
- declared change targets;
- exact evaluation anchors;
- verifier-owned gate requirements;
- unresolved assumptions and non-claims.

The generic layer never computes a universal fitness score.

## Evaluation grounding

R1 adopts the external-grounding distinction used by contemporary formal RSI work.

Three modes are represented:

```text
EXTERNALLY_ANCHORED
MIXED
SELF_REFERENTIAL
```

An anchor is not a statement that the evaluator is correct. It records where the evaluation
standard comes from and binds its exact identity.

For `EXTERNALLY_ANCHORED`, candidate-owned anchors are rejected. For `MIXED`, at least
one external and one candidate-owned anchor must exist. `SELF_REFERENTIAL` is representable
for research comparison, but the compiled projection explicitly reports
`externallyGrounded=false`.

## Gate law

Each required succession gate is narrow and verifier-owned:

```text
frozen evaluation anchor
        +
exact predecessor/candidate contract
        ↓
owner-native verifier
        ↓
SATISFIED | UNSATISFIED | UNKNOWN
```

A SATISFIED/UNSATISFIED record requires evidence. UNKNOWN may be evidence-empty.

Mechanical successor closure requires:

1. every required gate result exists;
2. every required result is SATISFIED;
3. result contract digest is exact;
4. verifier owner and support scope match;
5. evaluation-anchor identities match;
6. no unresolved contract assumptions remain.

Even then:

```text
mechanicalSuccessorClosure = true
promotionAuthorityEstablished = false
domainImprovementEstablished = false
```

This is deliberate.

## Authority separation

Recursive improvement must not become recursive authority.

The preferred topology remains:

```text
proposal / target discovery
        !=
candidate materialization
        !=
independent evaluation
        !=
promotion decision
        !=
physical commit / Git / release truth
```

The same model may participate in more than one step only when the caller/domain explicitly
permits it, but the durable authority identities remain distinct.

## Relation to Cognitive Circuit R1

Cognitive Circuit R1 binds a scoped objective to already-selected methods, capabilities,
owner-scoped stages, typed edges, and cross-owner gates.

Successor Contract R1 binds a predecessor/candidate pair and the evidence needed for a
possible successor transition.

They compose as:

```text
Cognitive Circuit
      ↓ execute / observe
Improvement process
      ↓
candidate
      ↓
Successor Contract
      ↓
verifier-owned gates
      ↓
mechanical succession closure
      ↓
external promotion owner (if any)
```

Neither object is a workflow engine.

## Relation to Interface R2 and Cross-domain R3

Interface R2 may supply currentness/compatibility evidence to a successor verifier.

Cross-domain R3 adapters may discharge seam-specific obligations and provide evidence refs.

Neither is absorbed into Successor Contract R1.

## Anti-growth laws

R1 must not grow:

- autonomous target discovery;
- candidate generation;
- a global system-state registry;
- a universal evaluator;
- universal metrics or scalar fitness;
- automatic promotion;
- release/Git mutation authority;
- workflow state;
- retry/scheduling;
- model training authority;
- a persistent RSI controller.

## External research alignment

The design is intentionally compatible with several mature/current directions:

- Generalized Agent Iteration: improvement-mechanism inclusion and external evaluation
  grounding are separate axes.
- Darwin Gödel Machine: persistent source modification plus empirical validation and lineage.
- AlphaEvolve / ShinkaEvolve: candidate search remains separate from task evaluators.
- RSI-Exam: long-horizon improvement must transfer to sealed unseen evaluation.
- ModularRSI: modular, benchmark-disjoint evolution reduces attribution and overfitting risk.
- 2026 RSI surveys: evaluator strength and meta-evaluation are central constraints on reliable
  self-improvement.

These sources motivate the boundary; they do not become Ordivon runtime authority.
