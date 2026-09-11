# Ordivon Distribution v2

Greenfield, external-first Distribution control plane. This repository intentionally does **not** copy provider capability catalogs, OAuth scope matrices, schedulers, file-transfer engines, package registries, rollout controllers, or attestation formats into Ordivon.

## R3 architecture

```text
exact Distribution intent
        |
        v
schema + RFC8785 occurrence verification
        |
        +--> Runtime execBound named InputAuthority
        |       +--> bound provider observation
        |       +--> bound exact-effect authority when present
        |
        v
OPA policy/admission
        |
        +--> user/provider handoff when blocked
        |
        v
existing Temporal/Runtime orchestration
        |
        +--> Postiz       social/content dispatch
        +--> rclone       file/object/cloud transfer
        +--> generated    provider-native OpenAPI clients
        +--> native thin  providers not covered by mature aggregators
        |
        v
provider-native observation/read-back
        |
        v
reconciliation policy
        +--> confirmed
        +--> reconcile required
        +--> retry only with provider idempotency or authoritative absence proof
```

## Residual Ordivon semantics

Only four cross-provider rules are candidates for long-lived ownership here:

1. one exact effect must be bound to one exact intent/artifact/account occurrence;
2. write/destructive external effects require exact user effect authority, independent of reusable provider credentials;
3. local Runtime/HTTP/upload/scheduler success is never provider acceptance;
4. provider-authoritative observations are handed to existing Artifact/Assurance/Feedback owners rather than self-attested here.

`occurrenceRef` is only a reconciliation coordinate. It is **not** provider idempotency, provider acceptance, safe-retry authority, desired-state generation, or proof that any external effect happened.

## R2 authority-bound admission

R2 removed caller-supplied effect classification and boolean authorization from the intent. Before OPA sees an input, the control plane requires JSON Schema conformance, recomputes the RFC 8785 occurrence reference, verifies digest-bound provider observation and exact-effect authority objects, checks exact binding to the same provider/account/effect/occurrence, and rejects stale validity windows.

## R3 Runtime-bound evidence inputs

R3 no longer accepts provider/effect-authority evidence from an ambient caller path. `scripts/admission_bound.py` requires Runtime `ORDIVON_INPUT_ROOT` and accepts evidence only by relative path beneath that read-only input presentation. Production Runtime now has a dedicated named InputAuthority `distribution-r3-evidence`; `workspace.execBound` freezes the exact expected digest into Job-owned `effectiveInputs` under the `contained_local` profile.

The real GitHub read positive control was replayed this way and remained `preflight_ready`. A separate authenticated GitHub capability observation showed the current credential has repository write capability, but the corresponding `create_issue` intent remained `user_action_required` because there was no bound exact-effect authority. No external write was performed.

R3 also adds minimal reconciliation semantics: ambiguous outcomes cannot be retried merely because local execution failed or readback is absent. Retry is permitted only when normalized bound evidence establishes provider idempotency or authoritative absence; provider acknowledgement followed by authoritative absence escalates to manual review.

See `docs/R3-RUNTIME-BOUND-INPUTS.md` and `evidence/r3-validation-20260911.json`.

## Activated external substrate

- Open Policy Agent: policy decision point; no Python clone of the admission state machine.
- Postiz: social/content dispatch aggregator; it does not become provider-truth authority.
- OpenAPI Generator: generated clients for provider-native APIs where a useful OpenAPI document exists.
- rclone: file/object/cloud transfer substrate; Ordivon does not reimplement transfer/resume/provider filesystem semantics.
- Existing Ordivon Temporal/Runtime: durable orchestration and immutable-input authority remain one owner; Postiz/n8n/Windmill are not promoted into competing global workflow engines.

See `external-lock.json`, `composition-v1.json`, `contracts/`, `policy/`, `docs/`, and `scripts/test-all.sh`.
