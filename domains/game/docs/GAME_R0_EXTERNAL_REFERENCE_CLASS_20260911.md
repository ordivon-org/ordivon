---
schema_version: 1
id: game.r0.external-reference-class.20260911
title: Ordivon Game — R0 External Reference Class 2026-09-11
type: research-decision
profile: product-discovery
lifecycle: superseded
source_role: superseded-r0-cheap-baseline-corpus
visibility: public
owners:
  - ordivon-game
updated: 2026-09-11
summary: Superseded first R0 attempt. Retained for cheap-baseline analysis, but its small-team feasibility filter no longer defines the external success universe or first R1 teardown set.
evidence_status: externally-grounded
readiness: SUPERSEDED_AS_R1_ADMISSION
applies_to:
  - ordivon-game
related:
  - game.front-half.external-reference-profile
  - game.external-mature-practice-adoption-r1
  - game.development-model
---
# R0 External Reference Class — 2026-09-11

> **SUPERSEDED AS R1 ADMISSION AUTHORITY (2026-09-11).** The current R0 authority is [`GAME_R0_SUCCESS_UNIVERSE_20260911.md`](GAME_R0_SUCCESS_UNIVERSE_20260911.md). This document remains useful only for cheap-baseline/reproduction-cost analysis. Balatro, Vampire Survivors and Mini Metro are not a representative success universe and are not the current first R1 set.

## 0. Decision boundary

This is the first concrete `R0 — Reference Class` execution under [`GAME_FRONT_HALF_EXTERNAL_REFERENCE_PROFILE.md`](GAME_FRONT_HALF_EXTERNAL_REFERENCE_PROFILE.md).

It does **not** select the first Ordivon game. It chooses which mature external games are worth learning from next.

```text
SuccessfulGame != ValidProductionBaseline
PopularNow != MatureReference
DesignReference != CloneTarget
SmallTeamOrigin != SmallCurrentProduct
ReferenceAdmission != G0Admission
```

Steam's current Charts are retained as a **market pulse**, not as product authority: the current top-selling/most-played list changes rapidly, while R0 needs durable design evidence. Steam's Tag Wizard is used for similarity dimensions because it explicitly spans genre/subgenre, visuals/viewpoint, themes, features, player activities and similar titles.

Sources:
- https://store.steampowered.com/charts/
- https://partner.steamgames.com/doc/store/tags

## 1. R0 selection dimensions

A reference is judged on separate axes rather than one score:

```text
SuccessEvidence
Maturity / longevity
Core-loop causal legibility
Small-scope reproducibility
Expression dependence
Content burden
Online / LiveOps burden
Production-scale comparability
Postmortem / developer-evidence availability
Value as a controlled baseline
```

`SuccessEvidence` may include long-lived high user approval, reported sales, awards or durable audience. None of those identifies the causal reason for success.

`Production-scale comparability` asks whether a tiny team can reproduce the **relevant interaction**, not whether it can recreate the complete commercial product.

## 2. Reference corpus

### Tier A — historical cheap-baseline candidates

#### A1 — Balatro

Observed mature pattern:
- compact symbolic rules;
- familiar card/poker representation;
- short repeated decisions;
- multiplicative build interactions and visible number feedback;
- run-based progression with little spatial-content burden.

External standing:
- Steam currently reports `Overwhelmingly Positive`, roughly 98% of more than 100k English reviews;
- publisher Playstack reported more than 5 million units sold by 2025-01-21;
- developed by LocalThunk, a solo creator; early public prototype history is available.

Why Tier A:
- extremely high success evidence;
- the causal skeleton can be reproduced with ordinary cards, text and numbers;
- original art/audio/theme can be completely omitted from a learning reproduction;
- no server, physics, animation or hand-authored level dependency is required for the central loop.

Primary R1 question:
> What minimum combination of familiar hand grammar, constrained choice, modifier discovery, compounding synergy and escalating target creates the `one more hand/run` decision cadence?

Sources:
- https://store.steampowered.com/app/2379780/Balatro/
- https://www.playstack.com/news/balatro-5-million-copies-sold/
- https://www.gamedeveloper.com/business/balatro-dev-gives-look-at-first-prototype-joker-poker

#### A2 — Vampire Survivors

Observed mature pattern:
- extremely small direct control surface;
- automatic attacks separate movement skill from build choice;
- frequent level-up choices;
- escalating enemy density turns numerical growth into visible power;
- short runs plus persistent unlocks.

External standing:
- Steam currently reports roughly 98% positive across more than 127k English reviews;
- the initial development is documented as a tiny operation centered on Luca Galante;
- the design became a durable reference point for the survivor/bullet-heaven form.

Why Tier A:
- the baseline can be reproduced with primitives and placeholder shapes;
- feel depends on timing, density and feedback, but not on AAA-quality authored content;
- it provides a real-time/action contrast against Balatro.

Primary R1 question:
> Which cadence of movement-only control, autonomous offense, reward interval, choice frequency and enemy-density escalation is necessary before the loop feels like growth rather than passive waiting?

Sources:
- https://store.steampowered.com/app/1794680/Vampire_Survivors/
- https://www.gamedeveloper.com/design/vampire-survivors-development-sounds-like-an-open-source-fueled-fever-dream

#### A3 — Mini Metro

Observed mature pattern:
- one immediately legible real-world metaphor;
- continuous network optimization;
- few resource types;
- procedural demand growth;
- clean abstract expression;
- system state itself becomes the visual output.

External standing:
- Steam currently reports about 95% positive across roughly 7k English reviews;
- its developer postmortem describes two core full-time developers with part-time specialist support;
- the team explicitly constrained ideas around no hand-built levels, nothing art-heavy and no reliance on audio, and treated a two-day prototype as a useful feasibility bound.

Why Tier A:
- unusually close match to the production conditions of a tiny technical team;
- central loop can be reproduced with points, lines, queues and resource tokens;
- provides a continuous systems/optimization contrast to both A1 and A2.

Primary R1 question:
> How much of Mini Metro's appeal survives when reduced to network topology, passenger demand, limited upgrades and overload pressure before signature presentation/audio is restored?

Sources:
- https://store.steampowered.com/app/287980/Mini_Metro/
- https://www.gamedeveloper.com/audio/postmortem-dinosaur-polo-club-s-i-mini-metro-i-

### Tier B — high-value reserve baselines

#### B1 — FTL: Faster Than Light

Why retain:
- mature real-time-with-pause systems game;
- clear resource scarcity, crew roles, ship subsystems, probabilistic events and run structure;
- Steam currently shows about 95% positive across more than 46k English reviews.

Why not first three:
- reproducing a useful baseline requires more coupled systems and content than A1–A3.

Use when:
- R1 needs a reference for multi-system crisis management, partial control and consequential run decisions.

Source: https://store.steampowered.com/app/212680/FTL_Faster_Than_Light/

#### B2 — Papers, Please

Why retain:
- mechanically compact inspection/checking loop;
- strong coupling between procedural rules, time pressure, mistakes and narrative/moral consequence;
- Steam currently reports roughly 97% positive across about 40k English reviews;
- Lucas Pope documents roughly nine months from first mockups to initial release.

Why not first three:
- the mechanical baseline is cheap, but much of the product's value depends on authored cases, pacing and contextual meaning.

Use when:
- studying how simple repeated verification acquires tension and meaning through changing rules and consequences.

Sources:
- https://store.steampowered.com/app/239030/Papers_Please/
- https://www.gamedeveloper.com/design/road-to-the-igf-lucas-pope-s-i-papers-please-i-

#### B3 — Slay the Spire

Why retain:
- long-lived benchmark for roguelike deckbuilding;
- Steam currently reports roughly 97% positive across more than 76k English reviews;
- excellent comparator for Balatro because both use run-based combinatorial builds while differing in combat grammar and information structure.

Why not first three:
- a faithful baseline requires enough enemies, cards, relics and encounter balance to expose its deeper loop; content/balance burden is materially higher than Balatro's first causal toy.

Source: https://store.steampowered.com/app/646570/Slay_the_Spire/

#### B4 — Into the Breach

Why retain:
- highly legible deterministic/telegraphed tactics;
- small maps turn combat into local planning puzzles;
- created by the two-person studio behind FTL;
- Steam currently reports roughly 93% positive across more than 12k English reviews.

Why not first three:
- small board size is deceptive: enemy/action design, interaction completeness and tactical balance make a valid baseline more expensive than A1–A3.

Use when:
- studying perfect-information planning, collateral-damage objectives, counterfactual legibility and compact tactical depth.

Sources:
- https://store.steampowered.com/app/590380/Into_the_Breach/
- https://www.gamedeveloper.com/design/-i-into-the-breach-s-i-designers-explain-how-to-follow-up-from-a-hit-game

### Tier C — ceiling / transfer references, not first clone baselines

#### C1 — Stardew Valley

Why retain:
- exceptional long-run audience evidence: Steam currently reports roughly 98% positive across nearly 400k English reviews;
- originated as Eric Barone's solo project and is a canonical example of one creator integrating code, design, art, writing and music.

Why ceiling only:
- the initial product required roughly four years of solo work and contains a very large authored-content/progression surface;
- it is evidence that a tiny origin can produce a huge game, **not** evidence that reproducing its whole scope is a rational first exercise.

Use for:
- progression rhythm, daily/seasonal cycles, activity portfolio, social/content layering and long-horizon retention.

Sources:
- https://store.steampowered.com/app/413150/Stardew_Valley/
- https://www.gamedeveloper.com/design/road-to-the-igf-concernedape-s-i-stardew-valley-i-

#### C2 — Hades

Why retain:
- Steam currently reports about 98% positive across more than 140k English reviews;
- Supergiant documents a little over three years to v1.0 and an Early Access process deliberately designed around player/community feedback.

Why ceiling only:
- Supergiant states that its original seven-person team had grown by more than twice that number;
- extensive hand-painted art, animation, combat feel, music, fully voiced characters and large narrative state are constitutive production burdens.

Use for:
- action feel, run-to-run narrative integration, Early Access feedback architecture and high-expression polish.

Sources:
- https://store.steampowered.com/app/1145360/Hades/
- https://www.supergiantgames.com/blog/hades-faq/

#### C3 — Return of the Obra Dinn

Why retain:
- solo-developed, critically durable deduction game;
- Steam currently reports around 96% positive across more than 18k English reviews;
- unusually strong evidence about changing a design to fit one-person production constraints.

Why ceiling only:
- Lucas Pope describes about four-and-a-half years of development and a substantial custom content/tooling burden;
- the deduction mechanism depends strongly on authored scenes, identities, temporal reconstruction and presentation.

Use for:
- deduction, information revelation, identity reasoning and aggressive scope reduction.

Sources:
- https://store.steampowered.com/app/653530/Return_of_the_Obra_Dinn/
- https://www.gamedeveloper.com/business/road-to-the-igf-lucas-pope-s-i-return-of-the-obra-dinn-i-
- https://www.gamedeveloper.com/design/on-that-incredible-demo-from-the-maker-of-i-papers-please-i-

## 3. Historical reason A1–A3 were initially considered cheap baselines

The superseded first teardown proposal used **three games, not ten**:

```text
Balatro            symbolic / turn-based / combinatorial
Vampire Survivors  real-time / action / density-growth
Mini Metro         continuous / systemic / optimization
```

Together they span three materially different causal forms while all allowing:
- a tiny lawful reproduction with original expression;
- no mandatory online service;
- no Runtime Agent requirement;
- no large authored world;
- no motion-capture/voice/cinematic dependency;
- fast mechanical falsification before expensive polish.

This is a **reference-learning portfolio**, not a product portfolio.

The first R1 round should not ask which of the three we personally like. It should produce comparable teardown records for:

```text
PlayerPromise
CoreVerbs
DecisionCadence
MicroLoop / SessionLoop / MetaLoop
InformationContract
Reward / Failure / Retry
Difficulty / pressure escalation
Progression / content grammar
ExpressionCriticality
What can be lawfully reproduced with placeholder expression
Smallest baseline that could falsify our causal interpretation
```

## 4. Explicit exclusions from first teardown

Not selected for first R1 does **not** mean inferior.

```text
Hades / Stardew Valley
  -> too much production/content confounding for first baseline work

Obra Dinn
  -> excellent solo constraint reference, but authored deduction content makes the baseline expensive

Slay the Spire / Into the Breach / FTL / Papers, Please
  -> retained reserve references; use after A1-A3 or when a specific causal question demands them

Steam live Top Sellers / Most Played
  -> market pulse only; recency/popularity does not establish mature transferable design laws
```

## 5. R0 result

```text
R0ReferenceClass = SUPERSEDED_BY_SUCCESS_UNIVERSE
ProductSelected = false
G0Entered = false
RuntimeAgentRequired = false
CheapBaselineSet = [Balatro, Vampire Survivors, Mini Metro]
FirstR1Set = NONE_CURRENTLY
ReserveSet = [FTL, Papers Please, Slay the Spire, Into the Breach]
CeilingSet = [Stardew Valley, Hades, Return of the Obra Dinn]
```

### Admission to R1

R1 may **not** begin merely from A1–A3. Any current R1 admission is owned by `GAME_R0_REFERENCE_STACKS_20260911.md`; this superseded record cannot grant it.

R1 must preserve the distinction:

```text
ObservedReferenceFact
!= InferredDesignCause
!= TransferableDesignLaw
```

No clone implementation is admitted until each teardown names the **smallest causal baseline** and the expression/content dimensions that must be omitted or retained for the comparison to remain valid.
