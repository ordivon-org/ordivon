---
schema_version: 1
id: game.authority
title: Game Owner Consumer Authority
profile: engineering
lifecycle: active
source_role: canonical
visibility: public
owners: [ordivon-game]
---
# Game Owner — current native authority

Status (2026-11-07): historical first-party named games are retired. The active Godot and Bevy examples are real native game consumers, not independently shipped Human-qualified products. The existing planning/lego-plan-r1.json contains the scoped G01–G11 R2.1 contracts and consumer evidence; it is not a second runtime registry or a formal verification certificate.

Game owns game-specific rules, mechanics, hypotheses and tests. Godot owns Scene/Resource/Signal/InputMap/ConfigFile and lifecycle; Bevy owns ECS/Plugin/System/rendering. Media, Artifact, Runtime, Harness, Security and distribution retain their external effects. Do not create another Game engine, generic Mod loader, Agent execution runtime or knowledge authority.

## Human and Agent entrypoints (run from domains/game)

| LEGO | Human | Agent / limited claim |
| --- | --- | --- |
| G01 external knowledge | Examine cited sources | pnpm knowledge:external -- --type sources --q curiosity; references only |
| G02 experiences | Read context-bound design observations | pnpm knowledge:mechanisms -- --mechanism knowledge-progression; hypothesis |
| G03 relations | Examine conditional mechanic interactions | pnpm knowledge:relationships -- --q exploration; not causality |
| G04 counterexamples | Examine documented failures | pnpm knowledge:counterexamples -- --q failure; not a global blacklist |
| G05 queries | Use existing CLI data views | pnpm check; retrieval does not authorize game effects |
| G06 Godot composition | Run godot --path examples/native-composition | mise run test:native; bounded state and scene replacement |
| G07 Bevy native product assembly | Run cargo run --locked inside examples/orbit-collector | mise run test:bevy; pure Rust/ECS source tests only |
| G08 Godot audio | Hear the native game feedback | mise run test:native; audio playback calls, not speaker evidence |
| G09 room narrative | Play choices in Room Encounter | mise run test:dialogue-native; native branching and rules |
| G10 native checkpoint | Use Save and Load in Room Encounter | mise run test:encounter; storage round-trip and validation |
| G11 Agent episode | Keep the original Room Encounter UI | mise run test:agent-episode; bounded symbolic JSON, not screenshots |

Use each examples/*/README.md for exact controls, source licensing and substitution points. Human enjoyment and accessibility require actual human-facing evaluation; a native, Agent or compile PASS cannot substitute for it.

## Source and release standing

The profiles/domains/game R1/R2/R3 JSON revisions form referenced historical evidence chains; an older input consumed by a newer view is not disposable cache. The R7 autonomous-interest study remains pre-generation. Godot release requires official export presets and version-matched export templates; Bevy compilation requires the pinned Cargo.lock. Neither build compilation nor a scene test qualifies a distributable installer. Native Linux and Windows x86_64 export tasks produce technical preview packages; standalone platform and human-use acceptance remain separate.

Use Godot snake_case source names, PascalCase nodes and native .uid / .import metadata. Preserve third-party addon licensing, Bevy ECS and source-licensed assets. Retire only with complete current consumer and source-input closure; never delete operating-system or another Owner's files.
