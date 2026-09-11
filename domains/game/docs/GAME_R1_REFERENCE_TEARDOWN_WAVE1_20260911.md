---
schema_version: 1
id: game.r1.reference-teardown.wave1.20260911
title: Ordivon Game — R1 Comparative Reference Teardown Wave 1
profile: product-discovery
type: research-decision
lifecycle: active
source_role: current-r1-reference-teardown
visibility: public
owners:
  - ordivon-game
updated: 2026-09-11
summary: First comparative teardown of twelve materially different successful games using one shared evidence schema. Public/official product facts are separated from causal hypotheses, alternative explanations and transferable micro-baselines; direct-play experience claims remain pending.
evidence_status: externally-grounded-desk-teardown
readiness: R1_DESK_TEARDOWN_COMPLETE_DIRECT_PLAY_PENDING
---
# R1 Comparative Reference Teardown — Wave 1

## 0. Claim boundary
This is **reference research**, not product selection and not reproduction admission.

```text
ObservedReferenceFact
!= InferredDesignCause
!= TransferableDesignLaw

CommercialSuccess
!= CoreMechanicCausality

DeskTeardown
!= ExperienceEvidence
```

All twelve references were read through the same schema:

```text
Observed facts
Causal hypotheses
Alternative explanations / confounds
Expression dependencies
Transfer hypotheses
Smallest falsifiable baseline
Baseline falsifier
Direct-play standing
```

The machine-readable record is `evidence/acceptance/game-r1-reference-teardown-wave1-20260911.json`.

## 1. Counter-Strike 2 — irreversible tactical commitment
**Observed.** Valve continues to frame Counter-Strike as a competitive, tactical, team-based FPS and CS2 as the Source 2 successor. Source: https://store.steampowered.com/app/730/CounterStrike_2/

**Hypothesis.** Short round resets + lethal commitment + incomplete information may make spatial mistakes unusually legible and costly; stable rules allow skill to accumulate in aim, movement, timing, map knowledge and coordination.

**Confounds.** Two decades of brand continuity, esports/community network, skin economy, workshop ecosystem and networking/production quality can all contribute to success.

**Smallest baseline.** One graybox objective map, two teams, lethal elimination, partial information and immediate round reset. Economy is a second experiment, not mandatory in the first carrier.

**Falsifier.** Remove lethal commitment or information scarcity. If positioning/information-seeking/tension barely changes, the proposed transfer is weak.

## 2. Dota 2 — role interdependence across a long power curve
**Observed.** Valve emphasizes 100+ heroes, flexible roles, large item variety and continuous game evolution. Source: https://store.steampowered.com/app/570/Dota_2/

**Hypothesis.** Team objectives, role asymmetry and long power curves may convert local choices into delayed collective consequences. Hero/item combinatorics create match-specific adaptation rather than a fixed solution.

**Confounds.** Massive established community, esports, many years of balance/content iteration, social retention and cosmetics.

**Smallest baseline.** One lane, two roles per side, minion pressure, one tower/objective and a simple level/item timing curve.

**Falsifier.** If each player can maximize local output independently and coordination/resource timing adds little, the role-interdependence claim is weak.

## 3. Fortnite — separate Battle Royale causality from ecosystem causality
**Observed.** Epic currently exposes Battle Royale and Zero Build, while Ranked explicitly values placement, eliminations, damage and storm progression. Fortnite also operates a creator ecosystem with publishing, playtests, analytics and monetization. Sources: https://www.fortnite.com/@epic/battle-royale ; https://www.fortnite.com/competitive/discover-competitive/fortnite-ranked-play-explained ; https://create.fortnite.com/

**Hypothesis.** For the BR layer, one-life survival + uncertain loot + forced spatial convergence may repeatedly create route-versus-engagement decisions. For the product layer, longevity may also depend on social presence, live change and creator variety.

**Confounds.** Free-to-play reach, cross-platform network effects, IP collaborations, cosmetics, creator economy and live-ops cadence are not Battle Royale mechanics.

**Smallest baseline.** Eight-entity shrinking arena with sparse loot, one life and placement outcome. Building is excluded initially and tested separately.

**Falsifier.** Compare to static respawn arena. If storm/one-life conditions do not change routes, engagement or resource timing, the BR transfer is weak.

## 4. Minecraft — persistent transformation and self-authored goals
**Observed.** Mojang explicitly states Minecraft has no single required goal. Blocks can be broken, crafted and placed; Survival adds resource/danger constraints while Creative removes them. Sources: https://www.minecraft.net/en-us/article/what-minecraft ; https://www.minecraft.net/en-us/about-minecraft

**Hypothesis.** A small, composable world-manipulation grammar may be powerful because players can translate their own intentions into persistent spatial state. Survival constraints create reasons to explore/build without fully specifying what the player should build.

**Confounds.** Cultural ubiquity, multiplayer/server network, modding, creator/video ecosystem, education and merchandise.

**Smallest baseline.** Compact block field with break→obtain→place and one environmental constraint, but no authored objective beyond changing the space.

**Falsifier.** If players do not form self-authored spatial intentions, or persistent transformation does not shape later choices, the authorship claim is weak.

## 5. Grand Theft Auto V — cross-system freedom in a dense world
**Observed.** Rockstar presents a shared Los Santos/Blaine County setting across story and GTA Online; Online combines heists, races, businesses, vehicles, adversary modes and social spaces. Source: https://www.rockstargames.com/gta-v

**Hypothesis.** Walking, driving, combat and world response may feel like one possibility space because actions cross subsystem boundaries inside a persistent dense world. Escalating response can produce unscripted short stories.

**Confounds.** Massive content and production scale, brand, cinematic writing/performance, music, online network and a decade of live operations.

**Smallest baseline.** One city block with walking/driving, vehicle acquisition, civilians, escalating law response and at least two escape routes.

**Falsifier.** If players use each verb as an isolated minigame and rarely improvise cross-system plans, the systemic-freedom transfer is weak.

## 6. ELDEN RING — combat commitment plus route freedom
**Observed.** Official material describes a seamless world connected to complex dungeons, many combat/build approaches, readable enemy intentions, dodge/parry/guard timing, and the explicit option to avoid strong enemies and return later. Sources: https://en.bandainamcoent.eu/elden-ring/elden-ring ; https://en.bandainamcoent.eu/elden-ring/news/what-elden-ring-about ; https://en.bandainamcoent.eu/elden-ring/news/elden-ring-early-game-tips

**Hypothesis.** Combat mastery may come from reading telegraphs and accepting commitment windows rather than raw stat growth alone. Open routing may transform difficulty walls into a strategic choice among persistence, exploration and later return.

**Confounds.** Souls legacy, worldbuilding, boss spectacle, large content volume, community discovery and multiplayer discourse.

**Smallest baseline.** Experiment A: one graybox duel, telegraph→commit→evade/block→punish→death/retry. Experiment B: matched world with bypass/return-later routing.

**Falsifier.** If repeated attempts do not change anticipation/timing, or route choice does not change how players respond to excessive difficulty, the proposed transfers weaken independently.

## 7. Baldur's Gate 3 — reactivity must acknowledge mechanically different approaches
**Observed.** Larian describes choices affecting characters/outcomes, environmental interaction and D&D-derived turn-based combat. Larian also documented changing combat ordering during Early Access based on feedback/testing. Sources: https://baldursgate3.game/about ; https://baldursgate3.game/news/a-little-about-combat-stealth_3 ; https://store.steampowered.com/app/1086940/Baldurs_Gate_3/

**Hypothesis.** Agency becomes credible when mechanically different approaches cause retained state that later characters/world content acknowledge. Environmental systems can broaden problem solving beyond dialogue branching alone.

**Confounds.** D&D IP, enormous writing/cinematic/performance volume, co-op, production scale and long Early Access iteration.

**Smallest baseline.** One authored situation with three mechanically distinct solutions, persistent consequence state, one observer/companion reaction and a later acknowledgement scene.

**Falsifier.** If players regard approaches as cosmetic equivalents or later acknowledgement does not alter interpretation of the earlier choice, the reactivity claim is weak.

## 8. Factorio — automation as persistent leverage
**Observed.** Wube defines mining, logistics, production, infrastructure, research, energy, automation and defense as the product core, with progression from manual work toward automated industrial systems. Sources: https://www.factorio.com/game/content ; https://wiki.factorio.com/

**Hypothesis.** Automation is valuable because previous manual effort becomes persistent capability. Bottlenecks expose specific redesign questions, and every successful expansion can generate new system-level constraints.

**Confounds.** Huge recipe/technology graph, years of tuning, modding, co-op, content depth and high simulation quality.

**Smallest baseline.** Source→transport→processor→sink with power and one throughput target; allow redesign while retaining production history.

**Falsifier.** If automation does not shift cognition from repetitive execution toward diagnosis/architecture, or bottlenecks remain opaque, the leverage claim is weak.

## 9. Mario Kart 8 Deluxe — separate driving mastery from comeback volatility
**Observed.** Nintendo explicitly exposes drift, rocket start, mini-turbo and related techniques. Items can disrupt or boost racers and are described as turning the race; Grand Prix, Time Trial, VS and Battle support different competitive contexts. Sources: https://www.nintendo.com/sg/switch/aabp/about/index.html ; https://www.nintendo.com/sg/switch/aabp/sp/item/index.html

**Hypothesis.** A stable skillful driving core may coexist with item-driven recoverability/volatility, broadening viable social races without deleting mastery. Short races keep rematch cost low.

**Confounds.** Nintendo IP, family/local context, extraordinary audiovisual polish, large track/character catalogue and platform reach.

**Smallest baseline.** One short track with drift/mini-boost and ghost timing; matched second condition adds position-sensitive boost/disruption items.

**Falsifier.** If items merely add noise without changing comeback probability, tactical risk or rematch behavior, the catch-up hypothesis is weak.

## 10. Animal Crossing: New Horizons — place attachment and a low-pressure return promise
**Observed.** Nintendo describes self-paced gardening, fishing, collecting, decorating and resident relationships. Time of day and seasons follow real time; the island develops persistently from sparse beginnings. Sources: https://animalcrossing.nintendo.com/new-horizons/explore/ ; https://www.nintendo.com/us/store/products/animal-crossing-new-horizons-switch/

**Hypothesis.** Persistent decoration/collection may turn routine actions into place attachment, while real-time changes create a gentle reason to return instead of continuous session pressure.

**Confounds.** Brand/characters, social sharing, release-era context, content volume and Nintendo audience.

**Smallest baseline.** One persistent small space with several daily activities, decoration, collection log, one resident acknowledgement and a next-session real-time change.

**Falsifier.** If players do not develop routine/place ownership, or return intent is only checklist completion, the attachment/return hypothesis is weak.

## 11. Candy Crush Saga — one stable action grammar, many recontextualized board problems
**Observed.** King describes switching/matching across a long level sequence. Official community guidance describes adjacent swaps, three-or-more matches, level-specific goals, move limits, blockers and special candies. Sources: https://www.king.com/game/?language=en ; https://community.king.com/en/candy-crush-saga/discussion/584247/how-to-play

**Hypothesis.** A tiny control vocabulary can stay strategically variable if goals, blockers and move scarcity repeatedly change which local swap is valuable. Cheap retries fit interrupted mobile sessions.

**Confounds.** User acquisition, free-to-play monetization, live ops, social progression, brand familiarity and years of level tuning.

**Smallest baseline.** Ten original match-3 boards with one swap rule, two goal types, blockers, move limits and one special-piece interaction; no monetization or energy.

**Falsifier.** If board goals/blockers do not materially alter move evaluation or retry behavior, the stable-rule/recontextualization hypothesis is weak.

## 12. Beat Saber — an embodied perception-action rhythm loop
**Observed.** Meta describes slashing, ducking and dodging to the beat while matching note color and direction. Levels are handcrafted to music and use visual effects plus haptic feedback. Sources: https://www.meta.com/experiences/beat-saber/1304877726278670/ ; https://beatsaber.com/

**Hypothesis.** Directional whole-arm movement may bind beat prediction to motor learning more tightly than non-spatial rhythm input. Immediate visual/audio/haptic feedback may make timing error unusually legible.

**Confounds.** VR novelty, hardware affordances, licensed music, fitness appeal, spectator/video appeal and high audiovisual craft.

**Smallest baseline.** One 60–90 second original-audio VR beatmap with direction/color notes, dodge obstacles and immediate timing feedback.

**Falsifier.** Compare with a matched non-spatial rhythm control. If embodied mapping does not change anticipation, motor learning or replay intent, the transfer is weak.

## 13. Cross-reference synthesis
The twelve references do **not** converge to one universal core loop. They do reveal a more useful repeated structure:

```text
small action grammar
+ consequential context
+ rapid feedback
+ repeated reinterpretation over time
```

But the context is radically different:

```text
CS2        information + lethal round commitment
Dota 2     roles + economy + shared objectives
Fortnite   survival + uncertainty + live/social ecosystem
Minecraft  persistent world transformation + self-authored goals
GTA V      cross-system open-world affordances
ELDEN RING enemy commitment + route freedom
BG3        reactive state + acknowledged consequence
Factorio   automation + bottleneck diagnosis
Mario Kart driving mastery + comeback volatility
Animal Crossing persistent place + real-time return
Candy Crush goal/blocker/move-budget recontextualization
Beat Saber embodied rhythm mapping
```

This is still a **hypothesis map**, not a transferable design law.

A second repeated result is equally important: commercial success is heavily multiplexed. Brand/IP, community/network effects, content scale, live operations, expression quality, distribution, hardware and social context can all contribute independently of the smallest mechanic. R2 must therefore reproduce **one causal claim at a time**, not imitate the visible surface of a hit product.

## 14. Direct-play gate
No first-person feel/experience claim is admitted from this desk teardown.

```text
combat feel          PENDING_DIRECT_PLAY
racing feel          PENDING_DIRECT_PLAY
embodied rhythm      PENDING_DIRECT_PLAY_HARDWARE
player tension       PENDING_DIRECT_PLAY
perceived agency     PENDING_DIRECT_PLAY
place attachment     PENDING_DIRECT_PLAY
replay desire        PENDING_DIRECT_PLAY
```

Public videos/manuals/product pages may support observable mechanics and product structure, but they do not substitute for playing under the intended input/hardware conditions.

## 15. Standing and next frontier

```text
R1 Desk Teardown Wave 1    COMPLETE
R1 Direct Play             PENDING
R2 Baseline Reproduction   NOT_ADMITTED
ProductSelected            false
G0Entered                  false
RuntimeAgentRequired       false
```

Next work should be **access-aware direct play**, not implementation. Recover which of the twelve can be run lawfully on current equipment/accounts; play them under a frozen observation sheet; keep unavailable console/VR references in the set with experiential standing pending. Only after direct-play evidence may R1 nominate a small number of specific causal claims for R2 reproduction.
