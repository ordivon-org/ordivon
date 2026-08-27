---
schema_version: 1
id: game.development-paradigm-research
title: Ordivon Game — Game Development Paradigm Research
profile: research
lifecycle: active
source_role: canonical-research
visibility: public
owners:
  - ordivon-game
updated: 2026-08-27
summary: Cross-paradigm research that separates Game semantic foundations from the problem of discovering, validating, producing and evolving games. It compares Ordivon's current development model against mature design, preproduction, prototyping, playtesting, content-production, live-operations and Agent-era practices, then identifies the stable responsibilities missing beneath a stage-only view.
evidence_status: mixed
readiness: CURRENT
applies_to:
  - ordivon-game
related:
  - game.development-model
  - game.development-core
  - game.core-research.reset
---
# Ordivon Game — Game Development Paradigm Research

## 0. Question

Ordivon Game has unusually deep research on:

```text
Play / Game
Action / Control / Skill
Challenge / Failure / Mastery
Authority / determination
World state / consequence
Agent observation / cognition / admission / recovery
```

But this does not imply an equally deep theory of **how games are discovered and developed**.

This research asks:

> What are the stable responsibilities and evidence loops by which an uncertain game idea becomes a coherent, producible, learnable, player-validated and operable game?

Existing Station Zero, Casefile, Concept Lab and Pre-G0 playables are retained only as experimental apparatus and historical evidence. They receive no product momentum from this research.

## 1. Main finding

The current `DEVELOPMENT_MODEL.md` is useful but was carrying two different jobs:

```text
A. stage / commitment projection
G0 → G1 → ... → G8

B. explanatory model of game development
what work actually reduces uncertainty and creates a game
```

Those jobs should be separated.

The first survives.

The second needs a richer model because game development is not causally explained by stage order. Mature practice repeatedly shows overlapping loops of design, prototyping, player learning, content construction, expression, production realization and player evidence.

Therefore:

```text
G0–G8 = StageProjection
StageProjection != GameDevelopmentCore
```

A stage can be useful for coordination, commitment and scope without claiming that every development responsibility advances uniformly or monotonically.

## 2. External paradigm comparison

### 2.1 Formal Abstract Design Tools — design vocabulary, intention and perceivable consequence

Doug Church's Formal Abstract Design Tools treats design language as a shared analytical tool rather than a recipe. Its `INTENTION` and `PERCEIVABLE CONSEQUENCE` distinction independently converges with Ordivon's strong action/consequence/legibility research.

Transfer:

```text
shared design vocabulary = useful
vocabulary = analytical affordance
vocabulary != recipe
vocabulary != product authority
```

Ordivon already performs strongly here. The remaining gap is not more nouns; it is turning existing distinctions into development decisions.

Source:
- Doug Church, “Formal Abstract Design Tools,” Game Developer.

### 2.2 MDA — mechanics, dynamics and aesthetics as a bidirectional bridge

MDA separates:

```text
Mechanics
→ Dynamics
→ Aesthetics / player experience
```

and explicitly supports reasoning in both directions: implementation choices can be examined for experience effects, while intended experience can constrain mechanics.

Ordivon already has richer semantics than MDA for rules, action, authority, feedback and player-value claims. What it lacks is a compact **development bridge** that forces every intended experience claim to name the dynamics expected to cause it and the mechanics/content/expression expected to realize those dynamics.

Transfer:

```text
ExperienceTarget
↔ ExpectedDynamics
↔ RealizationMechanisms
```

This is a development relation, not a new Game Foundation.

Source:
- Hunicke, LeBlanc, Zubek, “MDA: A Formal Approach to Game Design and Game Research,” AAAI 2004.

### 2.3 Cerny / John Method — preproduction is discovery, not scheduled production

The Method separates preproduction from production and uses four keystones:

```text
preproduction vs production
publishable first playable
macro vs micro design
gameplay testing
```

The key pressure on Ordivon is not the historical “publishable” quality bar itself. It is that **preproduction is an uncertainty-reduction environment**. Rapid experiments may fail; they should be visible, but they should not be mistaken for production milestones.

The Method also separates:

```text
Macro design = what breadth/structure must exist
Micro design = day-to-day realization learned during production
```

This exposes an Ordivon gap: our `Content` responsibility and `content grammar` are correct but underdeveloped as a positive **macro content/progression architecture**.

Transfer:

```text
PreproductionProgress != amount of finished code/content
PreproductionProgress ≈ consequential uncertainty removed

MacroArchitecture != MicroContent
```

Source:
- Mark Cerny & Michael John, “Game Development: Myth vs. Method,” Game Developer, June 2002.

### 2.4 Playcentric / playful production — phases exist, but iteration remains inside them

Richard Lemarchand's `A Playful Production Process` retains recognizable phases — ideation, preproduction, full production, post-production — while centering conceptualization, building, playtesting, iteration, communication and project management.

This is evidence against a false dichotomy:

```text
stages
vs
iteration
```

A mature process can retain stage commitments while treating the actual work inside and across stages as iterative and evidence-driven.

Transfer:

```text
Stage = coordination / commitment view
Iteration = causal learning mechanism
```

Source:
- Richard Lemarchand, `A Playful Production Process`, MIT Press, 2021.

### 2.5 Prototype media — the cheapest prototype is not always the valid prototype

Roblox's current prototyping guidance explicitly separates paper and Studio prototypes. Paper increases exploration speed and breadth but cannot represent some mechanics and can produce false positives; in-engine prototypes are slower but expose technical feasibility and are reusable.

This reveals a missing concept in Ordivon's `cheapest falsifier` discipline:

```text
cheap != valid by identity
```

Prototype selection requires a **medium-fit contract**:

```text
TargetQuestion
RepresentedDimensions
OmittedDimensions
FalsePositiveRisks
FalseNegativeRisks
ReuseIntent
DecisionRule
```

A paper rule set can test strategic choice but not input feel. A browser mock can test information flow but not controller timing. A deterministic simulator can test reachability but not Human tension. A polished slice can test expression while hiding production cost.

Source:
- Roblox Creator Hub, “Prototyping.”

### 2.6 Rational Game / Level Design — semantic distinctions are not yet a content-design method

Rational-design practice decomposes mechanics into parameters, readability, difficulty/learning curves and content combinations. The Rayman Origins account emphasizes orderly mechanic introduction, macro flow and extracting depth from a smaller mechanic set instead of accumulating one-shot mechanics.

Ordivon GDF1/GDF2 already gives stronger semantic guards around skill, challenge and mastery. But those guards are not yet a **positive content/progression construction method**.

Transfer:

```text
MechanicDepth
× ParameterVariation
× IntroductionOrder
× CombinationOrder
× PlayerSkillGrowth
→ ContentProgressionArchitecture
```

This is a major missing development capability.

Sources:
- Chris McEntee, “Rational Design: The Core of Rayman Origins,” Game Developer.
- “The Rational Design Handbook: An Intro to RLD,” Game Developer.

### 2.7 Skill atoms / player learning — the game teaches a model, not just controls

Daniel Cook's skill-atom model uses a loop roughly of:

```text
Action
→ Simulation
→ Feedback
→ Modeling
```

Ordivon already has the deeper semantic pieces in R4, GDF1 and GDF2. The development-model gap is operational: player learning is currently scattered across G2/G3 comprehension, onboarding and G6 difficulty instead of represented as a continuous design responsibility.

Transfer:

```text
PlayerLearningModel =
what distinction is learnable
+ prerequisite knowledge/skill
+ evidence/feedback
+ practice opportunity
+ transfer expectation
+ current observed failure
```

Actual Human learning remains Human evidence; Game owns only the intended learning/feedback structure and its game-local observations.

Source:
- Daniel Cook, “The Chemistry of Game Design,” Game Developer.

### 2.8 Games User Research — playtest is a decision instrument, not a milestone ritual

Mature user-research practice starts from:

```text
what decision are we trying to make?
what do we need to know from players?
```

and uses different methods at different uncertainty regimes: player/context research before building, early observed playtests for concept/value, comprehension/onboarding studies during production, larger quantitative work for balance, and telemetry plus interviews/surveys after release.

This exposes a major Ordivon weakness. `C0 Human Canary` is an evidence boundary, but it is not a complete **Player Evidence Programme**.

Needed representation:

```text
PlayerEvidenceQuestion
TargetPopulation / Context
ClaimType
Method
SampleScope
DecisionToInform
KnownBias / Limitation
ResultStanding
```

Sources:
- Games User Research, “Five essential playtests throughout development.”
- Games User Research, “Choose the right playtest method.”

### 2.9 Live game analytics and experiments — real populations create another causal-evidence regime

Roblox and PlayFab both expose mature telemetry and controlled experimentation. These systems distinguish observation from causal experiments and track outcomes such as retention, engagement, onboarding and other game/business metrics.

This does not imply every Ordivon game needs live-service metrics or monetization.

It establishes a conditional development responsibility:

```text
when real audience behavior materially determines the product,
PopulationEvidence != internal playtest evidence
and
RandomizedExperiment != machine counterfactual simulation
```

Ordivon's exact machine counterfactual evaluators are strong but cannot be promoted to population evidence.

Sources:
- Roblox Creator Hub, “Analytics” and “Experiments.”
- Microsoft PlayFab, “Experimentation.”

### 2.10 Procedural/content pipelines — produce grammars and tools, not only units

Unreal's PCG framework explicitly treats procedural generation as an iterative authoring pipeline that can range from asset utilities to whole worlds and blend with conventional workflows.

This strengthens an existing Ordivon idea:

```text
ContentGrammar != list of content nouns
```

A production-ready content architecture may include:

```text
Grammar
Generators / templates
Constraints
Authoring tools
Validation
Curation
Bake/runtime boundary
Variation budget
Provenance
```

Agent generation is one possible generator, not the definition of this responsibility.

Source:
- Epic Games, Unreal Engine 5.8 Procedural Content Generation Framework documentation.

### 2.11 Agent-era production — implementation friction changes faster than game-design responsibility

Unity's 2026 project-aware AI Agent can observe live project context including scene graph, GameObjects/components, packages, build settings and console output, while Roblox is explicitly moving toward playtesting, analytics and experiment Agents.

This is a genuine production-paradigm change:

```text
Human/Agent intent
→ project inspection
→ project mutation
→ test/observe
→ revision
```

can become much cheaper and tighter.

But the evidence does **not** establish:

```text
lower realization cost
→ solved game design
```

The most durable Agent-era change is therefore environmental:

```text
Production Agents expand reachable search/realization bandwidth.
They do not inherit product, player-value or evidence authority.
```

Sources:
- Unity, “Unity's AI tools in beta: How to get started,” 2026.
- Unity, “The In-Editor AI Assistant: Ask, Plan, and Agent Modes Explained,” 2026.
- Roblox, “Build Without Limits on Roblox,” 2026.

## 3. Where current Ordivon is already strong

| External concern | Current Ordivon standing |
| --- | --- |
| Intention / consequence | strong semantic and executable support |
| Rules vs effective authority | stronger than typical design frameworks |
| Cheap baseline / deletion pressure | strong |
| Exact replay / causal evidence | strong |
| Agent vs World authority | strong |
| Negative-result retention | strong |
| Prototype as experiment | present, but medium validity under-modeled |
| GameForm vs Agent role | strong after decoupling repair |

The next move is not importing an external methodology wholesale.

## 4. Where current Ordivon is materially weak

### 4.1 Stage model carrying too much explanatory weight

G0–G8 are useful stage semantics, but a single stage cannot faithfully represent different maturities in:

```text
experience evidence
play causality
player learning
content scalability
expression fidelity
production repeatability
technical stability
audience evidence
operational readiness
```

### 4.2 Experience target lacks an explicit Dynamics bridge

We can describe fantasy, verbs and desired value, but the canonical development model does not require the explicit chain:

```text
ExperienceTarget
→ ExpectedDynamics
→ RequiredMechanics / Content / Expression
```

This makes it easier for a technically valid mechanism to survive without a crisp causal claim about why the player experience should change.

### 4.3 Player learning is semantically rich but development-poor

GDF1/GDF2 distinguish skill/challenge/mastery well. Development still lacks a practical learning/progression map that can drive onboarding, level/content ordering and feedback design.

### 4.4 Content architecture is too noun-like

`characters / places / encounters / items / missions` describes content classes but not:

```text
how mechanics are introduced
how combinations create variety
how challenge evolves
how content breadth scales
how generators/tools participate
```

### 4.5 Prototype validity is not represented

`cheapest falsifier` can accidentally become:

```text
cheapest implementation
```

rather than:

```text
cheapest valid evidence carrier for this claim
```

### 4.6 Vertical Slice currently bundles several claims

Current G4 asks both “is this worth producing?” and “can we repeatedly produce it?” These are related but distinct.

A slice can separately establish:

```text
ExperienceRepresentativeness
QualityBar
IntegrationProof
PipelineProof
ThroughputEstimate
PerformanceEnvelope
```

It does not automatically establish market demand, population retention, or even broad Human Player Value.

### 4.7 Human evidence is under-modeled

`Human Player Value required` is a good anti-collapse law, but insufficient as a research method. We need target population/context, claim type, method and decision scope.

### 4.8 Product ecology is mostly deferred to G8

For some products this is correct. For platform-dependent, multiplayer, social, UGC or live games, distribution, community, safety/moderation, economy, retention and update cadence can constrain design from early preproduction.

Therefore ecology is conditional but not necessarily late.

## 5. Core correction: Game Core is not one universal equation

The historical Game Core compression:

```text
Authoritative World
+ Meaningful Agency
+ Player Experience
+ Persistent Consequence
```

was productive under Station Zero-era pressure, but it should no longer be read as a universal ontology of Game.

Reasons already available inside Game's own frozen research:

```text
Play != Game
NoFixedGlobalGoal != NoEvaluation
World != Map/Lore/Simulation
Persistence != continuous simulation
Player experience is an evidence target, not Game-owned phenomenological truth
```

And many valid game forms do not require cross-session or even cross-round persistence.

Therefore the four-term formula is retained as a **historical pressure lens**, not promoted as the universal development Core.

Current development-use Core should instead be a responsibility view over frozen semantics; see `GAME_DEVELOPMENT_CORE.md`.

## 6. Final disposition

```text
GDF0–GDF3 = unchanged
GPR0–GPR7 = unchanged
GDF4 = NOT_ADMITTED
GPR8 = NOT_ADMITTED
G0–G8 stage identities = preserved
Existing playable experiments = retained apparatus / no product momentum

New conclusion:
GameDevelopmentCore != StageProjection
```

The next Game owner work should improve the development representation and its Agent affordances before selecting any product.
