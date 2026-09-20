# Ordivon Agent Service — Control Stability R1

Date: 2026-09-18
Status: **DYNAMIC PERTURBATION COMPLETE / NO PRODUCTION CONTROL-LAW PROMOTION YET**

Analyzed implementation: `0721009237365ea61cd975bd187be5171f1dcd52` (Agent Service R14)
Historical experiment runner at acceptance time: `scripts/run_agent_service_control_stability_r1.py` (preserved in Git history)
Current regression support: `tests/agent_service_control_stability_support.py`
Current regression tests: `tests/test_agent_service_control_stability.py`
Evidence: `evidence/analysis/agent-service-control-stability-r1.json`

## One-sentence result

R14 is strong at execution ownership, exact failover replay, historical-success fencing, and credential freshness, but dynamic experiments expose three unresolved control-system gaps: placement observations lack freshness coordinates, the placement loop has no recovery damping, and failover does not model common-mode failure domains.

## Experiment design

The experiment intentionally distinguishes:

```text
CONVERGES
FAIL_CLOSED
CONTRACT_DEPENDENCY_EXPOSED
OSCILLATION_EXPOSED
STALE_OBSERVATION_EXPOSED
FAILURE_DOMAIN_UNMODELED_EXPOSED
```

An exposed scenario is not automatically a production bug. It means the current control contract does not contain the tested stabilizer or coordinate.

Nine deterministic perturbations are run against the frozen R14 implementation.

## Results

### S1 — Placement flap

Input observations:

```text
READY
UNKNOWN
READY
UNKNOWN
READY
```

Observed AgentInstance states:

```text
READY
PROVISIONING
READY
PROVISIONING
READY
```

Events:

```text
AGENT_BIRTH_REQUESTED
AGENT_READY
AGENT_READINESS_LOST
AGENT_READY
AGENT_READINESS_LOST
AGENT_READY
```

Classification:

```text
OSCILLATION_EXPOSED
```

The current loop maps every observed edge immediately into semantic readiness.

This is not automatically wrong: immediate downgrade on uncertainty is conservative. The dangerous conclusion would be to add generic symmetric hysteresis immediately.

## S2 — Late stale READY

Perturbation:

```text
fresh READY
fresh UNKNOWN
late stale READY
```

Current ProviderObservation carries:

```text
placement_id
state
evidence_ref
```

It has no sequence, generation or observed-at coordinate.

Result:

```text
after fresh UNKNOWN      -> PROVISIONING
after late stale READY   -> READY
```

Classification:

```text
STALE_OBSERVATION_EXPOSED
```

The controller cannot distinguish recovery from reordered stale evidence.

### Natural provider evidence already exists

The Harness materialization ledger already stores:

```text
effect_generation
updated_at_ms
```

in `sqlite_conversation_materializer.py`.

But `campaign_birth.py::campaign_census` projects only:

```text
agentId
effectId
materializationStanding
providerResource
blindResendForbidden
```

and discards the monotonic/freshness coordinates.

Then `AgentAutomationCarrierAdapter.observe` maps census into a ProviderObservation that also has no freshness coordinate.

Therefore the highest-value next repair is **freshness conservation**, not generic damping.

## S3 — Runtime response loss with exact replay

The simulated Runtime commits one external Job, then loses the response.

Agent Service retries using the same durable Assignment clientRequestId.

When Runtime honors exact replay:

```text
submit calls       2
clientRequestId    same
external Jobs      1
bound Job          original Job
Task               RUNNING
```

Classification:

```text
CONVERGES
```

## S4 — Runtime violates exact replay

The same response-loss sequence is run against a deliberately broken Runtime adapter.

It creates:

```text
first external Job -> response lost
second external Job -> returned
```

Agent Service binds the second Job and cannot discover the first.

Classification:

```text
CONTRACT_DEPENDENCY_EXPOSED
```

This is not evidence that the current Ordivon Runtime is broken. It proves that Agent Service's local durability depends on the Runtime's exact-clientRequest replay contract.

### Live Runtime dogfood

The real local Runtime was called twice with the same clientRequestId and identical operation.

Both responses returned:

```text
same JobId
same AttemptId
same operationDigest
```

Therefore the natural local Runtime currently satisfies this dependency.

The correct response is not a second Agent Service Runtime ledger.

## S5 — Credential proof expires between calls

First request:

```text
current IdentityProof
-> resolve transient secret material
-> Authorization header
```

Then the proof is expired before a second call.

Result:

```text
second call blocked
external material provider not invoked again
```

Classification:

```text
FAIL_CLOSED
```

This loop is currently well aligned.

## S6 — Local and remote controllers race for one Task

A local Assignment claims the Task first.

A remote Binding then attempts delivery.

Result:

```text
TaskExecutionClaim = LOCAL_ASSIGNMENT
remote DeliveryAdapter.send calls = 0
remote delivery blocked
```

Classification:

```text
FAIL_CLOSED
```

This validates K2 — one current execution owner — under a controller-overlap perturbation.

## S7 — Exact failover replay

The same failover request is submitted twice.

Result:

```text
same transfer receipt
quiescence adapter invoked once
replay-safety adapter invoked once
claim remains fallback owner
```

Classification:

```text
CONVERGES
```

R12's durable sub-request identities prevent retry multiplication inside Agent Service.

## S8 — Shared failure-domain fallback

Primary:

```text
A2A
https://shared-provider.example.test/.../a2a
```

Fallback:

```text
MCP
https://shared-provider.example.test/.../mcp
```

The source is safely quiesced and replay is safe, so current R12 admits the claim transfer.

But TransportBinding has no failure-domain coordinate.

Classification:

```text
FAILURE_DOMAIN_UNMODELED_EXPOSED
```

This is not a duplicate-effect safety violation. It is a resilience-quality gap: the fallback can share the same backend/common-mode failure.

A future failure-domain model should be derived first. Same-host must not be turned into a universal ban because providers can have different isolation semantics behind one hostname and the opposite can also be true.

## S9 — Remote success followed by failure regression

Provider history:

```text
terminal success
then terminal failure
```

Current failover scans historical observations.

Result:

```text
historical success retained
failover blocked
quiescence adapter calls = 0
replay-safety calls = 0
```

Classification:

```text
FAIL_CLOSED
```

A later regressed status cannot erase evidence that a prior execution may have completed or produced effects.

## Control-theory interpretation

### Placement loop

Current law is effectively high-gain / no-memory:

```text
latest observation
-> immediate readiness transition
```

The first repair should add ordering/freshness evidence.

Only after that should recovery damping be experimented with.

A plausible asymmetric control policy is:

```text
READY -> uncertain
  immediate conservative downgrade

uncertain -> READY
  require fresh monotonic observation
  optionally require stable dwell / repeated confirmation
```

This preserves conservative failure handling while reducing stale-recovery and flap-induced re-admission.

### Runtime loop

The Agent Service side already supplies a stable replay identity.

The actual exactly-once physical admission property belongs to Runtime.

That is the correct authority boundary.

### Failover loop

R12 controls semantic/effect safety well.

Its remaining weakness is not replay correctness but **fallback independence**.

The next reliability question is:

```text
safe to replay?
AND
likely independent of the failed source?
```

Those are separate questions and should remain separate.

## STPA implications

The experiments provide concrete evidence for previously derived hazards:

- H1 retry multiplication: bounded locally by execution claim and exact request identities, but still dependent on natural provider replay contracts.
- H4 quiescence vs replay safety: current R12 remains safe.
- H6 interacting controllers / oscillation: placement flap demonstrates a real undamped loop.
- Common-mode fallback: not yet a duplicate-effect loss, but can defeat recovery goals.

## Recommended next order

### 1. Freshness conservation — highest confidence

Propagate natural provider freshness/generation coordinates through:

```text
Harness materialization ledger
-> campaign census
-> AgentAutomationCarrierAdapter
-> ProviderObservation
-> DesiredPlacement observation gate
```

A stale observation must not move the control state forward.

### 2. Asymmetric readiness damping experiment

Only after freshness exists:

```text
downgrade immediately on uncertainty
recover only from fresh stable READY evidence
```

Do not install symmetric hysteresis blindly.

### 3. Failure-domain derivation

Prototype derived evidence such as:

```text
provider/backend
account/principal
credential issuer
host/node
network path
region
model/provider family
```

and measure whether it changes actual failover choices.

Do not create a universal failure-domain database from one experiment.

### 4. Controller-ownership admission

Before adding another retry/recovery loop, require:

```text
effect identity
natural retry owner
maximum retry/backoff policy
observation freshness requirement
cancellation owner
interaction with Agent Service failover
```

## Promotion decision

Control Stability R1 does **not** modify production R14 semantics.

It promotes only evidence:

```text
freshness loss is reproducible              YES
placement oscillation is reproducible       YES
Runtime exact-replay dependency is real     YES
local Runtime satisfies exact replay        YES
credential expiry fail-closed               YES
single execution-owner fencing              YES
failover exact replay                        YES
shared failure-domain gap                   YES
historical-success fencing                   YES
```

The first production change should therefore be a narrowly scoped freshness-preservation design, with its own compatibility and provider-authority review.
