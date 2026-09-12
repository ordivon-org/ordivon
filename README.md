# Ordivon Distribution v2

Greenfield, external-first Distribution control plane. This repository intentionally does **not** copy provider capability catalogs, OAuth scope matrices, schedulers, file-transfer engines, package registries, rollout controllers, or attestation formats into Ordivon.

## R5 architecture

```text
prepared artifact / payload
        ↓
exact intent + payload digest
        ↓
provider capability observation
        ↓
exact effect authority
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

R5 changes the success criterion: an external project's feature matrix is not counted as Ordivon-local carrier coverage. A lane is covered only when the current environment can traverse identity/configuration, admission, provider execution or observation, provider object identity, and provider-native readback.

### GitHub provider-native

GitHub is the first real carrier lane with provider-native read/readback proof. The environment has authenticated repository capability and can independently read a real GitHub issue by provider object number. The live readback test verifies stable `id`, `node_id`, and `number`, which is the acceptance pattern for a future bounded write. The proposed `create_issue` effect remains blocked by the exact-effect authority gate; no GitHub write has been performed.

### rclone file/object/cloud

`rclone` is installed and local copy/check is proven, but the current configuration exposes zero remotes. A Cloudflare account API-token file exists, but no rclone-compatible R2/S3 access-key/secret configuration was observed. Therefore real remote object transfer is not yet covered.

### Postiz social

The Postiz public API surface is reachable and correctly requires authorization. No local Postiz API credential, connected integration, or local Postiz service was observed. Postiz upstream platform breadth is substrate capability only and does not count as local Distribution coverage until an authenticated integration and bounded publish/readback episode succeed.

### YouTube native

No YouTube OAuth upload identity was observed. Existing `google*.json` files are generic provider/model API-key configurations rather than installed/web OAuth credentials suitable for YouTube upload. Real video upload/readback is therefore not yet covered.

See `docs/R5-CARRIER-COVERAGE.md` and `evidence/r5-carrier-coverage-20260912.json`.

## Activated external substrate

- Open Policy Agent: policy decision point; no Python clone of the admission state machine.
- GitHub CLI/API or provider-native APIs: provider observation/readback; no internal provider catalog.
- Postiz: social/content dispatch aggregator; not counted as local coverage until authenticated integrations exist.
- OpenAPI Generator: generated clients for provider-native APIs where a useful OpenAPI document exists.
- rclone: file/object/cloud transfer substrate; local mechanics proven, remote coverage pending real configuration.
- Existing Ordivon Temporal/Runtime: durable orchestration, immutable-input authority, and optional external-file ingress remain one owner.

See `external-lock.json`, `composition-v1.json`, `contracts/`, `policy/`, `docs/`, and `scripts/test-all.sh`.
