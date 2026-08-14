---
schema_version: 1
id: game.development-model
title: Ordivon Agent Game Development Model
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
updated: 2026-08-14
summary: Canonical development model for classifying, prototyping, validating, producing, and shipping Ordivon games with consequential Agent participation while keeping normal game development as the outer lifecycle and Studio as the owner of medium-specific production.
evidence_status: derived
readiness: READY
applies_to:
  - ordivon-game
related:
  - game.vision
  - game.authority
---
# Ordivon Agent Game Development Model

## Purpose

Ordivon Game has accumulated strong evidence about authoritative Worlds, bounded Agent cognition, action admission, partial information, hierarchical control, recovery, replay, and player-facing causal legibility. Those are **Agent-game mechanisms**. They are not, by themselves, a complete game-development process.

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

Agent-specific work runs as a lane inside that lifecycle. It does not replace the lifecycle.

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
| ordinary game stages only | concept, prototype, slice, production, QA, release | no explicit proof that Agent observation/action/consequence is legitimate or valuable | keep as outer lifecycle, insufficient alone |
| Agent-first creative loop as the whole lifecycle | fast hypothesis search, matched play, falsification | content, art/audio, production throughput, platform and shipping become secondary | reject as outer lifecycle |
| nested model | normal production outside; Agent consequence/research inside | requires resisting process inflation | **retain** |

Deletion pressure makes the distinction operational:

- remove the outer lifecycle and the project cannot tell when a prototype has earned vertical-slice or production investment;
- remove the Agent lane and an LLM feature can reach production without proving bounded observation, legal action or meaningful consequence;
- promote the Agent research loop to the outer lifecycle and Game becomes research-rich but production-poor again;
- remove classification and current tools/architecture begin choosing the product by accident.

There is one product lifecycle, not two process authorities.

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

## 2. Classification before implementation

Genre names remain useful shorthand, but genre alone is not a sufficient production specification. Ordivon classifies a candidate game using two profiles.

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

### 2.2 Agent Participation Profile

Then describe why Agents exist in this game rather than assuming “Agent game” is one genre:

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

The **Form Profile determines the normal game-production burden**. The **Agent Participation Profile determines the extra cognition/authority/feedback burden**.

Do not reverse them.

## 3. The Agentic Consequence Loop

The smallest Agent-specific kernel that Ordivon research has repeatedly supported is:

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

## 4. Complete development lifecycle

The lifecycle below is the outer process for Ordivon games. It is intentionally recognizable as normal game development.

### G0 — Define

**Question:** What game are we making and why should it exist?

Produce a bounded Game Definition:

- player fantasy and target experience;
- Conventional Form Profile;
- Agent Participation Profile;
- target platform/input/session shape;
- one-sentence core loop;
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
- player ↔ Agent responsibility split;
- authoritative World boundaries;
- Agentic Consequence Loop where Agents materially participate;
- content grammar: what kinds of levels, encounters, characters, items or activities the game needs;
- production risks: art, animation, audio, networking, performance, model latency/cost.

Use competing designs and deletion tests. Avoid polishing content before the core loop has a reason to survive.

**Exit gate:** a small set of falsifiable design pillars and a prototype plan exist; every proposed permanent system can name the player/world failure it addresses.

### G2 — Kernel / graybox prototype

**Question:** Do the rules and Agent roles produce interesting decisions before expensive presentation exists?

Build the cheapest executable surface that can test:

- core loop;
- major rules and verbs;
- information boundaries;
- Agent decision/action consequence;
- failure/success;
- latency/cost budget;
- one representative content unit.

Prefer fixture/policy Agents first when they isolate game rules better than live Providers. Introduce a real model only when the hypothesis depends on cognition the fixture cannot represent.

**Studio consumption:** normally minimal. Placeholder geometry, icons, text, procedural sound and graybox media are sufficient unless presentation itself is the mechanic.

**Exit gate:** repeated play demonstrates a loop worth improving; Agent participation survives at least one cheaper-baseline comparison; major rules can be changed cheaply.

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

A vertical slice combines, in one bounded piece of real gameplay:

- near-final gameplay quality;
- representative Agent cognition and fallbacks;
- representative level/encounter/content quality;
- target-ish UI/UX;
- target art direction;
- representative animation/VFX;
- representative audio/music/voice where applicable;
- performance and loading expectations;
- production handoffs that can actually be repeated.

This is the first stage where broad Studio consumption is expected.

**Exit gate:** the team can answer both “is this worth producing?” and “can we repeatedly produce it?” A beautiful demo that depends on bespoke one-off labor fails the second question.

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

## 5. The Agent research lane inside the lifecycle

Agent-first development is a **method of iteration**, not a substitute lifecycle.

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

## 6. Game ↔ Studio production contract

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

## 7. Tool consumption follows the production need

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

## 8. Content and infrastructure use different admission standards

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

## 9. Falsifier cases: the model must survive games unlike Station Zero

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
normal game-development outer lifecycle
Conventional Form Profile
Agent Participation Profile
Agentic Consequence Loop
World/cognition/admission separation
content vs infrastructure distinction
Game ↔ Studio production ownership
production-need-driven tool selection
```

Station Zero-specific Plans, Turns, Commander forms, factions, tactical Zones, sealed enemy Plans and exact Host execution shape do not survive and therefore remain product-local.

## 10. Start packet for any future Ordivon game

Before implementation, answer these in one bounded record:

1. **Fantasy:** who is the player and what is the desired experience?
2. **Form:** what are the verbs/cadence, control topology, space/camera, session/progression and social form?
3. **Agent role:** which beings are Agents, what autonomy do they own, and why are they not cheaper scripts?
4. **Kernel:** what authoritative state, resources, information and consequences define play?
5. **Core loop:** what does the player repeatedly observe/decide/do and why is the repetition interesting?
6. **Content grammar:** what kinds of levels/characters/items/events/creations must be repeatedly produced?
7. **Production risk:** which art/audio/animation/network/model/runtime capabilities are likely to dominate cost or uncertainty?
8. **First falsifier:** what is the cheapest prototype that could prove the concept is not worth continuing?

Only after this packet should engine, provider and production-equipment choices become commitments.

## 11. Stage routing rule

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
