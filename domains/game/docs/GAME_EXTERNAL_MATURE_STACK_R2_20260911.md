---
schema_version: 1
id: game.external-mature-stack-r2-20260911
title: Ordivon Game — External Mature Stack R2
profile: research-engineering
lifecycle: candidate
source_role: composition-candidate
visibility: internal
owners:
  - ordivon-game
updated: 2026-09-11
base_revision: 5d555906ce539e35e0e9b84add8670623e9390d5
---
# Game External Mature Stack R2

> **Historical/superseded selection profile (2026-09-13).** R3 (`GAME_EXTERNAL_MATURE_STACK_R3_20260913.md`) replaces the hard `GitHub stars >= 10k` software-candidate gate with a maintenance/compatibility/release/security-first screen. R2 remains historical evidence for the externalization/subtraction decisions below.

## 0. Decision rule

This round is external-first.

```text
Authoritative external standard / official platform mechanism
+ mature >=10k-star GitHub substrate where a software substrate is needed
+ current Ordivon horizontal owner
+ irreducible Game semantics
```

is preferred over a Game-local generic replacement.

Project candidate admission rule for this round:

```text
GitHub stars >= 10k
```

Projects below that threshold are outside the candidate pool. Standards, specifications, official platform workflows, and professional-practice authorities are evaluated independently of GitHub stars.

A local extension is admitted only after an exact external mismatch is demonstrated and a thin adapter/profile cannot preserve the required Game invariant.

## 1. Research E2E conclusion

The 2026-09-10 R1 external-first decision remains supported. Mature external authorities already cover the generic process surface:

| Concern | External authority / mechanism | Game disposition |
| --- | --- | --- |
| discovery process | Design Council Double Diamond | DIRECT_ADOPT process skeleton; Game supplies external-reference search content |
| requirements | ISO/IEC/IEEE 29148:2018 | DIRECT_ADOPT |
| software lifecycle | ISO/IEC/IEEE 12207:2026 | DIRECT_ADOPT; G0-G8 is only a Game commitment projection |
| product quality | ISO/IEC 25010:2023 | DIRECT_ADOPT |
| quality in use | ISO/IEC 25019:2023 | DIRECT_ADOPT |
| HCD | ISO 9241-210:2019 | DIRECT_ADOPT |
| usability concepts | ISO 9241-11:2018 | DIRECT_ADOPT |
| Human/market research service | ISO 20252:2026 + applicable ICC/ESOMAR duties | DIRECT_ADOPT where scoped |
| game user research | mature Games User Research practice | DIRECT_ADOPT method-selection practice |
| game accessibility | Xbox Accessibility Guidelines v3.2 | DIRECT_ADOPT baseline |
| browser/web accessibility | WCAG 2.2 | DIRECT_ADOPT where applicable |
| public/closed playtest access | Steam Playtest | PLATFORM_NATIVE when needed |
| randomized population experiments | PlayFab Experiments / mature online experimentation | PLATFORM_NATIVE when needed |
| platform release | Steamworks review/release and target-platform equivalents | PLATFORM_NATIVE |
| build/source provenance | SLSA v1.2 | DIRECT_ADOPT via Artifact/Engineering |
| SBOM/component exchange | SPDX 3.0 | DIRECT_ADOPT via Artifact/Engineering |
| OSS compliance programme | ISO/IEC 5230:2020 OpenChain | DIRECT_ADOPT where applicable |
| game causal vocabulary | MDA and comparable mature design lenses | REFERENCE_ONLY |

The external mechanisms do not eliminate the irreducible Game layer:

```text
ExperienceIntent
PlayableSemantics
Game rules / content / scenario meaning
Mechanics -> dynamics -> player-relevant causal hypotheses
Content/progression grammar
Game-specific claim questions and falsifiers
Product-value interpretation
Product-direction decision
```

## 2. >=10k-star software substrate census

Only projects that can plausibly carry a Game E2E concern are retained.

### 2.1 Primary production substrates

```text
Godot
  role: game engine/editor/runtime carrier
  disposition: CURRENT PRIMARY CARRIER where the selected GameForm requires it

Blender
  role: 3D DCC / modeling / rigging / animation / scene authoring
  disposition: DIRECT_CONSUME when 3D production pressure exists

FFmpeg / ffprobe
  role: media conversion, inspection, validation and batch processing
  disposition: DIRECT_CONSUME

Audacity
  role: audio recording/editing
  disposition: OPTIONAL DIRECT_CONSUME when the audio workflow benefits

Git LFS
  role: large binary asset transport/versioning extension to Git
  disposition: ON_DEMAND; activate only after real asset-size/history pressure
```

### 2.2 Operations substrates

```text
Prometheus
  role: service/system metrics collection/query
  disposition: Operations owner; CURRENTLY AVAILABLE locally

Grafana
  role: observability visualization/dashboards
  disposition: Operations owner; ON_DEMAND

Sentry
  role: error/crash/performance monitoring platform
  disposition: Operations owner; ON_DEMAND
```

Game emits semantic events and candidate/context identity. These substrates do not own Game meaning, ProductValue, Human standing, fairness, fun, accessibility fit or rights.

### 2.3 Backend substrate

```text
Nakama
  role: multiplayer/backend capabilities such as auth, matchmaking,
        leaderboards, chat and social/multiplayer services
  disposition: ON_DEMAND only after a selected GameForm requires them
```

Do not create Game-local generic auth/matchmaking/leaderboard/chat infrastructure while a mature backend is suitable.

### 2.4 Alternative carriers — compare, do not compose by default

Bevy, MonoGame, Phaser, raylib and GDevelop are mature alternative game carriers/frameworks. They are not dependencies to stack on top of Godot. They become active candidates only when a concrete GameForm/platform/tooling requirement falsifies the current Godot path.

```text
Alternative carrier != additive dependency
```

## 3. Current local physical inventory

Observed on 2026-09-11 in the current Game environment:

```text
AVAILABLE
  Godot      4.7.1.stable.arch_linux.a13da4feb  /usr/bin/godot
  Blender    5.2.1 LTS                          /usr/bin/blender
  FFmpeg     9.0                                /usr/bin/ffmpeg
  FFprobe    9.0                                /usr/bin/ffprobe
  Prometheus 3.14.0                             /usr/bin/prometheus
  Promtool   3.14.0                             /usr/bin/promtool
  Git        2.55.0
  Node       26.7.0
  pnpm       10.33.2

NOT CURRENTLY MATERIALIZED AS COMMANDS
  Git LFS
  Grafana server
  Sentry CLI
  Nakama server
```

Physical availability does not grant Game semantic authority and does not require activation.

## 4. Production composition

### 4.1 Runtime and editor

Current default when a real engine is required:

```text
Game-owned semantics
      ↓ thin project/profile binding
Godot 4.7.1
      ↓
platform build/export
```

Godot owns engine/editor/runtime mechanics. Game owns scenes/content only insofar as they express the selected game's product semantics and acceptance conditions. Workstation owns physical software materialization/binding; Runtime/Engineering own admitted execution mechanics.

Do not build a Game-local engine, editor automation platform, generic process runner, or software-discovery service.

### 4.2 3D asset waist

Preferred mature waist:

```text
Blender source
   ↓
glTF 2.0 / GLB
   ↓
Godot importer/runtime representation
```

FFmpeg/ffprobe carries media transformation/inspection where applicable. No Ordivon Game asset interchange format is admitted.

### 4.3 Large binary assets

The current repository has no `.gitattributes` and no Git LFS installation. Current largest tracked Game binaries are under approximately 0.5 MB, so there is no present evidence that LFS activation would improve the current carrier.

Therefore:

```text
Git LFS = ADOPTABLE_EXTERNAL_MECHANISM / NOT_YET_ACTIVATED
```

Activation should be pressure-triggered by real DCC/media asset size, clone/history cost, or repository-host limits rather than by architecture fashion.

## 5. Operations composition

Target boundary:

```text
Game semantic event / exact candidate identity
            ↓
Operations adapter
            ↓
Prometheus / Sentry / platform analytics
            ↓
Grafana or platform-native visualization
```

Game may define an event such as `observation_succeeded` or `mission_failed` and its domain payload. It must not implement a generic telemetry warehouse, time-series database, dashboard platform, crash service or population experiment service.

Historical Veilwild telemetry/evidence runtime remains regression/history apparatus and must not become the default future telemetry architecture.

## 6. Platform and population composition

```text
External-player access       -> Steam Playtest or target-platform equivalent
Release/review               -> platform-native review/release workflow
Population causal experiment -> PlayFab Experiments or equivalent mature mechanism
```

The Game/Research layer owns:

```text
question
exact candidate/condition
population/context boundary
Game hypothesis
Game interpretation
```

The platform owns access, assignment, delivery, scorecard/release mechanics inside its native scope.

## 7. Engineering E2E local subtraction map

### 7.1 EXTERNALIZE / MOVE — highest-priority current source targets

#### `src/team/provider-runtime.ts`

Current responsibility includes process spawn, stdout/stderr capture, timeouts, abort and process-tree kill. This is generic execution machinery.

Target:

```text
MOVE -> Runtime / Host / Provider execution owner
KEEP in Game -> no process lifecycle semantics
```

#### `src/team/provider-preflight.ts`

Current responsibility includes executable-path and credential readiness probes, including hard-coded CLI locations. This is Workstation/Provider availability, not Game semantics.

Target:

```text
MOVE -> Workstation / Provider owner
Game consumes capability/availability result only
```

#### `src/team/codex-cli.ts` and `src/team/hermes-cli.ts`

Current responsibility includes CLI invocation/isolation/environment construction and usage validation.

Target:

```text
MOVE transport/execution -> Host/Runtime/Provider owner
KEEP -> Game-specific context contract + parsed decision schema + admission
```

#### `src/team/provider-chain.ts`

Generic provider retry/fallback ordering is orchestration. Game only needs the selected provider result and exact evidence needed for Game decision admission.

Target:

```text
MOVE generic fallback execution -> Host/Provider owner
KEEP Game policy only if provider ordering itself is an intentional Game evaluation condition
```

### 7.2 SPLIT — do not delete wholesale

#### `src/storage.ts`

Generic/implementation portion:

```text
SQLite setup
WAL/busy handling
filesystem/storage error plumbing
snapshot implementation mechanics
```

Game-owned portion:

```text
World command/event identity
World revision
Game invariants
exact Game state recovery
Game consequence of corruption/recovery
```

Do not replace the whole file with a generic database/event-store abstraction unless the external substrate preserves the Game atomicity and replay invariants.

#### `src/replay/*`

KEEP:

```text
World-state-at-revision semantics
Game causal replay
mission/objective/resource/authority key turns
hidden-information and player-relevant diagnosis
```

Move only genuinely generic provenance/graph transport if a clean owner boundary exists.

#### `src/deployment/*`

KEEP the exact Game evaluation/deployment condition such as actor/provider/loadout/coordination semantics when those change gameplay or evaluation.

MOVE generic build/release/platform deployment mechanics to Engineering/Artifact/Distribution.

### 7.3 KEEP

Do not externalize merely because the code is large:

```text
src/station-zero-v3/* Game rules/reducer/content/planning semantics
Game World authority and legal transitions
Game-specific Team action/authority admission
Mission Control player/product projections
Game-specific replay interpretation
Game-specific product-value/falsifier logic
Game content/progression semantics
```

A generic framework may carry execution but cannot become authority for what those facts mean in the game.

### 7.4 HISTORY / REGRESSION

`experiments/veilwild-r1/*` contains valuable failure witnesses and production history, including custom telemetry, behavior, integration and validation apparatus.

Disposition:

```text
retain as HISTORY / REGRESSION corpus
not a template for new generic infrastructure
```

## 8. Horizontal owner composition

The desired owner topology is:

```text
External standards / mature platforms / >=10k substrates
                         │
Research E2E ------------┤ question / evidence method
Engineering E2E ---------┤ realization / V&V / integration
Workstation E2E ---------┤ physical software/equipment binding
Runtime / Host ----------┤ generic execution / provider/process continuity
Artifact E2E ------------┤ build identity / provenance / SBOM
Distribution E2E --------┤ platform release/access
Operations E2E ----------┤ telemetry transport / monitoring / incidents
                         │
                         ↓
              thin Game adapters/profiles
                         ↓
                 Game semantic kernel
                         ↓
                    actual game
```

No horizontal E2E or external substrate inherits Game semantic truth merely because it executes or transports a Game operation.

## 9. Selected stack versus optional stack

### Activate now / already active

```text
External standards routing
Godot where current GameForm needs engine runtime
Blender where 3D production is required
FFmpeg/ffprobe for media mechanics
Prometheus only through Operations concerns
Research/Engineering/Workstation/Runtime/Artifact owner boundaries
```

### Activate only on real pressure

```text
Git LFS       -> large binary/history pressure
Grafana       -> observability visualization demand
Sentry        -> production crash/error/performance monitoring demand
Nakama        -> multiplayer/backend demand
Steam Playtest-> external-player access demand
PlayFab       -> real population causal experiment
SLSA/SPDX/OpenChain artifacts -> build/release/compliance pressure
```

### Do not compose by default

```text
Godot + Bevy + MonoGame + Phaser + raylib + GDevelop
```

Select one primary runtime carrier for one product unless an explicit boundary requires another.

## 10. Next Engineering E2E migration order

```text
E1  Move provider process execution out of Game.
E2  Move provider availability/preflight out of Game.
E3  Reduce Codex/Hermes adapters to Game decision-schema/admission bindings.
E4  Reclassify provider fallback as external orchestration unless intentionally part of a Game evaluation condition.
E5  Split storage implementation mechanics from Game world/recovery semantics without changing transactional truth.
E6  Keep replay semantics; externalize only generic transport/provenance fragments proven separable.
E7  Ensure future telemetry uses Operations substrates rather than Veilwild-style local generic recorders.
E8  Add Git LFS only after measurable asset pressure.
E9  Activate Sentry/Nakama/platform mechanisms only when a real product condition requires them.
E10 Preserve Veilwild as a regression corpus, not a reusable framework.
```

## 11. Current verdict

```text
GAME_E2E_EXTERNAL_COMPOSITION_R2 = KEEP_AND_SUBTRACT
GREENFIELD_GAME_E2E_V2           = NOT_ADMITTED
```

The current Game E2E architecture is already unusually clean after R5. The remaining improvement is a narrow second subtraction pass around generic provider/process execution and selected implementation mechanics, plus direct consumption of mature external production/operations/platform mechanisms when real pressure activates them.
