# Ordivon Game — operating contract for all Game agents

This is the **canonical Game-owner instruction**. Read the root `AGENTS.md` first.
Keep this file current with the actual `domains/game` source, native consumers
and independent product outcomes. The three long-running projects below are
the entire Game engineering scope until the user changes it.

## 0. Goal and currently observed baseline

**Goal:** make an independent game increasingly an exercise in combining
mature, replaceable mechanics, infrastructure, media, level/content, UX, and
release capabilities; author new game-specific rules only where external
capabilities and native engine primitives do not satisfy the desired behavior.

**Existing evidence (2026-11-02; inspect current main again before work):**
- G01 source-grounded external references; G02 mechanism experiences;
  G03 rebuildable relationship projection; G04 counterexample memory;
  G05 read-only query consumers; G06 bounded *native Godot* acceptance;
  G07 a Bevy-native product assembly; G08 native Godot movement audio feedback.
  G07/G08 are source/consumer-qualified but not human-playtest proofs.
  The authoritative inventory is
  `planning/lego-plan-r1.json`, not this prose.
- `src/` contains query input policy, knowledge file reading, pure graph
  derivation and counterexample projection. `scripts/` are CLI/File-I/O
  adapters. `knowledge/` holds source-bound material and derived views.
- There is **no current first-party product**. Do not restore retired
  Station Zero, Casefile, Causal Lag or Veilwild source as an implicit product.
  A native Godot fixture is not a finished indie game.
- Mechanism relationships and external examples are **hypotheses**, not
  recommendations, player preference evidence, engine standards or proof
  of game-quality transfer.
- Other agents may be relocating `meta/next/domains/game` frozen protocol
  material. That is not an invitation to move version-bound R7 inputs:
  first inspect real experiment consumers, SourceCuts and open PRs.

**Natural truth owners:** Git for source/commits; the current engine and
dependency lock for executable behavior; original provider and license for
external assets; native game process and playtest evidence for product behavior;
GitHub required checks/merge queue for publication; Host Work for task
continuity. This file is guidance, not another registry or authority.

## 1. Project A — semantic decomposition and high-cohesion / low-coupling

Start with **Parnas information hiding**: a module boundary conceals one
independently changing design decision, not a folder, file, class or Agent.
Use Design Structure Matrix (DSM) **only when actual dependency evidence changes
a split**. Preserve the smallest stable game-native interface.

Current owner seams:
| Change reason / responsibility | Native source or interface | Dependents / acceptance |
|---|---|---|
| External reference selection | `knowledge/game_external_knowledge_base_r1.json`; external-knowledge query | G01/G05 CLI + tests |
| Mechanism observation/transfer | experience library and mechanism query | G02; human-outcome transfer remains UNKNOWN |
| Relationship inference | `src/mechanism-relationship-graph.ts` | G03 deterministic derived graph + CLI |
| Counterexample enrichment | `src/counterexample-projection.ts` | G04; failure-context and source fidelity |
| CLI parsing and file boundary | `src/query-input.ts`, `src/knowledge-file.ts`, `scripts/cli-argument.ts` | G05 bounded read-only CLI entrypoints |
| Native game state / rule / view composition | `examples/native-composition` | G06 real PackedScene/Resource/Signal acceptance |
| Bevy rules and native ECS app | `examples/orbit-collector/{src,Cargo.toml,Cargo.lock}` | G07 rule/Plugin system tests and native build; GPU runtime UNKNOWN |
| Source-licensed Godot audio effects | `examples/native-composition/{main.tscn,movement_audio_feedback.gd,assets/kenney-ui-audio}` | G08 actual state Signal -> AudioStreamPlayer and replaceable WAV |

**Allowed dependency direction:** evidence source -> pure projection ->
application/CLI adapter -> native consumer. The engine/runtime owns physics,
nodes, scenes, assets, ECS, input, scheduling and lifecycle by default. Do not
reimplement these as Ordivon services. Product behavior may depend on a
versioned engine port; mechanism hypotheses must not authorize game effects.

For each proposed split or merge:
1. Bind exact `git rev-parse HEAD`, target paths, real imports/CLI/tests,
   runtime and downstream consumers; distinguish observed edges from suspected.
2. Name the independently changing decision, external assumptions, current
   public behavior and replaceable contract; compare KEEP / MERGE / SPLIT /
   DELETE / REUSE / COMPOSE, including the cost of adapter glue.
3. Extract pure rules/derivations away from I/O **only if this removes duplicated
   policy or enables proven substitution**. Preserve stable scripts and their
   output until a named consumer opts into a new contract.
4. Prove relevant preservation at the level of the claim: deterministic
   byte/hash equality for reproducible projections; targeted differential
   test for query behavior; engine-native run for scene substitution; model
   checking only for explicitly encoded transitions; installation/readback
   for effects. One passing model never proves source or player outcomes.
5. Retire redundant adapter/fixtures after live-consumer closure, not by file
   age or "future reference" value. No compatibility shim for a dead consumer.

**Do not split** a few lines of stable pure code into many decorative
crates/plugins, introduce universal Game abstractions, duplicate authority in
a "knowledge registry", or treat a derived graph as a normative ontology.

## 2. Project B — canonical directories, names and representations

Name by **domain responsibility and actual tool semantics**, not by
`new`, `temp`, `next`, team/Agent identity or implementation technique.
Keep public contracts stable and use native naming idioms:
- Game owner: `domains/game/` is canonical. `src/` = reusable pure/owner
  implementation, `scripts/` = executable CLI entrypoints, `knowledge/` =
  advisory data/projections, `test/` = native consumer fixtures and tests,
  `docs/` = current architecture/decision references, `planning/` =
  non-authoritative work projections.
- TypeScript: kebab-case modules, explicit exported names; stable external
  CLI names stay unchanged unless all consumers can be updated in one slice.
  Rust: normal crate/module conventions; never invent a Rust crate simply
  to represent one LEGO. Python: snake_case modules when Python is genuinely
  the owner consumer. Maintain pnpm and the owner lockfile.
- Godot 4.x: snake_case file/folder names, PascalCase node names, assets
  near the scenes that consume them, external add-ons in `addons/` when that
  matches their actual engine role, not a monolithic universal asset folder.
  Scene, Resource and Signal are first-class native composition interfaces.
- Bevy: Components contain game state, Systems implement bounded transforms,
  Plugins assemble app features, Resources represent owned shared state.
  Prefer real engine-supplied interfaces over a parallel Ordivon ECS.
- Media files: use meaningful asset IDs and preserve creator, exact source
  URL, downloaded revision/digest, effective license/attribution obligations,
  formats and conversion pipeline; an unverified search result is only
  a candidate. For interoperable 3D delivery, prefer glTF 2.0/GLB where
  supported, not custom scene interchange.
- Legacy/frozen SourceCut inputs and externally consumed exact paths are
  **protocol identities**, not free cosmetic rename targets. First migrate
  their real readers and assertions, then delete old sources if closure is
  established. Do not rewrite frozen historical claims.

A physical move is warranted only when a new location improves change isolation,
consumer discovery, or replacement, with a concrete old->new reader map.
For each move, use `git mv`, update source-reading imports, CLI/docs/CI and
native resource paths, verify current consumer behavior, and inspect the Git
rename diff. If the present path is already idiomatic, **KEEP** it.

## 3. Project C — external base LEGO discovery and actual game composition

### 3.1 Capability versus catalog versus release

A **candidate** (URL or reference) is not an installed component, an
admitted R2.1 LEGO, a licensable shipped asset or a composable game.
Track provider identity, native interface, version range, license,
source/consumer evidence, assumptions and unknowns in the Game owner's
existing knowledge/projection carriers. Avoid a second database, generic
Game registry, package manager, runtime, broker or machine-wide taxonomy.

For a formally **DECLARED/ADMITTED** LEGO, instantiate the effective typed
R2.1 contract from `.agents/skills/recursive-lego-calculus/SKILL.md`:
`ell=(I,O,S,pre,post,inv,eff,c,epsilon,prov,unfold)`. It must state real
effect authority, cost/approximation or scoped typed UNKNOWN—not fabricated
zeros. For raw candidate search, use a lightweight identity/source/role/seam
record without falsely declaring it formally admitted.

Always discriminate SOURCE / CONFIGURED / INSTALLED / EXECUTED / CONSUMER /
FORMAL / CURRENTNESS; separately record product playtest outcome. Evidence
grades OBSERVED / DECLARED / DERIVED / VERIFIED / UNKNOWN / FALSIFIED are
not interchangeable. External legal and runtime compatibility checks are
real integration obligations, not ornamental compliance tests.

### 3.2 Priority upstream building blocks

Check the **official current** documentation and the owner source before
selecting an exact version:
- **Godot** for scene/resource/signal composition, content authoring and
  bounded rapid game prototyping; existing G06 is its concrete native seam.
- **Bevy** for Rust ECS/Data-oriented architecture and Plugin-based assembly
  when its actual feature/runtime profile fits the product.
- **Rapier** for Rust 2D/3D physics instead of implementing collision/rigid
  bodies, with exact Bevy plugin/engine compatibility proved at selection.
- **Khronos glTF 2.0** for portable 3D model/scene delivery; not a scripting,
  gameplay or whole-art-pipeline format.
- **Kenney CC0 game assets** as a source of potential art/audio prototypes;
  verify license on the exact asset page, not only an umbrella listing.
- Game-specific level editors, music/audio tools, UI systems, localization,
  animation, narrative and accessibility capability providers are acquired
  **on demand**; availability, licensing and conversion must be checked before
  a product dependency is established.

Known external references:
- https://bevy.org/learn/quick-start/getting-started/ecs/
- https://bevy.org/learn/quick-start/getting-started/plugins/
- https://docs.godotengine.org/en/4.7/tutorials/best_practices/project_organization.html
- https://rapier.rs/docs/
- https://registry.khronos.org/glTF/specs/2.0/glTF-2.0.html
- https://kenney.nl/support
- https://doi.org/10.1145/361598.361623

Current Game composition evidence now includes three distinct native cases:
`examples/native-composition/` (Grid scene + native audio),
`examples/room-encounter/` (three-room combat with tunable rules/HUD and
native audio), and `examples/kenney-visual-composition/` (two-image
appearance substitution only). `NATIVE_COMPONENT_EXECUTED` must never be
promoted to a playable game outcome. Inspect with the **existing**
`pnpm composition:inspect`, which now uses a pure, source-bound projection
`src/prototype-composition.ts` behind its existing CLI entrypoint. Do not
invent an engine-neutral execution registry or a new gameplay product.

For directly inspectable, **source-backed prototype assembly candidates**, use
`pnpm composition:inspect` and
`planning/prototype-composition-candidates-r1.json`. These are Game's
advisory composition hypotheses and not a second provider registry.
The native Godot path is now `examples/native-composition/`; Bevy's
`examples/orbit-collector/` is a separately owned native Rust App.
A compiled Bevy prototype is not evidence of actual desktop play or human fun.

Use `knowledge/game_external_skill_watchlist_r1.json` for optional method
discovery, not as trusted executable instructions or a product authority.
Existing method Skills `compositional-contracts`,
`design-structure-matrix`, `ck-design`, `causal-intervention`, and
`recursive-lego-calculus` are sufficient until a recurring, actually
demonstrated Game-specific gap justifies another Skill.

**Executed third-party Game media seam:** `examples/native-composition`
consumes a pinned Kenney CC0 UI button via native TextureButton and reuses
the **single existing** MovementAudio component with its two CC0 clips.
Do not re-add the duplicate audio controller or copy a full asset pack:
source-asset provenance and actual consumer are documented next to the scene.

### 3.3 Compose through native interfaces and explicit obligations

For a real product requirement, choose ONE primary engine/product environment
first. Use this order:

**Gameplay contract -> engine capability -> native ports -> media/content
assets -> minimal game-specific glue -> native executable -> playtest ->
publish**.

A candidate assembly must describe:
1. **Product goal:** target player, session length, platform, controls,
   experience hypothesis and named observation.
2. **Modules:** gameplay mechanics, player/enemy/world state, actions,
   rules, level composition, save/runtime effect, audio, art, UI/UX,
   narrative and accessibility **only where actually required**.
3. **Assume/guarantee seams:** who supplies each input, event, state, asset
   schema, update order and failure behavior; which component guarantees what;
   whether the replacement strengthens assumptions or weakens guarantees.
4. **Native implementation:** actual Godot PackedScene/Resource/Signal or
   Bevy Component/System/Plugin interfaces, not a generic "LEGO executor".
5. **Evidence:** exact source revisions/licenses, lockfile, asset manifest,
   replayable build, native run and targeted action/transition or physics
   tests. Human enjoyment/readability claims need independent user evidence.
6. **Substitution:** replace at least one real component or asset through the
   native interface, then check invariants and visible output. Mark unproven
   assumptions UNKNOWN; do not veto novel mechanics from advisory records.

**Minimal assembly demonstration already in the repo:**
`mise run test:native` exercises real Godot gameplay and sound PackedScenes, Resource-configured
player variants, legal/illegal actions, finite-state rules, Signal-driven
feedback and presentation scene substitution. It establishes only G06's bounded
contract; G08 adds a source-qualified, user-input-driven AudioStream effect.
G07 is the separate Bevy ECS/Plugin game example (`cargo test --locked` and
`cargo check --locked --all-targets` in its own Cargo root), not a new engine.
Neither is a launched indie game. A future playable 5-minute product must
have its own playable build and product evidence; never promote fixture PASS.

**Reusable dialogue LEGO assembly:** the already-installed 4.2.0 upstream
Dialogue Manager provides branch/condition evaluation, while
`examples/room-encounter/narrative/gate_state.gd` derives room-clear eligibility and calls only EncounterRules.advance;
native Control/Buttons own presentation. Inspect the
`branching-dialogue-gate` record through the **existing**
`pnpm composition:inspect -- --id branching-dialogue-gate`.
That is a native integrated consumer, not a human-playtested full game.
The separate `dialogue-led-exploration` remains DESIGN_CANDIDATE:
a connected room narrative does not prove art, music, localization or player value. Never create a second DSL,
story-state database or duplicate Game G09.

Narrative native consumer G09:** `examples/room-encounter/narrative/`
uses the current upstream MIT Dialogue Manager v4.2.0 with an exact source
pin, its ordinary `.dialogue` importer and runtime, and one Godot 4.7.2
project. The scene Control/Buttons own choice presentation; a separate
game-state adapter only derives eligibility from EncounterRules, projecting through a
native `state_changed` Signal. The addon supplies branch and condition
evaluation; `mise run test:dialogue-native` checks native import,
legal room advance, leave branch and native door routing. Do **not**
introduce an Ordivon dialogue DSL, duplicate renderer/backend or claim
story quality, accessibility and a shipped product from a headless test.

**Native Game save/resume G10:** the actual examples/room-encounter
scene composes Godot ConfigFile with a separate rule-owned checkpoint
validation contract and UI Save/Load buttons/keys. Audio consumes explicit
action_accepted signals, not state changes or inferred turn increments:
a restored run cannot sound like an attack. The real test:encounter
consumer verifies native readback and atomic rejection. Extend the existing
consumer rather than building another generic save service. Human playtest,
power-loss durability, migration and shipped quality remain UNKNOWN.

**Composition criterion:** for required property P and components A,B,
the environment must discharge each required precondition/assumption, their
outputs and effects must be compatible, and observable composed behavior must
refine P. Testing A and B individually does not prove P for A+B. When a seam
cannot yet be proven, use one cheap falsifiable graybox prototype rather than
a universal proof claim or an enormous synthetic test suite.

## 4. One complete work loop (not a repeated plan-only cycle)

1. Inspect current `origin/main`, PRs, owned Work, exact SourceCut,
   consumers and external provider versions before taking a slice.
2. Identify the highest-value broken consumer frontier among A/B/C.
   Prefer DELETE -> REUSE -> COMPOSE -> EXTEND -> CREATE. Stay in Game owner
   paths unless an actual explicit cross-owner contract requires more.
3. Implement the full smallest *consumer-visible* end-to-end improvement:
   code/asset or justified deletion, real reader updates, relevant
   machine-verified/native behavior, source commit and publication.
4. Check `mise run game:verify` at repository root (or the current root task)
   and `mise run verify` inside this directory as applicable; verify
   engine-native scene acceptance, not merely TypeScript unit tests.
5. Use the existing GitHub PR + required checks + merge queue; preserve
   branch protection. Publish only what evidence supports, inspect merge
   result and newer `main` before claiming SOURCE merged or installed.
   Do not create a release pipeline, CI framework or manual policy bypass.
6. Update `planning/lego-plan-r1.json` **only when an independently
   contractable responsibility truly changes**; record consumer and evidence
   truth, not file counts. Delete completed redundant wrappers, unused
   generated products, dead worktrees and branches only after actual
   consumer/active-Job closure.
7. Continue to the next known high-value Game frontier while budget and
   execution permit; leave one exact Work handoff with accomplished vs
   unknown source/installed/product states. Do not stop at "recommendation".

**Non-goals:** universal Game framework; infinite asset mirroring; copying
unreviewed third-party assets into source; presuming "fun" from a design
score; rebuilding physics/renderer/ECS/license tools; preserving dead game
archives; broad reroutes of historical frozen protocols; tests whose only
purpose is asserting that a documentation paragraph exists.

## Native Room Encounter composition (2026-11-03)

G09 narrative and G10 ConfigFile now run in one Godot 4.7.2 product scene with rules, input, audio, and replaceable HUD. Upstream pinned MIT Dialogue Manager was relocated using git mv (no duplicate vendor source); unused standalone narrative project removed. Dialogue GateState derives its only token from EncounterRules.phase=cleared and requests only EncounterRules.advance. Door UI and N/Enter request dialogue choices rather than bypassing them. mise run test:dialogue-native exercises the actual combined consumer. Human narrative quality and final indie-game shipment remain unverified. Prefer native scene composition over new orchestrators or duplicated engine wrappers.
