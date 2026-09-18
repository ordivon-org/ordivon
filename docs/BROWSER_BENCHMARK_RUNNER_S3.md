# Browser Benchmark Runner S3

## Purpose

BCR-S3 supplies replaceable, effect-capable route adapters after the S2 measurement contract.

It does not move physical execution authority into the benchmark layer. The runner prepares an
exact Runtime execution proposal. A caller with Runtime authority decides whether to admit it.

## Execution graph

    S2 case + exact READY receipt
            |
            v
    S3 run preparation
            |
            +--> PREEXEC_BLOCKED -> no proposal, no effect
            |
            v
    exact route-run request
            |
            v
    Runtime execution proposal
       |                    |
       | local_linux        | windows_native
       v                    v
    Browser Use adapter     Jev adapter
       |                    |
       +------ bounded execution observation ------+
                                                    |
                                                    v
                                          S2 finalize_execution
                                                    |
                                                    v
                                       EXECUTED + explicit witness

No S3 component chooses a fallback route.

## Same executable task

The current benchmark task embeds one bounded inline HTML document in the S2 task identity.

Both routes receive the exact same HTML bytes and must click the exact accessibility target:

- role: button
- name: Complete Benchmark
- success text: BCR_TARGET_OK

The task digest also binds the goal and text witness. Changing fixture HTML, button identity, goal,
success text, or witness changes task identity.

Browser Use already admits data URLs. Jev now admits only bounded data:text/html in addition to
its prior http/https/file schemes; arbitrary data media types remain rejected.

## Route adapters

### Jev Fast / Windows Chrome

The Jev route runs through Runtime windows_native using the pinned Windows Python reported by
Workstation v2. The Harness route-adapter script and request are referenced through the WSL UNC
namespace, so there is no second C: copy of Harness source.

The Runtime proposal carries only non-secret launch configuration such as PYTHONUTF8, dedicated
Chrome path/profile, and CDP port. Secret values are never serialized into the proposal. Required
secret names are reported separately.

The route adapter delegates browser decisions/actions to Jev, then maps Jev's explicit witness and
bounded receipt into S2 metrics.

### Browser Use / Browserless

The Browser Use route runs on local_linux. It uses the existing structured Browser Use adapter and
the generic browser-agent-* Browserless pool.

The fixed program is:

1. attach/bootstrap the existing Browserless endpoint;
2. open the benchmark data URL;
3. observe structured accessibility affordances;
4. require exactly one target matching the bound role and name;
5. click that exact indexed affordance;
6. observe again and evaluate the bound success text;
7. close the benchmark session.

It does not invoke an LLM. modelRequestCount=0 is therefore an observed property for this route.

## Readiness races

S2 READY is necessary but not sufficient to claim execution.

If a route loses a prerequisite after preflight but before the benchmark effect fence, the route
adapter returns PRE_EFFECT_ABORTED. S2 does not finalize that run as EXECUTED.

Once an effect may have occurred, failure/ambiguity is retained as an execution observation with an
UNVERIFIED or FAIL witness rather than rewritten as a safe retry.

## Runtime proposal

browser_benchmark_runner.py prepare emits an exact proposal with:

- execution target/profile;
- executable;
- arguments;
- non-secret environment;
- required secret environment names;
- adapter-script and request-file digests;
- output/timeout bounds.

The proposal is not Runtime admission, task authorization, or semantic success.

## Measurement interpretation

This first S3 suite is a route-execution benchmark, not an intelligence leaderboard.

Jev is a provider-internal decision executor. Browser Use is currently a caller-directed structured
executor. The benchmark can compare whether each route completes the same fixed task, its observed
latency/actions, failure modes, and telemetry coverage. It must not interpret those measurements as
a fair comparison of model intelligence or general browser-agent quality.

## Current live standing — 2026-09-18

Live preparation on the current machine remains:

- Jev: PREEXEC_BLOCKED / CREDENTIAL_MISSING / TYPESAFE_API_KEY;
- Browser Use: PREEXEC_BLOCKED / POLICY_DISABLED / browser-agent-21.

Both live preparations emitted executionProposal=null and effectsExecuted=false.

Separately, a no-effect Windows-native probe proved that the pinned Windows Python can load the S3
route adapter directly through its WSL UNC path. The cross-target source seam is therefore
materialized without duplicating Harness source.
