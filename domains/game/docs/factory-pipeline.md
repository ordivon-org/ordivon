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


## Orbit Linux native verified-preview contract — R2.1 refinement (2026-11-10)

This section is the **existing Game Factory product contract's scoped execution spec and implementation plan**, not a new source of truth or an extra LEGO. Global Agent engineering guidance remains [Agent Contract Execution R2.1](../../../docs/architecture/AGENT_CONTRACT_EXECUTION_SPEC_R1.md). Product G07 retains its present eleven-coordinate R2.1 declaration at [Game LEGO plan](../planning/lego-plan-r1.json); it is not renamed, re-admitted or duplicated.

**SourceCut for the discovered discrepancy:** main 8346863be965da34371944679d063fd9fd0358ac. **Named consumer:** Orbit Collector Linux preview publisher and its downloadable-artifact recipient. **Natural owner:** Game for building, graphical smoke and preview eligibility; Bevy/wgpu, Xvfb/Mesa, Git/GitHub Actions and Artifact retain their own native authorities.

### The real problem and legitimate alternatives

Two different consumer outcomes must remain distinguishable:

- **Build-only:** factory:build:bevy produces a compiled Rust/Bevy executable. It is useful even on hosts without graphical hardware. It never claims a rendered window or verified distribution.
- **Verified preview:** factory:package:orbit-linux requires a successful source-bound native Xvfb window/renderer smoke *before* it emits an archive-readiness result. Missing runtime graphical prerequisites must be ENV_BLOCKED/nonzero, not a successful unverified package. The GitHub Orbit workflow invokes the **same** Game-native packaging implementation rather than copying it.

The preceding task permitted an absent xvfb-run/timeout to print ORBIT_WINDOWED_SMOKE_NOT_RUN_NO_XVFB and still create an archive and print ORBIT_FACTORY_LINUX_PREVIEW_READY. The original shell branch was **actually reproduced** in a disposable Game workspace: a controlled fake build prerequisite plus simulated absent Xvfb yielded exit 0, an archive, NOT_RUN and READY together. That experiment is only a command-contract negative test; no native GPU rendering was simulated or claimed.

Retain the current Rust/Cargo/Z3 checks and upstream Vulkan/X11 tools. Do **not** require these tools of the separate build-only consumer. Do not invent a new Game packaging framework, Agent task engine, universal CI checker or parallel verifier registry.

### Formal contract (scoped, not a proof of actual rendering)

Let B mean the locked native binary exists, D mean both xvfb-run and timeout are discoverable, S mean GNU timeout --verbose rc=124 **and its actual TERM deadline-expiry diagnostic**, plus the real window and AdapterInfo witnesses, without fatal diagnostics, and A mean the source-bound archive exists.

The product acceptance predicate is:

~~~text
  VerifiedPreviewReady  =>  B AND D AND S AND A
  NOT D                 =>  ENV_BLOCKED and exit != 0 and NOT VerifiedPreviewReady
  B AND D AND NOT S      =>  SMOKE_FAILED and exit != 0 and NOT VerifiedPreviewReady
~~~

This is a **proposed implementation invariant and native-test obligation**, not a Lean/TLA+ theorem. In particular, exit=124 alone can be the child process's own exit status and does not prove elapsed duration or successful graphics initialization, and a window/adapter log is not proof of actual player-visible frames, input latency or player enjoyment. Any missing tool/renderer on a specific host yields a scoped blocker rather than a conclusion that the binary itself is invalid.

In Hoare-style *partial correctness* terms, success and failure paths are separate, not an unjustified promise that every environment can render:

~~~text
  { compiled_binary AND supported_runtime_environment }
     package_orbit_linux
  { exit=0 => S AND A AND VerifiedPreviewReady }

  { NOT D }
     package_orbit_linux
  { exit!=0 AND ENV_BLOCKED AND NOT VerifiedPreviewReady }
~~~

Assume–guarantee composition: the Build stage guarantees B; the Packaging stage **assumes** B and a runnable X11/Vulkan environment and guarantees smoke-bound archive eligibility only when S holds; the Publisher must require the packaging success outcome rather than the existence of any archive alone. An environment capable of compiling Rust is *not* automatically capable of rendering with wgpu. The contract is silent/UNKNOWN about Windows foreground play, native audio, real human satisfaction, GPU/frame stability outside the observed window and universal trace refinement.

### Effective R2.1 task-local binding (existing G07, not a new LEGO)

| Coordinate | Effective scoped meaning |
| --- | --- |
| I | locked Cargo/Bevy source, compiled native binary, X11 virtual display / software Vulkan environment, target output path, exact source revision |
| O | archive, native log/receipt and digest on success; explicit ENV_BLOCKED or SMOKE_FAILED on failure |
| S | ephemeral shell/renderer process and temporary build output; no game state owned by this packaging interface |
| pre | B and actual external toolchain; missing Xvfb/timeout diagnosed without pretending the user goal is impossible |
| post | READY only after graphically started native binary satisfies S and a checked archive A exists |
| inv | skipped/failed smoke cannot be promoted to verified-preview readiness; build-only execution remains independent |
| eff | native binary/window/smoke execution, filesystem archive, stdout and CI artifact publication under natural owners |
| c | native 14-second bounded smoke window plus build time and resource cost UNKNOWN(host, driver, CI); not assumed free |
| epsilon | native smoke log and renderer adapter are limited observability; actual player experience/real hardware still UNKNOWN |
| prov | Git SourceCut, Cargo.lock and Bevy pin, script and GitHub workflow, actual process exit/log and archive SHA256 |
| unfold | Game mise factory:build:bevy and factory:package:orbit-linux, scripts/package_orbit_linux.sh, .github/workflows/game-orbit-factory.yml, Bevy src/gameplay.rs |

### Mature thinking methods / management grounding

| Method (existing thought LEGO / mature upstream) | Correct application here | Do not infer |
| --- | --- | --- |
| Hoare / weakest preconditions | distinguish supported preconditions, success, ENV_BLOCKED and smoke failure | native software or display always succeeds |
| Pacti assume–guarantee | build output is not graphical-environment guarantee; publisher must consume actual smoke outcome | identical file names prove behavioral compatibility |
| TLA+ safety/liveness / CEGAR | reject NOT_RUN=>READY and use concrete shell/native traces to refine the contract | finite smoke proves all asynchronous states/fairness |
| NASA systems engineering V&V | trace consumer claim to command, source, environment, observer and exact evidence | compilation/CI PASS means human validation |
| Parnas information hiding | keep build, smoke and publication behind existing native Game interfaces and one shared package script | new universal workflow service is necessary |
| Lean/Jidoka and HRO operational sensitivity | stop verified publication at observed missing dependency while leaving legal build work enabled | every blocked environment must block all work |
| Deming/IHI PDSA and Theory of Constraints | fix the witnessed release bottleneck; inspect native effect and correct the next action instead of multiplying plans | model-A/B tests or generic throughput scores are required |
| Matt to-spec/to-tickets + two-axis code-review | use this current source/consumer scope and exact tracer steps; review standards independently of spec satisfaction | install the entire Matt issue-management workflow |
| ECC contract-first/brownfield + Superpowers TDD/verification | keep one native execution seam, test failure path, then real graphical CI and actual receipt | ECC Stop regex or self-written test PASS grants distribution authority |

Primary references: NASA Systems Engineering Handbook https://www.nasa.gov/reference/5-0-product-realization/ ; Pacti https://www.pacti.org/docs/getting_started/ ; Parnas 1972 https://doi.org/10.1145/361598.361623 ; High Reliability Organizations (operational sensitivity) https://doi.org/10.1002/9781119175834.ch05 ; IHI PDSA https://www.ihi.org/library/model-for-improvement/testing-changes ; Bevy official graphical CI https://github.com/bevyengine/bevy-website/blob/main/content/learn/book/development-practices/testing.md ; GitHub Actions reusable script https://docs.github.com/en/actions/reference/workflows-and-actions/workflow-syntax .

### Independent cross-audit: per-artifact GO/REVISE/NO-GO

A read-only Codex 0.163.0 independently reviewed the **exact main SourceCut** and project/upstream Skills, exit 0 without editing files. The separate Host Space challenge is recorded in topic:ordivon-capability-task-forum-r1:03-refinement:20261101, messages 25822 and 25839. A Space discussion is not a passing test or authorization. Audit dimensions for **every carrier**: theory/math; R2.1/Owner; actual consumer; Skill fit; anti-conservatism; substantive vs cosmetic; zero-base reuse; verifier/negative control; source-bound fix.

| Carrier | Assessment and mandatory response |
| --- | --- |
| Global AGENT_CONTRACT_EXECUTION_SPEC_R1 | **GO/REUSE** for its own bounded architecture scope; all nine audit dimensions adequate. Do not edit or duplicate its global truth while parallel Owner PRs run |
| Game agent-execution-contract-spec R1.1 | **REVISE** Hoare example: clean checkout + Godot available do not guarantee successful import; express successful and failed outcomes separately. Other eight dimensions adequate |
| Game agent-execution-implementation-plan R1.1 | **REVISE** claimed NameError RED: missing new reader function is not evidence the *old* reader accepted corrupt real receipts. Require semantically relevant old-vs-new negative evidence; retain actual executed results |
| Game Orbit mise native package task | **REVISE** real consumer mismatch: missing xvfb-run/timeout produced successful READY; build-only remains legal. Need runtime negative test and native smoke on CI |
| Game Orbit GitHub native workflow | **REUSE/COMPOSE** existing pinned checkout and actual Xvfb/Mesa GPU smoke. **REVISE** duplicated shell packaging implementation by consuming one shared Game native packaging script, retaining explicit source/sha receipt and workflow artifact upload |

The independent reviewer found an actual **Standards/Spec contradiction**: Game AGENTS says package with target platform smoke, while this Factory guide previously said Xvfb smoke merely "when available". This task resolves the ambiguity for *verified preview* without prohibiting a build-only artifact. The reviewer did **not** execute native smoke, so it supplied no claimed CI/native PASS.

### Exact implementation DAG (no new tracker)

1. **E1 — consumer RED:** execute the actual existing packaged task shell in a disposable checkout with the build stage replaced by a fixture and xvfb-run discovery deliberately masked. Expected old exit=0, archive exists, NOT_RUN and READY: *observed* at SourceCut above.
2. **E2 — single native provider:** move existing Orbit smoke/package mechanics into one Game-owned script; local mise and GitHub CI both invoke it after their ordinary native Rust builds. Missing xvfb-run/timeout => ENV_BLOCKED and nonzero, without a READY marker or verified archive.
3. **E3 — persistent negative control:** exercise the shared package script with missing-tool PATH fixtures and native GNU timeout early-124 behavior, asserting fail-closed; do not label fixture test a native GPU smoke. CI continues to execute the actual Bevy binary under Xvfb/Mesa.
4. **E4 — eliminate duplicate CI path:** replace replicated CI smoke/archive shell with one call to Game script; retain exact Git checkout, real renderer/window markers and artifact upload. Run actionlint and the negative contract test.
5. **E5 — true affected verification:** Game native test:agent-episode, Cargo/Bevy plus formal checks, owner mise verify as available, native packaging on a graphical-capable host or exact CI runner. ENV_BLOCKED is not PASS.
6. **E6 — independent review/integration:** Matt Standards vs Spec review, check all nine cross-audit questions again against the diff, commit isolated branch, protected PR and read current GitHub CI. MERGED/INSTALLED/HUMAN_CONSUMED are independent outcomes.

**Stop:** once real build-only remains available and no unchecked smoke path can issue verified preview READY. Do not extend Game into a new general scheduler, math calculus, GPU backend or agent evaluator. Further product-level player acceptance remains an independent Game consumer decision.
