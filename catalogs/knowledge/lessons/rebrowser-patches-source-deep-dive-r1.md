# Rebrowser Patches Source Deep Dive R1

Date: 2026-09-17
Upstream: `rebrowser/rebrowser-patches`
Observed upstream HEAD: `6373894fde8379eb9b8d393e1d607706eecd8e70`
Observed package version: `1.0.19`
Scope: mechanism-level study of automation protocol side channels and ablation-friendly patch design. This is not a production security-control bypass runbook.

## 1. Rebrowser Patches is a narrow patch layer over installed automation libraries

The repository is intentionally small:

- patch files for `puppeteer-core` and `playwright-core`;
- a patch/unpatch/check CLI;
- environment-variable-controlled modes for selected mechanisms.

Unlike a custom browser distribution, it mutates the installed automation library's Node driver/package. Its own README explicitly warns this approach is fragile across upstream source changes.

This makes Rebrowser particularly useful as a **mechanism-level experimental arm**.

## 2. Its main research object is execution-context discovery without standard persistent `Runtime.enable`

Standard Puppeteer/Playwright use the CDP Runtime domain to receive execution-context lifecycle events. Rebrowser rewrites that logic so context IDs can be acquired through alternate paths and synthetic context-created events can be fed back into the library's internal state.

The important research abstraction is:

`CONTROL_FRAMEWORK_NEEDS_CONTEXT_ID` does not imply one immutable `CONTEXT_DISCOVERY_STRATEGY`.

Different strategies create different protocol/page-visible side effects and different compatibility constraints.

## 3. The repository exposes multiple runtime-fix modes

The source and README expose distinct strategies under an environment-controlled switch, including:

- a binding-based strategy;
- an isolated-world strategy;
- a short enable/disable fallback strategy;
- disabled/unpatched behavior.

For Ordivon Security, the value is that these can serve as **controlled ablations**. Instead of comparing two huge stacks, an authorized lab can keep browser/network/profile/framework constant and vary one context-discovery mechanism.

The specific bypass recipe is not the durable asset; the experiment topology is.

## 4. Each mitigation introduces its own new surface and functional constraints

The patch source demonstrates that avoiding one persistent subscription can require other mechanisms:

- Runtime bindings/events;
- `Page.addScriptToEvaluateOnNewDocument`;
- isolated-world creation;
- synthetic/internal execution-context events;
- altered worker handling;
- different context disposal/reacquisition behavior.

The project also documents functionality limitations in some modes, such as isolated-world access and debugger/page-pause behavior.

Therefore every mitigation must be evaluated bidirectionally:

`removed observable -> replacement mechanism -> new observables + new correctness risks`

This should become a standard Ordivon Security review pattern.

## 5. Utility-world and source-label artifacts are independent leak families

Rebrowser also changes framework-identifying metadata such as utility-world naming and script source labels. Whether or not a specific detector currently uses them, their presence demonstrates that automation identity can be encoded in seemingly diagnostic/internal naming conventions.

For Ordivon these belong in separate families:

- `EXECUTION_WORLD_NAMING`
- `SCRIPT_SOURCE_METADATA`

They must not be conflated with `Runtime.enable` or webdriver presentation.

## 6. The patcher is intentionally reversible

`scripts/patcher.js` supports `patch`, `unpatch`, and `check`, using dry-run patch state detection. This makes the same installed upstream package suitable for paired experiments.

The conceptual pattern is valuable:

- preserve one upstream baseline;
- apply one named mechanism patch;
- verify patch state;
- run the same measurement suite;
- reverse the patch;
- confirm baseline restoration.

That is stronger causal evidence than comparing unrelated browser images.

## 7. Rebrowser also proves detector coverage is orthogonal

Fixing a protocol-side channel cannot fix unrelated browser/network fingerprint inconsistencies. The project's own documentation warns that proxy, UA, fingerprint and behavior remain separate dimensions.

This supports the Ordivon `DETECTOR_COVERAGE_MATRIX`: every detector/result must name which observable family it covers rather than producing a universal `bot_score` conclusion.

## 8. Required Ordivon experiment primitive: mechanism ablation

Define a browser-security experiment as:

`baseline bundle + exactly one declared mechanism delta + detector set + correctness set`

Required fields:

- `baselineControlLayerDigest`
- `mechanismDeltaId`
- `mechanismDeltaDigest`
- `changedObservableFamilies[]`
- `expectedFunctionalTradeoffs[]`
- `detectorSuiteDigest`
- `correctnessSuiteDigest`
- `patchStateBefore`
- `patchStateDuring`
- `patchStateAfter`

This turns external patch projects into hypothesis generators rather than opaque dependencies.

## 9. Suggested first detector-family decomposition

Combining Rebrowser with the previous source studies:

1. browser/process launch presentation;
2. webdriver presentation;
3. protocol-domain subscription state;
4. execution-context discovery;
5. page/isolated-world artifacts;
6. script source/stack metadata;
7. framework utility-world naming;
8. browser fingerprint consistency;
9. network/transport consistency;
10. session/behavior observations.

A detector should declare which of these it can observe.

## 10. Implication for old Ordivon vs Browserless

Rebrowser strengthens the hypothesis that the relevant variable is not simply `CDP used` vs `CDP not used`.

Both old Ordivon and current Browserless can use CDP, yet differ in:

- launcher owner;
- controller attachment timing;
- protocol domains enabled before first navigation;
- execution-context strategy;
- framework-owned page state;
- launch arguments and profile/network state.

The correct experiment must isolate those dimensions one at a time.

## 11. What to absorb vs what not to copy

### Absorb

- reversible mechanism patches as ablation tooling;
- explicit execution-context strategy identity;
- removed-surface/replacement-surface analysis;
- detector-coverage declarations;
- paired baseline restoration checks.

### Do not absorb into Ordivon core

- third-party anti-detection patch implementation;
- site-specific pass claims;
- a claim that one protocol patch makes the overall browser trustworthy.

Rebrowser Patches is best treated as a mechanism study / authorized-lab provider.

## Sources

- Local clone of `https://github.com/rebrowser/rebrowser-patches`, HEAD `6373894fde8379eb9b8d393e1d607706eecd8e70`
- `patches/playwright-core/src.patch`
- `patches/puppeteer-core/src.patch`
- `scripts/patcher.js`
- `scripts/utils/index.js`
- `README.md`
- `package.json`
