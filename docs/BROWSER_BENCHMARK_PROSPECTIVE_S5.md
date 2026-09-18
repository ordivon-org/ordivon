# Browser Benchmark Prospective Pairing S5

## Purpose

BCR-S5 freezes the paired experiment before live route-readiness observation.

It does not enable routes, inject provider credentials, unmask Browserless carriers, submit Runtime
Jobs, or infer semantic outcomes. It prepares a campaign only after both exact benchmark routes are
simultaneously READY under their ordinary policy.

## Prospective manifest

The manifest binds:

- benchmark suite and task digests;
- the exact Jev and Browser Use case digests;
- campaign identity;
- pair count;
- one runId per route trial;
- an alternating AB / BA execution order;
- the rule that all routes must be READY before any trial is materialized;
- no fallback and no caller readiness override.

The CLI default of eight pairs is a convenience, not a scientific law. pairCount remains an explicit
bounded parameter from 1 through 50 and changing it changes manifest identity.

## Why alternate order

A fixed order would confound route with ordering effects such as warm caches, provider/network
variation, or substrate startup state.

S5 therefore freezes:

    odd pair:  Jev -> Browser Use
    even pair: Browser Use -> Jev

This is deterministic and auditable. It is not claimed to remove every temporal confound.

## Dual normal-readiness gate

For each route S5 invokes the normal exact-route planner without a caller-supplied readiness
override. The S4 exact-route isolation rule therefore applies: sibling routes are not probed.

If either route is not READY:

    standing = BLOCKED_BY_ROUTE_READINESS
    trialBundles = []
    effectsExecuted = false
    runtimeJobsCreated = false

No route-run request is materialized in this branch.

Only after both routes independently report SELECTED + READY does S5 capture the exact readiness
snapshot and use it to materialize every frozen trial. This avoids a second live readiness probe
changing the campaign identity between the gate and preparation.

## Ready campaign output

A ready campaign produces exactly 2 * pairCount trial bundles. Every bundle binds:

    pairIndex
    orderIndex
    routeId
    runId
    caseDigest
    preparationDigest
    admission templateDigest

The result still contains only Runtime admission templates. No Runtime Job is created by S5.

Jev required secret names may be carried as names, but secret values remain excluded from the
campaign artifacts and Runtime templates.

## Interpretation boundary

This campaign measures the current route implementations on one fixed browser task. It is not a
general model-intelligence leaderboard.

In particular:

- Jev delegates decision/execution to its provider path;
- the Browser Use benchmark route is currently caller-directed structured execution;
- latency, actions, telemetry coverage and outcome success are meaningful route-level observations;
- no single campaign result should be generalized into universal browser-agent superiority.

## Current live gate — 2026-09-18

The frozen prospective-r1 manifest was generated with eight pairs / sixteen trials before live
readiness observation.

The live gate then reported:

- Jev: CREDENTIAL_MISSING;
- Browser Use: POLICY_DISABLED;
- campaign standing: BLOCKED_BY_ROUTE_READINESS;
- trial bundle count: 0;
- state files materialized: 0;
- Runtime Jobs created: false;
- effects executed: false.

No route policy was changed to obtain benchmark data.

## Remaining execution gate

The engineering path through paired preparation is complete. The experiment itself remains blocked
until both routes become READY through their normal operating configuration.

At that point S5 can generate the frozen paired admission set. Runtime admission and result
collection must still pass the S4 reconciliation chain; READY does not imply execution or PASS.
