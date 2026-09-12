# Ordivon Distribution v2

Greenfield, external-first Distribution control plane. This repository intentionally does **not** copy provider capability catalogs, OAuth scope matrices, schedulers, file-transfer engines, package registries, rollout controllers, or attestation formats into Ordivon.

## R4 architecture

```text
exact Distribution intent
        |
        +--> effect payload canonical digest
        |
        v
RFC8785 occurrence identity
        |
        +--> mature provider observer (for GitHub: gh api)
        |       ↓ Runtime Job evidence
        |       ↓ consume-only InputAuthority
        |
        +--> exact EffectApprovalRequest
                ↓ NON-AUTHORITATIVE
                ↓ dedicated approval ingress still required
        |
        v
Runtime execBound immutable inputs
        |
        v
OPA admission
        |
        +--> exact effect authority required for write/destructive effects
        |
        v
external execution only after authority
        ↓
provider-native readback
        ↓
reconciliation / safe-retry policy
```

## Residual Ordivon semantics

Only four cross-provider rules are candidates for long-lived ownership here:

1. one exact effect must be bound to one exact intent/artifact/account/payload occurrence;
2. write/destructive external effects require exact user effect authority, independent of reusable provider credentials;
3. local Runtime/HTTP/upload/scheduler success is never provider acceptance;
4. ambiguous external outcomes cannot be blindly retried without provider idempotency or authoritative absence evidence.

`occurrenceRef` is only a reconciliation coordinate. It is **not** provider idempotency, provider acceptance, safe-retry authority, desired-state generation, or proof that any external effect happened.

## R2 authority-bound admission

R2 removed caller-supplied effect classification and boolean authorization from the intent. Before OPA sees an input, the control plane requires JSON Schema conformance, recomputes the RFC 8785 occurrence reference, verifies digest-bound provider observation and exact-effect authority objects, checks exact binding to the same provider/account/effect/occurrence, and rejects stale validity windows.

## R3 Runtime-bound evidence inputs

R3 removed ambient provider/effect-authority file paths. `scripts/admission_bound.py` requires Runtime `ORDIVON_INPUT_ROOT`; `workspace.execBound` freezes exact expected digests into Job-owned read-only `effectiveInputs` under `contained_local`.

R3 also added reconciliation semantics: ambiguous outcomes remain non-retryable until provider idempotency or authoritative absence is proven.

## R4 producer separation and payload binding

R4 adds the canonical digest of `effect.payload` to occurrence identity. Changing a title, body, target parameter, or other effect payload changes the occurrence and invalidates previously bound observations/authority.

Provider observation does not gain another Ordivon framework. For the GitHub lane, the mature GitHub CLI/API is the producer. A Runtime Job executed `gh api` against `ordivon-org/ordivon-runtime`, observed current issue support and authenticated repository capability, and materialized a digest-bound observation for later `execBound` consumption. Even with `admin=true` and `push=true`, the exact `create_issue` intent remained `user_action_required` because no exact effect authority existed.

R4 introduces `EffectApprovalRequest`, which binds the exact occurrence and effect payload but is structurally **not** an `EffectAuthority`. Distribution does not mint its own grant from that request.

Production Runtime already has mature `input.ingest`, but ingress is enabled only for explicitly operator-configured authorities. At the R4 cut, Distribution's evidence authority is consume-only. The next authority-side gate is therefore an Operations-controlled dedicated approval authority/ingress (for example `distribution-effect-approvals`), not reuse of another domain's ingress and not a self-authored Distribution approval service.

No real external write was performed in R4.

See `docs/R4-PRODUCER-SEPARATION.md` and `evidence/r4-validation-20260912.json`.

## Activated external substrate

- Open Policy Agent: policy decision point; no Python clone of the admission state machine.
- GitHub CLI/API or provider-native APIs: current provider observation; no internal provider catalog.
- Postiz: social/content dispatch aggregator; it does not become provider-truth authority.
- OpenAPI Generator: generated clients for provider-native APIs where a useful OpenAPI document exists.
- rclone: file/object/cloud transfer substrate; Ordivon does not reimplement transfer/resume/provider filesystem semantics.
- Existing Ordivon Temporal/Runtime: durable orchestration, immutable-input authority, and optional external-file ingress remain one owner.

See `external-lock.json`, `composition-v1.json`, `contracts/`, `policy/`, `docs/`, and `scripts/test-all.sh`.
