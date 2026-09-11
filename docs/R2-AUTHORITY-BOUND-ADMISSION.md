# Distribution v2 R2 — Authority-Bound Admission

R2 continues the independent greenfield Distribution v2. It does not patch or migrate the legacy `ordivon-media` implementation.

## Hard gates added

1. Distribution intent is validated against JSON Schema before policy evaluation.
2. `occurrenceRef` is recomputed from RFC 8785 canonical JSON and must exactly match the intent.
3. Caller-supplied `effect.mode` is removed from the intent. Effect classification comes from the bound provider observation.
4. Caller-supplied boolean user authorization is removed. Write/destructive admission consumes a separately bound exact-effect authority object.
5. Provider observations are digest-bound and must bind the same occurrence/provider/account/adapter/effect as the intent.
6. Provider observations and effect-authority objects have explicit validity windows and fail closed when stale or expired.
7. OPA receives only the normalized result of these gates; it continues to contain no provider catalog or OAuth matrix.

## Important non-claim

R2 proves local semantic binding and fail-closed admission. The `sourceRef` fields are not yet cryptographic or Runtime-native proof that the observation/authority was produced by the named external authority. Provenance/authority resolution therefore remains the next trust-boundary gate before any real external write is admitted.
