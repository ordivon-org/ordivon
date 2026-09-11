---
schema_version: 1
id: game.r0.success-universe.20260911
title: Ordivon Game — R0 Success Universe 2026-09-11
type: research-decision
profile: product-discovery
lifecycle: active
source_role: current-r0-success-universe
visibility: public
owners:
  - ordivon-game
updated: 2026-09-11
summary: Corrected R0-A success universe. Observe broad current and durable game-success surfaces before feasibility filtering; derive archetype coverage separately and demote cheap baseline candidates to learning-order aids only.
evidence_status: externally-grounded
readiness: R0ABC_INITIAL_COMPLETE_R1_REFERENCE_TEARDOWN_ADMITTED
---
# R0 Success Universe — 2026-09-11

## 0. Correction
The prior R0 prematurely used small-scope reproducibility to decide which games should be studied first. That conflated **reference value** with **reproduction cost**.

```text
Success Universe
  -> Archetype Map
  -> Representative Reference Stack
  -> Learning Order
  -> R1 Teardown

UniverseMembership != LearningOrder
CheapBaselineSet != RepresentativeSuccessUniverse
```

Balatro, Vampire Survivors and Mini Metro remain useful cheap baselines. Their earlier status as the first R1 set is superseded. R1 is held until representative stacks are derived from the wider universe.

## 1. Source surfaces
These measurements are deliberately not scalarized into one fake global ranking.

- Steam Top Sellers US: **complete current Top 100 by revenue**. https://store.steampowered.com/charts/topselling/US
- Steam Most Played: **complete current Top 100 by current players**. https://store.steampowered.com/charts/mostplayed/
- Xbox Most Played US: official Microsoft Store current first page is exactly 1–50 of 476. An initial local serialization used `|` as a delimiter and therefore split titles containing `Xbox Series X|S`; that embedded capture is explicitly invalidated. The corrected exact 50-title surface is retained separately in `evidence/acceptance/game-r0-xbox-most-played-20260911.json`. https://www.microsoft.com/en-us/store/most-popular/games/xbox
- PlayStation August 2026: official PS5 Top 20 US/Canada, Top 20 EU and F2P Top 10. https://blog.playstation.com/2026/09/04/playstation-store-august-2026s-top-downloads/
- PlayStation full-year 2025: official complete yearly PS5, PS4, PS VR2 and F2P top-download tables for US/Canada and EU. This annual surface counterbalances one-month launch/discount effects and adds durable evidence for fighting, co-op, VR/rhythm and older-platform play. Exact lists are retained in `evidence/acceptance/game-r0-playstation-2025-annual.json`. https://blog.playstation.com/2026/01/14/playstation-stores-top-downloads-of-2025/
- Nintendo: official worldwide lifetime unit-sales leaders as of 2026-06-30, Switch Top 10 plus listed Switch 2 leaders. https://www.nintendo.co.jp/ir/en/finance/software/switch.html and https://www.nintendo.co.jp/ir/en/finance/software/index.html
- Mobile August 2026: Sensor Tower worldwide App Store + Google Play revenue/download charts; third-party Android markets excluded. Source prose exposes the top five names on each list while its image contains the full top 10. https://sensortower.com/blog/top-10-worldwide-mobile-games-by-revenue-and-downloads-in-august-2026

Exact observed title lists are retained in `evidence/acceptance/game-r0-success-universe-20260911.json`.

## 2. What the complete Steam Top 100s falsify
The two complete Steam surfaces simultaneously contain competitive shooters, MOBAs, battle royale/extraction, survival craft, open-world action, MMORPG/ARPG, CRPG, sports, vehicle simulation, grand strategy/4X, management simulation, automation/factory, sandbox/UGC/social worlds, co-op PvE, asymmetric horror, roguelike/card strategy, life simulation and viral/experimental titles.

Therefore a first research portfolio made only of compact indie loops is **not representative of successful games**.

Current rank also mixes maturity, launch effects, discounts, major updates and live-service spend. Counter-Strike 2 can sit beside one-week launches in the same revenue Top 100. Rank is evidence of market position in its own window, not a causal design explanation.

## 3. Cross-platform corrections
Nintendo's lifetime table forces forms upward that a PC concurrency view underweights: Mario Kart 8 Deluxe 71.53M, Animal Crossing: New Horizons 50.29M, Super Smash Bros. Ultimate 38.14M, Breath of the Wild 34.06M and Super Mario Odyssey 30.80M as of 2026-06-30.

Xbox and PlayStation keep Fortnite, Roblox, Minecraft, Call of Duty, GTA, sports, Rainbow Six and Rocket League highly visible, preserving controller, F2P, sports and cross-platform social/competitive archetypes.

Mobile adds another regime. Sensor Tower's August 2026 prose names Honor of Kings, Gossip Harbor, Whiteout Survival, Royal Match and Candy Crush Saga as the top five by worldwide revenue; Roblox, Free Fire, Block Blast!, Subway Surfers and Arrow Puzzle lead downloads. It also describes paced events, rewards, collaborations and cosmetics as important live-ops mechanisms among revenue leaders.

## 4. R0-B archetype map
This is a coverage map, not a universal genre ontology:

- competitive tactical FPS — Counter-Strike 2, Rainbow Six Siege
- hero/team shooter — Marvel Rivals, Overwatch, THE FINALS
- battle royale / extraction — PUBG, Apex, Fortnite, Escape from Tarkov
- MOBA / team strategy — Dota 2, Honor of Kings
- UGC / social platform — Roblox, FiveM, VRChat, Garry's Mod
- open-world action/crime — GTA V, Red Dead Redemption 2, Cyberpunk 2077
- action RPG / hunt / Souls — Elden Ring, Monster Hunter, Diablo, Path of Exile
- reactive CRPG — Baldur's Gate 3
- MMORPG / persistent world — FFXIV, Black Desert, ESO, MapleStory
- survival craft — Rust, Valheim, ARK, Project Zomboid, Palworld
- sandbox / creation — Minecraft, Terraria, No Man's Sky
- automation / factory — Factorio, Satisfactory
- grand strategy / 4X — Hearts of Iron, Civilization, Crusader Kings, Total War
- management / life simulation — RimWorld, The Sims, Farming Simulator, Football Manager
- racing / vehicle — Mario Kart, Forza Horizon, BeamNG, iRacing, Euro Truck
- sports — EA Sports FC, NBA 2K, Madden, MLB The Show
- party / local-social — Smash Bros., Mario Party, Gang Beasts, Among Us, Fall Guys
- life / cozy / social — Animal Crossing, Stardew Valley
- platformer — Super Mario Odyssey, New Super Mario Bros., Donkey Kong
- open-world exploration — Zelda BOTW/TOTK, No Man's Sky
- roguelike / run-based — Binding of Isaac, Slay the Spire
- card / deck strategy — Slay the Spire, Balatro, MTG Arena, Yu-Gi-Oh!
- co-op PvE — Helldivers 2, Warframe, Left 4 Dead 2, Payday 2
- asymmetric horror — Dead by Daylight
- mobile live-ops strategy — Honor of Kings, Whiteout Survival
- mobile merge/match/casual — Gossip Harbor, Royal Match, Candy Crush, Block Blast!
- endless-runner mobile — Subway Surfers
- precision arcade — Geometry Dash, Brawlhalla
- fighting / brawler — Smash Bros., Mortal Kombat X, Injustice 2, Brawlhalla
- survival horror — Resident Evil, The Forest
- real-time strategy — Age of Empires II
- cooperative adventure — It Takes Two, Split Fiction, A Way Out, Unravel Two
- VR / rhythm / embodied play — Beat Saber, Pavlov, Job Simulator
- cinematic action-adventure — Spider-Man 2, Assassin’s Creed, God of War
- live-service gacha action — Wuthering Waves, Zenless Zone Zero

The annual/lifetime pressure test also leaves explicit **coverage debt** rather than pretending completeness: pure puzzle/puzzle-adventure, stealth/immersive-sim, metroidvania, text-first/visual-novel and tower-defense forms are weakly represented in the present bounded census. They remain reopen targets for historical/genre-specific evidence rather than being inferred absent.

## 5. R0-C result and R1 boundary

The initial three-layer stacks are now materialized in [`GAME_R0_REFERENCE_STACKS_20260911.md`](GAME_R0_REFERENCE_STACKS_20260911.md) and `evidence/acceptance/game-r0-reference-stacks-20260911.json`.

For each materially important archetype, the stack separates:

```text
Flagship reference
  = what the form can achieve at high expression/scale
Canonical mature reference
  = repeatedly validated interaction grammar
Cheap causal baseline
  = smallest lawful reproduction that can test one claim
```

Only the **cheap causal baseline** is filtered by implementation cost. Flagship/canonical membership is not.

A huge product can therefore still be studied through a tiny causal slice: Elden Ring can yield one graybox telegraph→commit→evade→punish→death/retry duel; Counter-Strike can yield one round economy/information/commitment micro-map; Minecraft can yield break→obtain→place→transform; BG3 can yield one reactive situation with multiple valid approaches.

## 6. Standing
```text
R0-A Success Universe    BOUNDED_COMPLETE_CURRENT_CENSUS
R0-B Archetype Map       PRESSURE_TESTED_INITIAL_MAP
R0-C Reference Stacks    INITIAL_COMPLETE
R1 Reference Teardown    ADMITTED_WAVE1
R1 Clone Implementation  NOT_ADMITTED
PreviousFirstR1Set       SUPERSEDED
CheapBaselineSet         [Balatro, Vampire Survivors, Mini Metro]
ProductSelected          false
G0Entered                false
```

No chart position is treated as proof of fun, design causality, transferability or commercial probability for a future Ordivon game.
