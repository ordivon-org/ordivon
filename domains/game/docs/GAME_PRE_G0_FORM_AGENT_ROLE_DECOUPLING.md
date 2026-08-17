---
schema_version: 1
id: game.pre-g0-form-agent-role-decoupling
title: Ordivon Game Pre-G0 — GameForm × AgentRole Decoupling
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
summary: Reframes Pre-G0 so game-form selection is independent of runtime-Agent affinity. Establishes a broad traditional GameForm atlas, separates Production Agents from runtime system intelligence and world Agents, and treats Agent leverage as an orthogonal production/runtime decision rather than a genre prior.
evidence_status: mixed
readiness: READY
applies_to:
  - ordivon-game
related:
  - game.pre-g0-direction-search
  - game.pre-g0-ds1-cheap-falsifiers
  - game.development-model
---
# Ordivon Game Pre-G0 — GameForm × AgentRole Decoupling

## 0. Why this correction exists

Pre-G0 DS0 made a useful move away from Station Zero implementation momentum, but it still embedded `AgentParticipationProfile` directly inside `DirectionVector`. DS1 then naturally favored candidates whose value claims were easy to formalize and whose Agent-necessity contrast was cheap to simulate.

That creates two distinct biases:

```text
AgentAffinityBias:
forms that obviously admit NPC/LLM/Agent participation appear more relevant to Ordivon.

MeasurabilityBias:
forms with cheap structural metrics receive evidence earlier than embodied,
aesthetic, social, expressive or game-feel-heavy forms.
```

Neither bias is a legitimate product-selection rule.

The correction is therefore:

```text
Question A: What game is worth making?
Question B: How can Agents expand the production frontier for that game?
Question C: Does any runtime role actually require Agent cognition?
```

These questions are related, but they are not the same question and must not be collapsed.

Strong laws:

```text
AgentBuiltGame != AgentGame
ProductionAgentNeed != RuntimeAgentNeed
RuntimeGenerationNeed != WorldAgentNeed
WorldAgentNeed != ModelNeed
AgentUsefulness != AgentNecessity
```

A completely traditional platformer, racing game, tactics game, puzzle game or RPG built with extremely heavy Agent assistance is a first-class Ordivon Game outcome.

---

# 1. New product-search factorization

The old search mixed conventional form and runtime Agent participation too early.

The corrected factorization is:

```text
OrdivonGameCandidate =
GameFormProfile
× ProductionAgentProfile
× RuntimeAgentProfile
```

Only `GameFormProfile` is required to define what the player is playing.

Both Agent profiles may be empty.

## 1.1 GameFormProfile — player/product truth

```text
GameFormProfile =
PlayerFantasy
× CentralPlayerValue
× CoreVerbs / Cadence
× ControlTopology
× WorldForm
× Space / Camera
× SessionShape
× InformationContract
× GoalStructure
× Progression / ConsequenceHorizon
× ContentGrammar
× SocialForm
× ExpressionDependency
```

Rule:

```text
Do not reward or penalize a GameForm because it is easy or difficult to imagine an LLM inside it.
```

## 1.2 ProductionAgentProfile — how the game is made

Production Agents exist outside the authoritative player-facing game loop. They may research, design, code, build prototypes, operate editors, create draft assets, simulate players, test, balance, localize, coordinate production or triage release evidence.

A production Agent can be essential to Ordivon's ability to make a game while being completely invisible to the player.

## 1.3 RuntimeAgentProfile — intelligence inside the shipped experience

Runtime intelligence is admitted only after the game form has a player-value hypothesis that can name the missing causal distinction.

Runtime roles divide again into:

```text
Game-System Intelligence
vs
World / Subject Intelligence
```

A pacing director, semantic adjudicator or procedural generator need not be a diegetic character. A companion, opponent or faction is a World participant. Those are different authority and feedback problems.

---

# 2. Broad GameForm atlas — coverage before selection

This atlas is a **coverage basis**, not a ranking and not an ontology of all games. Steam's current official Tag Wizard separates genre/subgenre from visual perspective, theme, features and player activities; that is useful evidence that camera, mood, multiplayer, procedural generation and AI should not be mistaken for one genre axis.

The atlas intentionally restores traditional forms that DS0 underrepresented.

| ID | Form family | Repeated player activity / value center | Representative conventional neighborhoods | Runtime Agent required by default? |
| --- | --- | --- | --- | --- |
| F01 | Precision movement / platforming | move, jump, route, recover; sensorimotor mastery | precision platformer, 2D/3D platformer, runner | no |
| F02 | Combat action / aiming / brawling | read, aim, dodge, attack, punish; execution + opponent reading | FPS/TPS, character action, beat 'em up, hack-and-slash, bullet hell | no |
| F03 | Fighting / duel mind-game | space, timing, conditioning, punish; embodied adversarial mastery | 2D/3D fighting, arena duel | no; human/script baseline strong |
| F04 | Racing / vehicle handling | line choice, braking, acceleration, control; embodied optimization | racing, combat racing, vehicle sim | no |
| F05 | Sports / physical competition | execute sport-specific verbs under opposition | football, basketball, golf, tennis, skating | no |
| F06 | Rhythm / musical timing / performance | perceive pattern, time input, sustain flow | rhythm, music-based play, typing/performance | no |
| F07 | Puzzle / spatial / logic | transform state, infer rule, search solution | Sokoban, match-3, logic, word, physics puzzle | no |
| F08 | Investigation / epistemic mystery | observe, hypothesize, test, reconstruct | investigation, detective, hidden-object, mystery | no |
| F09 | Exploration / traversal / adventure | navigate, discover, unlock, interpret place | exploration, point-and-click, metroidvania, open-world adventure | no |
| F10 | Tactical conflict | inspect local state, predict, position, commit | turn-based tactics, real-time tactics, tactical RPG | no |
| F11 | Strategic / macro conflict | plan, allocate, expand, negotiate, adapt over long horizon | RTS, 4X, grand strategy, wargame, tower defense | no |
| F12 | Card / deck / tabletop combinatorics | draft, compose, sequence, bluff, adapt | card battler, TCG, board game, chess-like | no |
| F13 | Build / automation / logistics / management | construct, route, scale, diagnose, optimize | automation, base/city building, management, programming | no |
| F14 | Simulation / stewardship / life | observe systems/subjects, intervene, care, interpret emergence | life sim, colony sim, farming, god sim, medical/vehicle/space sim | no |
| F15 | RPG / character progression / party | inhabit role, build character, quest, choose, fight, relate | CRPG, JRPG, action RPG, party RPG, dungeon crawler | no |
| F16 | Survival / crafting / scarcity | acquire, craft, risk, shelter, explore under pressure | survival, open-world survival craft, extraction-like loops | no |
| F17 | Narrative / interactive fiction | choose, interpret, converse, witness authored consequence | interactive fiction, visual novel, choice adventure | no |
| F18 | Creative construction / sandbox / UGC | make, revise, combine, share, express | sandbox, construction, level editor, creative world | no |
| F19 | Social / multiplayer coordination / deception | cooperate, compete, signal, deceive, negotiate | party, social deduction, co-op, competitive multiplayer | no; humans are strong baseline |
| F20 | Incremental / idle / delegation optimization | invest, wait, automate, reprioritize, compound | clicker, idle, time-management | no |
| F21 | Systemic immersive problem-solving | observe affordances, improvise, combine systems, exploit environment | immersive sim, stealth-systemic, heist/problem sandbox | no |
| F22 | Experimental / novel interaction | discover a new verb/interface/rule and build mastery around it | experimental, mixed-medium, unusual input/semantic play | no |

## 2.1 Cross-cutting attributes are not base-form exclusions

The following may transform any row without becoming the whole GameForm:

```text
2D / 2.5D / 3D / VR
first-person / third-person / side / top-down / abstract
horror / comedy / fantasy / sci-fi / historical / cozy
solo / local co-op / online PvP / MMO
procedural generation / hand-authored / UGC / generative model
finite campaign / run-based / persistent world
high-fidelity audiovisual expression / minimalist abstraction
```

`AI` is also cross-cutting. Steam itself lists AI as a feature tag rather than a top-level genre; Ordivon should preserve the same conceptual separation.

## 2.2 Coverage rule

Before narrowing GameForm space, any candidate set must demonstrate coverage across materially different value centers:

```text
embodied mastery
strategic/decision mastery
knowledge/inference
system construction/optimization
exploration/discovery
role/progression
story/meaning
creation/expression
social interaction
```

A candidate portfolio concentrated in only the forms easiest to simulate is invalid even if its metrics are excellent.

---

# 3. Agent role atlas

`Agent` is not one game role. Ordivon needs a role taxonomy by **locus**.

## 3.1 Layer P — Production Agents

These roles help make/test/operate the game. They are not game characters and do not require runtime model calls.

| ID | Production role | Primary leverage | Typical output / action | Human evidence still required? |
| --- | --- | --- | --- | --- |
| P01 | Research / evidence scout | search breadth, precedent discovery, failure retrieval | evidence set, comparison, source map | yes for judgment |
| P02 | Design-space expander | mechanic/level/economy alternative generation | competing hypotheses, variants | yes |
| P03 | Prototype builder | lowers idea→playable latency | graybox, toy, disposable implementation | yes |
| P04 | Gameplay / software engineer | code throughput, debugging, refactor | systems, tooling, integration | engineering validation |
| P05 | Content / asset authoring assistant | content and expression throughput | draft levels, dialogue, images, audio, animation, data | craft/rights review |
| P06 | Editor / tool operator | converts intent into owner-native project state | scene edits, imports, configuration, builds | mechanical + craft review |
| P07 | Synthetic player / simulation population | trajectory volume and state-space coverage | play traces, scenario distributions | yes for Player Value |
| P08 | Falsifier / QA / exploit hunter | finds bugs, degenerate strategies, softlocks | counterexamples, repro cases | human triage often |
| P09 | Balance / analytics analyst | detects dominance, pacing/economy anomalies | comparisons, sensitivity, metrics | yes for intended experience |
| P10 | Producer / production orchestrator | dependency and iteration coordination | work packets, routing, acceptance checks | strategic ownership |
| P11 | Localization / accessibility assistant | breadth and consistency | translations, alt text, accessibility checks/drafts | native/accessibility review |
| P12 | Release triage / support analyst | compresses operational evidence | issue clusters, regression hypotheses, patch candidates | release owner decides |

Current external evidence strongly supports this layer: Unity's 2026 AI tools expose an editor-integrated project-aware Agent, generators, an AI gateway and MCP control; its tooling explicitly covers project edits and project-ready assets. Unity ML-Agents explicitly lists automated testing and pre-release design evaluation as uses. EA/AIIDE research has shown automated Agents can explore thousands of game simulations and expose imbalance/inconsequential choices; later work extends Agent-based testing to human-like play styles and AAA testing coverage.

## 3.2 Layer S — Runtime Game-System Intelligence

These roles affect the shipped experience without necessarily existing as a diegetic subject.

| ID | System role | What it controls | Cheapest baseline before model cognition |
| --- | --- | --- | --- |
| S01 | Content / encounter generator | maps, quests, encounters, dialogue fragments, variants | authored grammar / PCG / search |
| S02 | Director / pacing controller | event timing, pressure, difficulty, dramatic pacing | rules / utility policy |
| S03 | Semantic interpreter / adjudicator | maps open input to bounded game actions/outcomes | parser / templates / authored intent set |
| S04 | Player model / personalization | inferred preference/skill and adaptation | explicit settings / telemetry rules |
| S05 | Matchmaking / meta controller | pairing, queues, difficulty bands, event allocation | ranking/rules/optimization |
| S06 | World-process controller | non-character ecology/economy/faction-scale dynamics | simulation rules / stochastic process |
| S07 | Tutor / hint / accessibility assistant | explanation, hint selection, guidance | authored hints / state machine |

Important:

```text
SystemIntelligence != WorldAgent
```

A procedural dungeon generator does not become an NPC merely because a model generated the dungeon.

## 3.3 Layer W — World / Subject Agents

These roles are participants the player can model as acting subjects or delegates.

| ID | World role | Central interaction | Typical proof burden |
| --- | --- | --- | --- |
| W01 | Opponent / adversary | anticipate, counter, outplay | adaptation must improve play over scripts/humans/bots |
| W02 | Teammate / subordinate | coordinate, delegate, recover from mismatch | coordination value beyond command macros |
| W03 | Persistent companion | relate, remember, act with continuity | attachment/continuity beyond authored branching |
| W04 | NPC / inhabitant | social/world interaction | behavior must alter reachable/meaningful futures |
| W05 | Faction / institution | negotiate, compete, form long-horizon policy | institution-level behavior beyond simulation policy |
| W06 | Economic actor | trade, bargain, produce, consume strategically | strategic adaptation beyond market rules |
| W07 | Narrator / game master | interpret and reshape presentation/events | value beyond authored/procedural director |
| W08 | Co-creator / critic | create against/with learnable preferences | responsiveness must itself be playable |
| W09 | Player proxy / delegate | acts on player's behalf under bounded authority | delegation must create useful leverage without erasing play |
| W10 | Persistent society / population | many interacting subjects create histories/institutions | highest proof and validation burden |

No row implies LLM use. For every row:

```text
script / FSM / utility policy / planner / authored branching / human role
```

remains a mandatory baseline where applicable.

---

# 4. AgentRoleVector — what must be recorded when an Agent is proposed

A role name alone is too weak.

```text
AgentRoleVector =
Locus
× Function
× Authority
× Visibility
× TemporalScope
× StateAccess
× Persistence
× CheapestBaseline
× Criticality
```

Where:

```text
Locus        = production | runtime-system | world-subject
Authority    = advise | draft | propose | act | commit-with-admission
Visibility   = invisible | indirect | directly player-facing
Temporal     = offline | build-time | session | cross-session | persistent
StateAccess  = public | bounded-local | privileged-tooling | authoritative-read | write-via-admission
Persistence  = none | task | session | cross-session identity/world history
Criticality  = optional leverage | production-enabling | runtime-enhancing | core mechanic
```

This prevents the phrase “use an Agent” from silently bundling product architecture, autonomy and authority.

---

# 5. Production frontier model

Agent production leverage must not be assumed merely because a model can perform a task.

For each GameForm, record a conventional baseline burden first:

```text
B0(GameForm) =
design/search
+ implementation/integration
+ repeated content
+ expression
+ systems/balance
+ online/ops
+ validation
```

Then measure Agent effects separately:

```text
AgentProductionDelta(role) =
work avoided
+ search space newly reachable
+ iteration latency reduced
- review/rework cost
- provenance/rights cost
- coordination/tooling cost
- model/compute cost
```

Do not simply replace `B0` with a lower number.

Key distinction:

```text
Production-enabling Agent:
without the Agent, this GameForm may exceed Ordivon's practical resource frontier.

Runtime-essential Agent:
without the Agent, the player's core form of play collapses or materially changes.
```

Those are independent claims.

A high-expression traditional action game may have:

```text
ProductionAgentProfile = heavy
RuntimeAgentProfile = none
```

and still be more strategically attractive to Ordivon than an Agent-native social game.

---

# 6. Runtime Agent admission test

Runtime Agent candidacy begins only after a GameForm has a central Player Value mechanism.

Canonical test remains counterfactual:

```text
RuntimeAgentNecessary(candidate, role)
iff replacing that role with the cheapest adequate baseline
removes a player-relevant causal distinction central to the GameForm's value.
```

But the order changes:

```text
GameForm value hypothesis
→ cheapest non-Agent realization
→ player-facing causal proof
→ identify missing distinction
→ admit the smallest runtime intelligence role
→ compare baseline vs Agent
```

Not:

```text
we have Agents
→ choose Agent-friendly genre
→ design gameplay around them
```

---

# 7. Reinterpretation of DS0 / DS1

DS0 and DS1 remain useful evidence, but their authority narrows.

## 7.1 What survives

```text
Player Value must be stated without AI novelty.
Cheaper baselines are mandatory.
Structural falsifiers can kill weak realizations cheaply.
SimulationSurvival != PlayerValueProof.
Poor realization != dead form.
ResponsiveOtherNeed != LLMNeed.
Information scarcity can create epistemic agency.
```

## 7.2 What no longer survives as a search-order rule

The following DS0/DS1 implication is retired:

```text
structural survivors
→ automatically receive next playable budget before untested forms
```

Reason:

```text
MeasurabilityBias + AgentAffinityBias
```

D03/D04/D05/D14 are now **local mechanism evidence**, not privileged finalists.

D02/D15 micro-realization failures also do not demote entire traditional families in the broadened atlas.

## 7.3 Existing D-series mapping is partial

The old D01–D16 basis covers some regions of F01–F22, but not enough to claim broad GameForm coverage. In particular, precision platforming, racing, sports, rhythm, fighting, broad shooter/action, systemic immersive problem-solving and several conventional adventure/RPG realizations were underrepresented.

Therefore the next search does not begin by continuing D-number elimination.

---

# 8. New Pre-G0 search sequence

## Pass A — GameForm coverage without Agent preference

Construct a deliberately diverse form portfolio across F01–F22.

For each candidate ask only:

```text
What does the player repeatedly do?
What kind of value could become deep/replayable?
What must be perceptually and causally legible?
What is the cheapest valid playable proof?
What conventional production burden dominates?
```

Runtime Agent is set to `none` unless the form definition literally collapses without one.

## Pass B — Production leverage map

For each surviving/high-information form:

```text
Which P-layer roles materially reduce iteration cost?
Which previously unaffordable content/expression/testing burdens become reachable?
Which Agent outputs create review/rework/provenance debt instead of leverage?
```

This is where Ordivon's Agent-first infrastructure can legitimately change what traditional games are feasible.

## Pass C — Runtime intelligence admission

Only after a form has a player-facing mechanism worth protecting:

```text
Would S-layer or W-layer intelligence create a new central causal distinction?
Can a cheaper rule/policy/human baseline already realize it?
```

Most forms may legitimately end with `RuntimeAgentProfile = none`.

## Pass D — portfolio resource allocation

Research budget is allocated by expected information gain, not by Agent density or ease of metric collection.

```text
next experiment priority =
uncertainty reduced
× decision relevance
÷ experiment burden
```

Hard constraint:

```text
No candidate earns priority merely because Ordivon already has infrastructure for it.
```

---

# 9. What “Agent-first Game” now means

The phrase should refer primarily to **how Ordivon works**, not what the player must see.

A useful spectrum is:

```text
Traditional game, conventional production
Traditional game, Agent-assisted production
Traditional game, Agent-dominant production
Traditional game + runtime system intelligence
Traditional game + selected world Agents
AI-native core loop
persistent multi-Agent world
```

Ordivon is allowed to stop anywhere on this spectrum.

A stronger definition:

```text
Ordivon Game is Agent-first when Agents materially improve the research,
design, production, validation or operation loop while product authority remains explicit.

The shipped game is Agent-native only when runtime Agent cognition is constitutive
of the player's core form of play under a cheaper-baseline counterfactual.
```

This also aligns with current AI-native-games research, which explicitly distinguishes AI-assisted production and AI-augmented games from games whose runtime generative AI is constitutive of the core loop.

---

# 10. FoundationReopenCondition audit

This correction changes product-search coordinates and development classification, not Game Foundations v1.

```text
New primitive required beyond F1–F9: none
Contradiction among F1–F9: none
Missing authority/state semantics: none
Missing participant-coupling distinction: none
Generative provenance/identity failure beyond F6 + existing views: none
```

`ProductionAgentProfile` is a production/workflow coordinate, not a new Game semantic primitive.

`RuntimeAgentProfile` remains representable through current Entity/State/Relation/Observation/Authority/Action coordinates and derived Agent/Subject views.

Therefore:

```text
FoundationReopenCondition = NOT TRIGGERED
Game Foundations v1 remains frozen.
```

---

# 11. External evidence anchors

Accessed 2026-08-17 unless noted.

- Steamworks — Steam Tags. Official taxonomy separates top-level genres, genres/subgenres, visuals/viewpoints, themes/moods, features and player activities; `Artificial Intelligence` is a feature rather than a genre: https://partner.steamgames.com/doc/store/tags
- Unity — AI game-development tools. Current suite includes an editor-integrated project-aware Agentic Assistant, AI Gateway, official MCP Server and generators for project-ready assets/scenes: https://unity.com/features/ai
- Unity (2026-05-05) — AI tools open-beta overview, including Ask/Plan/Agent modes, MCP, Gateway and generators: https://unity.com/blog/unity-ai-how-to-get-started
- Unity Technologies — ML-Agents Toolkit. Official project states trained Agents can control NPCs, automate game-build testing and evaluate design decisions pre-release: https://github.com/Unity-Technologies/ml-agents
- De Mesentier Silva et al. (EA/AIIDE 2018), “Exploring Gameplay With AI Agents.” Automated Agents explored thousands of simulations and exposed imbalances/inconsequential rewards in The Sims Mobile: https://doi.org/10.1609/aiide.v14i1.13034
- Le Pelletier de Woillemont et al. (Ubisoft/AIIDE 2022), “Automated Play-Testing through RL Based Human-Like Play-Styles Generation”: https://doi.org/10.1609/aiide.v18i1.21958
- Gillberg et al. (2023), “Technical Challenges of Deploying Reinforcement Learning Agents for Game Testing in AAA Games,” including Battlefield 2042 and Dead Space testing integration: https://arxiv.org/abs/2307.11105
- Maleki & Zhao (AIIDE 2024), “Procedural Content Generation in Games: A Survey with Insights on Emerging LLM Integration.” PCG predates LLMs and includes search-based, ML, noise/constructive and hybrid methods: https://doi.org/10.1609/aiide.v20i1.31877
- Google Cloud (2025 Games Report). Survey of 615 developers reports broad use of generative AI for repetitive work, code/script support and creative workflows: https://cloud.google.com/resources/games-report
- Google DeepMind — SIMA / SIMA 2. Generalist agents can operate across diverse 3D games/worlds, demonstrating game-playing Agent capability without implying those games must be Agent-native: https://deepmind.google/blog/sima-generalist-ai-agent-for-3d-virtual-environments/ and https://deepmind.google/blog/sima-2-an-agent-that-plays-reasons-and-learns-with-you-in-virtual-3d-worlds/
- Xu et al. (2026), “AI Native Games: A Survey and Roadmap.” Distinguishes AI-assisted production and AI-augmented games from runtime-AI-constitutive core loops: https://arxiv.org/abs/2607.00527

---

# 12. Exact next frontier

Do **not** resume DS2 as previously defined.

Next work is:

```text
Pre-G0 Form Search — broad traditional GameForm portfolio
```

The next round should:

```text
1. sample F01–F22 without Agent preference;
2. identify player-value mechanisms and cheapest valid proofs;
3. estimate conventional burden before any Agent discount;
4. separately map P-layer Agent production leverage;
5. only later admit S/W runtime Agent roles where cheaper baselines fail.
```

No product has been selected. Canonical G0 has not begun.
