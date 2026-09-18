# Browser Benchmark Runtime Handoff S4

## Purpose

BCR-S4 is the boundary between an S3 execution proposal and Runtime's physical Job/Attempt truth.

It does not call Runtime and does not store provider secret values. It produces a deterministic
workspace.exec admission template for a caller that already holds Runtime authority, then reconciles
Runtime's exact physical observation with the S3 route-run result.

The core invariant is:

    Runtime process SUCCEEDED
        != route benchmark EXECUTED
        != semantic outcome PASS

Each equality requires independent evidence.

## Readiness observation isolation

An explicit route request now performs static eligibility checks before dynamic readiness probing.

When explicitRouteId is present:

1. only that exact route is admitted to the candidate set when providerFlow matches;
2. sibling routes are not probed, even when they share the same providerFlow;
3. a statically incompatible exact route is reported as NOT_PROBED_STATIC_INCOMPATIBLE without
   executing its readiness probe;
4. a providerFlow mismatch produces no dynamic route probe.

This prevents a slow, unhealthy, credential-blocked, or side-effectful sibling readiness source from
contaminating an exact-route benchmark preparation. Non-explicit routing retains multi-route
readiness observation because fallback selection genuinely depends on those candidates.

## Admission template

A PREEXEC_BLOCKED S3 preparation produces no Runtime operation and no execution object.

A READY_FOR_RUNTIME preparation produces an ADMISSION_TEMPLATE_READY object containing:

- deterministic clientRequestId;
- exact workspaceId;
- executable, args, cwd, execution target/profile and limits;
- non-secret environment only;
- names of required secret environment variables;
- exact preparation/proposal/request identities.

Secret values are never serialized by S4. Their names remain a caller-side binding requirement.

### Linux source continuity

For local_linux, S4 converts S3's adapter-script and request-file digests into exact Runtime
hostDependencies. Runtime therefore binds those two files into operation identity and witnesses their
host-namespace path/digest continuity through the Attempt.

This is Runtime's documented partial host-path continuity contract, not a complete environment
snapshot.

### Windows source continuity

The current windows_native provider does not support hostDependencies. S4 therefore marks Windows
source continuity as:

    PROPOSAL_DIGEST_ONLY_NO_WINDOWS_HOST_DEPENDENCY_WITNESS

The proposal still binds adapter/request digests and the Windows executable is Runtime-owned, but
the UNC Harness script/request paths do not yet receive the Linux-equivalent Runtime host dependency
witness. This is an explicit remaining hardening gap before a strong Windows prospective result.

## Runtime reconciliation

S4 recognizes these physical/domain standings:

| S4 standing | Meaning |
| --- | --- |
| PREEXEC_BLOCKED | no Runtime admission should exist |
| RUNTIME_RECONCILIATION_REQUIRED | Runtime has not mechanically converged |
| RUNTIME_FAILED | committed terminal Runtime execution did not succeed |
| RUNTIME_RESULT_UNRESOLVED | physical state/result cannot be bound to one route result |
| PRE_EFFECT_ABORTED | S3 proved no benchmark provider effect was admitted |
| BENCHMARK_EXECUTED | exact S3 route result and S2 EXECUTED receipt were bound |

Semantic standing remains separate:

- NOT_EXECUTED
- UNVERIFIED
- PASS
- FAIL

Runtime must report semanticCompletionEvaluated=false. Any Runtime observation that claims domain
semantic completion is rejected.

A committed Runtime executionDisposition=succeeded requires exitCode=0. Even then, no semantic
conclusion is drawn unless an exact S3 route-run result is supplied and validates against the same
runId, routeRunRequestDigest, caseDigest and routeId.

## Route result continuity

S3 route-run results now carry their own resultDigest. The S3 Runtime proposal also carries runId and
routeRunRequestDigest.

S4 therefore validates this chain:

    preparationDigest
      -> proposalDigest
      -> routeRunRequestDigest
      -> route result resultDigest
      -> benchmarkReceipt receiptDigest
      -> explicit outcomeWitness

A mismatch at any link fails closed.

## Current live standing — 2026-09-18

The current machine still produces no benchmark Runtime admission:

- Jev: PREEXEC_BLOCKED because TYPESAFE_API_KEY is absent;
- Browser Use: PREEXEC_BLOCKED because browser-agent-21 is operator-masked.

For both routes, S4 therefore emits a blocked admission template with runtimeOperation=null and
execution=null, and reconciliation reports semantic NOT_EXECUTED.

No credential policy or operator mask was changed to manufacture A/B data.

## Next gate

The architecture is ready for a prospective paired run only when each exact route independently
reaches READY under its normal policy.

The next experiment must not treat enabling a route specifically for the benchmark as evidence about
ordinary route readiness. Windows Jev should also close or explicitly accept the weaker UNC source
continuity boundary before a strong reproducibility claim.
