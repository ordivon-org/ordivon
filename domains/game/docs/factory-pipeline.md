# Game Factory — current production pipeline

2026-11-08. This is a product-native assembly line, **not** an Ordivon workflow engine and not a game-selection ontology. The relevant mature sources are Godot CLI, Bevy ECS/Plugins, Unity DevOps Build Automation, Epic BuildGraph and GameCI. Use the facilities already installed and actually consumed.

## Batch contract

For one product batch, place a small build brief next to the real project source: audience/player goal, repeated action loop, target build/platform, needed mechanics/assets, composition interfaces, and observable completion conditions. Use the existing source repository as truth; do not add a central Game registry.

Either deliver a runnable product slice bound to source+assets+tests, or stop the failed composition with a named falsifier. Do not expand the source catalog, a local mechanic or engine infrastructure to avoid this decision.

| Station | Operator action | Produced result / failure condition |
| --- | --- | --- |
| Demand | choose bounded playable behavior | one real consumer and acceptance, or STOP |
| Supply | reuse compatible licensed native code, assets and ideas | exact version/provenance/interfaces; missing required input is STOP |
| Assemble | compose scene/ECS gameplay, controls, goal, content, feedback | runnable whole-loop in one real engine; broken seam is STOP |
| Test | use existing engine/game acceptance; check true consumer and key negative controls | explicit PASS/FAIL/NOT_RUN; local models cannot certify external effect |
| Package | export/build native platform artifact; include notices | nonempty loadable binary/archive, reproducible SHA256/source revision |
| Deliver | GitHub protected CI and artifact upload on supported branch | versioned downloadable technical preview; no unverified release claim |
| Feedback | target-player or Agent observations tied to the *actual* build | repair/replace/delete or enter next production batch |

**Supported native line A — Godot technical preview:** mise run factory:validate:godot executes live TypeScript readers, upstream scene/asset substitution, Room Encounter narrative/Agent/native acceptance and appropriate signed-arithmetic model proof. mise run factory:package:room then exports official Godot Linux and Windows bundles and prints their digests. Room Encounter is only one existing exemplar, not the next game chosen by fiat.

**Delivered factory batch 02 — Beacon Relay:** The independent Godot game uses the pinned official Godot demo for Player movement, RigidBody enemy physics, InputMap, HUD, sound and source art. Native Godot content and display glue compose a four-delivery risk/return loop with increasing hazards, real collision loss, win and replay. test:beacon drives all deliveries through native input and physics. factory:package:beacon exports Linux/Windows previews with upstream MIT/OFL/CC-BY attribution. This is a second full game product, not a mechanic catalog.

**Supported native line B — Bevy executable:** mise run factory:validate:bevy runs the existing locked Cargo/ECS tests and Orbit rules model. mise run factory:build:bevy builds a native executable. No cross-platform Bevy installer is claimed until a real release consumer exists.

**Whole owner** mise run verify remains the monorepo-required source gate; the optional GitHub Game factory action publishes technical-preview artifacts. It does not weaken or bypass existing required checks.

## Contract and stopping rule

Use existing typed LEGO pre/post/inv/effect/provenance only where a specific assembly seam needs it. A successful component test is not a successful composed product. Change, substitute or discard at the product boundary; source search and test framework construction have no independent production value without a consuming build.

Factory performance is the throughput of **complete usable build compositions**, with rebuild/failure cost and actual consumer fit; never count catalogs, test assertions, docs, commits or refined LEGO as factory output. Stop polishing a satisfied component. A batch is done only if its product preview is consumed at the defined stage or its named blocking hypothesis is falsified and the batch retired.

## Upstream practices to reuse

- Godot official CLI/import/export: https://docs.godotengine.org/en/stable/tutorials/editor/command_line_tutorial.html
- Bevy ECS and plugins: https://bevy.org/learn/quick-start/getting-started/ecs/
- Unity DevOps source-triggered build automation: https://docs.unity.com/en-us/devops
- Epic Unreal BuildGraph dependent build nodes and artifacts: https://dev.epicgames.com/documentation/en-us/unreal-engine/buildgraph-for-unreal-engine
- GameCI engine-native build patterns: https://game.ci/docs/cli/build/

Historical pre-November Game product/VOI and mechanism-search papers have been retired from the current tree; their frozen claims remain in Git only. R7 research protocol/source and its consumed schema are retained under the dedicated study consumer, never used as this production scheduler.
