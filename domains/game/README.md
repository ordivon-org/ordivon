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

Current first-party games: NONE. Station Zero, Causal Lag, Veilwild, Casefile,
old playable experiments and generic prototypes are retired from active source.
They remain recoverable from Git history only, not product dependencies.

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

## Native composition acceptance

G06 in planning/lego-plan-r1.json registers a bounded native-Godot
assembly verifier, not a new game or engine. Run mise run test:native for
actual scene/resource configuration, action transitions, native Signal-to-UI
feedback and resource/scene replacement. The fixture lives at
test/fixtures/native-godot-assembly. No products or experiments were added.

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
