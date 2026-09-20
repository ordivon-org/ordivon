# Effect admission differential

Security v2 does not migrate the old `RangeSession` runtime, backend lifecycle, event recorder, checkpoint logic, or VM mechanics merely to preserve effect admission semantics.

The residual contract is split deliberately:

- OPA/Rego owns the stateless authorization decision over exact actor, authority, zone, and capability bindings;
- `ReplayBinding` owns only request-identity immutability: exact replay returns the original admission; reuse of the same request ID with changed content fails closed;
- neither component executes the requested effect.

`differential_effect_admission.py` executes the frozen old Security implementation as the oracle and compares the complete old admission record against the v2 OPA decision for admitted, unknown actor, unknown authority, authority/actor mismatch, wrong zone, and wrong capability cases. It separately compares exact-replay and changed-content replay behavior.

The goal is semantic equivalence with a much smaller ownership surface, not source-code similarity.

## R1 closure — 2026-09-12

The differential was executed against old Security revision `5e3142b92fc5aed3259295b63c0300f01b45e04a` using the old repository's own Python 3.12 environment and implementation as the oracle.

All six cases matched the complete old `RangeEffectAdmission.to_dict()` record exactly:

- admitted;
- unknown actor;
- unknown authority;
- authority/actor mismatch;
- zone not granted;
- capability not granted.

For every case, exact replay returned the original admission and reuse of the same request identity with changed request content failed closed in both implementations.

Result: `passed=true` for all decision and replay comparisons.

This establishes a migration boundary: the old `RangeSession.admit_effect()` semantics are preserved without migrating `RangeSession`, backend lifecycle, Range event recording, checkpointing, VM control, or execution mechanics. Admission remains permission only; it does not execute the effect.
