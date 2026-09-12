# Ordivon Distribution v2

Greenfield, external-first Distribution control plane. This repository intentionally does **not** copy provider capability catalogs, OAuth scope matrices, schedulers, file-transfer engines, package registries, rollout controllers, or attestation formats into Ordivon.

## R6 architecture

```text
prepared artifact / payload
        ↓
exact intent + payload digest
        ↓
provider capability observation
        ↓
EffectApprovalRequest (non-authoritative)
        ↓
Runtime input.ingest -> distribution-effect-approvals
        ↓
workspace.execBound immutable approval bytes
        ↓
narrow EffectAuthority translator
        ↓
OPA admission
        ↓
provider execution substrate
        ↓
provider object identity
        ↓
provider-native readback
        ↓
reconciliation / safe retry
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

R4 added the canonical digest of `effect.payload` to occurrence identity and separated provider observation from exact-effect approval. GitHub provider capability is observed through the mature GitHub CLI/API rather than a local provider catalog. `EffectApprovalRequest` is explicitly non-authoritative.

## R5 real carrier coverage

R5 changed the success criterion: an external project's feature matrix is not counted as Ordivon-local carrier coverage. GitHub provider-native read/readback is real; rclone remote, Postiz social, and YouTube upload remain blocked on actual identities/configuration.

## R6 exact approval ingress is live

Production Runtime and Workstation now contain a dedicated operator-owned `distribution-effect-approvals` InputAuthority. Runtime ingress is explicitly enabled for that authority in addition to the pre-existing artifact ingress. The authority root is `/var/lib/ordivon/distribution-effect-approvals`, mode `0750`, and was empty immediately after rollout.

The repository now contains a narrow `produce_effect_authority.py` translator. It accepts approval bytes only through Runtime `ORDIVON_INPUT_ROOT`, validates the explicit approval schema, requires the exact current occurrence, enforces approval validity windows, and emits an EffectAuthority bound to provider/account/effect/occurrence. Ambient approval paths are rejected. Synthetic tests prove that payload mutation, wrong occurrence, and expired approval all fail closed.

This rollout prepares the authority path; it does **not** create an approval. The current `create_issue` candidate therefore remains `NOT_ADMITTED`, and no GitHub write has been performed.

### Current carrier standing

- GitHub: authenticated read/provider observation/readback proven; actual write still requires a real ingested exact approval.
- rclone: local transfer/check proven; no configured remote or compatible R2/S3 credential observed.
- Postiz: public API surface reachable; no authenticated integration observed.
- YouTube: no OAuth upload identity observed.

See `docs/R6-APPROVAL-INGRESS.md` and `evidence/r6-validation-20260912.json`.

## Activated external substrate

- Open Policy Agent: policy decision point; no Python clone of the admission state machine.
- GitHub CLI/API or provider-native APIs: provider observation/readback; no internal provider catalog.
- Postiz: social/content dispatch aggregator; not counted as local coverage until authenticated integrations exist.
- OpenAPI Generator: generated clients for provider-native APIs where a useful OpenAPI document exists.
- rclone: file/object/cloud transfer substrate; local mechanics proven, remote coverage pending real configuration.
- Existing Ordivon Temporal/Runtime + Workstation ingress: durable orchestration, immutable-input authority, and exact external-file ingress remain shared infrastructure owners.

See `external-lock.json`, `composition-v1.json`, `contracts/`, `policy/`, `docs/`, and `scripts/test-all.sh`.
## R7 Artifact release-standing handoff

Artifact-backed distribution intents now bind Artifact SHA-256, `releaseReady`, `trustStanding`, and source lineage into occurrence identity. Effectful publication is rejected with `artifact_release_not_ready` unless `releaseReady=true`; release readiness never replaces exact user EffectAuthority. The real post-retirement Artifact development package was evaluated through this gate with `externalEffectPerformed=false`. See `docs/R7-ARTIFACT-HANDOFF.md`.
