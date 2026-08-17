---
schema_version: 1
id: game.pre-g0-direction-search
title: Ordivon Game Pre-G0 Direction Search — DS0 Candidate Space, External Evidence and Cheapest Falsifiers
type: research
profile: research
lifecycle: active
source_role: canonical
visibility: public
owners:
  - ordivon-game
audience:
  - designer
  - researcher
  - builder
  - agent
updated: 2026-08-17
summary: Canonical start of Pre-G0 Game Direction Search after provisional Game Foundations v1. Opens the product GameForm space without selecting Station Zero, Casefile, Agent society, generative Persona or any existing implementation; introduces direction-search coordinates, external precedent evidence, a deliberately diverse candidate basis, Agent-necessity tests, production-burden profiles and cheapest falsifiers.
evidence_status: mixed
readiness: READY
applies_to:
  - ordivon-game
related:
  - game.foundations-research.r29
  - game.foundations-research.map
  - game.development-model
---
# Ordivon Game Pre-G0 Direction Search — DS0

## 0. Status and boundary

This document begins **Pre-G0 Game Direction Search**.

It is not:

```text
R30 Foundations
G0
Station Zero continuation
Casefile continuation
Agent-society selection
SillyTavern-like selection
an engine decision
an LLM feature roadmap
```

The input semantic stack is provisionally frozen `Game Foundations v1` from R29:

```text
F1 Entity / Reference
F2 State
F3 Relation
F4 Transition / Constraint
F5 Time
F6 Authority / Provenance
F7 Observation / Representation
F8 Evaluation / Motivation
F9 Action / Capability / Policy / Control
```

`DEVELOPMENT_MODEL.md` remains the sole authority for G0–G8. This search stays pre-G0 until one candidate is intentionally selected on evidence.

No candidate receives credit for existing Ordivon implementation maturity.

Strong boundary:

```text
TechnicalMaturity = feasibility evidence.
TechnicalMaturity != PlayerValue evidence.
```

---

# 1. What DS0 is trying to decide

The search question is not:

> What can Ordivon already build well?

It is:

> Which materially different GameForms contain a player-value hypothesis worth falsifying, and which of those actually need Agent cognition rather than cheaper authored/systemic mechanisms?

The correct order is:

```text
open form space
→ state player-value hypothesis
→ identify cheaper baseline
→ estimate production burden
→ design cheapest falsifier
→ run falsifiers
→ narrow on evidence
→ intentionally select one candidate
→ enter canonical G0
```

If no candidate dominates, retain finalists. Do not force a winner to satisfy process symmetry.

---

# 2. Direction Search Coordinates

The candidate universe is a cross-product, not a genre list.

DS0 uses the following product-search coordinates. They are **design coordinates**, not new Game Foundations:

```text
DirectionVector =
PlayerFantasy
× PlayerValueHypothesis
× CoreVerbs / Cadence
× ControlTopology
× WorldForm
× Space / Camera
× Time / Session
× InformationContract
× GoalStructure
× ContentSource
× SocialForm
× Progression / ConsequenceHorizon
× AgentParticipationProfile
× ExpressionDependency
```

## 2.1 Player fantasy

Examples:

```text
duelist / survivor / investigator / explorer
commander / strategist / ruler / diplomat
builder / engineer / optimizer / creator
caretaker / companion / social manipulator
storyteller / performer / director / observer
```

Fantasy is not flavor. It predicts which causal distinctions must become playable.

## 2.2 Player-value hypothesis

Use R2/R5/R6 as a broad lens, not one utility function.

Candidate value may come primarily from:

```text
Ability      — execution, timing, mastery, dexterity
Decision     — planning, trade-offs, inference, adaptation
World        — discovery, simulation, systems, emergence
Meaning      — identity, relationship, story, expression, interpretation
```

A candidate can combine these, but must name its irreducible center.

Deletion test:

> If AI novelty, technical spectacle and extrinsic reward disappear, what repeated behavior remains worth doing?

## 2.3 Core verbs / cadence

Coverage includes:

```text
real-time act / aim / dodge / move
turn-based inspect / choose / commit
plan / allocate / route / build / automate
explore / infer / hypothesize / test
negotiate / deceive / persuade / coordinate
create / curate / revise / perform
observe / intervene / delegate / wait
```

## 2.4 Control topology

```text
direct body/avatar
party/unit direct control
high-level orders
hierarchical delegation
world editing
conversation / speech-act control
meta-authorial control
observer + intervention
```

## 2.5 World form

```text
abstract state machine / board
authored spatial world
procedural spatial world
systemic economy/ecology
social graph / institution space
narrative/epistemic state space
creative artifact space
persistent mixed world
```

## 2.6 Space / camera

```text
none / text
abstract graph
2D grid/board
2D side/top-down
isometric / 2.5D
first/third-person 3D
multi-scale strategic map
```

This is a production predictor, not a value ranking.

## 2.7 Time / session

```text
reflex real time
continuous pausable
turn / phase
short encounter
run
mission
campaign
cross-session persistent world
asynchronous / idle
```

## 2.8 Information contract

```text
perfect information
telegraphed hidden future
partial observation
mystery/evidence reconstruction
private roles / deception
opponent-model uncertainty
soft language interpretation
```

## 2.9 Goal structure

```text
fixed win/loss
score / optimization
local objectives + open continuation
self-authored projects
survival / stewardship
relationship / identity trajectories
creative/expression goals
story completion / interpretation
```

## 2.10 Content source

```text
hand-authored
systemic recombination
procedural generation
player-created / UGC
human multiplayer emergence
generative model output
hybrid authored grammar + generation
```

## 2.11 Social form

```text
solo no social actors
solo with authored/systemic characters
solo with Agents
human co-op
human competitive/deceptive
mixed human + Agent
persistent population
```

## 2.12 Progression / consequence horizon

```text
none / score
within encounter
within run
meta progression
campaign state
character relationship/history
world/institutional persistence
player knowledge only
```

## 2.13 Agent Participation Profile

Use `DEVELOPMENT_MODEL.md` fields:

```text
role
autonomy depth
epistemic boundary
continuity
organization
cognition tier
```

Agent participation is orthogonal to genre/form.

## 2.14 Expression dependency

```text
low: abstract/text/icons are sufficient to test value
medium: readability/character identity matters
high: animation/audio/3D feel/presentation is part of the mechanic or fantasy
```

This tells us how cheap a valid falsifier can be.

---

# 3. Agent Necessity — stronger than Agent usefulness

A candidate must not receive Agent complexity because an Agent can be inserted.

Canonical DS0 test:

```text
AgentNecessary(candidate)
iff replacing Agent cognition with the cheapest adequate baseline
removes a player-relevant causal distinction central to the candidate's value hypothesis.
```

Baseline ladder, cheapest first where applicable:

```text
static authored content
→ deterministic rule / script
→ FSM / utility policy
→ procedural generator
→ search / planner
→ authored branching / lookup
→ human-controlled role
→ model cognition
→ persistent model Agent
```

Important separations:

```text
GenerationNeed != AgentNeed
DialogueNeed != AgentNeed
VariationNeed != AgentNeed
OpponentNeed != AgentNeed
SocialNeed != AgentNeed
```

A generative narrator may be justified while persistent autonomous Agents are not. Human players may supply the social intelligence a multiplayer game needs more cheaply and better than Agents.

---

# 4. Production burden model

Do not collapse production burden into one score. DS0 tracks six independent burdens:

```text
C = repeated content authoring burden
E = expression / art / animation / audio / UX burden
S = systemic simulation / balance / state-space burden
A = Agent/model latency, cognition, authority and fallback burden
O = online/network/live-operations/provider burden
V = validation/evaluation burden
```

Scale:

```text
0 none
1 low
2 moderate
3 substantial
4 high
5 dominant / product-defining
```

These are form-level prior estimates only. They are not cost quotations and do not use current Ordivon code maturity.

---

# 5. External product evidence — what materially different games prove can carry value

External references are used as **existence proofs and falsifiers**, not templates to clone.

## 5.1 Legible deterministic decision can be enough

**Into the Breach** explicitly centers telegraphed enemy attacks and finding a counter each turn. This is evidence that high strategic value can arise from stable, highly legible rules without rich opponent cognition.

Pressure on Ordivon:

```text
Do not use Agent unpredictability to manufacture depth
when a legible decision space can carry the game better.
```

## 5.2 Composition and automation can dominate content spectacle

**Factorio** identifies mining, logistics and production as the core, then lets simple components combine into increasingly large automated systems.

Pressure:

```text
System composition + self-created structure
can carry long-form value with almost no character Agent requirement.
```

## 5.3 Knowledge itself can be progression

**Outer Wilds** is an open-world mystery in a time loop where locations change over time and the player advances by learning the world's causal structure. **Return of the Obra Dinn** explicitly centers exploration and logical deduction.

Pressure:

```text
Persistent inventory / XP / Agent memory are not necessary for persistence value.
Player knowledge can be the durable state that transforms future play.
```

## 5.4 Combinatorial buildcraft can support repeated runs

**Slay the Spire** and **Slay the Spire 2** center deck construction, encounters, relics and procedural variation. The sequel entered Early Access in March 2026 while preserving that recognizable core.

Pressure:

```text
Repeated play can come from combinatorial decision structure,
not generated prose or simulated societies.
```

## 5.5 Action + authored narrative can survive high repetition

**Hades** combines fast action, repeated runs, changing builds and character-driven narrative, with repeated story events across many runs.

Pressure:

```text
High-replay narrative does not imply generative dialogue;
a carefully authored grammar can remain valuable under repeated systemic play.
```

## 5.6 Story generation does not require LLM inhabitants

**RimWorld** describes itself as a story generator. Its storyteller analyzes colony state and selects events to shape drama while colonists have needs, traits, skills and relationships.

Pressure:

```text
Emergent story can be generated by systemic state + event policy.
Agent language is only one possible realization mechanism.
```

## 5.7 Life and relationship simulation can be deeply systemic

**The Sims 4** centers creating/controlling people, personalities, aspirations, relationships and homes; Neighborhood Stories also allows off-screen households to undergo autonomous life and relationship changes. **Crusader Kings III** combines ruler fantasy, dynastic succession, relationships, influence, intrigue and large event spaces.

Pressure:

```text
Relationship / identity / social drama are not evidence by themselves
that free-form model cognition is necessary.
```

## 5.8 Human players are a powerful social-AI baseline

**Among Us** centers teamwork and betrayal among human players with hidden roles.

Pressure:

```text
For social deduction/deception, the baseline is not only scripted NPCs.
Human social intelligence may be the correct content source.
```

## 5.9 Creative value can shift content production toward tools and UGC

**Minecraft** exposes survival and creative modes; in creative mode the player receives unrestricted building materials and construction freedom, while multiplayer/servers let players share worlds.

Pressure:

```text
A product can invest in possibility grammar + tools
instead of authoring every finished content unit.
```

## 5.10 Open generative interaction creates governance work immediately

**AI Dungeon** lets the player type arbitrary Do/Say/Story actions and directs the AI to continue the story. Its own help materials foreground Retry/Edit, Memory, Story Cards and context controls for keeping output useful and coherent.

Pressure:

```text
Open intent creates value potential,
but also moves product burden into coherence, memory, revision and authority boundaries.
```

## 5.11 Structured generative constraints may be more game-like than maximal freedom

**Hidden Door** combines open roleplay with light RPG stats/dice and deliberate in-world limits. External hands-on coverage of its 2025 early-access form observed that the system rejects world-breaking actions, preserving challenge/fictional constraints, while also reporting noticeable generation latency and some disjointed storytelling.

Pressure:

```text
OpenIntentSpace + StructuredConsequenceSpace
is a stronger candidate pattern than unlimited wish fulfillment.
```

## 5.12 Natural language can itself become the core mechanic — but AI novelty is not sufficient proof

**Suck Up!** makes spoken deception the central verb: the player talks to AI characters and tries to gain trust/access. As observed on Steam in August 2026, the product still has only mixed overall user reviews, and its March 2026 developer update reported service downtime caused by an AI-provider integration break.

Pressure:

```text
Language-as-action can create a genuinely new interaction surface.
But Agent novelty does not guarantee broad Player Value,
and provider dependence becomes product operations burden.
```

## 5.13 Constraint-based AI co-creation is a distinct lane

The 2025 research game **1001 Nights** uses an AI character with preferences as an active constraint: players strategically tell stories to influence the character and obtain useful outcomes.

Pressure:

```text
AI can matter most when it is part of the rule/opposition structure,
not merely a content faucet.
```

## 5.14 Motivation research is useful as a probe, not an objective function

Self-Determination Theory game research links perceived autonomy, competence and relatedness with enjoyment/engagement. A 2024 HCI critique warns that SDT is often applied shallowly in game research.

DS0 usage:

```text
competence / autonomy / relatedness = useful player-value probes
!= complete theory of fun
!= candidate ranking scalar
```

---

# 6. Candidate basis — deliberately diverse, not exhaustive

The following 16 candidates are **basis vectors** selected to span materially different portions of the DirectionVector space. They are not finalists and are not ranked by current implementation maturity.

Burden notation is `C/E/S/A/O/V`.

| ID | Candidate form | Core fantasy / repeated behavior | Central Player Value hypothesis | Claimed Agent need | Burden prior |
| --- | --- | --- | --- | --- | --- |
| D01 | Precision Action Duel | duelist/hunter; read, move, time, punish | mastery of timing + opponent reading remains satisfying under repeated execution | optional/conditional adaptive adversary | `2/4/2/2-4/1/3` |
| D02 | Legible Tactical Puzzle | commander; inspect, predict, reposition, commit | dense consequential decisions from readable future threats | none by default | `3/2/2/0/0/2` |
| D03 | Epistemic Mystery / Knowledge Exploration | investigator/explorer; observe, infer, revisit | knowledge changes reachable action; solving causal structure is progression | none by default | `5/3/2/0-1/0/4` |
| D04 | Combinatorial Roguelike Buildcraft | survivor/deck architect; choose, combine, adapt | synergies + risk under changing constraints create repeatable decision depth | none by default | `4/2/3/0/0/4` |
| D05 | Automation / Logistics Engineering | engineer; route, automate, scale, debug | self-authored systems produce competence, expression and optimization depth | none by default | `2/2/5/0-1/0/4` |
| D06 | Colony Story-Generator Simulation | steward; allocate, intervene, recover, interpret | interacting needs/resources/events generate memorable causal stories | optional/conditional at selected Subject tiers | `3/2/5/1-3/0/5` |
| D07 | Life / Relationship Simulation | caretaker/director; influence lives/relationships | social trajectories + self-authored identity stories create attachment and curiosity | optional/conditional | `4/3/4/1-4/0/5` |
| D08 | Grand Strategy / Political Drama | ruler/dynasty; bargain, scheme, allocate, inherit | long-horizon strategic consequences become personal through characters/relations | optional/conditional | `5/3/5/1-3/0/5` |
| D09 | Authored Party RPG / Companion Drama | adventurer; explore, fight, choose, relate | authored world + companion reaction makes decisions emotionally consequential | optional/conditional | `5/5/3/1-3/0/5` |
| D10 | Human Social Deduction / Deception | detective/impostor; infer, lie, coordinate | theory-of-mind against humans creates unique social tension | no Agent required; humans are baseline | `2/2/2/0/4/3` |
| D11 | Creative Construction Sandbox / UGC | builder/creator; make, iterate, share | expressive authorship and tool mastery are intrinsically valuable | none by default; optional co-creator | `2/3/4/0-2/1-4/4` |
| D12 | Generative Open-Intent RPG | protagonist/director; say/do nearly anything | natural-language intent dramatically expands expressive/narrative agency | generation likely needed; persistent Agents not automatically needed | `1/1/2/5/4/5` |
| D13 | Conversational Social Infiltration | spy/vampire/diplomat; persuade, deceive, probe | language strategy works because interlocutors interpret context and beliefs dynamically | strong Agent hypothesis | `2/3/2/5/4/4` |
| D14 | Constraint-Based Co-Creation Game | storyteller/performer; create under a responsive critic/opponent | creativity becomes gameable when another mind has learnable preferences/constraints | strong but falsifiable Agent hypothesis | `2/2/1/4/3/4` |
| D15 | Incremental / Delegation Optimizer | allocator/automator; invest, unlock, delegate | compounding system understanding transforms sparse decisions into large effects | none by default | `2/1/3/0/0/3` |
| D16 | Persistent Multi-Agent Society Sandbox | observer/ruler/participant; influence a living society | autonomous subjects create histories/institutions the player can understand and steer | high claimed need, highest proof burden | `3/2/5/5/5/5` |

---

# 7. Candidate cheapest falsifiers

The falsifier must target the **value hypothesis**, not merely prove execution.

## D01 — Precision Action Duel

```text
Build one tiny 2D arena and one opponent.
Compare fixed telegraphed policy vs adaptive policy/model.
Reject Agent treatment if adaptation does not create better anticipation/counterplay,
or latency/randomness harms mastery attribution.
```

Do not start with 3D animation production.

## D02 — Legible Tactical Puzzle

```text
Use an abstract 6×6 board, 3 player units, visible enemy intents and 8 hand-built states.
Reject if decisions converge to obvious moves or repeated turns feel like bookkeeping.
```

No model call is permitted in the first treatment; Agent complexity would contaminate the proof.

## D03 — Epistemic Mystery

```text
Create one 20–30 minute evidence graph with one hidden causal history.
Player can inspect evidence, form hypotheses and commit deductions.
Reject if solution is checklist accumulation rather than model revision,
or if uncertainty is arbitrary rather than inferable.
```

## D04 — Roguelike Buildcraft

```text
CLI/card prototype: ~30 effects, 5 encounter archetypes, short run.
Reject if one dominant build appears quickly,
choices are local arithmetic rather than trajectory shaping,
or procedural variation does not change strategy.
```

## D05 — Automation / Logistics

```text
Grid/text simulator with ~6 resources, ~8 machines and throughput objectives.
Reject if scaling is repetitive placement with no topology/constraint insight,
or one layout solves every objective.
```

## D06 — Colony Story Generator

```text
Text-first simulation with 4–6 inhabitants, needs, skills, resources and event director.
Use deterministic/utility policies first.
Reject if player interventions do not produce interpretable causal stories or meaningful trade-offs.
Only then test whether selected Agent cognition adds value.
```

## D07 — Life / Relationship Simulation

```text
Four characters, small household, multidimensional relationship state and 6 recurring activities.
Compare structured policy dialogue/behavior vs model-supported character choices.
Reject Agent layer if remembered relationship arcs and player attachment are not materially improved.
```

## D08 — Grand Strategy / Political Drama

```text
Abstract graph of ~6 houses/factions, succession, obligations, resources and private interests.
No map art.
Reject if diplomacy/scheming collapse into one scalar optimization or relations have little strategic consequence.
```

## D09 — Authored Party RPG

```text
One companion, three authored dilemmas, one short combat/systemic challenge.
Compare authored branching companion reaction with model-mediated reaction over the same authoritative facts.
Reject Agent layer if it adds prose variation without stronger attachment, surprise or causal consequence.
```

## D10 — Human Social Deduction

```text
Run the rules as a paper/Discord/web-room game with 4–6 humans and minimal UI.
Reject if hidden-role inference, deception and coordination are not compelling before graphics/content expansion.
```

Agent opponents are a later accessibility/solo hypothesis, not the initial product thesis.

## D11 — Creative Construction Sandbox

```text
Tiny editor with ~12 composable pieces, constraints and share/export.
No extrinsic progression.
Reject if players do not voluntarily iterate on self-authored artifacts or cannot distinguish personal expression from mere arrangement busywork.
```

## D12 — Generative Open-Intent RPG

```text
Text-only world with hard authoritative state, one local objective and open natural-language input.
Compare unrestricted continuation vs OpenIntent + StructuredConsequence admission.
Reject if free-form action does not create valued agency after novelty fades,
or coherence/authority correction dominates play.
```

## D13 — Conversational Social Infiltration

```text
Three characters, one building/social graph, one infiltration objective.
Player persuades/probes by text before voice/3D.
Compare model interlocutors with strong authored dialogue/policy baseline.
Reject Agent hypothesis if distinct language strategies do not change trust/information/access in learnable ways.
```

## D14 — Constraint-Based Co-Creation

```text
One AI-responsive evaluator/character with hidden but learnable preferences.
Player creates a short artifact/story under constraints to influence an outcome.
Compare Agent opponent/critic with static scoring rubric and generator-as-tool.
Reject if adaptation to the other mind is not itself enjoyable.
```

## D15 — Incremental / Delegation Optimizer

```text
Spreadsheet/CLI state with 5–8 compounding mechanisms and sparse intervention.
Reject if optimal play is passive waiting, rote upgrades or one dominant investment order without meaningful re-planning.
```

## D16 — Persistent Multi-Agent Society

```text
Do NOT start with many live model Agents.
Build a text/graph micro-society with deterministic policies, partial observation, relationships/institutions and player interventions.
Reject the form if the player cannot infer or steer society-level causal structure.
Only then ablate selected high-level Subjects between policy vs model cognition.
```

This prevents the most expensive candidate from consuming the search before its basic player loop is proven.

---

# 8. First elimination laws

A candidate is eliminated or demoted when any of the following occurs.

## 8.1 Value deletion failure

```text
remove AI novelty / rewards / spectacle
→ core repeated behavior is no longer worth doing
```

## 8.2 Cheaper-baseline parity

```text
script/policy/authored/human baseline
≈ intended experience
```

Then delete or shrink the Agent layer.

## 8.3 Causal-access failure

If the player cannot infer which distinctions matter or how action affects futures, internal sophistication is not playable.

```text
ComplexWorld without PlayerCausalAccess
= production burden, not depth.
```

## 8.4 Content exhaustion failure

If the candidate requires continuous bespoke content to remain interesting and the content grammar does not scale, production burden may dominate value.

## 8.5 Cadence mismatch

If model latency, human coordination or heavy simulation breaks the intended action/decision cadence, that realization fails even if the abstract form remains valid.

## 8.6 Evaluation impossibility

If we cannot distinguish a better treatment from a merely different one at reasonable cost, the candidate needs a sharper hypothesis before further build investment.

## 8.7 Promotion-debt failure

Generative candidates fail when generated content repeatedly creates continuity/authority obligations whose repair cost exceeds the value of generation.

---

# 9. Search order — information gain, not winner ranking

The best early sequence is not “build the most promising product”. It is “buy the most information per unit cost”.

## Wave A — cheap zero-Agent value baselines

```text
D02 tactical puzzle
D03 epistemic mystery
D04 roguelike buildcraft
D05 automation/logistics
D15 incremental optimizer
```

Purpose:

```text
recalibrate what strong Player Value looks like
without any Agent novelty contamination.
```

## Wave B — direct Agent-necessity contrasts

```text
D01 action adversary
D07 relationship simulation
D09 companion RPG
D12 open-intent RPG
D13 conversational infiltration
D14 constraint co-creation
```

Purpose:

```text
run matched cheaper-baseline ablations where Agent value is actually in question.
```

## Wave C — social and broad-system forms

```text
D06 colony story generator
D08 grand strategy/political drama
D10 human social deduction
D11 creative sandbox/UGC
```

Purpose:

```text
pressure social/systemic/creative value without defaulting to model Agents.
```

## Wave D — expensive synthesis candidate

```text
D16 persistent multi-Agent society
```

D16 is tested last, not because it is weak, but because almost every local value claim it contains can be falsified more cheaply in narrower candidates first.

Strong rule:

```text
Breadth does not earn priority.
The broadest candidate inherits the proof debts of its narrower components.
```

---

# 10. What would justify intentional G0 selection later

Pre-G0 should not select on one exciting demo.

A candidate becomes eligible for intentional G0 only when evidence supports all of:

```text
1. Player-value survival:
   the core behavior remains worth repeating after novelty removal.

2. Causal legibility:
   players can form a useful model of important consequences.

3. Distinctive value mechanism:
   we can say what this form does unusually well without naming implementation tech.

4. Agent necessity, if claimed:
   at least one cheaper baseline materially degrades the intended experience.

5. Burden plausibility:
   content/expression/simulation/Agent/ops/evaluation cost has a credible production path.

6. Cheapest-falsifier survival:
   the concept survived experiments capable of killing it cheaply.

7. Definition convergence:
   two independent readers can describe roughly the same game from the candidate definition.
```

If multiple candidates satisfy this, preserve a finalist portfolio and run discriminating tests. Do not select by aesthetics or code maturity alone.

---

# 11. FoundationReopenCondition audit

DS0 introduces many new **product-search dimensions**, but none currently satisfies R29's Foundation Admission Test.

Current result:

```text
New player-relevant counterfactual not representable through F1–F9: none found
Systematic contradiction among F1–F9 under current evidence: none found
Derived view needing new authority/state semantics: none found
New participant-coupling distinction missing from F7/F9: none found
Generative provenance/identity/state failure beyond F6 + existing views: none found
```

Examples:

```text
ContentSource
ExpressionDependency
SessionShape
Camera
Genre cluster
Agent count
Human multiplayer
```

are product/production dimensions, not new semantic foundation coordinates.

Therefore:

```text
FoundationReopenCondition = NOT TRIGGERED
Game Foundations v1 remains frozen.
```

---

# 12. DS0 strongest conclusions

```text
1. GameForm space must be opened as a multidimensional product space, not a genre menu.
2. A deliberately strong zero-Agent portfolio is mandatory; otherwise Agent novelty contaminates selection.
3. Agent necessity is proven only by cheaper-baseline failure.
4. Generation necessity and Agent necessity are separate claims.
5. Human players are a serious baseline for social intelligence.
6. Knowledge, creation, systems, timing and combinatorial strategy can each carry value without rich Subjects.
7. Social/relationship/world richness does not automatically require LLM cognition.
8. Natural language becomes especially interesting when it is a consequential verb, not merely dialogue flavor.
9. Structured generative consequence is a stronger game hypothesis than unlimited generative freedom.
10. Production burden must remain vector-valued; low content cost can hide high coherence/ops/evaluation cost.
11. The broad persistent-Agent society form should inherit proof from narrower falsifiers rather than lead the programme.
12. No FoundationReopenCondition has appeared.
```

---

# 13. Exact next frontier

DS0 opens the candidate space. It does **not** narrow it yet.

Next work:

```text
Pre-G0 DS1 — Cheap Falsifier Battery
```

Primary objective:

```text
build/run the smallest comparable treatments for Wave A and the highest-information Wave B contrasts;
collect evidence about actual decision density, causal legibility, repeat desire and Agent baseline delta;
eliminate aggressively before any expensive vertical prototype.
```

The first DS1 experiment should be chosen for information gain across multiple candidates, not because it resembles the current repository implementation.

---

# 14. External evidence anchors used in DS0

Accessed 2026-08-17 unless noted.

- Subset Games — Into the Breach: https://www.subsetgames.com/itb.html
- Factorio official game/content pages: https://www.factorio.com/ and https://www.factorio.com/game/content
- RimWorld official site: https://rimworldgame.com/
- Outer Wilds Steam product page: https://store.steampowered.com/app/753640/Outer__Wilds/
- Return of the Obra Dinn Steam product page: https://store.steampowered.com/app/653530/Return_of_the_Obra_Dinn/
- Mega Crit — Slay the Spire / Slay the Spire 2 press materials: https://www.megacrit.com/press-kits/slay-the-spire/ and https://www.megacrit.com/press-kits/slay-the-spire-2/
- Supergiant Games — Hades FAQ: https://www.supergiantgames.com/blog/hades-faq/
- Electronic Arts — The Sims 4 official pages / Neighborhood Stories: https://www.ea.com/games/the-sims/the-sims-4
- Paradox Interactive — Crusader Kings III official product/press pages: https://www.paradoxinteractive.com/games/crusader-kings-iii/
- Innersloth — Among Us: https://www.innersloth.com/games/among-us/
- Minecraft official pages: https://www.minecraft.net/en-us/about-minecraft
- AI Dungeon official/help pages: https://www.aidungeon.io/ and https://help.aidungeon.com/
- Hidden Door product/company materials and 2025 early-access hands-on coverage.
- Suck Up! Steam product page and March 26, 2026 server incident note: https://store.steampowered.com/app/2726370/Suck_Up/
- Fu et al. (2025), “I Like Your Story!” / 1001 Nights, arXiv:2503.09102.
- Ryan, Rigby & Przybylski (2006), “The Motivational Pull of Video Games”, DOI 10.1007/s11031-006-9051-8.
- Przybylski, Rigby & Ryan (2010), “A Motivational Model of Video Game Engagement”, DOI 10.1037/a0019440.
- Tyack & Mekler (2024), “Self-Determination Theory and HCI Games Research: Unfulfilled Promises and Unquestioned Paradigms”, arXiv:2405.12639.
