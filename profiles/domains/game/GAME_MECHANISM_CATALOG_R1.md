# Game Mechanism Catalog — R1

Status: **WORKING EXTERNAL-SOURCE CROSSWALK / EXTENSIBLE / NOT A CLOSED PERIODIC TABLE**  
Observed: 2026-09-14

## Authority boundary

There is no universally accepted closed list of game mechanics. The sources disagree partly because they answer different questions:

- **Sicart:** mechanics are agent-invoked methods for interaction with game state; useful discipline is to describe mechanics as verbs and distinguish them from rules.
- **Game Ontology Project:** organizes game elements and relationships rather than games; top-level elements are Interface, Rules, Entity Manipulation and Goals.
- **Björk/Holopainen gameplay design patterns:** recurring gameplay interactions, with explicit consequences and relations among patterns; the published pattern language spans game elements, resources, information, actions/events, narrative/predictability, social interaction, goals, sessions, mastery/balance, meta/replay/learning.
- **Machinations/Dormans:** resource/economy systems can be modeled with Source, Pool, Drain, Converter, Trader and Gate plus resource/state connections.
- **BoardGameGeek:** a large practical mechanism vocabulary including action selection, auctions, drafting, hidden roles, negotiation, programmed movement, simultaneous action, worker placement and many others.
- **Steam:** current commercial vocabulary exposes mechanics/features such as automation, crafting, deckbuilding, inventory/resource management, procedural generation, PvP/PvE, turn-based combat/tactics, trading, time manipulation, level editing and more.

Next therefore owns only a **normalized crosswalk**. Original sources remain semantic authorities.

Current R1 census contains **424 unique normalized design elements across 431 family memberships**. Seven elements intentionally belong to more than one family (for example `trading`, `initiative`, `reputation` and `communication-limits`). Families are therefore facets, not exclusive buckets.

## Mechanism families

### Player/agent actions

**Basis:** Sicart; Steam feature/activity tags; GOP entity manipulation

move, jump, dash, climb, swim, fly, drive, steer, aim, shoot, strike, block, parry, dodge, grab, throw, push/pull, interact/use, collect, place, build, destroy, craft, equip, switch, inspect, scan, hide, sneak, hack/program, command, delegate, select/choose, dialogue, trade, negotiate, vote, signal/communicate, draw/play-card, draft, bid, bet/wager, create/edit, save/share

### Space, topology and position

**Basis:** Game Ontology Project; BGG mechanisms; gameplay design patterns

grid-movement, hex-movement, point-to-point-movement, area-movement, free-continuous-movement, relative-movement, zone-of-control, line-of-sight, cover, facing, range, adjacency, pathfinding, route/network-building, territory-control, area-majority/influence, enclosure, spatial-blocking, teleport/portal, verticality, landmarks, hidden-movement, secret-deployment, environmental-destruction, physics-spatial-manipulation

### Time, turn and action scheduling

**Basis:** BGG mechanisms; Steam real-time/turn-based tags; gameplay design patterns

turn-taking, initiative, simultaneous-action-selection, simultaneous-resolution, real-time, real-time-with-pause, action-points, action-queue, programmed-movement, command-queue, cooldowns, wind-up/startup, recovery-window, timing-window, reaction/interrupt, deadline/time-limit, delays/queues, tick/step, speed/tempo, bullet-time/slow-time, time-rewind, time-loop, phase-order, variable-turn-order

### Information, uncertainty and knowledge

**Basis:** Game Ontology Project; Björk patterns; BGG mechanisms

perfect-information, hidden-information, partial-observation, asymmetric-information, fog-of-war, clues/evidence, deduction, pattern-recognition, telegraphing, prediction/preview, last-known-state, information-age/staleness, provenance/source, inspection-cost, information-scarcity, reveal, secret-role, secret-objective, bluffing, deception, targeted-clues, communication-limits, memory/knowledge-persistence, random-unknown-outcome, unknown-rule/discovery

### Goals and challenge structures

**Basis:** Game Ontology Project Goals; Björk goal patterns; BGG

required-goal, optional-goal, self-authored-goal, score/high-score, race, survive, eliminate, capture/control, defend, escort/protect, deliver/pick-up-and-deliver, collect/set-collection, construct, optimize, solve-puzzle, discover, escape, infiltrate, boss-challenge, mission/scenario, contract/task, multi-objective-tradeoff, end-condition, sudden-death, completion/collectionism

### Resources and economy

**Basis:** Machinations; Dormans; Björk resource-management patterns; BGG

resource-source, resource-pool/storage, resource-drain/sink, resource-converter, resource-trader/exchange, resource-gate/distribution, resource-flow, state-modifier, capacity-limit, inventory, queue/backlog, scarcity, upkeep/maintenance, production-rate, consumption-rate, currency, health/stamina, ammo, energy/mana, time-as-resource, workers/actions-as-resource, market/price, trading, auction/bidding, commodity-speculation, closed-economy, automatic-resource-growth, interest/compounding

### Production, transformation and logistics

**Basis:** Machinations; Steam automation/resource-management features; systems-design synthesis

crafting-recipe, processing-chain, transport, routing, network-flow, bottleneck, buffering, throughput, batching, machine-allocation, worker-allocation, supply-demand, conversion-yield, waste/byproduct, maintenance/breakdown, automation, programmable-automation, scaling/economies-of-scale, placement-efficiency, dependency-chain, feedback-control

### Risk, randomness and outcome resolution

**Basis:** Game Ontology Project rules; BGG; gameplay patterns

deterministic-resolution, dice/random-resolution, card/draw-randomness, random-production, critical-success/failure, reroll/locking, push-your-luck, risk-reward, hidden-roll, probability-modification, advantage/disadvantage, random-events, procedural-variance, permadeath, lives, checkpoint, save/load, resource-loss-on-failure, insurance/safety-net, catch-up/rubber-banding

### Conflict and combat

**Basis:** Steam genre/feature vocabulary; BGG; pattern synthesis

hitpoints/damage, armor/mitigation, range/position-combat, melee-combat, projectile-combat, area-of-effect, status-effects, combo/chaining, rock-paper-scissors-counterplay, target-priority, threat/aggro, initiative, cover-combat, stealth-detection, morale, suppression, knockback/force, friendly-fire, resource-costed-attacks, capture/disable, duel, team-combat, boss-patterns

### Composition, drafting and buildcraft

**Basis:** BGG; Steam deckbuilding/crafting; pattern synthesis

drafting, deck-building, bag/pool-building, hand-management, loadout-building, equipment-slots, skill-build, tech-tree, synergy/combos, set-bonus, recipe-composition, modular-construction, tile-placement, worker-placement, variable-player-powers, asymmetric-roles, once-per-game-ability, gating/unlocking, upgrade-choice, mutually-exclusive-upgrades, build-path-dependency, respec/reconfiguration

### Progression and persistence

**Basis:** Steam features; GameRefinery meta-game lens; gameplay patterns

experience-points, levels, stats-growth, skill-tree, equipment-progression, unlock, collection, quest/campaign-progression, reputation, faction-standing, relationship-state, base/home-persistence, world-state-persistence, character-permadeath, inheritance/legacy, run-meta-progression, new-game-plus, prestige/reset, achievements, leaderboards/rank, season/battle-pass-like-progression

### Social interaction and strategic interdependence

**Basis:** BGG; Björk social-interaction patterns; Steam player-count/features

cooperation, competition, team-based-play, alliances, negotiation, trading, gifting, voting, bargaining, contracts/promises, betrayal/traitor, hidden-roles, social-deduction, communication-limits, shared-resource, public-good, prisoners-dilemma, kingmaking/catch-leader, role-asymmetry, shared-control, coordination-timing, player-judge, storytelling-to-others, spectating, reputation-among-players

### Role, narrative and relationships

**Basis:** Steam choices/dialogue/narrative features; gameplay patterns

role-assumption, character-customization, dialogue-choice, branching-choice, choices-matter, quest, relationship-state, trust/affinity, companion, faction, reputation, moral/value-choice, persistent-consequence, multiple-endings, dynamic-narration, authored-narrative, emergent-story, storylet/event-system, identity/role-change, memory-of-actions, legacy/history, perspective-shift

### Exploration and discovery

**Basis:** Steam activities/subgenres; MDA discovery lens; gameplay patterns

map-reveal, fog-clearing, landmark-navigation, shortcut-discovery, secret-area, hidden-object, rule-discovery, environmental-clue, backtracking-with-new-capability, gating-by-knowledge, gating-by-tool, world-transformation-opens-route, procedural-exploration, scouting, surveying/scanning, collection-as-discovery, spatial-memory, route-hypothesis, risked-exploration

### Creation, sandbox and UGC

**Basis:** Steam building/modding/level-editor features; gameplay patterns

freeform-building, constrained-building, level-editor, character-design, decoration/customization, terraforming, drawing/painting, music/composition, storytelling/authorship, programmable-entities, logic/circuit-building, vehicle/machine-construction, save-revision, share/publish, modding, ugc, remix, blueprints/templates, constraint-budget, responsive-critique/audience

### Feedback, learning and mastery

**Basis:** skill-atom / MDA / accessibility and difficulty guidance synthesis

immediate-action-feedback, hit-confirm, telegraph, preview, score, combo-meter, accuracy/timing-grade, progress-meter, cause-effect-log, replay, ghost, death-recap, prediction-vs-outcome, tutorial/onboarding, practice/training, difficulty-scaling, dynamic-difficulty, assist-options, hint-system, error-recovery, fast-retry, safe-vs-risky-route, rank/grade, mastery-challenge

### Session, replay and meta structures

**Basis:** Björk session/meta/replay patterns; Steam tags

round/match, run, mission/scenario, campaign, persistent-session, score-and-reset, daily/weekly-challenge, events, variable-setup, procedural-seed, randomized-encounters, branching-campaign, meta-progression, leaderboards, time-trial, speedrun-support, challenge-modifiers, difficulty-modes, mutators, new-game-plus, seasonal-structure, community-workshop/mods

### System generation and adaptation

**Basis:** Steam procedural-generation/AI/physics features; Game Ontology rules; systems-design synthesis

procedural-generation, random-generation, simulation/emergence, agent-policy, adaptive-opponent, director/event-manager, dynamic-difficulty-adjustment, economy-simulation, ecosystem-simulation, relationship-simulation, physics-simulation, rule-changing, player-manipulable-rules, generated-missions, generated-maps, generated-loot, spawn-system, population-simulation, weather/time-cycle, world-state-machine, responsive-audience/opponent

## Composition law

A useful design object is not a bag of mechanics but a **mechanism graph**.

```text
Mechanism A --enables--> Mechanism B
Mechanism B --consumes--> Resource X
Information Scarcity --modulates--> Choice Value
Failure --feeds--> Fast Retry --supports--> Mastery
Progression --gates--> New Verb --changes--> Exploration Topology
```

Normalized edge vocabulary:

`enables / requires / gates / constrains / consumes / produces / transforms / reveals / hides / modulates / amplifies / dampens / rewards / penalizes / synchronizes / competes-with / cooperates-with / persists-into / resets / conflicts-with`

The relations matter at least as much as the nodes. `crafting + exploration + combat` is not a design until their causal connections are specified.

## Experience layer — deliberately separate

Mechanics are not Player Value. Use outcome lenses separately:

- **MDA aesthetics:** sensation, fantasy, narrative, challenge, fellowship, discovery, expression, submission.
- **Quantic Foundry motivations:** destruction, excitement, competition, community, challenge, strategy, completion, power, fantasy, story, design, discovery.

These are hypothesis/evaluation vocabularies, **not scalar objective functions** and not reasons to skip Human evidence.

## Composition record

Every future candidate composition should record:

```text
player/context
anchor mechanics
support mechanics
coupling edges
time model
information model
goal structure
feedback/learning loop
target dynamics
target experience/motivation
known conflicts
reference specimens
evidence standing
cheapest falsifier
kill conditions
```

This lets Game search combinations rather than genres while still mapping a resulting product back to external market categories later.

## External anchors

- Sicart, Defining Game Mechanics — https://gamestudies.org/0802/articles/sicart
- Game Ontology Project — https://gameontology.com/
- Björk, Lundgren, Holopainen, Game Design Patterns — https://dl.digra.org/index.php/dl/article/view/60
- Gameplay Design Patterns — https://virt10.itu.chalmers.se/index.php/Main_Page
- Machinations Framework — https://machinations.io/docs/framework-basics
- Dormans, Simulating Mechanics to Study Emergence in Games — https://ojs.aaai.org/index.php/AIIDE/article/view/12477
- BoardGameGeek mechanics — https://boardgamegeek.com/browse/boardgamemechanic
- Valve Steam Tags — https://partner.steamgames.com/doc/store/tags
- Quantic Foundry motivation model — https://quanticfoundry.com/2015/07/20/how-we-developed-the-gamer-motivation-profile-v2/
- Xbox Accessibility Guidelines — https://learn.microsoft.com/en-us/xbox/accessibility/guidelines
