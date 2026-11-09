---
schema_version: 1
id: game.start
title: Ordivon Game Factory
profile: engineering
lifecycle: active
source_role: canonical
visibility: public
owners: [ordivon-game]
summary: Assemble playable games through a native source-to-artifact production line.
---
# Ordivon Game Factory

**Mission:** repeatedly assemble, validate and deliver playable game compositions from existing mature LEGO. A factory output is an executable product or bounded product fixture, not another catalog, a local LEGO optimization or a historical thesis debate.

Read the [factory production contract](docs/factory-pipeline.md), [Agent instructions](AGENTS.md) and [consumer authority](docs/authority.md).

| Station | Input → output | Native supplier |
| --- | --- | --- |
| Intake | player outcome, platform, action loop → one product brief | Game owner |
| Supply | requirements → engine, verified providers/assets and licenses | existing Game source knowledge, upstream native engines |
| Compose | parts → real scene/ECS application | Godot Scene/Resource/Signal or Bevy App/Plugin |
| Verify | runnable candidate → actual consumer test receipt | existing Godot/Bevy tests, targeted formal when needed |
| Package | tested source → native platform artifact and checksum | built-in Godot exporters / Cargo |
| Deliver | revision and artifact → GitHub CI/artifact | protected repository checks + Game factory workflow |
| Learn | real player/Agent consumption → fix, replace, delete or next batch | game-specific evidence, not generic proxy scores |

## Run an existing factory line

From domains/game:

    mise run factory:validate:godot
    mise run factory:package:room
    mise run factory:package:beacon
    mise run factory:validate:bevy
    mise run factory:build:bevy
    mise run verify

Beacon Relay is production batch 02: an independent Godot game composed from a pinned MIT-licensed official demo and game-specific pickup, delivery, escalation and replay. Native input tests and Linux/Windows exports run through factory:package:beacon. Room Encounter (Godot) remains the earlier technical preview, not a mandatory game product. Orbit Collector (Bevy) is an independent native Rust/ECS build line, not an installer release. Both are replaceable product consumers.

Available source-read interfaces (inputs only): pnpm knowledge:external, pnpm knowledge:mechanisms, pnpm knowledge:relationships, pnpm knowledge:counterexamples, and pnpm knowledge:counterexample-themes.

G01–G11 in planning/lego-plan-r1.json are available capabilities/evidence, not mandatory manufacturing stations. The knowledge/*.json corpus and existing read-only queries are inputs, not a separate game product authority.

Pre-November PC01/PC02/PC03 dossiers, mechanism-census documents, historical experiments and the unconsumed prototype-composition query have been retired from the live tree. Exact historic revisions remain in Git; old EXECUTE_NEXT fields must not schedule current production work. Frozen R7 protocol/schema remain solely for their existing isolated research selftest.
