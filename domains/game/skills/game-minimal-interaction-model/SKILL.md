---
name: game-minimal-interaction-model
description: Optional World/State -> Observation -> Action -> Transition/Consequence lens for reasoning about interactive systems. A working model, not a universal Game ontology or kernel law.
---

# Minimal Interaction Model

Use this Skill when a four-part interaction model makes a game or mechanic easier to reason about:

```text
World / State
  -> Observation
  -> Action
  -> Transition / Consequence
  -> next World / State
```

## Authority

This Skill is **optional and advisory**. The four-part model is a working hypothesis, not a minimality theorem. It may be replaced, expanded, collapsed, or discarded. It must not block a creative composition merely because that composition does not fit the model cleanly.

## Good uses

- tracing causal consequences;
- separating hidden state from player-visible information;
- checking whether an action actually changes anything;
- describing a deterministic or Agent-mediated loop;
- comparing two implementations of the same mechanic.

## Counterexamples are valuable

If a game needs a different primitive, ambiguous boundary, simultaneous relation, embodied coupling, social convention, performative rule, or other structure that does not fit this model, record that as useful evidence. Do not force the game back into the four boxes.

## Non-goals

- no universal Game kernel;
- no ban on new primitives;
- no shared-code promotion rule;
- no requirement that all genres expose these parts explicitly;
- no creative admission gate.
