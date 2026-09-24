# Game Category Crosswalk — R1

Status: **WORKING EXTERNAL CROSSWALK / NOT A UNIVERSAL ONTOLOGY**  
Observed: 2026-09-14

## Why categories are not the design primitive

Platform/store taxonomies exist mainly for discovery, recommendation, competitor analysis and publishing. Valve's Tag Wizard explicitly separates genre/subgenre from visuals/viewpoint, themes/moods, features/gameplay mechanics, design ingredients, player activities and player count. Apple, Google Play and Microsoft expose overlapping but non-identical consumer-facing genre lists. GameRefinery likewise treats category/genre/subgenre as a market-research hierarchy while using defining mechanics to distinguish otherwise similar products.

Therefore Next uses **category as a crosswalk**, not as the thing from which a game must be designed.

```text
mechanism composition -> dynamics -> player experience -> product form
                                                -> market genre labels
```

A game can have several legitimate labels; a store or analytics product may still require one primary bucket for market measurement.

## Broad market/product families

The normalized union currently keeps these broad families:

| Family | Typical subfamilies / neighboring forms |
| --- | --- |
| **Action** | action-adventure, character-action, beat-em-up, hack-and-slash |
| **Adventure** | exploration, point-and-click, walking-sim, action-adventure |
| **Arcade** | score-attack, reflex, classic-arcade |
| **Platformer** | 2d-platformer, 3d-platformer, precision-platformer, metroidvania |
| **Shooter** | fps, tps, arena-shooter, hero-shooter, twin-stick, bullet-hell |
| **Fighting / Brawler** | 2d-fighter, 3d-fighter, platform-fighter, beat-em-up |
| **Role-Playing** | crpg, jrpg, action-rpg, party-rpg, tactical-rpg, mmorpg |
| **Strategy** | rts, turn-based-strategy, 4x, grand-strategy, auto-battler |
| **Tactics** | turn-based-tactics, real-time-tactics, tactical-rpg |
| **Simulation** | life-sim, vehicle-sim, space-sim, god-game, political-sim |
| **Management / Builder** | city-builder, colony-sim, base-building, farm-sim, tycoon |
| **Automation / Factory** | factory-automation, programming, logistics |
| **Survival** | survival-crafting, survival-horror, open-world-survival-craft |
| **Sandbox / Creative** | construction-sandbox, ugc, god-game, open-world-sandbox |
| **Roguelike / Run-Based** | traditional-roguelike, roguelite, action-roguelike, roguevania |
| **Card / Deck** | card-battler, deckbuilder, tcg, solitaire |
| **Board / Tabletop** | board-game, chess, tabletop-simulation |
| **Puzzle** | logic, sokoban, match-3, hidden-object, puzzle-adventure |
| **Narrative / Interactive Fiction** | visual-novel, interactive-fiction, choose-your-own-adventure, narrative-adventure |
| **Investigation / Mystery** | deduction, detective, causal-reconstruction |
| **Stealth / Immersive Sim** | stealth, immersive-sim, infiltration |
| **Racing / Driving** | arcade-racing, sim-racing, combat-racing |
| **Sports** | football, basketball, golf, tennis, extreme-sports |
| **Rhythm / Music** | rhythm, music-performance |
| **Social / Party** | social-deduction, party-game, co-op-coordination |
| **Idle / Incremental** | idler, clicker, incremental-optimizer |
| **Educational / Word / Trivia** | educational, word, typing, trivia |
| **Casino** | slots, poker-like, casino-simulation |
| **Experimental** | unusual-interface, novel-rule-form, experience |

These are **not mutually exclusive design classes**. They are a practical cross-platform vocabulary. For example, a single product may simultaneously be an Action Roguelite, Deckbuilder, Tactical RPG and Co-op title depending on which axis is being described.

## Orthogonal structural axes

Genre alone loses too much information. Every composition may additionally be described along:

- **time model:** real-time / turn-based / simultaneous / real-time-with-pause / tick / asynchronous;
- **session model:** micro-session / round / run / mission / campaign / persistent world / endless;
- **social model:** solo / local / online / co-op / competitive / teams / asymmetric / MMO;
- **world topology:** linear / branching / hub / levels / grid / graph / open world / sandbox / procedural;
- **information model:** perfect / hidden / partial / asymmetric / fog / probabilistic / deceptive;
- **control model:** direct avatar / units / system control / delegation / programmed action / language / editor;
- **progression horizon:** none / session / run / campaign / account-meta / persistent world;
- **content source:** authored / systemic / procedural / player-generated / community-generated / mixed;
- **failure model:** instant retry / checkpoint / lives / run reset / persistent loss / permadeath / recovery;
- **presentation/input:** dimensionality, camera/view, text, controller, keyboard/mouse, touch, voice, motion/VR.

The machine-readable version is `game-design-space-r1.json`; it currently records 29 broad market families, 10 orthogonal structural axes, 18 mechanism families and 424 unique normalized design elements.

## External anchors

- Valve Steam Tags / Tag Wizard — https://partner.steamgames.com/doc/store/tags
- Apple App Store categories — https://developer.apple.com/app-store/categories/
- Google Play category/tag guidance — https://support.google.com/googleplay/android-developer/answer/9859673
- Microsoft Store game genres — https://learn.microsoft.com/en-us/windows/apps/publish/publish-your-app/msix/categories-and-subcategories
- GameRefinery genre taxonomy — https://docs.gamerefinery.com/en/articles/2278730-what-are-categories-genres-and-subgenres
