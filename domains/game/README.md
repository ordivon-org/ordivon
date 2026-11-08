---
schema_version: 1
id: game.start
title: Ordivon Game LEGO
profile: research
lifecycle: active
source_role: canonical
visibility: public
owners: [ordivon-game]
summary: Source-bound Game LEGO discovery without retained first-party games.
---
# Ordivon Game — reusable LEGO, no legacy games

Current independently released and Human-qualified first-party games: NONE.
Room Encounter (Godot) and Orbit Collector (Bevy) are playable **native technical
examples**, with Linux/Windows Room Encounter export entrypoints. Retired
Station Zero, Causal Lag, Veilwild and Casefile source remains recoverable
from Git history only, not as current product dependencies.

## Current three Game workstreams

The active agent operating contract is [AGENTS.md](AGENTS.md): (1) semantic
decomposition, (2) directory/naming representation, (3) upstream Game LEGO
discovery and consumer-verified prototype composition. Do not confuse an
upstream addon listing or a proposed composition with an installed Game.

Inspect seven source-backed composition hypotheses without installing anything.
Two additional existing native consumers now appear directly in query results:
a three-room Godot encounter with rules/HUD/CC0 audio, and an avatar
appearance-only PackedScene swap. The latter is an executed **component**,
not an independently playable game:

    pnpm composition:inspect
    pnpm composition:inspect -- --id native-action-loop
    pnpm composition:inspect -- --engine bevy
    pnpm composition:inspect -- --id room-encounter
    pnpm composition:inspect -- --id kenney-avatar-appearance
    pnpm composition:inspect -- --id branching-dialogue-gate

The query source resolver is a **pure function** in
`src/prototype-composition.ts`; the original stable CLI remains an I/O
adapter in `scripts/prototype-composition-query.ts`. Component status is
source-supplied, not a synthetic verification certificate: `NATIVE_SUBSET_EXECUTED`
means a bounded game slice; `NATIVE_COMPONENT_EXECUTED` means only one
replaceable presentation component.

Plans are in `planning/prototype-composition-candidates-r1.json`; provider
source evidence is already in the Game knowledge index. One Godot-native
micro-loop is executable today via `mise run test:native`; external
art and AI additions remain independent candidates; native sound and Dialogue Manager narrative have executable example consumers.

## Directly reusable LEGO

The natural-owner planning/lego-plan-r1.json records the existing source-bound
responsibilities; it is not a second runtime registry:
- external game/engine/scientific reference retrieval;
- mechanism interaction experience retrieval;
- derived mechanism relationship retrieval;
- failure and counterexample retrieval;
- read-only query tools and optional non-exhaustive theme views.

Use from this directory:

    pnpm install --frozen-lockfile
    pnpm knowledge:external -- --type sources --q curiosity
    pnpm knowledge:mechanisms -- --mechanism knowledge-progression
    pnpm knowledge:relationships -- --q exploration
    pnpm knowledge:counterexamples -- --q failure
    pnpm knowledge:counterexample-themes -- --q local
    pnpm check

The five `scripts/*-query.ts` files remain stable CLI and consumer entrypoints.
Their shared, pure input parsing policy lives in `src/query-input.ts`:
individual queries still own their source datasets, filter semantics and result caps.
The internal module does not claim Game design authority or create a query registry.
G05 is a read-only interface adapter, not a verifier: retrieving a record does
not establish a Game behavior or proof. G06 owns bounded native-Godot tests.

G03 relationship queries derive from the authoritative Experience Library and
authored Relationship Spec using the existing pure source-byte projector. The
stable knowledge:relationships CLI loads these inputs on demand, preserving
source digests and query results. The redundant 17,184-line generated snapshot
and manual publication command are retired; no new registry replaces them.

## Knowledge layout

`knowledge/` holds source-grounded datasets, experience records, conditional
relationship projections and counterexamples. These are **evidence and advisory
retrieval data, not normative standards**. Existing `scripts/*-query.ts` CLI
entrypoints remain stable; their shared filesystem reading is implemented by
`src/knowledge-file.ts`, while each query owns its matching semantics.

## Counterexample projection boundary

`src/counterexample-projection.ts` resolves Experience → Counterexample →
Theme references as a pure projection from supplied records. The existing
counterexample query CLIs own data loading, filters and result claims. Unknown
references remain failures, not fabricated evidence. `src/query-input.ts`
holds pure query filter policy while `scripts/cli-argument.ts` reads
`process.argv` only for existing CLI entrypoints.

## Native composition acceptance

G06 in planning/lego-plan-r1.json registers a bounded **runnable Godot
composition example**, not a registered game or engine. Run mise run test:native
for actual scene/resource configuration, action transitions, native Signal-to-UI
feedback and resource/scene replacement. The executable example lives in
examples/native-composition with its own acceptance test. It has a composition
root, grid rules, configuration Resource and interchangeable state-view scenes.
No historical product or generic game framework was restored.

The current Godot Grid scene also consumes one Kenney CC0 TextureButton,
which changes existing rules, view and the **existing** MovementAudio. It
does not add a second audio backend. Run `mise run test:native`; source
PNG and exact provenance are stored alongside the scene.

## Native narrative LEGO

G09: `examples/room-encounter/narrative/` installs upstream Dialogue Manager
v4.2.0 under Godot 4.7.2. The addon imports real `.dialogue` source;
native Control buttons select branches, while the game-state Node remains
the authority for tokens and gate rules. Run `mise run test:dialogue-native`.
An executed branching gate component does not prove a completed exploration
game, human narrative quality or shipped product.

## Owner operating contract

The detailed three-track Game engineering program, representation rules, native
composition criteria and publication loop live in [AGENTS.md](AGENTS.md).
The current boundary and external-reference decisions live in
[architecture-and-composition.md](docs/architecture-and-composition.md).

## Assembly

Choose a real consumer and target behavior. Reuse mature game engines,
scenes, resources, tools, research, mechanic combinations and native mod
interfaces; write only missing game-specific rules. Check compositional
contracts with existing types, invariants, tests or a suitable mature
formal checker. Do not turn hypothesis retrieval into a recommendation or
whole-game formal proof.

Players may replace and combine rules, scenes, data and mods through the
chosen game engine and trust environment; a new user-defined ruleset does
not need to preserve a retired official game's semantics. No Ordivon-wide
Mod Runtime, content engine, or platform is currently justified.

Remove any knowledge carrier or query that loses its real consumer. Past
existence is not a reason for preserving live code.

For all G01鈥揋11 Human and Agent tools see [current Game Owner authority](docs/authority.md).

Source-bound signed-integer proof and separate native Room evidence: [formal/README.md](formal/README.md).

## Two native operation modes

- **Human:** Launch `examples/room-encounter` with the Godot GUI; buttons and keyboard act on EncounterRules. Evaluate comprehension, difficulty and enjoyment from actual players, not from headless test output.
- **Agent:** After native editor import, run `godot --headless --path examples/room-encounter --script res://agent_episode.gd -- --actions attack,advance`. The schema-v2 prefixed JSON now defaults to player-visible Godot HUD/dialogue (privileged snapshots require explicit --observation debug) from the **same** Godot scene, with no claim of screenshot perception or persistent interactive agent sessions. Use `mise run test:agent-episode` for the actual native acceptance. Full instructions: `examples/room-encounter/README.md`.

This is a concrete G11 native consumer port rather than a reusable Game-wide runner or a new runtime service.
