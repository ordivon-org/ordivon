# Top Game Mechanism Specimens — R1

Status: **EXTERNAL DESK DECOMPOSITION / NOT SUCCESS CAUSATION**
Observed: 2026-09-14

## Scope

This wave decomposes **16 elite/canonical market specimens** into mechanism graphs. Selection combines current durable market presence with unusually clear mechanism exemplars. The goal is not to copy games or rank genres; it is to identify recurrent coupling patterns worth testing.

## Specimen map

| Game | Mechanism center | Primary dynamic |
| --- | --- | --- |
| **Counter-Strike 2** | `aim, shoot, partial-observation, round-match` | execution skill + information economy + inter-round resource economy |
| **Dota 2** | `variable-player-powers, asymmetric-roles, team-based-play, equipment-progression` | role interdependence + power curves + objective timing |
| **Fortnite Battle Royale** | `permadeath, random-production, inventory, risk-reward` | uncertain resources + forced convergence + one-life consequence |
| **Minecraft** | `destroy, collect, craft, place` | tiny block manipulation grammar + persistent composition + self-authored goals |
| **Factorio** | `resource-source, transport, resource-converter, resource-drain-sink` | solve manual work once, then move cognition upward to the next constraint |
| **Slay the Spire** | `deck-building, drafting, synergy-combos, build-path-dependency` | stable combat grammar + constrained acquisition + path dependence |
| **Balatro** | `deck-building, synergy-combos, combo-chaining, score-high-score` | familiar base grammar + rule-breaking modifiers + multiplicative synergy |
| **ELDEN RING** | `telegraphing, dodge, block, parry` | attributable failure + retry + route freedom |
| **Baldur’s Gate 3** | `branching-choice, persistent-consequence, relationship-state, role-assumption` | agency becomes credible when different mechanical routes produce later acknowledgement |
| **The Legend of Zelda: Tears of the Kingdom** | `modular-construction, physics-spatial-manipulation, recipe-composition, shortcut-discovery` | general-purpose verbs + consistent rules + many valid solutions |
| **Stardew Valley** | `time-as-resource, automatic-resource-growth, craft, relationship-state` | many low-pressure loops compete for one scarce daily schedule |
| **Hades** | `run, randomized-encounters, variable-player-powers, synergy-combos` | failure is both mechanical reset and narrative progression |
| **Sid Meier’s Civilization VI** | `tile-placement, adjacency, tech-tree, variable-player-powers` | irreversible spatial commitments + multiple victory logics + long-horizon tech progression |
| **RimWorld** | `simulation-emergence, director-event-manager, adaptive-opponent, relationship-simulation` | simulation state is narrative substrate |
| **The Sims 4** | `character-customization, self-authored-goal, relationship-simulation, relationship-state` | create people + create space + simulate consequences |
| **Into the Breach** | `grid-movement, telegraphing, deterministic-resolution, push-pull` | near-perfect information + deterministic consequence + multi-objective spatial manipulation |

## Recurring structural motifs

### m01 — Stable grammar, changing context

A small stable action grammar can support long-term depth when goals, state, topology, resources or modifiers repeatedly revalue the same actions.

**Seen in:** top-minecraft, top-slay-spire, top-balatro, top-into-breach, top-stardew

### m02 — Persistent consequence turns actions into authorship

When actions persist and later systems acknowledge them, choices become material for future play rather than isolated transactions.

**Seen in:** top-minecraft, top-bg3, top-stardew, top-sims4, top-rimworld, top-factorio

### m03 — Failure must preserve information

Retry loops are strongest when failure yields an attributable model update, route/build knowledge or strategic information.

**Seen in:** top-elden-ring, top-hades, top-into-breach, top-cs2, top-slay-spire

### m04 — Path dependence creates build identity

Earlier choices should alter the value or availability of later choices; otherwise progression becomes a linear shopping list.

**Seen in:** top-dota2, top-slay-spire, top-balatro, top-hades, top-bg3, top-civ6

### m05 — General-purpose mechanics outperform bespoke interactions when rules stay consistent

A few composable, consistently simulated verbs can generate large solution/content spaces without enumerating every interaction.

**Seen in:** top-minecraft, top-factorio, top-totk, top-rimworld, top-sims4

### m06 — Scarcity creates choice only when alternatives stay legible

Time, information, life, inventory or currency scarcity creates strategy only when tradeoffs are understandable rather than merely deprivation.

**Seen in:** top-cs2, top-fortnite, top-stardew, top-elden-ring, top-slay-spire

### m07 — Multiple timescales create durable loops

Top specimens often couple second-to-second actions, session commitments and long-horizon progression/economy so one timescale changes another.

**Seen in:** top-cs2, top-dota2, top-factorio, top-hades, top-stardew, top-civ6

### m08 — Randomness works best upstream of decisions

Randomized offers, layouts and events create adaptation when players respond to them; opaque random outcome resolution weakens attribution.

**Seen in:** top-slay-spire, top-balatro, top-hades, top-fortnite, top-rimworld

### m09 — Role depth requires non-substitutable responsibility

Roles matter when players possess different capabilities, information or responsibilities that cannot be trivially replaced.

**Seen in:** top-cs2, top-dota2, top-bg3

### m10 — Systemic freedom still needs pressure

Open possibility spaces gain direction from survival pressure, scarcity, self-authored goals, events or consequences; freedom alone is not a loop.

**Seen in:** top-minecraft, top-factorio, top-totk, top-rimworld, top-sims4

### m11 — Readable causality is the foundation of mastery

Intentional improvement requires system response to expose cause, constraint and consequence sufficiently well.

**Seen in:** top-factorio, top-elden-ring, top-into-breach, top-cs2, top-totk

### m12 — Meta systems should recontextualize core play

Progression is strongest when it changes future possibility or strategy, not when it only increases scalar output.

**Seen in:** top-hades, top-slay-spire, top-civ6, top-stardew, top-dota2

## Most important conclusion

The recurring pattern is not a particular genre or theme. Top specimens repeatedly use **small reusable rules whose value changes when coupled to context, persistence, scarcity, feedback, role asymmetry or path dependence**. The highest-value extraction target is therefore usually an **edge or loop**, not an isolated mechanic.

```text
Minecraft:  destroy → collect → craft → place → persistent world → new self-authored goal
Factorio:    flow → bottleneck → diagnosis → redesign → automation → new bottleneck
Slay Spire:  constrained offer → build path → encounter pressure → revalue future offer
Elden Ring:  telegraph → commit defense → recovery window → punish → death/retry → learned model
Hades:       run variation → build adaptation → failure → narrative/meta continuation → new run
TotK:        consistent physics + composable verbs → player-generated solution topology
```

Machine-readable authority: `game-top-mechanism-specimens-r1.json`.
