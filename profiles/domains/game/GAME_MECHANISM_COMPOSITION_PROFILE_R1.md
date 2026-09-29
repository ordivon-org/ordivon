# Game Mechanism Composition Profile — R1

Status: **ACTIVE DESIGN-SEARCH PROFILE**

## Core reframing

Forward Game discovery does not primarily ask `Which game should we make?` or `Which genre wins?`. It asks:

> **Which externally grounded mechanics/patterns should be combined, with which causal couplings, under which player/context constraints, to produce dynamics worth validating?**

```text
external mechanism/pattern knowledge
        + local evidence
        + player/context intent
                 ↓
          mechanism graph
                 ↓
       predicted dynamics
                 ↓
        cheapest playable
                 ↓
          Human evidence
                 ↓
 update node / edge / composition evidence
                 ↓
        next composition
```

## Search unit

The unit is a graph, not a genre and not a feature list.

A composition normally contains:

- 1–2 **anchor mechanics** carrying the repeated player work;
- supporting mechanics that create variation, pressure, feedback or persistence;
- explicit coupling edges;
- time, information, social and session models;
- a target dynamic hypothesis;
- a target player-experience/motivation hypothesis;
- a cheapest falsifier and kill condition.

This is a heuristic, not a mandatory template.

## Compatibility evidence

Mechanism-pair and mechanism-set evidence should accumulate with context. Supported relation states are:

```text
REINFORCES
CONFLICTS
CONTEXT_DEPENDENT
INDEPENDENT_OR_WEAK
UNKNOWN
```

Examples of the kind of claim we want to learn, not assume:

```text
fast retry + attributable failure -> may reinforce mastery
perfect information + deduction -> may destroy epistemic uncertainty in some contexts
information scarcity + consequential inspection -> may reinforce inference
large outcome variance + precision mastery -> may weaken self-attribution
progression unlock + exploration topology -> may create backtracking/discovery loops
```

Every relation remains scope-bound until tested.

## Genre becomes a projection

After a mechanism graph stabilizes enough to communicate externally, map it onto Steam/App Store/Google Play/Microsoft genre vocabulary and identify comparable products. That label is useful for market/distribution work but does not retroactively become the design authority.

## Historical Ordivon material

Old D01–D16 directions, Station Zero, Casefile, Last Light, Echo Hunt and Product Thesis Sprint outputs should be decomposed into:

```text
mechanism nodes
coupling edges
observed dynamics
Human/mechanical evidence standing
known conflicts/failures
carrier/prototype cost
```

They cease to compete as product directions. Their durable value is mechanism/composition evidence.

## Current evidence ledger

Current cumulative evidence is registered in [`GAME_MECHANISM_EVIDENCE_R2.md`](GAME_MECHANISM_EVIDENCE_R2.md) and `game-mechanism-evidence-r2.json`; R1 remains a frozen snapshot. R2 contains 50 specimens and 60 context-bound claims spanning sample compositions, Human falsifier templates, automated apparatus boundaries and measured Station Zero counterfactual evidence. Use them to combine supported edges with strategically important unknowns.
