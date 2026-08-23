---
schema_version: 1
id: game.product.station-zero-v3
title: Station Zero v3 — Product Definition
type: product-target
profile: product
lifecycle: accepted
source_role: canonical
visibility: public
owners:
  - ordivon-game
audience:
  - player
  - designer
  - builder
  - agent
  - producer
updated: 2026-08-15
summary: Stable human-facing product definition for the unregistered Station Zero v3 target: a delegated single-player asymmetric tactical command game that completed G3/G4 validation and is admitted to bounded G5 Production.
evidence_status: verified
readiness: READY
applies_to:
  - station-zero-v3-unregistered
related:
  - game.start
  - game.development-model
  - game.station-zero-v3.encounter
  - game.station-zero-v3.reducer
  - game.station-zero-v3.execution
  - game.station-zero-v3.planning
  - game.authority
---
# Station Zero v3 — Product Definition

## Current Game Core research interpretation

The 2026-08-16 Game Core research reset treats Station Zero as an executable **reference experiment**. Stage labels and admissions below are retained as historical claims about the v3 programme and its measured machine/runtime/production evidence; they do not select the next product. Canonical G0–G8 semantics are owned only by `DEVELOPMENT_MODEL.md`; current research interpretation is in `GAME_CORE_RESEARCH_RESET.md`.


## Status

Station Zero v3 is the accepted **unregistered replacement target** for the current Station Zero product.

```text
Target Scenario: station-zero@3
Target Ruleset: station-zero-core@4
World schema: 3
Development stage: G5 admitted — bounded Production
Registered replacement: not yet approved
```

This document owns the stable human-facing definition of the v3 target. It does not register v3 and does not replace the exact contracts in P0–P3.

Comparative product-value research and G4-V experiment evidence are owned by `STATION_ZERO_V3_PRODUCT_VALUE.md`; that document may narrow the surfaced controls or identify production gaps without redefining World authority.

The registered root product remains `station-zero@2 / station-zero-core@3` until a later explicit replacement decision.

---

## Product sentence

**Station Zero v3 is a single-player asymmetric turn-based tactical command game in which the player leads autonomous Rescue specialists through partial information, delegates local execution to Agents, commits one simultaneous plan each Turn, and accepts deterministic consequences in a hostile three-faction station crisis.**

A shorter working label is:

```text
Delegated Agentic Tactical Command
```

The game is not defined by the presence of an LLM. Its distinguishing interaction is the combination of delegated command, bounded autonomous cognition, partial information, and authoritative systemic consequence.

---

## Player fantasy

The player is **Mission Control**, not a puppeteer moving every unit step by step.

The desired fantasy is:

> I set mission intent, decide what risks matter, give capable specialists enough autonomy to act, inspect what they intend, commit under uncertainty, and then own the consequences when a hostile World makes part of that plan fail.

The player should feel responsible for:

- strategic priority;
- information acquisition;
- posture and formation;
- protection and retreat policy;
- lethal-force policy, retreat threshold, and an explicit protected-specialist contingency;
- known priority targets;
- scarce Commander abilities;
- whether the current simultaneous Turn is worth committing;
- when partial success or extraction is preferable to continued risk.

The player should **not** spend the session individually approving every ordinary move, attack, pickup, guard, repair, or stabilization action.

---

## Conventional Form Profile

| Field | v3 definition |
| --- | --- |
| player fantasy | Mission Control commanding autonomous Rescue specialists in a hostile station crisis |
| primary form | single-player asymmetric turn-based tactical command / strategy encounter |
| core verbs | observe, set intent, reveal information, review plans, commit, interpret aftermath, adapt |
| cadence | one simultaneous committed Turn followed by deterministic resolution and aftermath |
| control topology | delegated / supervisory command rather than direct unit micromanagement |
| space | 8 Rooms represented as 20 tactical Zones linked by authoritative Passages |
| camera / expression | current target is a 2D tactical command surface; no 3D requirement has been demonstrated |
| session | one bounded 20-Turn encounter |
| progression | faction objectives, extraction, casualties, equipment and encounter outcome; route/meta progression remains deferred |
| social/network form | solo/local product; no human multiplayer |

Genre influences such as tactics, roguelite, systemic crisis, character sim, and sandbox contribute mechanisms but do not override this product form.

---

## Agent Participation Profile

| Field | v3 definition |
| --- | --- |
| role | Rescue specialists plus adversarial Pirate Captain and Hive Alpha |
| autonomy depth | local tactical choice under player/faction strategic intent |
| epistemic boundary | faction-local Knowledge, last-known contacts, bounded observations, no omniscient prompt truth |
| continuity | persistent identity and feedback across the 20-Turn encounter |
| organization | three faction hierarchies with high-fidelity leaders/specialists and cheaper policy Actors |
| cognition tier | five high-fidelity Agent Actors; lower-fidelity units use deterministic policy expansion |

High-fidelity cognition is currently limited to:

```text
Engineer Imani
Medic Reyes
Security Chen
Pirate Captain Veyra
Hive Alpha
```

Lower-cost deterministic policies control the remaining Pirate and Swarm units.

The product deliberately does not make one expensive model call per Actor.

---

## Agentic Consequence Loop

Station Zero v3 implements the Game-wide Agentic Consequence Loop directly:

```text
bounded faction Knowledge
→ Agent Context
→ legal Candidates
→ Agent / policy Decision
→ exact Faction Plan
→ player Commit
→ deterministic World resolution
→ Resolution + Facts + Aftermath
→ owned action / responsibility feedback
→ next Planning Head
```

Provider prose never owns World truth.

A continuing Agent can only choose a Candidate already admitted from its exact Context. World rules decide movement, capacity, reactions, damage, capture, extraction, systems, objectives, and terminal outcomes.

Two Game-owned semantic markers make strategic intent legible without compiling a winning policy into the model:

- `responsibility:advance` means this legal Candidate directly advances the Actor's currently assigned Rescue responsibility;
- `objective:advance` means this legal Candidate directly advances the player's current primary objective from bounded current Knowledge.

These markers describe the current Candidate's meaning. They do not reveal hidden future state or prescribe a complete action sequence.

### Feedback is reason-aware

`FEEDBACK → ADAPT` does not mean "never attempt the same semantic action twice." G3 falsification showed that a blanket no-repeat policy destroyed an otherwise real Rescue strategy: in simultaneous play, `target_zone_capacity_lost` can mean that another Actor occupied a legal destination during the same committed Turn, not that the strategic route itself was wrong.

The retained rule is narrower:

```text
generic no_effect / contested / interrupted / invalidated
→ strong pressure to choose a different immediate action

target_zone_capacity_lost
+ Candidate is still responsibility:advance or objective:advance
→ bounded retry remains legal
```

This preserves adaptation without teaching Agents to abandon a valid strategic commitment whenever an adversary temporarily contests space. The exception is reason-specific and Game-semantic; it is not a general license to repeat failed actions.

---

## Core player loop

The stable player-facing loop is:

```text
OBSERVE
→ COMMAND
→ REVIEW
→ COMMIT
→ RESOLVE
→ OBSERVE
```

Terminal play ends in:

```text
DEBRIEF
```

Internally, authority remains more precise:

```text
Situation / Knowledge
→ Commander Order
→ Agent deliberation
→ exact three-faction Preview
→ selected Commit
→ deterministic Turn Batch
→ World consequence
→ retained evidence / feedback
→ next Planning Head
```

The internal authority states are not extra gameplay stages.

---

## Three product pillars

### 1. Delegated command must matter

The player's Order must materially change local Agent choices and later World trajectories without collapsing into direct unit control.

### 2. Partial information must create strategy, not confusion

Faction Knowledge is gameplay state. Scans, contact confidence, last-known locations, sealed enemy Plans, and local visibility should create meaningful uncertainty while remaining causally legible after resolution.

### 3. Consequence must create real tradeoffs

A strategy should be able to gain one valuable result while sacrificing another. Rescue, cargo recovery, enemy elimination, specialist survival, position, and time should not collapse into one universally dominant route.

---

## Encounter content grammar

The current representative encounter contains:

```text
3 factions
12 persistent Actors
20 tactical Zones
20 Passages
12 Abilities
15 Equipment definitions
14 Items
12 Commander Abilities
12 faction Objectives
4 coupled Systems
3 Hazards
20 committed Turns maximum
```

The current bounded v3 product now exposes two exact **Scenario Cases** over the same ruleset and World schema:

| Case | Product role | Exact current distinction |
| --- | --- | --- |
| `fixed-genesis` / **Contested Signal** | canonical baseline slice | original Junction capacity |
| `junction-bottleneck` / **Junction Bottleneck** | G5 bounded second slice | `junction-cover` capacity `2 → 1` |

`scenario_case_id` is retained with the Run and Genesis digest. A Case is content identity, not a new Ruleset, World schema, or generic mutation language. The player can select the Case before an operation and sees known Zone capacity on the tactical map.

The content grammar combines:

- named persistent Actors;
- asymmetric mandatory and optional objectives;
- scarce extraction capacity and time;
- coupled power / oxygen / heat / alert / biomass state;
- systems, hazards, loot and tactical passages;
- partial faction Knowledge;
- local movement, combat, repair, stabilization, rescue, capture, devour, hack, pickup, extraction and reaction;
- deterministic Turn resolution after commitment.

Broad encounter generation, a campaign, route map, meta progression, settlement, relationship simulation, or a large Agent population remain outside the current production commitment. G5 admits one bounded second **Case** only; it does not authorize a mission factory or generic Scenario framework.

---

## Why the encounter budget is 20 Turns

P0 originally froze a 14-Turn encounter. G3 strategic falsification showed that this made the mandatory Rescue objective effectively fake under the real tactical travel and contention cost.

The diagnosis separated three claims:

```text
World reachable
policy accessible
model realized
```

Before changing the budget, Game tested and rejected narrower explanations including:

- fixture successor-state defects;
- civilian support assignment defects;
- moving-Hive pursuit defects;
- Life Support Console capacity `2 → 3` as a research-only counterfactual;
- legal priority targeting;
- `emergency-uplink`;
- a research-only support heuristic.

With those issues separated, the same World rules, enemy policies, Knowledge boundaries, Candidate admission, and Rescue policy completed both mandatory Rescue objectives at Turn 20 when only the research encounter budget was extended. The canonical target was therefore corrected to 20 Turns.

The extra Turns do not make all strategies win. The final exact fixture matrix still contains narrow viable basins and many partial/failure outcomes.

---

## G3 strategic viability evidence

The canonical fixture evaluator is:

```text
pnpm eval:v3:fixture-strategies
```

It evaluates the exact first-order policy surface:

```text
3 primary objectives
× 3 postures
× 2 formations
= 18 deterministic profiles
```

Each profile runs once because the fixed Genesis and fixture policy are deterministic. The evaluator records objective progress, required fronts, extraction/cargo/Hive milestones, casualties, Intent results, selected actions, and raw Pareto outcome vectors.

After G3 diagnosis, reason-aware feedback validation, the 20-Turn correction, and the 2026-08-24 Core successor-commitment correction, each surfaced primary objective has real policy-accessible basins. The current exact 18-profile matrix retains **3/6 Rescue focus-complete victory profiles, 5/6 Core focus-complete profiles, and 6/6 Hive focus-complete profiles**:

| Primary objective | Representative viable fixture basin | Result |
| --- | --- | --- |
| rescue two civilians | cautious + cohesive | 2/2 civilians, 2/2 mandatory fronts, Rescue victory |
| recover Research Core | cautious/balanced with either formation, plus aggressive + split | Core 1/1 in 5/6 profiles; those five remain Rescue partial with 1/2 mandatory fronts; aggressive + cohesive can still fail under route-capacity and heat pressure |
| eliminate Hive Alpha | several cautious/balanced/split/cohesive basins | Hive 1/1, Rescue partial; aggressive variants can add casualty cost |

The matrix does **not** become trivial at 20 Turns. Rescue victory remains narrow. Core recovery is now broadly policy-accessible after fixing the cargo-carrier extraction successor discontinuity, but it remains a costly optional tradeoff rather than a Rescue-victory shortcut.

---

## G3 strategy plurality evidence

Pareto comparison uses raw World outcomes rather than the selected focus label:

```text
maximize:
  civilians extracted
  Core extracted
  Hive eliminated
  specialists extracted

minimize:
  specialist deaths
  specialist incapacitations
```

The final exact fixture surface contains **8 Pareto profiles collapsing to 3 materially different raw outcome signatures**:

1. **Rescue / survival** — two civilians and two specialists extracted, no specialist casualty, victory;
2. **Core recovery** — Core extracted and two specialists extracted, but with a specialist death, partial;
3. **Hive elimination** — Hive eliminated with no specialist death in bounded variants, but without mandatory extraction fronts, partial.

This is enough to reject the hypothesis that the Commander controls merely decorate one dominant strategy.

It does not prove final balance or human fun. Those remain later product claims.

---

## G3 live-Agent evidence

The live DeepSeek path is real product code, not a future stub:

```text
ORDIVON_GAME_V3_PROVIDER=deepseek
```

It uses the same Agent Context, Candidate admission, World authority, persistence, and browser contracts as the fixture baseline.

G3 performed a bounded current audit with six enabled credential sources and then full 20-Turn holdouts on fixture-proven strategic basins.

Across the baseline and two post-treatment full-run rounds used for the G3 diagnosis:

```text
live Provider calls: 950
successful calls:     950
retries:              0
hidden references:    0
```

All evaluated Runs remained verifiable.

The first live holdout exposed an important Context asymmetry: fixture scoring privately understood that routes such as `route:reactor-console` or bounded Hive pursuit advanced the selected primary objective, while the live Provider saw only generic route tags. Game corrected the semantic surface with `objective:advance` rather than compiling a winning sequence into the prompt.

Observed treatment effect:

- Core focus changed from 0/2 baseline completions to **2/2 post-treatment completions**, including Core acquisition, return, and extraction;
- Hive focus changed from 0/2 baseline completions to **1/2 post-treatment completions**; both post-treatment runs showed bounded objective-directed search, while only one converted it into the kill before Turn 20;
- Rescue remained 1/2 civilians in both post-treatment runs, but Agents repeatedly selected `responsibility:advance`; remaining failure was dominated by tactical Zone-capacity contention rather than responsibility loss.

The live Provider is therefore accepted for **bounded strategic realization**, not as an automatic solver. Model realization remains probabilistic and outcome failure remains legitimate play.

Current turn-plan latency is measured in seconds rather than real-time-action latency; G4 must judge whether the waiting experience is acceptable in the final presentation instead of hiding it behind an architecture claim.

---

## Experience state at G3 exit

The playable prototype already provides:

- situation-first information hierarchy;
- a validated tactical map derived from authoritative topology;
- Commander controls that materially alter planning;
- Plan Preview with sealed enemy commitment;
- Plan Impact without pretending to forecast outcomes;
- explicit Commit;
- temporal expression of visible Turn consequence;
- Plan Review against authoritative resolution;
- own-action and responsibility feedback into later cognition;
- persistent strategic intent;
- first-command orientation;
- terminal Operation Debrief.

Automated browser and Agent evidence proves the loop is executable, bounded and causally inspectable.

It does **not** establish human-specific claims such as delight, emotional attachment, aesthetic coherence, target-market comprehension, or return desire. Those claims remain explicitly open for Vertical Slice and later targeted human calibration.

---

## Production profile

Current production assumptions are deliberately conservative:

| Dimension | Current target |
| --- | --- |
| platform | local/browser first |
| representation | 2D tactical command surface |
| timing | turn-based; several seconds of Agent planning can be presented deliberately |
| authored geometry | Game-owned semantic topology, currently authored through Tiled |
| visual production | Studio-owned UI/vector/2D character/VFX work where the Vertical Slice proves need |
| audio | representative SFX/ambience/music required for G4; no current mature production loop |
| content scale | one representative encounter until the Vertical Slice proves production quality and repeatability |
| engine | browser remains the default; Godot is not admitted without a demonstrated runtime/presentation limitation |
| 3D | not required; Blender remains optional unless a concrete 2.5D/3D production decision is made |

Installed tools do not choose these decisions.

---

## G3 exit judgment

G3 Playable Prototype is accepted as complete enough to enter Vertical Slice because:

- the complete 20-Turn loop is playable end to end;
- authoritative consequence, persistence and recovery are stable;
- every surfaced primary objective has at least one fixture-accessible strategic basin;
- at least three non-dominated strategic outcome signatures exist;
- live Agent cognition can consume bounded objective/responsibility semantics and realize real strategic chains without hidden-information leakage;
- the remaining highest-risk questions are now production/experience questions rather than missing game authority or an obviously fake core loop.

G3 completion does **not** approve v3 registration or deletion of v2.

---

## G4 Vertical Slice objective

G4 answered two product questions with one representative slice:

```text
Is this final-ish form worth playing?
Can we repeatedly produce this quality at an understood cost?
```

The Vertical Slice must therefore combine the existing proved kernel with representative final-ish:

- tactical information hierarchy and map language;
- character/faction visual identity;
- movement/combat/interaction/environment expression;
- animation and VFX;
- SFX, ambience and music treatment;
- planning/waiting feedback for live Agent latency;
- accessibility-sensitive states and reduced-motion behavior;
- one coherent encounter presentation from landing through Debrief;
- an actual repeatable Game → Studio → runtime integration loop.

G4 is **not** permission to build a campaign, meta progression, generic RPG engine, large content factory, multiplayer, 3D conversion, or hundred-Agent world.

---

## Replacement boundary

The v3 root replacement decision remains later than G4 admission.

Before replacing the registered v2 product, evidence still needs to answer at least:

- whether target players understand delegated command and simultaneous commitment;
- whether plan explanations improve decisions rather than merely add prose;
- whether live-Agent planning latency is acceptable in the intended presentation;
- whether tactical uncertainty remains legible with final-ish art/audio;
- whether the final-ish slice is more compelling than the v2 intervention loop;
- whether obsolete v2 approval-loop code can be deleted cleanly rather than maintained in parallel.

Until that decision:

```text
v2 = registered product truth
v3 = accepted G5 target
```

---

## Explicit non-goals

Current G4 admission does not authorize:

- a universal Ordivon Game engine;
- a branching roguelite route map;
- cross-run meta progression;
- a second mission solely to create volume;
- human multiplayer;
- arbitrary generated rules;
- 3D migration without production evidence;
- one model call per low-fidelity Actor;
- a hundred-Agent society;
- relationship simulation without a demonstrated gameplay need;
- dialogue detached from consequence;
- model-generated authoritative World outcomes.
