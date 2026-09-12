# Consequence verification differential

Security v2 preserves the old Security invariant that authorization, execution, observation, and verified consequence are distinct facts without migrating the old Range event system or backend implementations.

The v2 consequence policy derives standing from three externally produced inputs:

1. an admitted effect record;
2. an executor receipt bound to the same request identity;
3. a later authoritative observation whose observed state digest matches the executor's post-write state digest.

The executor receipt is never sufficient to establish world truth. A receipt that self-claims `worldEffectVerified=true` is rejected by the v2 policy rather than trusted. A sensor-plane observation is also insufficient for this consumer; the old AF3 oracle requires a separate `world-truth` observation.

No persistent Ordivon consequence state machine is required. Standing is derived from currently supplied evidence:

- `NOT_ADMITTED`
- `ADMITTED_NOT_EXECUTED`
- `EXECUTION_BINDING_ERROR`
- `EXECUTION_RECEIPT_INVALID`
- `EXECUTED_UNVERIFIED`
- `OBSERVATION_NOT_AUTHORITATIVE`
- `CONSEQUENCE_MISMATCH`
- `VERIFIED_CONSEQUENCE`

The differential uses the frozen old AF3 local-service implementation as the oracle. It has no external network, model call, or VM dependency and therefore isolates the semantic distinction cleanly.

## R1 closure — 2026-09-12

The differential was executed against old Security revision `5e3142b92fc5aed3259295b63c0300f01b45e04a` using the old AF3 local-service implementation as the oracle.

All old semantic invariants were observed directly:

- admission did not mutate the world;
- the executor receipt reported `effectExecuted=true` while explicitly retaining `worldEffectVerified=false`;
- the consequence observation did not exist in the Range event view before backend polling;
- the later observation arrived on the `world-truth` plane;
- executor post-write state digest equaled the observed state digest;
- the observed state digest equaled the canonical final-state digest;
- rejected admission could not be executed by the old backend.

The v2 policy then passed all eight stage/falsification cases: admission-only, execution-only, verified consequence, rejected admission, self-verifying executor receipt, non-authoritative sensor observation, state-digest mismatch, and request-identity mismatch.

Final result: `passed=true`, and the v2 `verifiedConsequence` payload exactly equaled the old world-truth observation payload.

This closes the third old->v2 differential without migrating AF3, `RangeSession.poll_backend()`, the old Range event log, or a persistent consequence workflow engine.
