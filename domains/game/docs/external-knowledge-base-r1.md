---
schema_version: 1
id: game.external-knowledge-base.r1
title: Ordivon Game External Knowledge Base R1
profile: research
lifecycle: active
source_role: derived-navigation
visibility: public
owners:
  - ordivon-game
updated: 2026-11-02
summary: First large external knowledge corpus for creative-open Game research: standards, accessibility, design theory, player research, engine practice, developer teardowns, platform feedback and Agent Skills.
evidence_status: source-grounded-first-wave
readiness: ACTIVE_EXPANDING
---
# Ordivon Game External Knowledge Base R1

## 1. Purpose

This is an **external knowledge substrate**, not a second Game constitution. External knowledge may **never become a Game constitution** merely because it is famous, formal, popular, or useful elsewhere. The current R1 corpus contains **156 source records**, **56 teardown targets**, **37 source-bound targets**, and **12 external Skill/tooling candidates**. Fine-grained transfer hypotheses extracted from those sources live separately in the Mechanism Experience Library so source registry and derived design memory remain distinct.

The ingestion rule is deliberately Creative-Open:

```text
external source
  -> classify native authority
  -> extract mechanism / method / evidence / failure mode
  -> preserve scope + confounds + currentness
  -> route to optional Skill, Pattern, experiment, or owner

never
  -> source is famous
  -> therefore new universal Game law
```

## 2. Native authority ladder

1. **Normative standard** — authoritative only inside exact native scope (for example usability concepts, web accessibility, requirements, software lifecycle).
2. **Official platform guidance** — strong implementation/release/accessibility guidance for that platform, still not Game semantic truth.
3. **Official engine documentation** — implementation substrate authority for a particular engine/version.
4. **Validated/peer-reviewed model or instrument** — evidence about defined constructs; use as a lens or measurement instrument without inflating scope.
5. **Primary developer account** — best available evidence of what one team intended, tried, cut and learned; excellent for mechanism hypotheses, weak as universal causality.
6. **Agent Skill implementation / community guide** — reusable workflow candidate; must pass local fit, trust, currentness and transferability review.

## 3. First-wave coverage

- Standards / native guidance: ISO 9241-210, ISO 9241-11, WCAG 2.2, ISO/IEC/IEEE 12207:2026, ISO/IEC/IEEE 29148:2018, ISO/IEC 25010:2023, SLSA, SPDX.
- Game accessibility: Xbox Accessibility Guidelines, Game Accessibility Guidelines, IGDA GA-SIG, Apple game HIG.
- Design lenses: MDA, Rules of Play, FADT, Machinations, GameFlow, The Rule Book, SDT/PENS lineage.
- Player evidence: PXI, GUESS, Games User Research method/playtest guidance.
- Engine/production: Godot best practices, Unity 6 practices/Input/performance, Unreal Gameplay Framework/GAS, Android performance.
- Distribution/feedback: Steam Playtest and Steam User Reviews.
- Primary teardowns: FTL, Into the Breach, Celeste, Baba Is You, DOOM, Slay the Spire, Dead Cells, Subnautica, Mooncrash, Cultist Simulator, DMC5, Halo Wars 2, Heaven's Vault, Hades, Factorio, Zelda TOTK, Pikmin 4, Mario Wonder, Game Builder Garage.
- Agent Skills/tooling: abagames Agentic Gamedev Skills, Epic Unreal Skills/Toolsets/MCP, gda Godot Skill+CLI+MCP, current sickn33 game Skills as lower-confidence comparison material.

## 3.1 Component and content-production backfill (2026-11-02)

The original 140 source records focused on game mechanisms, postmortems,
standards and methods, so they were **not** a ready-to-compose Game components
inventory. We added 15 upstream-grounded candidates: Godot 4.7 Asset Store,
native Resource/PackedScene composition, Bevy plugins and official Bevy Assets
index, LimboAI, Dialogue Manager 4, Dialogic 2, Godot AnimationTree,
Kenney pixel art/UI/audio/prototype materials, Blender, LMMS and Kdenlive.

They cover **gameplay engine/plugins, narrative, NPC logic, 2D/UI, audio/music,
3D authoring and cinematics**. Their native artifacts have different semantics:
an addon or ECS plugin is executable capability; a CC0 texture is a content
asset; Blender/LMMS/Kdenlive are authoring tools, not installed gameplay
features. Store presence, upstream docs and creator licensing are source
evidence only. No third-party module, art pack or music pack was installed
or integrated by this source backfill.

- **Game-first engine composability:** Godot Scene/Resource/Signal and Bevy
  App/Plugin/ECS remain natural owners of engine behaviors; use official
  compatibility/currentness disclosures rather than assuming cross-engine
  portability.
- **Content ownership:** choose legally usable packs and import as native
  textures, audio or scene components; authoring application licenses do not
  automatically grant rights to samples, fonts or external source content.
- **Evidence-bound prototype plans:** see
  `planning/prototype-composition-candidates-r1.json` and
  `pnpm composition:inspect`. Four examples share one source index; only the
  existing Godot action-loop fixture has local executed native standing.
- **Missing executable product:** external add-ons, music/art and complete
  story/combat integrations are still candidate dependencies, not completed
  Game products.

This is a deliberately small, decision-led source wave, not a complete
marketplace, quality ranking or new category ontology.

## 4. Mechanism Combination Experience Library

Every primary teardown should eventually yield zero or more entries shaped like:

```text
mechanisms[]
hypothesis
observed/project context
confounds[]
falsifier
transfer risks[]
cheap reproduction / ablation
source refs[]
canBlockNovelCombination = false
```

This grows the **Mechanism Combination Experience Library**. It is an analogy and experiment generator, never a recipe database or ranking system.

## 5. Priority teardown wave

P0 now includes DOOM, Celeste, Into the Breach, Slay the Spire, Factorio, Baba Is You, Hades, Zelda TOTK, Pikmin 4, FTL, Dead Cells, Subnautica, Mooncrash, Heaven's Vault, Mario Wonder and Game Builder Garage, because primary developer evidence is already bound in the corpus.

P1/P2 expands toward Minecraft, RimWorld, Dwarf Fortress, Outer Wilds, Portal, Elden Ring, Monster Hunter, XCOM, BG3, Disco Elysium, Stardew Valley, Animal Crossing, Vampire Survivors, Balatro, Fortnite, Dota 2, League, Roblox, Mario Maker, The Witness, Papers Please, Obra Dinn, Rocket League, Overcooked, Keep Talking, Katamari and others. For these, extraction remains queued until a primary developer source is bound.

## 6. Skill ingestion rule

The strongest external Skill design signals so far are:

- **abagames / exploring-game-design-space**: search structurally different mechanics, preserve stable IDs/uncertainty, reject only demonstrated dead ends, no speculative fun ranking.
- **abagames / extracting-agent-skills**: extract behavior-changing procedures from evidence, including failed projects, and gate transferability.
- **Epic Unreal Skill guidance**: Skills should be Novel, Collegial, Flexible, Durable, Agnostic and Parsimonious; volatile tool details belong in discovery/tool surfaces.
- **gda**: Skill, CLI and MCP can be different access paths to one capability surface, with a strong version-lock pattern between Skill guidance and executable.

For Ordivon:

```text
Skill = reusable advisory instructions
Tool  = local concrete execution
MCP   = transport/discovery
Owner = semantic authority
```

No layer inherits another layer's authority automatically.

## 7. Anti-capture rules

- MDA is a lens, never the Game ontology.
- GameFlow, SDT/PENS, PXI and GUESS describe/measure bounded constructs, never a universal fun score.
- GDC/Nintendo/developer postmortems are primary project evidence, not causal laws.
- Engine frameworks are implementation options, not mechanism requirements.
- Accessibility/platform guidance can be strict inside native scope without dictating game genre/form.
- Community Skills remain advisory even when popular or trusted by the Skill registry.
- Secondary articles may discover leads, but mechanism extraction prefers primary developer evidence.

## 8. Machine surfaces

- `knowledge/game_external_knowledge_base_r1.json` — source registry with scope, authority, extracted ideas, candidate uses and evidence limits.
- `knowledge/game_teardown_queue_r1.json` — large cross-genre teardown queue with axes, primary-source targets, questions and transfer risks.
- `knowledge/game_external_skill_watchlist_r1.json` — external Skill/Tool/MCP patterns and adoption risks.
- `pnpm composition:inspect` — source-backed prototype component/replacement seam inventory and explicit unimplemented gaps.
- `pnpm knowledge:external -- --type sources|teardowns|skills [--q ...] [--authority ...] [--status ...]` — bounded retrieval over those records; it never ranks, recommends, approves or rejects a game idea.

Source records also carry a coarse `sourceStrength` class such as `NATIVE_HIGH`, `PRIMARY_PROJECT_HIGH`, `EVIDENCE_HIGH`, `EVIDENCE_MEDIUM_HIGH`, `IMPLEMENTATION_MEDIUM` or `COMMUNITY_DISCOVERY`. This is an evidence-routing aid, not a universal quality score: a high-strength source outside its native scope still cannot create Game semantic authority.

The explicit next-wave gaps include more non-Western primary developer archives, sports/racing feel, horror/fear, MMO institutions/economies, ethical mobile live-ops, failed/cancelled projects, and exact primary sources for several queued games. These gaps remain search targets rather than inferred knowledge.

These are discovery/evidence surfaces. They do not select a product, rank games, close creative search, or mint Human evidence.


## Current Game-native composition inventory (2026-11-02)

The owner query has been synchronized to three existing, concrete Godot
execution consumers: `examples/native-composition` for rule/Resource/view
and audio assembly, `examples/room-encounter` for room combat/alternate
native HUD/CC0 audio and `examples/kenney-visual-composition` for two
source-licensed Kenney Abstract Platformer appearance resources. The last
one is appearance-only and must not be interpreted as a standalone game.
The project-source mirror revision and exact two PNG digests are in its
README; original licensing authority is Kenney's CC0 pack page.

There are also a Bevy native Rust source/compiled-game candidate and two
uninstalled Godot AI/narrative proposals. The source ledger has 156 records.
`src/prototype-composition.ts` projects provider references and exact
source-supplied evidence states; the CLI merely loads evidence and prints
results. No second registry or source authority exists.


## Native dialogue branch evidence (2026-11-03)

The existing `examples/room-encounter/narrative` Godot 4.7.2 consumer now
has its own `branching-dialogue-gate` composition entry. It composes the
MIT-licensed, source-pinned upstream Dialogue Manager v4.2.0 runtime with a
separate game-authoritative gate/tokens state Node and native response UI.
Its import/branch/condition/state-effect consumer is the existing
`acceptance.gd`; no new parser, asset pack, registry or service was created.
This is an executed component-level closure, not proof of an exploration
game. The larger `dialogue-led-exploration` still lacks integration into
rooms/world, content, soundtrack, save/resume and human evaluation.
