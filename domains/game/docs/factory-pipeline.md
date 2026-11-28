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

**Supported native line A — Godot technical preview:** mise run factory:validate:godot executes real Godot scene/asset substitution, Room Encounter narrative/Agent/native acceptance and the bounded signed-arithmetic model proof. Advisory TypeScript/knowledge readers remain validated through the monorepo Game verify and the PR check's separate pnpm check, not redundantly in each native package. The `test:agent-episode` entry imports the actual native Godot project first, including on a checkout with no local `.godot` cache; the G11 source-bound acceptance obligations and remaining boundaries are in [the task-local contract](agent-execution-contract-spec.md). mise run factory:package:room then exports official Godot Linux and Windows bundles and prints their digests. Room Encounter is only one existing exemplar, not the next game chosen by fiat.

**Delivered factory batch 02 — Beacon Relay:** The independent Godot game uses the pinned official Godot demo for Player movement, RigidBody enemy physics, InputMap, HUD, sound and source art. Native Godot content and display glue compose a four-delivery risk/return loop with increasing hazards, real collision loss, win and replay. test:beacon drives all deliveries through native input and physics. factory:package:beacon exports Linux/Windows previews with upstream MIT/OFL/CC-BY attribution. This is a second full game product, not a mechanic catalog.

**Archived native line B — Orbit Collector (Bevy):** The completed source-to-distributed-preview experiment is retained at [the Orbit archive](../archive/orbit-collector/ARCHIVE.md), including the exact former CI, native smoke and formal model. It is not an active Game production station. Bevy remains an available mature upstream provider for future products if selected for a real consumer.

**Whole owner** mise run verify remains the monorepo-required source gate; the optional GitHub Game factory action publishes technical-preview artifacts. It does not weaken or bypass existing required checks.

## Source-qualified native bundle (manufacturing contract)

A manufacturing attempt is bound to one **clean repository-wide Git source
tree** and one native exporter/toolchain. Godot/mise can consume cascading
root configuration such as `mise.toml` outside `domains/game`; checking only
`git status -- .` from Game would accept a dirty root config as `SOURCE_WORKTREE=clean`.
Both package entries now check the **entire Git worktree** before native tests
and again before atomically publishing READY. Dirty source anywhere in that
checkout fails closed with `GAME_FACTORY_DIRTY_SOURCE_NOT_RELEASABLE` or
`GAME_FACTORY_SOURCE_CHANGED_DURING_BUILD`. Run targeted native tests while
iterating, or use a dedicated clean checkout and commit a reviewable Git source
cut before packaging. This deliberately favors source integrity over allowing
unrelated, simultaneous uncommitted changes in the **same** release checkout;
separate Git worktrees still permit concurrent Owner development.
The Game CI workflow therefore also includes root `mise.toml` in its
pull-request and main-push path filters, so toolchain/config changes
cannot silently skip the Game native consumer gate.
Neither `git rev-parse HEAD` alone nor a successful Godot process exit
proves that the produced bytes belong to a release.

The current `factory:package:room` and `factory:package:beacon` tasks are
stable `mise` entry points to the shared
[`scripts/package_godot_preview.sh`](../scripts/package_godot_preview.sh).
The script owns the common source snapshot, receipt, checksums, staging,
and publication lifecycle; each product retains its native acceptance,
export and license inventory. Each builds Linux/Windows outputs in a
disposable same-filesystem staging directory,
verifies the complete pair, and **atomically renames one complete directory**
to `dist/<product>/bundle-<source-prefix>-<attempt>/`. The directory
contains both archives, `BUILD_SOURCE.txt`, `SHA256SUMS`, and `READY`.
`BUILD_SOURCE.txt` records source commit/tree/clean status, Godot version,
observed export-template digests (or UNKNOWN), and explicitly
`RELEASE_PUBLISHED=false`. `SHA256SUMS` binds the archived binaries and
source receipt. The caller must consume only the exact
`GAME_FACTORY_BUNDLE_PATH=...` emitted after the successful rename and
verify `sha256sum -c SHA256SUMS`; an unrelated prior bundle, fixed path,
or an unverified tar/zip filename is **not** evidence of this attempt.
The source receipt is a sidecar for the **pair**, not embedded in either
individual archive; any later publisher of individual archives must retain
or link that sidecar and its exact digest relationship.

Failures preserve earlier complete bundles without publishing an incomplete
new one. The package is only `native_headless_preview`: receipt fields
`LINUX_SCOPE=native_headless_smoke` and `WINDOWS_SCOPE=export_only` make
that distinction machine-readable. Linux smoke does not certify full
gameplay, active hazard integration, GPU/audio peripherals, Windows
foreground input or Human play. A template recorded as UNKNOWN is
an incomplete provenance witness, not a verified release-ready build.
A full CI upload requires two known template digests, matching checkout
source commit, bundle manifest/digests, and fails closed otherwise.

The Game GitHub Actions workflow publishes only a **14-day technical-preview
Actions Artifact** with the exact completed bundle. It does **not** publish
GitHub Release assets. Any long-lived Release promotion must independently
bind downloaded exact bytes to the bundle's two archive SHA256 values,
identify a GitHub Release asset/tag, and read back the remote asset digest.
A release record still does not certify active gameplay or Human satisfaction.
Use the existing GitHub release and Artifact providers, not a second Game
Artifact DB or release scheduler.

Workspace cleanup remains a separate Runtime natural-owner effect.
On 2026-11-16 the two 2026-11-10 historical Game workspaces and their eight
ignored technical-preview archives were **closed after explicit business
discard approval, source-only Git refs verified 4/4, Native Runtime CAS close,
tombstone and physical-path readback** (Runtime lifecycle Host message #28300).
Those eight SHA256 values were not the same bytes as the four Edition001
Release assets; old local previews were deliberately discarded, **not**
claimed delivered or bit-rebuildable. This specific close outcome must
not be generalized: the Runtime/Harness ACTIVE-Run-vs-NativeClose
consumer-lifetime fence remains a separately evidenced system-wide defect.
Never force-close another Workspace on a mere no-active-Job finding.

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


## Archived Orbit proof and distribution

The original Orbit source, historical qualification contract and publicly distributed Windows/Linux preview remain discoverable via [the read-only archive](../archive/orbit-collector/ARCHIVE.md). No current Game build, CI or dependency update consumes this retired batch.

### Native export input identity

For the Linux factory runner, the supported x86_64 release presets use the official Godot editor's version-matched default templates under the absolute XDG_DATA_HOME (or ~/.local/share). Custom release templates, self-contained editors and the old receipt-only GAME_GODOT_TEMPLATE_DIR override are rejected rather than silently misattributed. The package gate captures editor and both template SHA256 values before validation/export and compares them again immediately before READY. A missing or changed input fails closed; the existing source and archive digest gates still apply. The before/after evidence does not prove upstream authenticity or prevent an adversarial change-and-restore during export. Windows scope remains export-only.
