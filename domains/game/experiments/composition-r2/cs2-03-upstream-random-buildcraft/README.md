# CS2-03 — Upstream-Random Buildcraft Falsifier

Status: **COMPUTATIONAL EVALUATION LOOP ACTIVE / HUMAN-SPECIFIC CLAIMS OPTIONAL**

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

## Automated browser gate

The browser apparatus is mechanically checked before it is used as an interaction carrier:

1. **Playwright** owns the complete deterministic 4×4 regression, reflections and JSON export;
2. **Browser Use** owns a bounded agentic perception/action probe through accessibility state and CDP.

These are ordinary automated verification/evaluation tools. The historical `pre-Human` naming is retained only in file names and evidence lineage; no Human handoff is required after they pass.

## Computational Player Science R1

The current evaluation path is [`COMPUTATIONAL_PLAYER_SCIENCE_R1.md`](COMPUTATIONAL_PLAYER_SCIENCE_R1.md):

```text
procedural player population
→ paired UPSTREAM/DOWNSTREAM counterfactual simulation
→ persona-balanced causal estimand
→ bootstrap / heterogeneity / uncertainty diagnostics
→ surrogate model
→ expected-information-gain experiment selection
→ direct follow-up simulation
→ surrogate replacement/update
↺
```

Current result:

```text
Persona-balanced score ATE   +0.282
95% CI                       [-0.600, +1.179]
Positive persona effects      50%
Random baseline effect         0.000
Standing                      MIXED / PLAYER-MODEL DEPENDENT
```

The first polynomial surrogate was deliberately rejected as weak (`R²=0.625`). High-EIG direct follow-up exposed large prediction errors. A Gaussian-process replacement on the same frozen independent test set reaches `R²=0.819`, `MAE=0.295`, and remains explicitly local to the declared synthetic-player envelope.

## Optional claim-specific Human observation

The browser study and historical C0 worksheet remain available only when a concrete decision requires a Human-specific observation such as one person's felt agency or preference.

```text
Human-specific claim unknown
!=
workflow blocked
```

No Human session is required for Composition Search, causal mechanism evaluation, synthetic-player modeling, surrogate learning, product-form exploration, or later engineering work.

## Computational kill / revision conditions

- the treatment effect is zero/negative across the decision-relevant modeled population;
- effects reverse strongly across plausible player models and the product cannot target the relevant class;
- information timing changes actions but not decision-relevant consequences;
- the player-model result is dominated by unbounded model-form uncertainty;
- surrogate predictions fail frozen tests or active-learning follow-up;
- a cheaper alternative coupling explains the same desired dynamics.

## Boundary

A structural PASS only establishes a non-degenerate apparatus. It does **not** establish fun, replay value, causal superiority in humans, or product value.
