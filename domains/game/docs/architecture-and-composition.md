# Game composition boundaries and source-cut decision (2026-11-02)

This note records **observed owner boundaries** and a bounded game-native
assembly path. It does not supersede `../AGENTS.md` or
`../planning/lego-plan-r1.json`.

## Current semantic decomposition

| R2.1 candidate / observed role | Native owner | What can change independently |
| --- | --- | --- |
| G01 external references | `knowledge/game_external_knowledge_base_r1.json` + `scripts/external-knowledge-query.ts` | Reference source set and scoped query |
| G02 experiences | `knowledge/game_mechanism_experience_library_r1.json` + query | Contextual mechanism transfer evidence |
| G03 derived relationships | `src/mechanism-relationship-graph.ts` + build CLI | Projection algorithm without changing source evidence |
| G04 counterexamples | `src/counterexample-projection.ts` + query | Contextual failure enrichment and false transfer rejection |
| G05 native read-only CLI contract | `src/query-input.ts`, `src/knowledge-file.ts`, `scripts/cli-argument.ts` | Input normalization and read boundary without duplicating each query |
| G06 native composition acceptance | `examples/native-composition` | Godot Resource, PackedScene, action rules and Signal-bound presentation substitution |
| G10 native persistence | Room Encounter rules + ConfigFile SaveSlot | Storage side effects separate from authoritative rules and accepted-action audio |
| G07 Bevy native product assembly | `examples/orbit-collector` | Rust pure rules -> Bevy ECS/Plugin/graphics source, locked cargo build + bounded native tests |
| G08 Godot movement audio effect | `examples/native-composition/movement_audio_feedback.gd`, original main scene, asset-local CC0 provenance | Actual GridRules Signal -> native AudioStreamPlayer, replaceable AudioStream and Godot execution |
| G09 native branching narrative | `examples/room-encounter/narrative/` vendored upstream Dialogue Manager v4.2.0, `gate.dialogue` and separate `gate_state.gd` | Upstream editor/compiler/conditions can change independently from game state, scene and UI |

**Observed edges:** G01/G02 source knowledge is read by G05 CLI
consumers; G02 feeds G03 derived graph and contextual G04 counterexamples;
G03 and G04 have independent CLI readers; G06 exercises engine-native
composition independently from read-only knowledge. G07, G08 and G09 have their
own installed native consumers and do not acquire G01-G05 as fake runtime
dependencies. G08 observes the Godot G06 example's *actual* rule Signal; G07
runs a separate Bevy ECS App rather than an adapter between engines. The Game graph/experience
outputs are advisory and have no authority to permit/reject a player design.

These are responsibility labels, **not** a list of physical plugins or
formally proven eleven-coordinate LEGOs. Query code already separates
pure source transforms from CLI I/O where it improves substitution. Do not
multiply modules for aesthetic symmetry.

## Naming decisions

- **KEEP** `domains/game/` as natural owner, `src/` pure policy,
  `scripts/` command adapters, `knowledge/` source and projection,
  `examples/native-composition/` native effect acceptance.
- **KEEP** existing external CLI names and bound JSON identities until a
  consumer-preserving new source cut exists; cosmetic all-at-once rename is
  negative value and breaks versioned protocol readers.
- **USE** snake_case Godot files, PascalCase nodes, and scenes with their
  directly consumed assets. Other asset types adopt their own native
  conventions and retain exact provenance. Future independent products
  use project-owned engine layouts; no `products/` folder without a product.
- **RETIRE** compatibility aliases and duplicate views when no consumer
  survives, rather than retaining `legacy/` or `archive/` trees.

## Native assembly pattern, with explicit stages

Example target: a room-gated short action prototype. This is a *recipe*,
not a statement that the prototype is currently shipped.

1. **Rules:** write a compact state/transition specification for an
   encounter: room locked -> enemy encounter -> enemies exhausted -> unlocked.
   Assign damage/cooldowns/loot as configuration, not UI scene side effects.
2. **Engine:** choose Godot Native Scene/Resource/Signal or Bevy ECS/Plugin as
   the host. Do not combine two full game engines for a trivial scene.
3. **Contracts:** use a minimal native input-action interface, a source of
   authoritative encounter state, and an event describing state changes.
   UI listens to events and cannot alter authoritative rules implicitly.
4. **Media and content:** start from verified CC0 assets or own graybox
   sources; mark each exact asset source, license and conversion.
5. **Native confirmation:** execute real scene and resource substitution,
   action-sequence invariant checks and a standalone build launch, then
   obtain real human playtest evidence about decision quality and readability.
6. **Replaceability:** swap art/view/audio/level/AI independently only where
   the native contract permits. Document each assumption not discharged
   by the new component.

Godot existing source fixture:
`examples/native-composition/{main.tscn,grid_state_view.tscn,grid_state_view_variant.tscn,configs/*.tres,assert.gd}`.
It demonstrates rules/view/resource composition but is **not** sufficient
evidence of playable room-gated roguelite quality or independent publication.

## Source selection and epistemic boundary

External base candidates are indexed in the existing Game knowledge/skills
carriers or a product-owned exact manifest when necessary; a GitHub
repository/page is not proof of install, license for its embedded assets,
engine version compatibility or compatible composed behavior. Check source,
lockfile, runtime, client consumption and product effects separately.

Sources and upstream theory:
- Parnas, *On the Criteria to Be Used in Decomposing Systems into Modules*, CACM 1972, DOI: https://doi.org/10.1145/361598.361623
- Bevy ECS / Plugins: https://bevy.org/learn/quick-start/getting-started/ecs/ and https://bevy.org/learn/quick-start/getting-started/plugins/
- Godot project organization: https://docs.godotengine.org/en/4.7/tutorials/best_practices/project_organization.html
- Godot scene boundaries: https://docs.godotengine.org/en/latest/tutorials/best_practices/scene_organization.html
- Rapier physics: https://rapier.rs/docs/
- Khronos glTF 2.0 specification: https://registry.khronos.org/glTF/specs/2.0/glTF-2.0.html
- Kenney CC0 license scope: https://kenney.nl/support

## Verification / falsification selection

Query refactor -> native Node/TypeScript tests plus unchanged result and
graph digests; path move -> real downstream import/CLI/Godot scene readback;
native assembly change -> run the Godot headless fixture with state, alternate
resource/view and bad configuration counterexamples; third-party library
adoption -> version-and-lock compatibility plus consumer execution; game
quality -> observed product playtest. No one check substitutes for the others.

To retrieve the actual owner contract, use the current
`planning/lego-plan-r1.json` and `mise run game:verify`, not a snapshot
in this note. Pending external provider adoption is explicitly UNKNOWN.

## Native save and audio refinement (2026-11-03)

Room Encounter is the actual consumer of ConfigFile and action_accepted.
Rules owns checkpoint validity, the native save-slot node only handles file
I/O, and audio no longer guesses combat input from changed turn counts.
Native test:encounter verifies readback and rejected load atomicity. This is
not a new storage framework or evidence of human playtest/production release.

## Integrated room-narrative boundary (2026-11-03)

G09 uses the same executable Room Encounter as G10, with upstream Dialogue Manager controlling text/choices and native Rules alone controlling combat/room state. The old standalone demo is retired; the upstream package is git-moved byte-identically, not duplicated. No extra quest state or runtime registry.

## Bounded Human / Agent game operation (G11)

A native test-only Agent episode port now lives in `examples/room-encounter/agent_episode.gd` with executable acceptance at `examples/room-encounter/agent_episode_acceptance.py`. It loads the real native game scene and routes actions to the existing `examples/room-encounter/encounter_rules.gd` node rather than rebuilding a second simulation. Its observation contract is an authoritative symbolic state, explicitly **not** screenshots, perception or Human preference. The transport is a single process with bounded comma-separated actions and a prefixed JSON receipt. Uninitialized scene state fails closed, so a missing Godot editor import cannot be mistaken for a successful playthrough.

Human players launch the original Godot scene and use its buttons and keyboard. Agents run bounded headless episodes; both consume the same rule authority. For detailed commands, use `examples/room-encounter/README.md`, not a second orchestrator. Godot owns engine lifecycle; Game owns local action semantics; Runtime/Harness remain separate owners of external job execution and agent coordination.

**External-first normalization:** Follow Godot's official project organization/scene composition recommendations (source assets next to their consumers, native Snake_case files, PascalCase nodes, third-party addons in `addons/`), and Bevy's official ECS/Plugin interfaces for Rust consumers. Reference sources: https://docs.godotengine.org/en/4.7/tutorials/best_practices/project_organization.html ; https://docs.godotengine.org/en/stable/tutorials/best_practices/scene_organization.html ; https://bevy.org/news/bevy-0-20/ . These upstream patterns are capability providers, not game-quality certificates.
