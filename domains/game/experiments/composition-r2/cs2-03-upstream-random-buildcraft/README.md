# CS2-03 — Upstream-Random Buildcraft Falsifier

Status: **APPARATUS / HUMAN EVIDENCE UNOBSERVED**

## Claim under test

```text
same build choices
+ same encounter distribution
+ randomness revealed before choice
vs
randomness revealed after choice
→ different attribution / adaptation quality?
```

This is the cheapest falsifier for Composition Search R2 candidate `cs2-03-upstream-random-buildcraft`.

## Control design

The carrier holds constant:

- four draft rounds;
- the card/module offers;
- card stats and synergy rules;
- encounter archetype distribution;
- scoring rule;
- run length;
- persistent build-path structure.

Only the **information timing** changes:

- `UPSTREAM`: current encounter is revealed before the pick;
- `DOWNSTREAM`: current encounter is revealed only after the pick.

Four difficulty-matched encounter sequences are used. Schedule `A` and `B` swap which sequence receives which condition across sessions.

## Structural admission gate

Run:

```bash
python experiments/composition-r2/cs2-03-upstream-random-buildcraft/scripts/structural_precheck.py
```

The carrier is admitted only if it shows build-path diversity, no universal first choice/build dominance, measurable context-adaptation value, and global path reasoning value over immediate greed.

## Human run

```bash
python -m http.server 8765 -d experiments/composition-r2/cs2-03-upstream-random-buildcraft
```

Then open `/web/` in a browser. A complete pilot is 16 picks across four short runs plus four brief reflections. Export the session JSON at the end.

## Human measures

Per run:

- choice attribution;
- perceived adaptation;
- causal understanding;
- voluntary retry;
- free-text strategy/model revision.

## Kill conditions

- upstream-information condition produces equal/worse attribution and adaptation;
- revealed encounter information does not change strategy;
- build intent is overwhelmed by encounter randomness;
- greedy/local choice performs equivalently to path-aware reasoning;
- Human evidence shows no meaningful strategy/model revision.

## Boundary

A structural PASS only establishes a non-degenerate apparatus. It does **not** establish fun, replay value, causal superiority in humans, or product value.
