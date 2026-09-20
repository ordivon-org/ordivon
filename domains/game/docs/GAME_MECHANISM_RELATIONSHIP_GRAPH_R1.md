---
schema_version: 1
id: game.mechanism-relationship-graph.r1
title: Ordivon Game Mechanism Relationship Graph R1
profile: research
lifecycle: active
source_role: derived-evidence-navigation
visibility: public
owners:
  - ordivon-game
updated: 2026-09-18
summary: Cross-game retrieval and conditionality graph derived from source-grounded mechanism Experiences without creating a closed mechanic ontology or design recommender.
evidence_status: source-grounded-conditional-hypotheses
readiness: ACTIVE_EXPANDING
---
# Ordivon Game Mechanism Relationship Graph R1

## Purpose

The Experience Library remembers bounded observations and hypotheses from individual reference projects. This graph asks a different question:

```text
What relationships become visible when those Experiences are viewed across games?
```

It has three deliberately different layers:

```text
1. Within-Experience co-occurrence
   exact mechanism tags that appear together in one Experience

2. Retrieval Facet
   an authored, incomplete semantic alias that recalls differently named mechanisms across games

3. Conditionality
   an apparent conflict or divergent design choice, plus conditions that may explain when each side is useful
```

None of these layers is a Game constitution, ranking, recommendation engine, compatibility matrix or mechanic ontology. **This is not a mechanic ontology.**

## Co-occurrence is not causality

A graph edge means only that two mechanism tags were present in the same source-grounded Experience record. It does **not** mean either mechanism caused the other, that the pair is good, or that the pair transfers safely.

```text
co-occurrence
  -> retrieval clue
  != causal proof
  != compatibility proof
  != Human outcome evidence
```

The graph mechanically derives one edge for every pair of mechanism tags inside every Experience so provenance remains exact.

## Retrieval Facets are not categories of all games

The Experience Library intentionally uses project-local mechanism language. As a result, semantically related ideas often have different tags. `Retrieval Facet` provides an optional search bridge such as:

- Failure / Reset / Persistence;
- Learning / Guidance / Opacity;
- Genre Recombination / Convention Inversion;
- Representation / Affordance / Interface;
- Procedural Variation / Authored Constraint;
- Production Capacity / Design Space;
- Sequel / Identity / Transformation.

Every facet is `ADVISORY_RETRIEVAL_ALIAS`, `exhaustive=false`, and `canRejectUnmatchedMechanism=false`. A mechanism that belongs to no current facet remains fully valid for exploration.

## Conditionality instead of contradiction theatre

Two successful projects using different methods are not automatically contradictory. A Conditionality is admitted only when exact Experience records support a useful **apparent conflict** and we can state plausible context distinctions without turning them into universal truth.

Examples:

```text
clarity / guidance
    vs
productive opacity / discovery

fast retry
    vs
consequence-carrying failure

predictable tactical resolution
    vs
procedural replay variation

broad idea search
    vs
shipped scope restraint

preserve sequel core
    vs
break enclosing form
```

Each Conditionality carries:

- exact Experience refs and source provenance;
- the apparent conflict;
- multiple distinguishing conditions;
- at least two false universalizations to avoid;
- a cheap discriminator that can be adapted into a new experiment;
- `canBlockNovelCombination=false`.

The conditions are hypotheses about transfer boundaries, not causal laws. They become stronger only when a new composition supplies its own evidence.

## The important shift

The knowledge system can now answer questions that are hard to express with a game-by-game teardown:

```text
Which different mechanisms have been used to control failure cost?
Where does opacity look productive versus destructive?
When is randomness placed in setup rather than resolution?
Which projects preserve identity by reusing a core, and which by breaking form?
When do teams search broadly but ship narrowly?
What state resets, and what persists, across repeated play?
```

The result should expand creative search, not narrow it:

```text
more experience
    -> more analogies
    -> more counterexamples
    -> better cheap discriminators

never
    -> more historical precedent
    -> smaller allowed design space
```
