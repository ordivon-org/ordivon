---
schema_version: 1
id: game.development-model
title: Ordivon Game Development Model
type: development-model
profile: product
lifecycle: active
source_role: canonical
visibility: public
owners:
  - ordivon-game
audience:
  - designer
  - builder
  - agent
  - producer
updated: 2026-08-17
summary: Canonical development model for classifying, prototyping, validating, producing, and shipping Ordivon games. Conventional GameForm is primary; Agent participation is split into optional production and runtime roles inside the normal game lifecycle, while Studio remains owner of medium-specific production.
evidence_status: derived
readiness: READY
applies_to:
  - ordivon-game
related:
  - game.vision
  - game.authority
---
# Ordivon Game Development Model

## Purpose

Ordivon Game has accumulated strong evidence about authoritative Worlds, bounded Agent cognition, action admission, partial information, hierarchical control, recovery, replay, and player-facing causal legibility. Those are **runtime-Agent mechanisms**. They are optional capabilities, not the definition of an Ordivon game and not, by themselves, a complete game-development process.

This model puts that research back inside ordinary game development:

```text
classify the game
→ define the experience and core loop
→ prove the game kernel
→ build a playable prototype
→ prove a representative vertical slice
→ produce content and media
→ balance, QA and polish
→ release and learn
```

Agent-assisted production may run throughout that lifecycle. Runtime-Agent work is a separate optional lane admitted only when the selected GameForm needs it. Neither replaces the lifecycle.

## The correction

Phase names such as P0–P3, GX/AF research rounds, or R1–R10 consumer improvements are historical work decomposition. They must not become the player's game loop or the permanent product architecture.

Likewise, installed equipment must not determine game form. A Blender installation is not evidence that a game should become 3D; an Agent-capable Provider is not evidence that every Actor should invoke a model.

The dependency points the other way:

```text
game form + experience target
→ mechanic and content requirements
→ presentation / production requirements
→ tool and equipment consumption
```

### Why this model, not the alternatives

Three organizations were tested against the work Game actually has to do:

| Model | What it gets right | What it loses | Verdict |
| --- | --- | --- | --- |
| ordinary game stages only | concept, prototype, slice, production, QA, release | hides concurrent responsibility/evidence standing and has no explicit Agent-value proof | retain as stage projection, insufficient alone |
| Agent-first creative loop as the whole lifecycle | fast hypothesis search, matched play, falsification | content, art/audio, production throughput, platform and shipping become secondary | reject as stage/process authority |
| nested model | normal production outside; Agent consequence/research inside | requires resisting process inflation | **retain** |

Deletion pressure makes the distinction operational:

- remove the stage/commitment projection and the project loses a coarse coordination language for product investment and scope;
- remove the Agent lane and an LLM feature can reach production without proving bounded observation, legal action or meaningful consequence;
- promote the Agent research loop to stage/process authority and Game becomes research-rich but production-poor again;
- remove classification and current tools/architecture begin choosing the product by accident.

There is one product-stage authority, not two competing process authorities. G0–G8 remain the canonical stage projection; they do not by themselves explain the causal work of discovering and developing a game.

## 1. What an Ordivon game is

The durable Game thesis remains:

```text
Ordivon Game
= authoritative World
+ meaningful agency
+ player experience
+ persistent consequence
```

A game may be tactical, social, creative, action-oriented, systemic, narrative, or something not yet represented by Station Zero. The shared discipline is that uncertain cognition and presentation do not silently become authoritative reality.

### Five product responsibilities

A useful game can be discussed through five responsibilities without turning them into five services:

| Responsibility | Question |
| --- | --- |
| **Experience** | Who is the player, what do they feel and do, and why would they return? |
| **Kernel** | What state, rules, verbs, resources, information and consequences make play possible? |
| **Content** | Which characters, places, encounters, items, missions, stories or creations instantiate the kernel? |
| **Expression** | How are those meanings made visible, audible, legible, affecting and coherent? |
| **Runtime** | Which engine, renderer, input, persistence, networking and platform mechanisms execute the product? |

Evidence, replay, playtest data and production receipts support these responsibilities; they are not a sixth gameplay layer.

### Development Core beneath the stage projection

The five responsibilities above describe the product being made. They are not sufficient to represent **development standing**. Current cross-paradigm research in [`GAME_DEVELOPMENT_CORE.md`](GAME_DEVELOPMENT_CORE.md) therefore exposes eight concurrent development views:

```text
D1 Intent / Audience Context
D2 Play Causality
D3 Player Learning / Legibility
D4 Evidence / Prototyping
D5 Content / Progression Architecture
D6 Expression / Feel
D7 Production Realization
D8 Product Ecology / Evolution
```

These are responsibility/evidence views, not new Foundations, services or stage names.

```text
GameDevelopmentCore != G0–G8 StageProjection
```

The stage projection remains useful for coordination and commitment. The Development Core explains what can be mature, weak, stale or reopened **inside the same stage**. A G4 project can have strong pipeline proof and weak Human experience evidence; the stage must not silently upgrade the weaker claim.

The external-paradigm comparison and the reasons for this repair are retained in [`GAME_DEVELOPMENT_PARADIGM_RESEARCH.md`](GAME_DEVELOPMENT_PARADIGM_RESEARCH.md).

## 2. Classification before implementation

Genre names remain useful shorthand, but genre alone is not a sufficient production specification. Ordivon classifies a candidate game using one required GameForm profile plus two orthogonal Agent profiles. A traditional game may have heavy Production-Agent use and no Runtime Agents at all.

### 2.1 Conventional Form Profile

Record the smallest conventional facts that materially predict game design and production work:

| Field | Examples | Why it matters |
| --- | --- | --- |
| **player fantasy** | commander, survivor, explorer, builder, companion, ruler | anchors experience and content judgment |
| **core verbs + cadence** | aim/dodge in real time, plan/commit by Turn, build/manage continuously | determines input, simulation and feedback requirements |
| **control topology** | direct avatar, party/unit control, delegated organization, world editing | determines UI, camera and autonomy boundaries |
| **space + camera** | abstract graph, 2D board, isometric 2.5D, first-person 3D, no spatial world | predicts level, animation and rendering workload |
| **session + progression** | encounter, mission, run, campaign, persistent world | predicts content volume, save model and retention design |
| **social/network form** | solo, local/online co-op, competitive, shared persistent world | predicts networking, moderation and synchronization work |

A conventional genre label such as `turn-based tactics`, `party RPG`, `colony simulation`, or `social sandbox` may summarize these fields, but it does not replace them.

### 2.2 Production Agent Profile

Separately describe how Agents help **make, test or operate** the game. These roles are production technology, not player-facing genre facts. Useful roles include research/evidence search, design-space expansion, prototype building, programming, draft content/asset authoring, editor/tool operation, synthetic play, QA/falsification, balance analysis, production orchestration, localization/accessibility assistance and release triage.

A Production Agent may be critical to Ordivon feasibility while remaining completely absent from the shipped runtime. Production leverage must be measured against review, rework, provenance, tooling and model cost rather than assumed.

### 2.3 Runtime Agent Participation Profile

Only when runtime intelligence is actually proposed, describe why it exists rather than assuming “Agent game” is one genre:

| Field | Useful values |
| --- | --- |
| **role** | companion, subordinate, adversary, inhabitant, economic actor, narrator, co-creator |
| **autonomy depth** | dialogue only, local choice, tactical delegation, strategic/systemic autonomy |
| **epistemic boundary** | public/common state, bounded local observation, asymmetric/hidden knowledge |
| **continuity** | one interaction, one session, cross-session character, persistent world inhabitant |
| **organization** | independent, peer group, party, hierarchy, institution/population |
| **cognition tier** | scripted/policy, model, mixed hierarchy, human+Agent joint control |

These fields are descriptive, not mandatory feature slots. A game with one persistent companion does not need population organization; a real-time boss does not need cross-session Agent memory merely because another Ordivon world does.

### Classification rule

The **Form Profile determines the conventional game and its baseline production burden**. The **Production Agent Profile measures how Agent tooling changes the reachable production frontier**. The **Runtime Agent Participation Profile determines any extra shipped cognition/authority/feedback burden**.

Do not reverse them. In particular:

```text
AgentBuiltGame != AgentGame
ProductionAgentNeed != RuntimeAgentNeed
```

## 3. The Runtime Agentic Consequence Loop — when applicable

When a shipped game contains a runtime Agent that can affect authoritative World state, the smallest Agent-specific kernel that Ordivon research has repeatedly supported is:

```text
Authoritative World
      ↓ bounded observation
Agent cognition
      ↓ bounded decision
Action admission
      ↓
World consequence
      ↓ owned feedback
updated cognition / later choice
```

More explicitly:

```text
OBSERVE
→ COGNIZE
→ DECIDE
→ ADMIT
→ RESOLVE
→ FEEDBACK
→ ADAPT
```

### Stable responsibilities

**World** owns entities, time, resources, legal transitions and authoritative consequence.

**Observation** decides what this Agent may know now. Hidden World truth is not a convenient prompt ingredient.

**Cognition** may be a deterministic policy, a model, a human, or a hierarchy. Game should not equate “Agent” with “one LLM request.”

**Decision** is an intention or selection at the semantic level required by the game.

**Admission** verifies identity, capability, authority, currentness and legal action space before cognition can become game action.

**Resolution** produces authoritative consequence through game rules rather than model narration.

**Feedback** gives the acting subject enough owned evidence to distinguish execution, failure, contest, interruption or no effect without granting omniscience.

**Adaptation** is earned when later decisions materially change from retained feedback, memory, relationships or world history.

### Optional Agent mechanisms

The following are important in some games but are **not** universal kernel requirements:

- long-term memory;
- relationships and reputation;
- language dialogue;
- organizations and institutions;
- planning hierarchies;
- economic ownership;
- creative artifact generation;
- cross-session identity;
- hundreds of simultaneous Agents;
- model calls for every Actor.

They are admitted by the selected game form and measured player value.

### Agent-value falsifier

An Agent earns its complexity only when at least one material experience degrades under a cheaper baseline.

Compare, where practical:

```text
script / deterministic policy
vs
Agent cognition
```

Ask whether Agent participation materially improves or creates:

- strategic adaptation;
- coordination or disagreement;
- social/character continuity;
- asymmetric information play;
- creative collaboration;
- adversarial variation;
- player attachment or surprise;
- persistent world consequences.

If the Agent mostly adds latency, cost and prose while the trajectory is equivalent, shrink it to the cheaper mechanism.

## 4. Canonical G0–G8 stage projection

The lifecycle below is the outer process for Ordivon games. It is intentionally recognizable as normal game development.

### G0 — Define

**Question:** What game are we making and why should it exist?

Produce a bounded Game Definition:

- player fantasy and target experience;
- Conventional Form Profile;
- Runtime Agent Participation Profile **when claimed**; a game with no runtime Agents records `none`;
- Production Agent strategy separately from the product definition;
- target platform/input/session shape;
- one-sentence loop summary plus loop topology when materially multi-scale;
- initial visual/audio direction only at the level needed to constrain production;
- explicit non-goals.

**Exit gate:** two people/Agents reading the definition should predict roughly the same game rather than merely the same technology.

**Do not:** choose an engine or build Agent infrastructure to compensate for an undefined game.

### G1 — Preproduction / core design

**Question:** What must be true for this game to be fun or valuable?

Define and attack:

- core player verbs;
- state/resources/information;
- success, failure and progression;
- player ↔ runtime-Agent responsibility split, when runtime Agents are claimed;
- authoritative World boundaries;
- Runtime Agentic Consequence Loop where runtime Agents materially participate;
- content grammar: what kinds of levels, encounters, characters, items or activities the game needs;
- production risks: art, animation, audio, networking, performance, model latency/cost.

Use competing designs and deletion tests. Avoid polishing content before the core loop has a reason to survive.

**Exit gate:** a small set of falsifiable design pillars and a prototype plan exist; every proposed permanent system can name the player/world failure it addresses.

### G2 — Kernel / graybox prototype

**Question:** Do the rules and Agent roles produce interesting decisions before expensive presentation exists?

Choose the cheapest **valid evidence carrier**, not merely the cheapest implementation. Paper/tabletop, formal models, simulations, interactive mocks, grayboxes, technical spikes and engine prototypes represent different dimensions and carry different false-positive/false-negative risks. A material prototype should name its target question, represented and omitted dimensions, comparison/baseline, observation method and decision rule.

Build the cheapest valid surface that can test:

- core loop / loop topology;
- major rules and verbs;
- information boundaries;
- runtime-Agent decision/action consequence, only when the form claims runtime Agents;
- failure/success;
- latency/cost budget;
- one representative content unit.

Prefer fixture/policy Agents first when they isolate game rules better than live Providers. Introduce a real model only when the hypothesis depends on cognition the fixture cannot represent.

**Studio consumption:** normally minimal. Placeholder geometry, icons, text, procedural sound and graybox media are sufficient unless presentation itself is the mechanic.

**Exit gate:** repeated play demonstrates a loop worth improving; if runtime Agent participation is claimed, it survives at least one cheaper-baseline comparison; major rules can be changed cheaply.

### G3 — Playable prototype

**Question:** Can a player complete the intended loop without developer intervention?

Add enough product surface for real play:

- start/session/end flow;
- understandable controls and feedback;
- representative Agent behavior;
- save/recovery appropriate to the session form;
- basic content variation;
- real browser/engine input rather than test-only invocation.

This phase tests comprehension and consequence, not final beauty.

**Exit gate:** independent play can reach success/failure; players can form a causal model of their important decisions; repeated technical execution is stable enough that playtest findings dominate engineering noise.

### G4 — Vertical Slice

**Question:** Can one representative slice demonstrate the intended final quality and prove the production pipeline?

A vertical slice is a **compound evidence bundle**, not one indivisible truth. It may separately establish experience representativeness, quality bar, integration proof, pipeline proof, throughput estimate and performance envelope. Audience resonance or market/population claims remain separately evidenced.

A vertical slice combines, in one bounded piece of real gameplay:

- near-final gameplay quality;
- representative runtime-Agent cognition and fallbacks, only when the selected form claims them;
- representative level/encounter/content quality;
- target-ish UI/UX;
- target art direction;
- representative animation/VFX;
- representative audio/music/voice where applicable;
- performance and loading expectations;
- production handoffs that can actually be repeated.

This is the first stage where broad Studio consumption is expected.

**Exit gate:** the team can answer both “is this worth producing at the currently justified evidence scope?” and “can we repeatedly produce it?” Preserve the component standing: a beautiful demo can pass quality and fail pipeline/throughput; a repeatable pipeline can exist without strong Human Player Value evidence.

### G5 — Production / content expansion

**Question:** Can the proven slice become the required breadth of game without losing coherence?

Scale the content grammar rather than inventing a new kernel each week:

- levels/encounters/missions;
- characters/enemies;
- items/abilities;
- narrative and world expression;
- animation/VFX/audio variants;
- accessibility and localization content;
- Agent behavior/content data and bounded evaluation sets.

Agent-first production should accelerate authoring, simulation, review and QA while preserving owner-native source and approval boundaries.

**Exit gate:** planned content can be produced at sustainable cost and quality; remaining kernel changes are exceptional rather than routine.

### G6 — Alpha / content-complete validation

**Question:** Does the whole game work as a game rather than as isolated good slices?

Focus on:

- complete progression/session flow;
- strategy/build viability;
- difficulty and economy;
- Agent behavior distributions and pathological loops;
- content pacing and repetition;
- save/recovery compatibility;
- performance budgets;
- broad QA and accessibility.

Large model-run matrices are useful here only when they approximate meaningful player/Agent trajectories. Simulation volume does not substitute for experience judgment.

**Exit gate:** all intended major content is present; no known blocker requires redesigning the core loop.

### G7 — Beta / polish / release candidate

**Question:** Is the game coherent, stable and shippable on the target surface?

Concentrate on:

- bugs and regressions;
- UX friction;
- animation/audio/UI polish;
- platform integration;
- localization/accessibility finalization;
- performance and memory;
- install/update/recovery;
- capture and publication assets;
- release configuration.

**Exit gate:** release candidate passes product, technical and distribution acceptance. New kernel features require exceptional evidence.

### G8 — Release / operate / learn

**Question:** What does real use teach us that development could not?

Depending on the game form:

- observe crashes, performance and operational failures;
- collect bounded gameplay/strategy evidence;
- review audience response without promoting one preference to universal truth;
- patch defects;
- rebalance when outcome evidence supports it;
- add content or expansions only where retained play justifies them.

A finite game may end here except for maintenance. A live or persistent game may loop G5–G8 repeatedly.

## 5. Evidence loops inside the stage projection

Stages do not decide which evidence method is valid. Start from the decision:

```text
DecisionToInform
→ ClaimType
→ valid evidence carrier / population / method
→ observation
→ scoped standing
→ retain / revise / delete / reopen
```

For Human/player claims, use a typed Player Evidence record rather than a generic “playtest passed” bit: target population/context, method, sample scope, decision, known limitation and result standing. Early context interviews, observed comprehension tests, experience/resonance studies, broader quantitative balance work and post-launch population experiments answer different questions.

For machine/synthetic evidence, retain the same discipline: reachability, strategy, causal control, robustness and regression evidence do not become Human experience by fluent narration or sample volume.

## 6. The Agent research lane inside the lifecycle

Agent-first development is primarily a **method of research, production and iteration**, not a promise that the shipped game contains Agents and not a substitute lifecycle.

At any stage where Agent participation matters:

```text
hypothesis
→ build smallest treatment
→ play / simulate real trajectories
→ observe owned consequences
→ compare cheaper/control baseline
→ attack with falsifiers
→ retain, shrink or delete
```

Useful Agent advantages include:

- rapidly generating competing mechanic hypotheses;
- building graybox implementations;
- running many deterministic/policy play trajectories;
- playing as bounded adversaries or companions;
- discovering edge cases and strategy failures;
- producing Studio briefs and draft media sources;
- inspecting rendered artifacts;
- regression testing and QA.

Do not confuse these with evidence that a feature is fun. Browser/E2E completion proves a journey works; simulation proves trajectories exist; human-response claims still require appropriate experience evidence when they are material.

### Strategy existence and Agent realization are different claims

Prior Game falsification established a durable separation:

```text
reachable future space
≠ policy-accessible future space
≠ model-realized future space
```

World rules may contain a viable strategy that a current policy cannot reach. A policy may expose that strategy while the current model still fails to preserve the commitment needed to realize it. Therefore:

```text
Agent failed
≠ Game has no strategy

counterfactual strategy exists
≠ current Agent can play it
```

Do not automatically compile a known winning counterfactual into Harness or policy. That may erase the decision problem instead of improving the Agent or the game.

### Learning scope

A successful treatment is promoted only as far as its evidence supports:

```text
one trajectory / ablation
→ local observation

repeated evidence inside one game form
→ game-medium prior candidate

survives materially different game pressure
→ durable prior candidate
```

Counterevidence may narrow, demote or retire any prior. Historical AF/GX/R results therefore remain evidence, not permanent workflow structure.

## 7. Game ↔ Studio production contract

Game and Studio solve different problems.

```text
GAME
owns gameplay meaning and runtime need
        ↓ bounded production brief
STUDIO
owns medium-specific editable expression and production
        ↓ exact selected outputs + evidence
GAME
integrates the outputs and owns their gameplay behavior
```

### Game owns

- current game/product truth;
- gameplay semantics;
- World entities and rules;
- semantic level/encounter structure;
- character/ability/item identity and behavior;
- collision/navigation/interactivity requirements;
- runtime interface and performance budget;
- the production need and acceptance criteria.

### Studio owns

Studio's existing authority remains unchanged:

```text
exact owner revision + bounded Claim
→ editable writing / visual / audio / motion / interaction source
→ selected Assets and exact bytes
→ render or composition
→ factual/mechanical review
→ medium craft judgment
→ Output
```

Studio owns medium choice within the brief, editable creative state, visual/audio/motion expression, selected Asset/Blob identity, provenance/rights, render/composition, QC/review preparation and delivery variants. A polished Output never becomes authoritative game-rule truth.

### Production brief

Do **not** introduce a cross-repository schema until repeated real productions force one. Initially a Game production brief needs only enough information to eliminate semantic ambiguity:

- exact Game source revision / owning object identity;
- experience purpose: what the player must perceive/feel/do;
- semantic meaning that must not be changed by art;
- required states/variants/animations or temporal events;
- dimensions, camera/runtime interface and technical budget when known;
- accessibility/localization requirements when applicable;
- acceptance/falsifier conditions;
- editable-source requirement and provenance constraints.

Studio may bind that brief into its existing Production/Claim/Asset/Output model.

### Return to Game

Game should consume:

- exact selected output identity/bytes;
- the editable source locator or retained Studio Production identity when future revision matters;
- required runtime metadata;
- scoped QC/provenance evidence;
- no Studio-private creative history unless the next Game decision depends on it.

Game then owns how the asset participates in gameplay. Studio does not decide hitboxes, objective truth, passage state, damage, AI authority or success conditions unless those are themselves part of a separately owned creative game-design task.

### Studio activation follows development stage

| Stage | Default Studio consumption | Usually premature |
| --- | --- | --- |
| G0–G1 Define / preproduction | references, style exploration, rough UX when they resolve product questions | full asset library or final media pipeline |
| G2 graybox | placeholders and only the media needed for legibility | final character/environment production |
| G3 playable prototype | targeted readability/UI/audio treatment when presentation blocks playtesting | broad production scale |
| G4 vertical slice | representative final-ish UI, art, animation/VFX, audio, editable source and QC pipeline | speculative factory beyond slice needs |
| G5 production | scaled owner-native media production and variants | repeated redesign of an unproven kernel |
| G6–G7 validation/polish | coherence, accessibility media, optimization, capture and publication preparation | new art direction without critical evidence |
| G8 release/live | delivery media, patches and justified new content waves | tool-driven redesign unrelated to player evidence |

Some games pull Studio earlier because expression is itself part of the core mechanic. The table is a default pressure model, not a prohibition.

## 8. Tool consumption follows the production need

Installed tools expand reachable production worlds; they do not prescribe them.

| Need proven by game form / brief | Typical owner/equipment | Boundary |
| --- | --- | --- |
| semantic 2D level topology / zones / object placement | Game + Tiled or engine level editor | geometry used by rules remains Game-owned |
| runtime/input/render integration | Game + browser/Godot/other mature engine | choose only after form/platform pressure |
| UI interaction architecture | Game; Studio/Figma may produce visual design | control semantics remain Game-owned |
| vector UI/icon/schematic expression | Studio + Inkscape/Figma | selected output does not own gameplay state |
| 2D sprite/animation/VFX source | Studio + Aseprite | frame/tag metadata may be consumed by Game |
| 3D scene/mesh/material/camera/animation | Studio + Blender | only when art/camera form requires 3D |
| sound design/music/editorial audio | Studio + REAPER and mature audio tools | Game owns trigger/behavior; Studio owns sound expression |
| gameplay/performance capture | Studio/QA + OBS | capture is evidence/media, not World truth |
| trailer/editorial/color/delivery | Studio + Resolve | publication pipeline, not gameplay runtime |
| transforms/probes/QC | Studio/Game as appropriate + FFmpeg/ImageMagick/etc. | mechanical facts do not imply aesthetic quality |
| GPU-frame debugging | Game engineering + RenderDoc when a real GPU surface exists | observability, not content production |

Tool admission rule:

```text
required game capability
AND mature existing tool materially reduces cost/risk
AND ownership boundary remains clear
→ consume the tool
```

Otherwise defer it.

## 9. Content and infrastructure use different admission standards

Infrastructure must justify persistent complexity:

- what responsibility does it uniquely own?
- what recurring failure exists without it?
- why is a local adapter or mature tool insufficient?
- what is its deletion/shrink path?

Creative content is admitted by experience value:

- does it create fun, tension, surprise, attachment, beauty, expression or curiosity?
- does it deepen the selected game fantasy?
- does it create a new meaningful possibility?
- is its production cost proportionate to that value?

Do not optimize content with the same minimalism used for authority infrastructure. That produces a technically elegant empty game.

## 10. Falsifier cases: the model must survive games unlike Station Zero

### Case A — real-time action game with one adaptive boss

Form: direct avatar, real-time action, 3D arena, short sessions.

Agent participation: one adversary with local tactical autonomy; no persistent population.

Required Agent loop: boss observes admitted combat state, chooses bounded tactics, World resolves attacks/movement, feedback informs adaptation.

Not required: Commander Orders, faction Plans, multi-Agent hierarchy, cross-session memory, turn persistence.

Production pressure: animation, VFX, hit readability, 3D environment, audio and latency dominate. This case falsifies any model that assumes Station Zero's turn/planning UI is universal.

### Case B — party RPG with autonomous companions

Form: direct/party exploration and combat, authored world, campaign progression.

Agent participation: persistent companions with local combat choice, dialogue, relationships and memory.

Required Agent loop remains; relationship/memory become game-specific extensions because later choices and player attachment depend on them.

Production pressure: characters, dialogue performance, quests, animation, environments and narrative continuity. This case falsifies a kernel that treats dialogue as irrelevant merely because Station Zero does not depend on it.

### Case C — colony simulation with many inhabitants

Form: management/simulation, persistent systemic world, long sessions.

Agent participation: many inhabitants; only a minority may need expensive cognition, with policy/hierarchical control for the rest.

Required Agent loop remains, but economic/social state and long-horizon persistence become central. A one-model-call-per-inhabitant architecture fails cost and latency pressure. This case validates cognition tiers rather than universal full-fidelity Agents.

### Case D — creative social world

Form: sandbox/creative/social, persistent or session-based shared spaces.

Agent participation: co-creators or inhabitants whose artifacts and relationships alter later possibilities.

The Agent loop ends not only in combat/resource state but also in authoritative created artifacts, ownership/placement/relationship consequences. Studio may become a frequent production collaborator, yet World ownership and publication/creative-expression ownership still remain distinct.

This case falsifies any definition of Game that equates consequence with tactical damage or objective scoring.

### Result of the falsifiers

The following survive all four cases:

```text
canonical G0–G8 stage projection + Development Core responsibility model
Conventional Form Profile
Agent Participation Profile
Agentic Consequence Loop
World/cognition/admission separation
content vs infrastructure distinction
Game ↔ Studio production ownership
production-need-driven tool selection
```

Station Zero-specific Plans, Turns, Commander forms, factions, tactical Zones, sealed enemy Plans and exact Host execution shape do not survive and therefore remain product-local.

## 11. Start packet for any future Ordivon game

Before implementation, answer these in one bounded record:

1. **Fantasy:** who is the player and what is the desired experience?
2. **Form:** what are the verbs/cadence, control topology, space/camera, session/progression and social form?
3. **Production Agent leverage:** which research/build/test/production roles can materially change cost, search breadth or iteration speed, and what review/rework debt do they add?
4. **Runtime Agent role:** if any shipped Agent is claimed, what autonomy/authority does it own, what player-relevant distinction requires it, and why is a cheaper script/policy/human baseline insufficient?
5. **Kernel:** what authoritative state, resources, information and consequences define play?
6. **Play causality / loop topology:** what does the player repeatedly observe/decide/do; which dynamics are expected to create the target experience; which micro/session/meta loops matter?
7. **Player learning:** what must become legible, learnable, practiced and progressively recombined?
8. **Content/progression architecture:** what grammar, introduction order, variation/combination space and macro structure must be repeatedly produced?
9. **Expression criticality:** which input/camera/UI/art/audio/animation/feel dimensions are merely representative and which are constitutive of the hypothesis?
10. **Production risk:** which tools, pipelines, art/audio/animation/network/model/runtime capabilities dominate cost, throughput or uncertainty?
11. **Evidence plan:** what decision is currently blocked, what is the cheapest valid evidence carrier, what dimensions does it omit, and what observation would change the decision?
12. **Player/product ecology:** which audience/context/distribution/community/telemetry/live-operation assumptions constrain this form now rather than only after release?

Only after this packet should engine, provider and production-equipment choices become commitments.

## 12. Stage routing rule

When work feels confused, do not invent another numbered research series first. Ask:

```text
What development stage are we in?
What stage exit gate is currently false?
Is the blocker gameplay, Agent participation, content, expression, runtime, or production throughput?
Which owner can change that fact?
```

Then create bounded research or production tasks under that stage.

A research round is a **search method**. It is not a product phase.

## Current boundary

This document deliberately does **not** reclassify, redesign, balance, register, or replace Station Zero. Station Zero is a later consumer used to test this development model after the model itself is canonicalized.

It also does not create a universal Ordivon game engine, shared Asset database, universal Agent registry, or cross-project workflow service.
