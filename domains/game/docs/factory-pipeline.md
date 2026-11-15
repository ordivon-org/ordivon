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

**Supported native line A — Godot technical preview:** mise run factory:validate:godot executes live TypeScript readers, upstream scene/asset substitution, Room Encounter narrative/Agent/native acceptance and appropriate signed-arithmetic model proof. The `test:agent-episode` entry imports the actual native Godot project first, including on a checkout with no local `.godot` cache; the G11 source-bound acceptance obligations and remaining boundaries are in [the task-local contract](agent-execution-contract-spec.md). mise run factory:package:room then exports official Godot Linux and Windows bundles and prints their digests. Room Encounter is only one existing exemplar, not the next game chosen by fiat.

**Delivered factory batch 02 — Beacon Relay:** The independent Godot game uses the pinned official Godot demo for Player movement, RigidBody enemy physics, InputMap, HUD, sound and source art. Native Godot content and display glue compose a four-delivery risk/return loop with increasing hazards, real collision loss, win and replay. test:beacon drives all deliveries through native input and physics. factory:package:beacon exports Linux/Windows previews with upstream MIT/OFL/CC-BY attribution. This is a second full game product, not a mechanic catalog.

**Supported native line B — Bevy executable and Linux distribution:** mise run factory:validate:bevy checks the pinned Cargo/ECS consumer and Orbit rules model. mise run factory:build:bevy creates the correctly named native binary, ordivon-orbit-collector. mise run factory:package:orbit-linux requires the native game to pass an Xvfb/Vulkan window-and-adapter smoke before claiming the Linux x86-64 verified preview archive with source receipt, instructions and licensing, and has an independent path-triggered GitHub job. This does not claim cross-platform installer or Human play evidence.

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


**Edition 001 consumption:** long-lived GitHub pre-release
https://github.com/ordivon-org/ordivon/releases/tag/game-factory-edition-001-20261109-a2598a2c
contains both Godot games for Linux/Windows. The released binaries were read back from
GitHub and started on Linux and in the Windows 11 service's native headless environment;
the latter is NOT Windows foreground Human input/audio/GPU evidence.
Actual players can report version-bound observations through the repository's native
game-player-feedback issue template. No custom feedback database is introduced.


## Orbit Collector Linux qualification — current G07 consumer contract

**Current owner:** Game. **Natural providers:** Rust/Cargo and Bevy for build and native graphics, Xvfb/Mesa/Vulkan for the CI graphical environment, GitHub Actions for published preview Artifacts. The existing G07 R2.1 contract lives in [the Game LEGO plan](../planning/lego-plan-r1.json); this section is a *consumer requirement*, not another LEGO or a workflow service.

Two outcomes must not be confused:

- **Build only:** `mise run factory:build:bevy` validates the locked Rust/Bevy source, tests the native ECS consumer, and builds `ordivon-orbit-collector`. It does not require a running display and must not assert graphics, player input, or distributable-preview qualification.
- **Verified Linux preview:** `mise run factory:package:orbit-linux` calls the *same* `scripts/package_orbit_linux.sh` used by `.github/workflows/game-orbit-factory.yml`. It requires a nonempty binary, `xvfb-run` and GNU `timeout`, a real native window and `AdapterInfo` witness, and a 14-second timeout-expiry diagnostic. Only then may it publish an archive containing source and binary digests, launch log, smoke receipt, instructions, and license. A child exiting 124 early is **not** a valid timeout witness.

**Failure and evidence boundary:** missing prerequisites => `ENV_BLOCKED`/nonzero; absent or failed native window/adapter smoke => failure/nonzero; both must suppress `ORBIT_FACTORY_LINUX_PREVIEW_READY` and a current candidate archive. The native negative tests in `scripts/test_orbit_package_contract.py` check missing tools and premature 124; they do **not** simulate a GPU. A successful CI Xvfb smoke does not establish actual player-visible frames, Windows operation, physical GPU performance, or Human enjoyment. Preserve `UNKNOWN` for those claims.

**Recheck the actual consumer:**

```sh
cd domains/game
mise run test:orbit-package-contract
mise run factory:build:bevy
mise run factory:package:orbit-linux  # only on a host with qualified graphics
```

The separate native GitHub workflow is the remote graphical-acceptance and Artifact producer. Inspect its exact run SHA/status before reporting a new release or real player acceptance. Generic `mise run verify` does not imply Linux graphical packaging passed.

**Historical incident (closed code change, not an instruction to re-execute the old plan):** at SourceCut `8346863be965da34371944679d063fd9fd0358ac`, the old packaging task could print `NOT_RUN` and `READY` together when Xvfb or timeout was missing. PR [#2002](https://github.com/ordivon-org/ordivon/pull/2002) replaced that path with the existing fail-closed script and shared CI invocation. The original proof discussion and completed step-by-step execution ledger remain available in Git history. Do not re-create a second package service, test farm, scheduler, or duplicate execution checklist.
