# Ordivon Distribution v2

Greenfield, external-first Distribution control plane. This repository intentionally does **not** copy provider capability catalogs, OAuth scope matrices, schedulers, file-transfer engines, package registries, rollout controllers, or attestation formats into Ordivon.

## R2 architecture

```text
exact Distribution intent
        |
        v
schema + RFC8785 occurrence verification
        |
        +--> bound provider observation
        +--> bound exact-effect authority
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
CloudEvents / in-toto / Sigstore / SLSA boundary when the concrete lane needs them
```

## Residual Ordivon semantics

Only four cross-provider rules are candidates for long-lived ownership here:

1. one exact effect must be bound to one exact intent/artifact/account occurrence;
2. write/destructive external effects require exact user effect authority, independent of reusable provider credentials;
3. local Runtime/HTTP/upload/scheduler success is never provider acceptance;
4. provider-authoritative observations are handed to existing Artifact/Assurance/Feedback owners rather than self-attested here.

`occurrenceRef` is only a reconciliation coordinate. It is **not** provider idempotency, provider acceptance, safe-retry authority, desired-state generation, or proof that any external effect happened.

## R2 authority-bound admission

R2 removes caller-supplied effect classification and boolean authorization from the intent. Before OPA sees an input, the control plane now requires JSON Schema conformance, recomputes the RFC 8785 occurrence reference, verifies digest-bound provider observation and exact-effect authority objects, checks exact binding to the same provider/account/effect/occurrence, and rejects stale validity windows.

This is a local semantic proof only. `sourceRef` is not yet Runtime-native provenance of the named authority, so no real external write is admitted by this repository on the basis of R2 alone. See `docs/R2-AUTHORITY-BOUND-ADMISSION.md`.

## Activated external substrate

- Open Policy Agent: policy decision point; no Python clone of the admission state machine.
- Postiz: social/content dispatch aggregator; it does not become provider-truth authority.
- OpenAPI Generator: generated clients for provider-native APIs where a useful OpenAPI document exists.
- rclone: file/object/cloud transfer substrate; Ordivon does not reimplement transfer/resume/provider filesystem semantics.
- Existing Ordivon Temporal/Runtime: durable orchestration remains one owner; Postiz/n8n/Windmill are not promoted into competing global workflow engines.

See `external-lock.json`, `composition-v1.json`, `contracts/`, `policy/`, `docs/`, and `scripts/test-all.sh`.
