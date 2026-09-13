---
schema_version: 1
id: game.external-mature-stack-r3-20260913
title: Ordivon Game — External Mature Stack R3 Maintenance-First Selection
profile: research-engineering
lifecycle: active
source_role: canonical-selection-profile
visibility: internal
owners:
  - ordivon-game
updated: 2026-09-13
supersedes:
  - game.external-mature-stack-r2-20260911
---
# Game External Mature Stack R3 — Maintenance-First Selection

## 0. Decision

R3 replaces the R2 software-substrate rule `GitHub stars >= 10k`.

That threshold was useful as an aggressive anti-niche filter but is invalid for specialized engine tooling: a narrow Godot testing or CI project can be mature, current and widely useful with far fewer than 10k stars. Stars remain supporting adoption evidence, not admission authority.

The forward order is:

```text
official standard / platform / engine mechanism
→ actively maintained mature OSS when a substrate is still required
→ current Ordivon horizontal owner
→ irreducible Game semantics
```

## 1. OSS admission profile

A non-official software candidate is evaluated on the following evidence, in order:

1. **current maintenance** — recent releases/commits/issues appropriate to the ecosystem cadence;
2. **exact compatibility** — explicit support for the current engine/platform version rather than generic “Godot 4” claims;
3. **release discipline** — tagged versions/changelog and a usable upgrade path;
4. **self-verification** — CI, tests, deterministic or machine-readable outputs where applicable;
5. **license fit** — permissive or otherwise explicitly accepted license;
6. **real adoption** — downstream users, forks, stars and community evidence as supporting signals;
7. **native-semantic preservation** — use `project.godot`, `export_presets.cfg`, engine CLI and provider-native identities instead of creating a second Ordivon configuration language;
8. **security posture** — no unresolved critical exposure incompatible with the intended trust boundary.

A project does not become authoritative because it wins this screen. It becomes a replaceable implementation selection under the relevant engine/platform owner.

## 2. Current Godot baseline

Current local primary engine carrier is Godot 4.7.1. Godot itself remains the authority for project import, parsing/runtime behavior and export semantics.

Forward default:

```text
project.godot
+ export_presets.cfg
+ Godot official CLI
```

Godot official documentation exposes `--headless`, `--import`, `--check-only`, `--path`, `--export-release`, `--export-debug` and `--export-pack`; command-line export is explicitly intended for automated/CI use. Export configuration remains in native `export_presets.cfg`, while confidential export material belongs outside that file.

Sources:
- https://docs.godotengine.org/en/latest/tutorials/editor/command_line_tutorial.html
- https://docs.godotengine.org/en/latest/tutorials/export/exporting_projects.html

Disposition: **DIRECT_ADOPT / AUTHORITY**.

## 3. Godot testing selection

### 3.1 Primary: GUT 9.7.1

Selected as the first default test framework for new Godot 4.7.x product code.

Current evidence:

- repository has long history and roughly 975 commits;
- about 2.7k GitHub stars and 150 forks at the 2026-09-13 observation;
- release `9.7.1` published 2026-07-10;
- project compatibility table explicitly maps `9.7.1 / godot_4_7` to **Godot 4.7.x**;
- MIT license;
- command-line test runner;
- parameterized tests, doubles/stubs/spies;
- standard JUnit XML export for CI/report consumers.

Sources:
- https://github.com/bitwes/Gut
- https://github.com/bitwes/Gut/releases

Disposition: **ADOPT_FOR_NEW_GODOT_PRODUCTS**.

Local acceptance on 2026-09-13 cloned exact tag `v9.7.1` / commit `aeb5d4f3f7f0a6c9b5e178876d6c99b791fda605` into an isolated temporary project and ran it under the current `/usr/bin/godot` 4.7.1 carrier. Result: 1/1 tests PASS, 3 assertions PASS, JUnit XML generated. Runtime evidence is retained in `evidence/external-mature-stack-r3-20260913.json`.

Boundary:

```text
GUT owns test-framework mechanics.
Game owns which rules/behaviours must be true.
Godot/runtime execution remains final engine truth.
```

Do not retrofit GUT across historical TS/browser experiments merely to increase tool uniformity.

### 3.2 Strong alternative: GdUnit4

GdUnit4 remains a first-class alternative rather than a second simultaneously installed default.

Current evidence:

- active 2026 releases in the 6.2 line;
- approximately 872 repository commits;
- low current open-issue count at observation;
- GDScript and C# support;
- editor-integrated tests, assertions, mocks/spies and scene testing;
- CLI/CI support and JUnit-style reporting;
- MIT license.

Sources:
- https://github.com/godot-gdunit-labs/gdUnit4
- https://github.com/godot-gdunit-labs/gdUnit4/releases

Disposition: **EVALUATE_ON_REQUIREMENT**.

Switch/choose GdUnit4 when a real product benefits materially from its scene-testing/editor/C# surface or when GUT compatibility/maintenance is falsified. Do not install both by default.

## 4. Godot CI / build selection

### 4.1 Primary external carrier: godot-ci

`abarichello/godot-ci` is the preferred external reference/carrier for Godot CI export when hosted/containerized CI is needed.

Current evidence:

- MIT license;
- approximately 1.1k stars and 164 forks at observation;
- GitHub Actions and GitLab CI examples;
- Docker images include Godot editor plus matching export templates;
- releases closely track Godot stable versions, including `4.7.1-stable` (2026-07-15) and `4.7.2-stable` (2026-08-18);
- workflows delegate actual build semantics to `godot --headless --export-release` and native `export_presets.cfg` rather than inventing a second exporter.

Sources:
- https://github.com/abarichello/godot-ci
- https://github.com/abarichello/godot-ci/releases

Disposition: **ADOPT_WHEN_NEW_PRODUCT_GETS_HOSTED_CI**.

A bounded local pull canary for `barichello/godot-ci:4.7.1` on 2026-09-13 was blocked before image acquisition by repeated Docker Hub registry timeouts. This is retained as `LOCAL_CANARY_BLOCKED_BY_REGISTRY_CONNECTIVITY`, not a godot-ci compatibility failure; upstream release/currentness evidence remains the adoption basis until hosted CI is activated and can execute the real project.

Local Runtime/Engineering execution may continue using the exact local Godot binding. Hosted CI should reproduce the same native command/preset semantics through godot-ci rather than a Game-owned build framework.

### 4.2 Alternative: firebelley/godot-export

A maintained GitHub Action focused narrowly on export; v8.0.0 was released 2026-05-28 and it also consumes Godot native export presets.

Source:
- https://github.com/firebelley/godot-export

Disposition: **VALID_ALTERNATIVE / DO_NOT_COMPOSE_WITH_GODOT_CI_BY_DEFAULT**.

Choose one export carrier per product CI path.

## 5. Optional static GDScript quality layer

`Scony/godot-gdscript-toolkit` supplies `gdlint`, `gdformat` and parser tooling and continues to run an active test workflow. It is useful for formatting/static hygiene but is not Godot runtime truth.

Sources:
- https://github.com/Scony/godot-gdscript-toolkit
- https://github.com/Scony/godot-gdscript-toolkit/releases

Disposition: **ON_DEMAND**.

Order of authority:

```text
gdformat/gdlint hygiene
< Godot parse/import/runtime
< product-target execution evidence
```

## 6. Cross-engine automation references

The following are architectural references, not dependencies for the current Godot product path:

```text
Unreal BuildGraph  -> large build dependency graph/reference
Unreal Gauntlet    -> packaged session/test orchestration reference
Unreal Horde       -> mature build farm/CI/test/device/artifact reference
GameCI             -> mature open-source game CI/CD reference
```

They demonstrate an important pattern:

```text
engine-native commands/configuration
+ ordinary CI/orchestration
+ packaged-build execution
+ retained evidence
```

rather than a universal Game-specific automation platform.

Disposition: **REFERENCE_ONLY unless engine/carrier changes**.

## 7. Agent / MCP selection

### 7.1 Production default: no Godot MCP dependency

No surveyed Godot MCP currently clears the same maturity bar as Godot CLI, GUT or godot-ci.

`ee0pdt/Godot-MCP` currently has open MCP-spec conformance issues and an open issue pointing to a published unauthenticated remote-code-execution advisory (CVSS 9.6). It is therefore not admitted to the production trust boundary.

Source:
- https://github.com/ee0pdt/Godot-MCP/issues

Disposition: **REJECT_FOR_PRODUCTION_CURRENTLY**.

`hybridindie/godot-mcp` has a stronger safety-oriented architecture (read-only default, gated toolsets, typed API) and targets modern Godot, but its first stable release is only from 2026-09-10 and adoption history is too short for production authority.

Source:
- https://github.com/hybridindie/godot-mcp

Disposition: **SANDBOX_EVALUATION_ONLY**.

Agent execution should prefer existing Runtime + exact Godot CLI/equipment bindings until a Godot MCP demonstrates sustained maintenance, security and interoperability evidence.

## 8. Agent Skills

Adopt the **Skill packaging convention** as a replaceable knowledge/procedure carrier, not third-party game-development skill content as semantic authority.

A Game/Godot Skill may provide:

```text
when to use Godot CLI
native project/export conventions
GUT invocation patterns
scene/resource editing cautions
official-doc references
known compatibility boundaries
```

It must not define product rules, player-value truth or a private Game framework.

Third-party skills are part of the Agent trust boundary and require source/audit review before installation.

Disposition: **FORMAT_ADOPTABLE / CONTENT_AUDIT_REQUIRED**.

## 9. Production-method selection

The method stack remains external-first:

```text
Double Diamond          -> discovery divergence/convergence skeleton
MDA                     -> reference-only causal design lens
Cerny/Method family     -> preproduction discovery/prototyping reference
Vertical Slice          -> representative quality/pipeline proof when appropriate
Connected systems proof -> substitute for slice when the product's value depends on broad simulation coupling
Games User Research     -> question-to-method player evidence practice
Scrum/Kanban/Lean       -> production coordination tools selected by work shape, not doctrine
```

None becomes an Ordivon-owned universal methodology.

## 10. Current activation matrix

| Capability | Selection | Standing |
| --- | --- | --- |
| engine/editor/runtime | Godot 4.7.1 + official CLI | **ACTIVE / AUTHORITY** |
| export configuration | native `export_presets.cfg` | **ACTIVE / AUTHORITY** |
| Godot unit/integration test framework | GUT 9.7.1 | **SELECTED FOR NEW PRODUCT / NOT RETROFITTED** |
| alternative Godot test framework | GdUnit4 6.2.x | **EVALUATE ON REQUIREMENT** |
| hosted Godot CI/export | godot-ci matching current stable line | **SELECTED WHEN HOSTED CI ACTIVATES** |
| alternative GitHub export action | godot-export | **ALTERNATIVE** |
| GDScript lint/format | gdscript-toolkit | **ON DEMAND** |
| Steam upload/release | SteamPipe/SteamCMD (+ mature wrapper only if useful) | **DEFERRED UNTIL REAL APPID** |
| Godot MCP | none | **NO PRODUCTION DEPENDENCY** |
| Agent Skill format | standard Skill package | **ADOPTABLE; CONTENT REQUIRES AUDIT** |

## 11. Migration consequences

Immediate rules for the first real greenfield product:

```text
1. keep `project.godot` and `export_presets.cfg` authoritative;
2. use Godot CLI directly for import/check/export/run mechanics;
3. add exactly one Godot test framework, default GUT 9.7.1 for current 4.7.x;
4. use godot-ci only when hosted CI is actually activated;
5. do not add a Godot MCP to the production dependency graph yet;
6. do not build Game-local generic test runner/build graph/exporter/editor RPC;
7. route SBOM/provenance/release standing to Artifact/Engineering;
8. route store upload/platform release to Distribution/platform-native tooling.
```

This profile is a selection policy, not a requirement to mutate historical experiments. New product demand activates selected tools at the product boundary.
