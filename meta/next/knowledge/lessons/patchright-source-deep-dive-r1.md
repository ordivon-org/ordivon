# Patchright Source Deep Dive R1

Date: 2026-09-17
Upstream: `Kaliiiiiiiiii-Vinyzu/patchright`
Observed upstream HEAD: `26ab9ae74516a68077f218b5de763d85be9f6d5a`
Scope: source-level study of Playwright driver observability, upstream-drift management, and functionality/observability trade-offs. This is not a third-party production bypass runbook.

## 1. Patchright is a source-to-source Playwright driver transformation

Patchright is not primarily a launch wrapper. The repository patches Playwright source using TypeScript/ts-morph transformations:

- `patchright_driver_patch.ts` orchestrates the patch set;
- `driver_patches/*.ts` transform Playwright client/server symbols;
- a generated `patchright.patch` documents the resulting difference against upstream Playwright;
- package repos consume the patched driver.

The patch orchestrator touches browser context, Chromium launch, execution contexts, DevTools, page/frame logic, service workers, network, bindings, tracing, screenshots, recorder, injected scripts, dispatchers and more.

Therefore the correct provenance object is `Playwright upstream revision + Patchright patch-set revision + browser revision`, not a single package version.

## 2. `Runtime.enable` is removed by restructuring execution-context discovery

The source explicitly removes `Runtime.enable` from multiple Playwright Chromium paths, including DevTools/page/frame/service-worker setup.

Because Playwright normally depends on Runtime domain events to learn execution contexts, Patchright must replace that dependency with alternate context-discovery/control logic. For example, its execution-context patch uses targeted Runtime operations and object discovery rather than permanently enabling the Runtime domain in the standard way.

The transferable lesson is not the replacement sequence. It is architectural:

**removing one observable protocol subscription can force broad changes to the control framework's state model.**

For Ordivon Security, `CDP_DOMAIN_SUBSCRIPTIONS` should be a first-class detector/provenance family.

## 3. Launch arguments are another independent observability family

`driver_patches/chromiumSwitchesPatch.ts` rewrites Playwright's default Chromium switches. It removes several upstream defaults and adds a different automation-related Blink feature setting.

This demonstrates that browser presentation has at least two separable control-layer surfaces:

- protocol behavior after launch;
- process launch arguments/default browser configuration.

A clean result on one does not imply a clean result on the other.

For Ordivon experiments, store the exact effective launch-argument digest rather than a Boolean such as `stealth=true`.

## 4. Console and init scripts expose functionality/observability trade-offs

Patchright disables/reworks some ordinary Playwright mechanisms to reduce their observable footprint. Its own test modification code documents consequences:

- console events are not equivalent when the Console CDP domain is disabled;
- init scripts are delivered by a different path and have timing/order limitations;
- sourceURL behavior changes;
- some upstream Playwright tests require Patchright-specific workarounds.

This is the strongest reason Ordivon must never promote a control-layer candidate on a detector score alone.

Every candidate needs two independent acceptance dimensions:

1. `AUTOMATION_CORRECTNESS` — actions, events, bindings, contexts and recovery still work;
2. `OBSERVABILITY_REGRESSION` — agreed diagnostic surfaces did not regress relative to the previous admitted version.

## 5. Upstream drift is treated as a machine-checkable engineering problem

Patchright contains tooling that:

- extracts the Playwright symbols touched by each patch;
- compares new upstream changes against those patched symbols;
- reports which patch assumptions may have been invalidated;
- rebuilds and runs modified/upstream tests;
- regenerates a human-readable patch comparison automatically.

`utils/check_patch_impact.ts` is especially relevant. Instead of waiting for runtime breakage after a Playwright release, it computes whether upstream changed code inside Patchright's patch surface.

This should be adopted conceptually in Ordivon as `UPSTREAM_PATCH_IMPACT_ANALYSIS`.

## 6. Patchright's own development model proves version bumps are security-relevant

The project automatically tracks Playwright releases, but explicitly acknowledges that upstream source changes can break patches and require repair. Its tests include dedicated detection smoke tests and modified Playwright tests.

Therefore a framework bump is not merely dependency maintenance. It changes:

- protocol-domain subscriptions;
- execution-context semantics;
- init script behavior;
- launch flags;
- injected/page-visible artifacts;
- potentially correctness and detector observations.

Ordivon should freeze and requalify the complete `CONTROL_LAYER_DIGEST` on every promotion.

## 7. Required Ordivon automation-leak taxonomy

From the actual Patchright patch surface, initial families should include:

- `PROCESS_LAUNCH_ARGUMENTS`
- `WEBDRIVER_PRESENTATION`
- `CDP_RUNTIME_DOMAIN_STATE`
- `CDP_CONSOLE_DOMAIN_STATE`
- `EXECUTION_CONTEXT_DISCOVERY`
- `PAGE_BINDING_ARTIFACTS`
- `INIT_SCRIPT_DELIVERY`
- `SOURCE_URL_AND_STACK_ARTIFACTS`
- `SERVICE_WORKER_CONTROL_STATE`
- `PAGE_WORLD_VS_ISOLATED_WORLD`
- `NETWORK_DOMAIN_SUBSCRIPTIONS`
- `DEBUGGER_DEVTOOLS_STATE`

This taxonomy is more useful than a generic `stealth` label.

## 8. Required provenance / witness fields

- `automationFramework`
- `automationFrameworkUpstreamRevision`
- `controlLayerPatchSetDigest`
- `controlLayerDigest`
- `browserBinaryDigest`
- `effectiveLaunchArgsDigest`
- `enabledProtocolDomains[]`
- `executionContextStrategy`
- `initScriptStrategy`
- `functionalRegressionSuiteDigest`
- `observabilityRegressionSuiteDigest`
- `upstreamPatchImpactReportDigest`

## 9. Implication for Agent Birth

Patchright is valuable as a mechanism-level experimental arm because it changes the same Playwright/CDP surfaces implicated by our Browserless investigation. It should not be inferred to be a universal clean client.

A useful authorized A/B can hold Chromium/network/profile constant and compare stock Playwright against one candidate control layer while recording per-detector-family observations and ordinary workflow correctness.

This can tell us whether a control-layer surface materially contributes to the observable difference without relying on a protected production challenge as the measurement instrument.

## 10. What to absorb vs what not to copy

### Absorb

- explicit patch-surface inventory;
- upstream patch-impact analysis;
- control-layer version fencing;
- dual correctness/observability regression gates;
- detector-family decomposition.

### Do not absorb into Ordivon core

- Patchright's anti-detection patch implementation;
- claims of permanent undetectability;
- site-specific pass/fail lists as domain truth.

Patchright belongs behind an experimental provider boundary if evaluated.

## Sources

- Local clone of `https://github.com/Kaliiiiiiiiii-Vinyzu/patchright`, HEAD `26ab9ae74516a68077f218b5de763d85be9f6d5a`
- `patchright_driver_patch.ts`
- `driver_patches/chromiumSwitchesPatch.ts`
- `driver_patches/crDevToolsPatch.ts`
- `driver_patches/crPagePatch.ts`
- `driver_patches/crExecutionContextPatch.ts`
- `utils/check_patch_impact.ts`
- `utils/modify_tests.ts`
- `.github/workflows/patch_file_updater.yml`
- `README.md`
