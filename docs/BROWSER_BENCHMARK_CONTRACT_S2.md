# Browser Benchmark Contract S2

## Role

BCR-S2 is the provider-neutral measurement boundary after Browser Capability Router R1 and before
effectful adapter dispatch. It does not execute a browser.

Each benchmark variant locks one explicit routeId. Router fallback is forbidden during benchmark
measurement because fallback would turn an A/B comparison into a comparison of different realized
routes.

## Three standings

PREEXEC_BLOCKED means the exact route was not ready and no benchmark execution occurred.

READY means Router selected the exact requested route, but S2 still did not execute it.

EXECUTED is accepted only by finalizing a READY receipt with a separately produced execution
observation bound to the same caseDigest, routePlanDigest, routeId, and outcomeCheckIds.

These standings are independent of semantic outcome:

| benchmark standing | allowed outcome witness |
| --- | --- |
| PREEXEC_BLOCKED | NOT_EXECUTED |
| READY | NOT_EXECUTED |
| EXECUTED | UNVERIFIED / PASS / FAIL |

Adapter/model DONE is therefore not benchmark PASS.

## Metrics

Every metric is a typed observation cell, either:

    {"standing": "OBSERVED", "value": 12}

or:

    {"standing": "NOT_OBSERVED", "value": null}

Missing telemetry is never encoded as zero.

S2 fixes these provider-neutral metric names:

- totalElapsedMs
- bootstrapElapsedMs
- taskElapsedMs
- actionCount
- browserProtocolCallCount
- providerApiRequestCount
- modelRequestCount
- inputTokenCount
- outputTokenCount
- retryCount
- staleActionRetryCount
- fallbackCount
- providerBilledMicrousd

A provider may leave unsupported metrics NOT_OBSERVED; future comparisons must not treat them as
zero.

## Current prospective suite

config/browser-benchmark-suite.json defines one generic navigate+click comparison group with two
explicit variants:

- jev-fast-windows-v1
- browser-use-browserless-v1

This is intentionally prospective. On the current machine Jev may be blocked by missing TypeSafe
credentials and Browser Use may be blocked by an operator systemd mask. S2 records those conditions
as PREEXEC_BLOCKED; it does not unmask Browser Use, invent credentials, substitute another route,
or fabricate execution metrics.

## Identity and anti-Goodhart constraints

A route-locked benchmark receipt carries suiteDigest, taskDigest, caseDigest, routePlanDigest, and
routeId. An execution observation must match the same case, plan, route, and predeclared outcome
check set.

Fallback is invalid for the benchmark variant. If a route is unavailable, the correct result is
PREEXEC_BLOCKED rather than silently executing a different route.

A metric that was not physically observed remains NOT_OBSERVED. A provider reporting DONE remains
UNVERIFIED unless the benchmark's explicit outcome witness passes.

## Authority boundary

S2 owns measurement contract, route/case identity binding, pre-execution receipts, and validation of
later execution observations.

It does not own provider authorization, browser effects, Runtime Job truth, or task semantics.
Effectful route adapters remain separate replaceable modules. Runtime remains the physical execution
truth. Outcome witnesses remain explicit task-domain evidence.
