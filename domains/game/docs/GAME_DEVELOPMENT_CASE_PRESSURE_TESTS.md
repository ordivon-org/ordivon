---
schema_version: 1
id: game.development-case-pressure-tests
title: Ordivon Game — Development Core Case Pressure Tests
profile: research
lifecycle: active
source_role: canonical-research
visibility: public
owners:
  - ordivon-game
updated: 2026-08-28
summary: Pressure-tests the D1-D8 Game Development Core against materially different real development histories: Into the Breach, Celeste, Outer Wilds, Factorio, Hades, and the Roblox live/creator environment. The goal is to falsify or narrow the Development Core, not to copy product formulas.
evidence_status: mixed
readiness: CURRENT
applies_to:
  - ordivon-game
related:
  - game.development-core
  - game.development-paradigm-research
  - game.content-progression-architecture
---
# Ordivon Game — Development Core Case Pressure Tests

## 0. Method

These cases are selected because they stress different development structures:

```text
Into the Breach → decision clarity / tactical combinatorics / aggressive subtraction
Celeste         → embodied skill / level sequencing / story-gameplay co-development
Outer Wilds     → curiosity / knowledge progression / unusual prototype media
Factorio        → systemic construction / teaching / tech-content progression
Hades           → replayable action + authored reactive narrative + Early Access ecology
Roblox          → live population evidence / experimentation / creator-production environment
```

The question is not which game is “best” or which Ordivon should imitate.

For each case:

```text
Development history evidence
→ pressure on D1-D8
→ falsifier / narrowing
→ transferable development law candidate
```

A single case cannot establish a universal law.

## 1. Into the Breach — fast micro evidence can starve macro design

### Development evidence

Subset described the project as beginning from a vague but consequential idea — roughly mechs versus monsters where collateral damage matters — while the final core mechanics only emerged after about a year of iteration. The full project took roughly four years and included extensive cut content.

The team also described near-continuous playtesting: they did not want to build a large system and merely hope its pieces became interesting later. This strongly supported minute-to-minute tactical design.

But the same developers identified a cost: the macro-strategy layer was harder and more frustrating precisely because its value could not be tested as immediately as individual combat interactions.

The final game then leaned hard into telegraphed enemy attacks, low randomness and clarity; the designers repeatedly sacrificed ideas that could not be communicated clearly enough.

### D1-D8 pressure

**D1 Intent / Audience**

A strong seed can be much smaller than a complete product definition:

```text
mechs vs monsters
+ collateral damage must matter
```

The eventual game can remain radically underdetermined for a long time.

Therefore:

```text
D1UsefulSeed != G0CompleteDefinition
```

**D2 Play Causality**

The core emerged by following constraints rather than implementing a pre-specified feature tree:

```text
collateral damage matters
→ buildings must matter
→ enemy intent must be legible
→ player needs counterplay
→ randomness/hidden outcomes shrink
```

This supports causal-chain design rather than feature accumulation.

**D3 Learning / Legibility**

Clarity is not merely UI polish. If strategic state cannot be perceived, the design itself fails.

**D4 Evidence / Prototyping**

Continuous playable evidence was extremely effective for micro interactions but weaker for long-horizon meta design.

This produces a new caution:

```text
FastEvidenceAvailability
can create
EvidenceFrequencyBias
```

A decision that yields feedback every minute can crowd out a decision whose consequences emerge after two hours.

**D5 Content / Progression**

The tactical kernel and the campaign/meta layer require different evidence horizons. One content architecture cannot assume all loops are equally cheap to test.

### Transferable law candidate

```text
EvidenceLatency must be represented.

Experiment priority
!= simply experiments with the fastest observable outcome.
```

Development Core survives, but D4 and D5 must explicitly model **evidence horizon** and multi-loop interactions.

Sources:
- GDC Vault, “Into the Breach Design Postmortem,” GDC 2019.
- Game Developer, “Into the Breach's designers explain how to follow up from a hit game,” 2018.
- Game Developer, “Road to the IGF: Subset Games' Into the Breach,” 2018.

## 2. Celeste — content is not downstream of design; content is a design instrument

### Development evidence

Celeste's development involved hundreds of demanding platforming rooms organized into larger mountain areas. Matt Thorson's level-design discussion emphasizes implicit teaching, reward structure, speedrunning considerations and the process of arranging many local stages into larger areas.

More importantly, the team described development as holistic: story and gameplay for each area were developed together, with the team repeatedly zooming between individual level, area and whole-game views. Good gameplay ideas could force story/pacing changes; good story ideas could cause gameplay changes; content was frequently cut or repurposed.

### D1-D8 pressure

**D2 Play Causality**

The causal unit is not just one mechanic. Level context changes what the same mechanic means and demands.

**D3 Player Learning**

Learning is embedded in level sequence and spatial construction, not isolated into a tutorial.

A level can function as:

```text
introduction
practice
variation
combination
exam
recovery
expression
```

**D5 Content / Progression**

This is the strongest pressure.

The naive model:

```text
mechanics complete
→ produce 300 levels
```

is false.

A better model is:

```text
mechanic hypothesis
↔ level construction
↔ player-learning hypothesis
↔ area pacing
↔ story/expression
↔ whole-game structure
```

Content units are themselves probes of the mechanic possibility space.

**D6 Expression / Feel**

For precision platforming, control response, timing and spatial readability are constitutive. Paper evidence may be useful for map structure but invalid for the central embodied claim.

### Transferable law candidate

```text
ContentUnit
can be both
ProductContent
and
DesignExperiment.
```

And:

```text
MacroStructure and MicroContent co-evolve;
neither is universally upstream.
```

This falsifies any strict “design first, content later” interpretation of D5.

Sources:
- GDC Vault, “Level Design Workshop: Designing Celeste,” GDC 2017.
- Game Developer, “GDC 2017 Level Design Workshop.”

## 3. Outer Wilds — progression can be entirely epistemic

### Development evidence

Outer Wilds began with two broad goals: capture the feeling of space exploration in a world driven by forces beyond player control, and create an open world where exploration is driven by questions rather than explicit objectives.

Those goals generated many apparently disconnected prototypes: model rockets, probes, quantum phenomena, forests and miniature solar systems. The project reportedly struggled to cohere until an “emotional prototype” was used to explore the intended mood.

Later development treated the game's mystery itself as something to prototype using both paper and digital methods. The final experience relies on curiosity and nonlinear knowledge acquisition as the dominant progression mechanism.

### D1-D8 pressure

**D1 Intent / Audience**

High-level experiential goals can precede and organize mechanic discovery:

```text
feel space exploration
+ curiosity-driven open world
```

This is stronger than genre or feature specification but weaker than a product contract.

**D4 Evidence / Prototyping**

Different questions demanded different prototype media:

```text
physics/system behavior   → digital prototype
mystery / information     → paper + digital structure
mood / emotional target   → emotional prototype
```

This strongly validates PrototypeEvidenceContract.

**D5 Content / Progression**

Progression is not primarily:

```text
XP / gear / stat / locked area
```

It is:

```text
Question
→ evidence
→ revised world model
→ newly reachable interpretation/action
→ deeper question
```

The content architecture is therefore an **epistemic dependency graph**, not a conventional unlock tree.

**D3 Player Learning**

Player learning and product progression nearly coincide, but they must still remain separate conceptually: the game can structure evidence; only the player actually learns.

### Transferable law candidate

```text
ProgressionArchitecture
must represent what changes future possibility,
not assume that progression is authoritative World/account state.
```

Possible progression carriers include knowledge, skill, relationship, access, power, content exposure and world transformation.

Sources:
- Game Developer, “Road to the IGF: Alex Beachum's Outer Wilds,” 2015.
- Game Developer, “Demaking Outer Wilds,” 2015.
- GDC Vault, “Sparking Curiosity-Driven Exploration Through Narrative in Outer Wilds,” GDC 2021.

## 4. Factorio — progression is an induced learning-and-construction programme

### Development evidence

Factorio's long-running developer logs provide unusually detailed evidence of progression design changing over time.

Science packs and technology were repeatedly redesigned because their context and design goals changed. The developers explicitly describe science packs as a way to guide the player toward automating things they should naturally need at that point. Later science redesigns aimed to smooth complexity and make meaningful branches clearer.

Its new-player-experience work made an even stronger distinction: teach the **order of concepts**, not merely the order of operations. The team framed Production as the central concept and deliberately changed the environment to remove premature prerequisites while teaching it. They also used external novice playtesting rather than assuming expert developers could simulate new-player cognition.

Campaign redesign fed changes back into Freeplay progression. Expansion design extended this pattern: planets, science packs, rewards and order choices were deliberately coupled so that each new region changed the production problem rather than merely adding scenery.

### D1-D8 pressure

**D3 Player Learning**

A progression architecture can deliberately teach a conceptual model:

```text
recipe
→ production chain
→ automation
→ scaling
→ logistics
→ increasingly coupled systems
```

The order of concepts can differ from the final system's dependency order.

**D5 Content / Progression**

Factorio demonstrates that progression is not just a reward schedule. It simultaneously manages:

```text
Concept introduction
Production pressure
Resource demand
Automation necessity
New option/reward
Complexity growth
Strategic branching
```

A good unlock can act as a design message about what kind of system the player should build next.

**D4 Evidence**

Campaign/tutorial work exposed flaws in Freeplay, proving that one content surface can serve as a diagnostic of the deeper progression architecture.

**D7 Production Realization**

The content system is highly systemic: changing a science recipe can propagate across resource ratios, factory size, technology dependencies and later balance. Tooling and analysis therefore become design capabilities.

**D8 Evolution**

In 2026, Wube still used office LAN playtesting and community evidence for its 2.1 work, while intentionally rejecting large new content categories because the existing progression was already considered strong. The live/release loop can therefore produce **subtraction and restraint**, not only expansion.

### Transferable law candidate

```text
ProgressionElement =
ChangeInPossibility
+ ChangeInPressure
+ LearningSignal
+ Reward/Desire
+ DownstreamCompositionalEffects
```

And:

```text
Unlock != RewardOnly
DifficultyCurve != NumericDifficultyOnly
```

Sources:
- Factorio Friday Facts #159, Research revolution.
- Factorio Friday Facts #245, Campaign concept.
- Factorio Friday Facts #275, 0.17 Science changes.
- Factorio Friday Facts #284, 0.17 experimental / new-player experience.
- Factorio Friday Facts #373/#376, Space Age progression and technology.
- Factorio Friday Facts #440, 2.1 plan, 2026.

## 5. Hades — development ecology can be product architecture

### Development evidence

Supergiant states that Hades was designed for Early Access from the beginning. The studio wanted a game that could evolve in public with community feedback; its modular structure and narrative design were shaped around that development model.

The team wanted immediacy, replayability, many viable playstyles and overlapping systems that could generate different runs. Narrative was built to react to player state and run history rather than depend on one fixed sequence. Early Access updates were organized on a repeated cadence, and new narrative/content had to integrate with the existing relationship/event graph rather than exist as isolated additions.

The final game included more than twenty thousand voiced dialogue lines, showing that “systemic/replayable” does not imply low authored-content burden; instead, it demands a content architecture that can condition, select and recombine authored material.

### D1-D8 pressure

**D1 Intent**

Early Access itself was part of the concept constraint, not merely a publishing decision added at G8.

**D5 Content / Progression**

Hades requires at least two coupled content architectures:

```text
combat build/run combinatorics
+
reactive narrative/event graph
```

Both must survive repetition without collapsing into sameness.

**D7 Production Realization**

A repeated update cadence creates production architecture pressure: content must be independently shippable, testable and integrable.

**D8 Product Ecology**

Community feedback becomes an ongoing evidence stream during development, but it does not automatically own design decisions.

This demonstrates:

```text
ProductEcology can begin before 1.0.
```

### Transferable law candidate

```text
Development / release model
can constrain content grammar and architecture
before conventional release.
```

And:

```text
AuthoredContent != LinearContent
SystemicGame != LowAuthorshipGame
```

Sources:
- Supergiant Games, Hades FAQ.
- Game Developer, “Supergiant's fourth outing Hades introduces a more mature, organized dev process,” 2019.
- Game Developer, “How Supergiant added new goddess Demeter to Hades' pantheon,” 2020.
- GDC Vault, “Breathing Life into Greek Myth: The Dialogue of Hades,” GDC 2021.

## 6. Roblox — population evidence and production agents create a different environment, not a universal game model

### Current environment evidence

Roblox Creator Hub exposes production analytics, onboarding funnels, retention and engagement metrics, configurable experiments and in-game/matchmaking A/B tests. Its current experiment system explicitly asks creators to begin with a causal hypothesis, select a goal metric, run controlled variants and inspect statistical uncertainty.

Roblox's 2026 Build/Studio direction also includes planned playtesting, analytics and experiment Agents, while text-to-game and generative asset/scene tooling lowers creation latency.

### D1-D8 pressure

**D3 Player Learning**

Onboarding is represented as a measurable funnel, but funnel completion/retention remains only a proxy for learning and experience.

**D4 Evidence**

A population experiment and an internal machine counterfactual are distinct evidence regimes:

```text
same hypothesis discipline
but different subjects, noise and authority
```

**D7 Production Realization**

Agentic tools can make project mutation, playtesting and analysis cheaper. This changes reachable production/search bandwidth.

**D8 Product Ecology**

Discovery, retention, social context, moderation, monetization and update cadence are tightly coupled to the environment. For games built on such a platform, D8 cannot be postponed until release.

But Roblox also creates a dangerous optimization surface:

```text
metric improves
!= experience improved by identity
```

A/B tests can establish causal metric effects; they cannot by themselves establish why the experience is better or whether the optimized metric expresses the intended product value.

### Transferable law candidate

```text
PopulationEvidence must name:
metric
population
intervention
causal scope
product interpretation
```

And:

```text
AgentProductionLeverage expands experiment throughput;
it does not make metric selection or product interpretation automatic.
```

Sources:
- Roblox Creator Hub, Analytics.
- Roblox Creator Hub, Experiments.
- Roblox Creator Hub, Onboarding.
- Roblox, “Build Without Limits on Roblox,” July 2026.

## 7. Cross-case falsification matrix

| Development-Core claim | ITB | Celeste | Outer Wilds | Factorio | Hades | Roblox | Standing |
| --- | --- | --- | --- | --- | --- | --- | --- |
| D1 intent/context matters before implementation | yes | yes | strong | yes | strong | conditional | survives |
| D2 play causality is distinct from feature list | strong | strong | strong | strong | strong | yes | survives |
| D3 player learning is continuous responsibility | yes | strong | strong | very strong | yes | strong | survives |
| D4 evidence medium must fit question | yes | yes | very strong | strong | yes | strong | survives |
| D5 content/progression is first-class architecture | macro weakness exposed | very strong | epistemic | very strong | very strong | live content | **strengthened** |
| D6 expression can be constitutive | UI clarity | very strong | mood/readability | moderate | strong | form-dependent | survives |
| D7 production realization is separate evidence | yes | yes | yes | strong | strong | very strong | survives |
| D8 ecology can constrain before release | weak | small | small | community | very strong | constitutive | **narrowed: conditional but potentially early** |
| G0-G8 alone explain development causally | no | no | no | no | no | no | rejected |

No case forces D9.

The main change is within D4/D5/D8, not expansion of the top-level responsibility count.

## 8. New laws / repairs earned by the cases

### 8.1 Evidence Horizon

Add to D4:

```text
EvidenceHorizon =
interaction
| encounter
| session
| run
| campaign
| cross-session
| population/time-window
```

A fast evidence loop must not receive priority solely because its feedback is cheap.

### 8.2 Multi-scale loop topology

D2/D5 should distinguish:

```text
micro interaction loop
encounter/content-unit loop
session/run loop
progression/campaign loop
population/live loop
```

A good micro loop cannot prove a good macro loop.

### 8.3 Content as experiment

```text
ContentUnit may be:
player-facing content
+ mechanic probe
+ learning probe
+ pacing probe
+ expression probe
```

Do not require content to wait until all design is “finished.”

### 8.4 Progression is carrier-relative

```text
ProgressionCarrier =
skill
| knowledge
| possibility/access
| power/resources
| system complexity
| relationship/identity
| world transformation
| content exposure
| social/institutional standing
```

No carrier is universal.

### 8.5 Ecology timing is form-relative

```text
D8StartTime = consequence of GameForm / platform / population dependency
not always G8.
```

## 9. Result

D1-D8 survives the first real-case pressure test.

But D5 was under-specified enough that it now deserves a deeper practical derived model. That model is `GAME_CONTENT_PROGRESSION_ARCHITECTURE.md`.

No new local playable is justified by this round.
