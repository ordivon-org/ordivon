# Consequence verification differential

Security v2 distinguishes admission, execution, reported observation content, and independently authenticated consequence. The September 2026 differential was a historically scoped *local-backend* content/readback check, not proof that an arbitrary later `world-truth` JSON field establishes independent source authenticity.

The v2 consequence policy derives standing from three externally produced inputs:

1. an admitted effect record;
2. an executor receipt bound to the same request identity;
3. a later caller-supplied observation claiming the `world-truth` plane whose observed state digest matches the executor's post-write state digest.

The executor receipt is never sufficient to establish world truth. A receipt that self-claims `worldEffectVerified=true` is rejected. A sensor-plane observation is insufficient; even a `world-truth`-labeled observation is **untrusted until a natural Owner independently authenticates the observer and observation-to-effect binding**. Neither OPA nor the original local differential authenticates this source.

No persistent Ordivon consequence state machine is required. Standing is derived from currently supplied evidence:

- `NOT_ADMITTED`
- `ADMITTED_NOT_EXECUTED`
- `EXECUTION_BINDING_ERROR`
- `EXECUTION_RECEIPT_INVALID`
- `EXECUTED_UNVERIFIED`
- `OBSERVATION_NOT_AUTHORITATIVE`
- `CONSEQUENCE_MISMATCH`
- `CONTENT_MATCHED_UNVERIFIED` — content and claim shape agree, but observation source is not authenticated; `verifiedConsequence` remains `null`

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

**Historical result (2026-09-12 only):** `passed=true`, and that then-current v2 policy returned the old world-truth observation payload as `verifiedConsequence`. This is a dated oracle outcome, not a valid present-day proof of independent world observation.

The current `differential_consequence_verification.py` retains the eight historical source-behavior cases but now expects the safe, weaker `CONTENT_MATCHED_UNVERIFIED` outcome. It must never promote a signed/unsigned, self-asserted observation field into world truth. The source retains no independent world observer or durable consequence workflow engine.

## 2026-11-08 proof/refinement boundary

A native OPA counterexample was replayed: a caller-generated observation with `plane="world-truth"` and an equal SHA-256 digest previously yielded `VERIFIED_CONSEQUENCE`, `observationAuthoritative=true` without any independent observer. This is an unsound specification-to-evidence promotion.

The Security policy now checks the **complete SHA-256 syntax** for both receipt and observation and reports only `CONTENT_MATCHED_UNVERIFIED`; its `observationAuthoritative` flag remains `false` and `verifiedConsequence` is always `null`. Rego verifies *input-content relationships*, not origin authenticity.

The **existing** formal Lean provider in `tools/formal` checks `formal/ConsequenceEvidence.lean`, which proves (1) a content match is insufficient for authenticated independent consequence, (2) genuine verification requires source authenticity and independence, and (3) absence of either source premise blocks verification. The model is not a proof of the Rego interpreter, parsing, caller provenance, deployed origin, or physical effects. Native OPA policy checks form the implementation comparison; they are not a universal Rego proof.

Before any future `VERIFIED_CONSEQUENCE` can be added, a natural Owner must produce an independently authenticated observation, a source-trust assertion verified outside caller-controlled fields, a request/effect/subject binding and an actual consumer readback. Version the public contract and prove refinement before restoring that stronger outcome. This is a bounded, **consumer-dependent** requirement, not a new Security-owned signing service.
